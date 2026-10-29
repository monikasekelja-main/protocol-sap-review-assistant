import json
import os
import subprocess
import sys
import uuid
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .models import Finding, Review
from .pipeline import VERSION, run_review, scope_signals, source_blocks


def process_next():
    now = timezone.now()
    # A timed-out worker cannot publish because its lease token is replaced on claim.
    Review.objects.filter(state="processing", lease_until__lt=now).update(
        state="failed",
        error="Processing timed out. Start a new review run to retry.",
        lease_token=None,
    )
    with transaction.atomic():
        candidates = Review.objects.filter(state="queued", project__deleting=False).order_by(
            "created_at"
        )
        if settings.DATABASES["default"]["ENGINE"].endswith("postgresql"):
            candidates = candidates.select_for_update(skip_locked=True)
        review = candidates.first()
        if review is None:
            return False
        token = uuid.uuid4()
        if not Review.objects.filter(pk=review.pk, state="queued").update(
            state="processing", lease_token=token, lease_until=now + timedelta(minutes=10), error=""
        ):
            return True
    try:
        for doc in review.documents.all():
            if doc.blocks:
                continue
            # Only minimal environment reaches the bounded parser process, including no model credential.
            result = subprocess.run(
                [sys.executable, "-m", "reviews.extraction", doc.file.path, doc.name],
                capture_output=True,
                text=True,
                timeout=60,
                env={"PATH": os.defpath, "LANG": "en_US.UTF-8"},
                cwd=settings.BASE_DIR,
            )
            data = json.loads(result.stdout)
            if data.get("error"):
                raise ValueError(data["error"])
            with transaction.atomic():
                locked = (
                    Review.objects.select_for_update()
                    .filter(
                        pk=review.pk, lease_token=token, state="processing", project__deleting=False
                    )
                    .first()
                )
                if not locked:
                    return True
                doc.blocks, doc.metadata, doc.limitations = (
                    data["blocks"],
                    data["metadata"],
                    data["limitations"],
                )
                doc.save(update_fields=["blocks", "metadata", "limitations"])
        blocked, _ = scope_signals(source_blocks(review))
        if blocked:
            Review.objects.filter(pk=review.pk, lease_token=token, state="processing").update(
                state="unsupported", error="; ".join(blocked), lease_token=None
            )
            return True
        if not review.scope_confirmed or not review.metadata_confirmed:
            Review.objects.filter(pk=review.pk, lease_token=token, state="processing").update(
                state="needs_input", lease_token=None
            )
            return True
        result = run_review(review)
        with transaction.atomic():
            locked = (
                Review.objects.select_for_update()
                .filter(
                    pk=review.pk,
                    lease_token=token,
                    state="processing",
                    lease_until__gt=timezone.now(),
                    project__deleting=False,
                )
                .first()
            )
            if not locked:
                return True
            # No replacement of successful runs or existing decisions.
            if locked.findings.exists():
                raise ValueError("This run already has findings. Start a new review.")
            for rank, item in enumerate(result["findings"]):
                Finding.objects.create(
                    review=locked, rank=rank, check_key=item.pop("check"), **item
                )
            locked.summary = result["summary"]
            locked.coverage = result["coverage"]
            locked.limitations = result["limitations"]
            locked.versions = {
                "parser": VERSION,
                "checks": VERSION,
                "prompts": VERSION,
                "schema": VERSION,
                "model": settings.ANTHROPIC_MODEL if settings.AI_ENABLED else "local-rules",
                "usage": result["usage"],
                "review_mode": result.get("mode", "local"),
            }
            locked.state, locked.completed_at, locked.lease_token = "ready", timezone.now(), None
            locked.save()
    except ValueError as exc:
        # ValueErrors are our bounded, content-free parser validation messages.
        Review.objects.filter(pk=review.pk, lease_token=token).update(
            state="failed", error=str(exc)[:300], lease_token=None
        )
    except Exception:
        Review.objects.filter(pk=review.pk, lease_token=token).update(
            state="failed",
            error="Processing failed. The existing review record has been preserved. Start a new run or ask the administrator to check configuration.",
            lease_token=None,
        )
    return True
