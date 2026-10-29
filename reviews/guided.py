from pathlib import Path

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import FileResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from lxml import etree

from .document_edits import build_document, editing_options, validate_edits
from .models import EditDecision, Event
from .views import authorised_reviews, detail, review_for


def step_url(review, step):
    return reverse("guide", args=[review.pk]) + f"?step={step}"


@login_required
def guide(request, pk, *, draft=None, step=None):
    review = review_for(request.user, pk)
    if review.state != "ready":
        # Keep the user on the same guided URL while extraction/confirmation completes.
        return detail(request, pk)
    findings = list(review.findings.select_related("edit_decision"))
    reviewed = sum(hasattr(f, "edit_decision") for f in findings)
    pending = next(
        (i for i, f in enumerate(findings) if not hasattr(f, "edit_decision")), len(findings)
    )
    try:
        index = int(step if step is not None else request.GET.get("step", pending))
    except ValueError:
        return HttpResponse("Choose a valid review step.", status=400)
    if index < 0 or index > len(findings):
        return HttpResponse("This review step does not exist.", status=404)
    finding = findings[index] if index < len(findings) else None
    decision = getattr(finding, "edit_decision", None) if finding else None
    options = editing_options(finding) if finding else []
    if draft:
        for option in options:
            option["after"] = draft["text"].get(f"after_{option['index']}", option["after"])
            option["selected"] = str(option["index"]) in draft["targets"]
    editable_documents = [d for d in review.documents.all() if d.name.lower().endswith(".docx")]
    return render(
        request,
        "reviews/guide.html",
        {
            "review": review,
            "findings": findings,
            "finding": finding,
            "decision": decision,
            "options": options,
            "draft_note": draft["note"] if draft else None,
            "index": index,
            "step_number": index + 1,
            "total": len(findings),
            "reviewed": reviewed,
            "pending": pending,
            "previous": max(0, index - 1),
            "next": min(index + 1, len(findings)),
            "progress": round(100 * reviewed / len(findings)) if findings else 100,
            "done": reviewed == len(findings),
            "approved": review.finalised_revision == review.revision
            and review.finalised_at is not None,
            "documents": editable_documents,
            "reference_documents": list(review.documents.all()),
            "has_pdf": review.documents.count() != len(editable_documents),
            "can_comment": any(
                o["evidence"]["document_id"] in {d.pk for d in editable_documents} for o in options
            ),
        },
    )


@login_required
@require_POST
def review_change(request, pk, finding_id):
    with transaction.atomic():
        review = get_object_or_404(
            authorised_reviews(request.user).select_for_update(), pk=pk, state="ready"
        )
        finding = get_object_or_404(review.findings, pk=finding_id)
        if request.POST.get("revision") != str(review.revision):
            return HttpResponse(
                "The review changed in another session. Reload before saving this decision.",
                status=409,
            )
        choice = request.POST.get("choice")
        if choice not in ("accepted", "rejected", "commented"):
            return HttpResponse("Choose Accept, Reject, or Add comment.", status=400)
        note = request.POST.get("note", "").strip()
        if len(note) > 2000 or any(ord(c) < 32 and c not in "\n\t" for c in note):
            return HttpResponse(
                "Use a note of at most 2,000 characters without control characters.", status=400
            )
        try:
            etree.Element("note").text = note
        except ValueError:
            return HttpResponse("The note contains a character Word cannot store.", status=400)
        edits = []
        try:
            if choice == "accepted":
                selected = request.POST.getlist("targets")
                if finding.kind == "discrepancy" and len(selected) > 1:
                    raise ValueError(
                        "Choose one passage to update so the two statements are not simply swapped."
                    )
                if not selected or len(set(selected)) != len(selected):
                    raise ValueError(
                        "Select the passage you want to change, then review its replacement wording."
                    )
                options = {str(o["index"]): o for o in editing_options(finding)}
                for key in selected:
                    option = options.get(key)
                    if not option or not option["editable"]:
                        raise ValueError(
                            "Choose an editable DOCX passage or add a Word comment instead."
                        )
                    edits.append(
                        {**option["evidence"], "after": request.POST.get(f"after_{key}", "")}
                    )
                validate_edits(review, edits, excluding=finding.pk)
            if choice == "commented" and not note:
                raise ValueError("Write the question or note you want to leave as a comment.")
        except ValueError as exc:
            # Preserve the submitted wording when a selection or overlapping edit needs attention.
            findings = list(review.findings.all())
            index = next(i for i, f in enumerate(findings) if f.pk == finding.pk)
            messages.error(request, str(exc))
            # Keep source text in this response only; never persist editing drafts in sessions.
            draft = {
                "note": note,
                "targets": request.POST.getlist("targets"),
                "text": {
                    key: value for key, value in request.POST.items() if key.startswith("after_")
                },
            }
            response = guide(request, pk, draft=draft, step=index)
            response.status_code = 400
            return response
        old = EditDecision.objects.filter(finding=finding).values("choice", "edits", "note").first()
        EditDecision.objects.update_or_create(
            finding=finding,
            defaults={"choice": choice, "edits": edits, "note": note, "actor": request.user},
        )
        finding.status = "dismissed" if choice == "rejected" else "action_needed"
        finding.revision += 1
        finding.save(update_fields=["status", "revision"])
        review.revision += 1
        review.finalised_revision, review.finalised_at = None, None
        review.save(update_fields=["revision", "finalised_revision", "finalised_at"])
        Event.objects.create(
            review=review,
            finding=finding,
            actor=request.user,
            kind="edit_decision",
            payload={"before": old, "after": {"choice": choice, "edits": edits, "note": note}},
        )
        index = list(review.findings.values_list("pk", flat=True)).index(finding.pk)
    return redirect(step_url(review, index + 1))


@login_required
@require_POST
def finalise(request, pk):
    with transaction.atomic():
        review = get_object_or_404(
            authorised_reviews(request.user).select_for_update(), pk=pk, state="ready"
        )
        if request.POST.get("revision") != str(review.revision):
            return HttpResponse(
                "The review changed. Reload the final preview before approving.", status=409
            )
        if review.findings.filter(edit_decision__isnull=True).exists():
            return HttpResponse(
                "Review every issue before approving the final documents.", status=409
            )
        if request.POST.get("approval") != "confirmed":
            return HttpResponse(
                "Confirm that you have reviewed the edits and any remaining comments.", status=400
            )
        try:
            validate_edits(review, [])
            # Build every editable copy now, so approval cannot succeed for a broken export.
            for document in review.documents.all():
                if document.name.lower().endswith(".docx"):
                    build_document(review, document)
        except ValueError as exc:
            return HttpResponse(str(exc), status=409)
        if not review.documents.filter(name__iendswith=".docx").exists():
            return HttpResponse(
                "Upload an original DOCX to create an updated document.", status=400
            )
        if review.finalised_revision != review.revision:
            review.finalised_revision, review.finalised_at = review.revision, timezone.now()
            review.save(update_fields=["finalised_revision", "finalised_at"])
            Event.objects.create(
                review=review,
                actor=request.user,
                kind="final_approval",
                payload={"revision": review.revision},
            )
    return redirect(step_url(review, review.findings.count()))


@login_required
def download_document(request, pk, doc_id):
    with transaction.atomic():
        review = get_object_or_404(
            authorised_reviews(request.user).select_for_update(), pk=pk, state="ready"
        )
        document = get_object_or_404(review.documents, pk=doc_id)
        if not document.name.lower().endswith(".docx"):
            return HttpResponse(
                "Use an original DOCX for updated documents and Word review copies.", status=400
            )
        mode = request.GET.get("mode", "updated")
        if mode not in ("updated", "review"):
            return HttpResponse("Choose an updated document or Word review copy.", status=400)
        if mode == "updated" and (
            review.finalised_at is None or review.finalised_revision != review.revision
        ):
            return HttpResponse(
                "Approve the current final version before downloading the updated document.",
                status=409,
            )
        try:
            reference = request.GET.get("reference")
            if reference and (
                mode != "review"
                or reference not in ("protocol", "sap")
                or not review.documents.filter(role=reference).exists()
            ):
                return HttpResponse(
                    "Choose an available reference for a Word review copy.", status=400
                )
            stream = build_document(review, document, tracked=mode == "review", reference=reference)
        except ValueError as exc:
            return HttpResponse(str(exc), status=409)
    filename = f"{Path(document.name).stem}-{mode}.docx"
    return FileResponse(
        stream,
        as_attachment=True,
        filename=filename,
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
