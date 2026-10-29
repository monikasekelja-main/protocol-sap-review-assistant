import hashlib
from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import F
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .discussion import discuss
from .forms import ChatForm, ClarificationForm, DecisionForm, UploadForm
from .models import STATUSES, Document, Event, Finding, Message, Project, Proposal, Review
from .pipeline import scope_signals, source_blocks
from .reports import export_review
from .schemas import Candidate, validate_finding


def authorised_reviews(user):
    return Review.objects.filter(project__members=user, project__deleting=False)


def review_for(user, pk):
    return get_object_or_404(authorised_reviews(user), pk=pk)


def finding_for(review, raw_id):
    if not str(raw_id).isdecimal():
        raise Http404("Finding not found")
    return get_object_or_404(review.findings, pk=raw_id)


def destination(review, finding=None):
    url = reverse("review", args=[review.pk])
    return f"{url}?finding={finding.pk}" if finding else f"{url}?general=1"


@login_required
def home(request):
    return render(
        request,
        "reviews/home.html",
        {
            "projects": Project.objects.filter(members=request.user),
            "deleting": Project.objects.filter(owner=request.user, deleting=True),
            "ai_enabled": settings.AI_ENABLED,
        },
    )


@login_required
@require_POST
def create_project(request):
    name = request.POST.get("name", "").strip()
    if not name or len(name) > 160:
        return HttpResponse("Provide a project name of 1–160 characters.", status=400)
    with transaction.atomic():
        project = Project.objects.create(name=name, owner=request.user)
        project.members.add(request.user)
    return redirect("upload", project.pk)


@login_required
def upload(request, project_id=None):
    project = (
        get_object_or_404(Project, pk=project_id, members=request.user, deleting=False)
        if project_id
        else None
    )
    form = UploadForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        saved = []
        try:
            with transaction.atomic():
                # Serialise with deletion, preventing a new upload from escaping its file inventory.
                if project is None:
                    project = Project.objects.create(
                        name=form.cleaned_data["title"], owner=request.user
                    )
                    project.members.add(request.user)
                else:
                    get_object_or_404(
                        Project.objects.select_for_update(), pk=project.pk, deleting=False
                    )
                review = Review.objects.create(project=project, title=form.cleaned_data["title"])
                for role in ("protocol", "sap"):
                    file = form.cleaned_data.get(role)
                    if not file:
                        continue
                    digest = hashlib.sha256()
                    for chunk in file.chunks():
                        digest.update(chunk)
                    file.seek(0)
                    doc = Document(
                        review=review,
                        role=role,
                        name=Path(file.name).name[:200],
                        sha256=digest.hexdigest(),
                    )
                    doc.file.save(
                        f"{review.id}-{role}{Path(file.name).suffix.lower()}", file, save=False
                    )
                    saved.append(doc.file)
                    doc.save()
            return redirect("guide", review.pk)
        except Exception:
            for file in saved:
                file.delete(save=False)
            raise
    return render(request, "reviews/upload.html", {"form": form, "project": project})


@login_required
def detail(request, pk):
    review = review_for(request.user, pk)
    selected = None
    findings = review.findings.all()
    if request.GET.get("general"):
        selected = None
    elif request.GET.get("finding"):
        selected = finding_for(review, request.GET["finding"])
    else:
        selected = findings.first()
    all_findings = "all" in request.GET
    visible = findings if all_findings else findings[:5]
    blocked, cues = scope_signals(source_blocks(review))
    return render(
        request,
        "reviews/review.html",
        {
            "review": review,
            "findings": visible,
            "finding_count": findings.count(),
            "selected": selected,
            "all_findings": all_findings,
            "decision_history": review.events.filter(kind="decision", finding=selected)
            .select_related("actor")
            .order_by("-id"),
            "decision_form": DecisionForm(
                initial={
                    "status": selected.status,
                    "note": selected.note,
                    "revision": selected.revision,
                }
            )
            if selected
            else None,
            "chat_form": ChatForm(),
            "clarification_form": ClarificationForm(),
            "conversation": review.messages.filter(finding=selected).order_by("id"),
            "proposals": review.proposals.filter(state="pending", finding=selected),
            "clarifications": review.events.filter(kind="clarification").select_related("actor"),
            "cues": cues,
            "blocked": blocked,
            "ai_enabled": settings.AI_ENABLED,
        },
    )


@login_required
@require_POST
def confirm(request, pk):
    with transaction.atomic():
        review = get_object_or_404(
            authorised_reviews(request.user).select_for_update(), pk=pk, state="needs_input"
        )
        if request.POST.get("scope") != "confirmed" or request.POST.get("metadata") != "confirmed":
            messages.error(
                request, "Confirm document metadata and the supported trial scope to continue."
            )
            return redirect("guide", pk)
        for doc in review.documents.all():
            meta = {
                key: request.POST.get(f"{doc.pk}_{key}", "").strip()[:200] or "Unknown"
                for key in ("title", "version", "date")
            }
            doc.metadata = meta
            doc.save(update_fields=["metadata"])
        review.scope_confirmed = review.metadata_confirmed = True
        review.state = "queued"
        review.save(update_fields=["scope_confirmed", "metadata_confirmed", "state"])
        Event.objects.create(
            review=review,
            actor=request.user,
            kind="scope_confirmation",
            payload={
                "scope": "two-arm parallel randomised superiority; continuous fixed-time primary endpoint; English",
                "metadata": "confirmed",
            },
        )
    return redirect("guide", pk)


@login_required
@require_POST
def decision(request, pk, finding_id):
    form = DecisionForm(request.POST)
    if not form.is_valid():
        return HttpResponse("Invalid decision. Reload and try again.", status=400)
    with transaction.atomic():
        review = get_object_or_404(
            authorised_reviews(request.user).select_for_update(), pk=pk, state="ready"
        )
        finding = get_object_or_404(review.findings, pk=finding_id)
        before = {"status": finding.status, "note": finding.note}
        changed = Finding.objects.filter(
            pk=finding.pk, revision=form.cleaned_data["revision"]
        ).update(
            status=form.cleaned_data["status"],
            note=form.cleaned_data["note"],
            revision=F("revision") + 1,
        )
        if not changed:
            return HttpResponse(
                "This finding changed in another session. Reload to compare the latest decision before saving.",
                status=409,
            )
        Review.objects.filter(pk=review.pk).update(revision=F("revision") + 1)
        Event.objects.create(
            review=review,
            finding=finding,
            actor=request.user,
            kind="decision",
            payload={
                "before": before,
                "after": {"status": form.cleaned_data["status"], "note": form.cleaned_data["note"]},
            },
        )
    messages.success(request, "Decision recorded.")
    return redirect(destination(review, finding))


@login_required
@require_POST
def chat(request, pk):
    review = review_for(request.user, pk)
    if review.state != "ready":
        return HttpResponse("Wait until the review is ready.", status=409)
    form = ChatForm(request.POST)
    if not form.is_valid():
        return HttpResponse("Ask a question of at most 4,000 characters.", status=400)
    selected = finding_for(review, request.POST["finding"]) if request.POST.get("finding") else None
    base_revision = selected.revision if selected else review.revision
    # A bounded pilot conversation avoids unbounded model spend and context accumulation.
    if (
        review.messages.count() >= 200
        or review.messages.filter(
            role="user", created_at__gte=timezone.now() - timedelta(minutes=1)
        ).count()
        >= 6
    ):
        messages.error(
            request,
            "Discussion limit reached. Wait a minute or start a fresh review for an extended discussion.",
        )
        return redirect(destination(review, selected))
    try:
        answer, evidence, proposal = discuss(review, selected, form.cleaned_data["message"])
    except (ValueError, RuntimeError):
        messages.error(
            request,
            "A verified discussion response could not be returned. No review record changed; try a narrower question or check model configuration.",
        )
        return redirect(destination(review, selected))
    with transaction.atomic():
        # Fence deletion while a model response is in flight.
        locked = get_object_or_404(
            authorised_reviews(request.user).select_for_update(), pk=pk, state="ready"
        )
        Message.objects.create(
            review=locked, finding=selected, role="user", text=form.cleaned_data["message"]
        )
        Message.objects.create(
            review=locked, finding=selected, role="assistant", text=answer, evidence=evidence
        )
        if proposal:
            Proposal.objects.create(
                review=locked,
                finding=selected,
                base_revision=base_revision,
                kind=proposal["kind"],
                payload=proposal,
            )
    return redirect(destination(review, selected))


@login_required
@require_POST
def propose(request, pk):
    form = ClarificationForm(request.POST)
    if not form.is_valid():
        return HttpResponse("A clarification must contain 1–2,000 characters.", status=400)
    with transaction.atomic():
        review = get_object_or_404(
            authorised_reviews(request.user).select_for_update(), pk=pk, state="ready"
        )
        selected = (
            finding_for(review, request.POST["finding"]) if request.POST.get("finding") else None
        )
        Proposal.objects.create(
            review=review,
            finding=selected,
            base_revision=selected.revision if selected else review.revision,
            kind="clarification",
            payload={"note": form.cleaned_data["text"]},
        )
    return redirect(destination(review, selected))


@login_required
@require_POST
def accept_proposal(request, pk, proposal_id):
    with transaction.atomic():
        review = get_object_or_404(
            authorised_reviews(request.user).select_for_update(), pk=pk, state="ready"
        )
        proposal = get_object_or_404(review.proposals.select_for_update(), pk=proposal_id)
        if proposal.state != "pending":
            return HttpResponse("This proposal has already been handled.", status=409)
        finding = proposal.finding
        if request.POST.get("choice") == "reject":
            proposal.state = "rejected"
        elif request.POST.get("choice") == "accept":
            revision = finding.revision if finding else review.revision
            if revision != proposal.base_revision:
                return HttpResponse(
                    "This proposal is stale. Reject it and propose an update against the latest record.",
                    status=409,
                )
            payload = proposal.payload
            if proposal.kind == "decision":
                if not finding or payload.get("status") not in dict(STATUSES):
                    return HttpResponse("Invalid proposed decision.", status=400)
                Event.objects.create(
                    review=review,
                    finding=finding,
                    actor=request.user,
                    kind="decision",
                    payload={
                        "before": {"status": finding.status, "note": finding.note},
                        "after": {"status": payload["status"], "note": payload["note"]},
                    },
                )
                finding.status, finding.note = payload["status"], payload["note"]
            elif proposal.kind == "new_finding":
                data = {k: v for k, v in payload.get("finding", {}).items() if k != "evidence"}
                data["evidence"] = [
                    {"block_id": e["block_id"], "quote": e["quote"]}
                    for e in payload.get("finding", {}).get("evidence", [])
                ]
                try:
                    candidate = validate_finding(
                        Candidate.model_validate(data), source_blocks(review)
                    )
                except ValueError:
                    return HttpResponse("Invalid proposed finding evidence.", status=400)
                Finding.objects.create(
                    review=review,
                    rank=review.findings.count(),
                    check_key=candidate.pop("check"),
                    **candidate,
                )
                Event.objects.create(
                    review=review,
                    actor=request.user,
                    kind="new_finding",
                    payload={"title": candidate["title"]},
                )
            elif proposal.kind == "clarification":
                Event.objects.create(
                    review=review,
                    finding=finding,
                    actor=request.user,
                    kind="clarification",
                    payload={"note": payload["note"]},
                )
            else:
                return HttpResponse("Invalid proposal type.", status=400)
            if finding:
                finding.revision += 1
                finding.save(update_fields=["status", "note", "revision"])
            Review.objects.filter(pk=review.pk).update(revision=F("revision") + 1)
            proposal.state = "accepted"
        else:
            return HttpResponse("Choose accept or reject.", status=400)
        proposal.save(update_fields=["state"])
    messages.success(request, f"Proposal {proposal.state}. Source evidence remains unchanged.")
    return redirect(destination(review, finding))


@login_required
def report(request, pk):
    with transaction.atomic():
        review = get_object_or_404(
            authorised_reviews(request.user).select_for_update(), pk=pk, state="ready"
        )
        stream = export_review(review)
    return FileResponse(
        stream,
        as_attachment=True,
        filename=f"review-{review.id}.docx",
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


@login_required
def document(request, pk, doc_id):
    review = review_for(request.user, pk)
    doc = get_object_or_404(review.documents, pk=doc_id)
    if request.GET.get("download") == "1":
        return FileResponse(
            doc.file.open("rb"),
            as_attachment=True,
            filename=doc.name,
            content_type="application/octet-stream",
        )
    return render(request, "reviews/document.html", {"review": review, "doc": doc})


@login_required
@require_POST
def add_member(request, project_id):
    project = get_object_or_404(Project, pk=project_id, owner=request.user, deleting=False)
    user = (
        get_user_model()
        .objects.filter(username=request.POST.get("username", ""), is_active=True)
        .first()
    )
    if not user:
        messages.error(
            request,
            "No active account with that username. Ask an administrator to create the account first.",
        )
    else:
        project.members.add(user)
        messages.success(request, "Project member added.")
    return redirect("home")


@login_required
def delete_project(request, project_id):
    project = get_object_or_404(Project, pk=project_id, owner=request.user)
    if request.method == "POST":
        if request.POST.get("confirm") != str(project.pk):
            return HttpResponse("Confirm project deletion.", status=400)
        with transaction.atomic():
            project = get_object_or_404(
                Project.objects.select_for_update(), pk=project_id, owner=request.user
            )
            list(project.reviews.select_for_update())
            project.deleting = True
            project.save(update_fields=["deleting"])
            project.reviews.update(state="cancelled", lease_token=None)
        try:
            for doc in Document.objects.filter(review__project=project):
                doc.file.delete(save=False)
        except OSError:
            messages.error(
                request,
                "Access is revoked, but file removal is incomplete. Retry deletion from the project list.",
            )
            return redirect("home")
        project.delete()
        messages.success(
            request,
            "Project files and records deleted from active storage. Backup copies follow the operator’s retention policy.",
        )
        return redirect("home")
    return render(request, "reviews/delete.html", {"project": project})


@login_required
@require_POST
def rerun(request, pk):
    with transaction.atomic():
        original = get_object_or_404(authorised_reviews(request.user).select_for_update(), pk=pk)
        if original.state in ("queued", "processing"):
            return HttpResponse("This review is already processing.", status=409)
        new = Review.objects.create(
            project=original.project,
            title=(original.title + " · New run")[:160],
            scope_confirmed=original.scope_confirmed,
            metadata_confirmed=original.metadata_confirmed,
        )
        for doc in original.documents.all():
            # Immutable originals may be shared by runs within the same project; project deletion removes them.
            Document.objects.create(
                review=new,
                role=doc.role,
                file=doc.file.name,
                name=doc.name,
                sha256=doc.sha256,
                metadata=doc.metadata,
                blocks=doc.blocks,
                limitations=doc.limitations,
            )
        Event.objects.create(
            review=new, actor=request.user, kind="rerun", payload={"previous_run": str(original.pk)}
        )
    return redirect("guide", new.pk)


@login_required
@require_POST
def remove_member(request, project_id):
    with transaction.atomic():
        project = get_object_or_404(
            Project.objects.select_for_update(), pk=project_id, owner=request.user, deleting=False
        )
        user_id = request.POST.get("user_id", "")
        if not user_id.isdecimal() or int(user_id) == project.owner_id:
            return HttpResponse("The project owner cannot be removed.", status=400)
        project.members.remove(int(user_id))
    messages.success(request, "Project access revoked.")
    return redirect("home")
