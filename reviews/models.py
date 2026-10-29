import uuid

from django.conf import settings
from django.db import models

STATUSES = [
    ("not_reviewed", "Not reviewed"),
    ("action_needed", "Action needed"),
    ("needs_discussion", "Needs discussion"),
    ("dismissed", "Dismissed"),
]


class Project(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=160)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="owned_projects"
    )
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="review_projects")
    deleting = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Review(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="reviews")
    title = models.CharField(max_length=160)
    state = models.CharField(max_length=24, default="queued")
    scope_confirmed = models.BooleanField(default=False)
    metadata_confirmed = models.BooleanField(default=False)
    revision = models.PositiveIntegerField(default=0)
    summary = models.JSONField(default=dict)
    coverage = models.JSONField(default=list)
    limitations = models.JSONField(default=list)
    versions = models.JSONField(default=dict)
    error = models.CharField(max_length=300, blank=True)
    lease_token = models.UUIDField(null=True)
    lease_until = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True)

    class Meta:
        ordering = ["-created_at"]


class Document(models.Model):
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name="documents")
    role = models.CharField(max_length=10, choices=[("protocol", "Protocol"), ("sap", "SAP")])
    file = models.FileField(upload_to="documents/%Y/%m/%d/")
    name = models.CharField(max_length=200)
    sha256 = models.CharField(max_length=64)
    metadata = models.JSONField(default=dict)
    blocks = models.JSONField(default=list)
    limitations = models.JSONField(default=list)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["review", "role"], name="one_document_per_role")
        ]


class Finding(models.Model):
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name="findings")
    check_key = models.CharField(max_length=40)
    kind = models.CharField(
        max_length=20,
        choices=[("discrepancy", "Document discrepancy"), ("question", "Question for the team")],
    )
    priority = models.CharField(
        max_length=10, choices=[("high", "High"), ("medium", "Medium"), ("low", "Low")]
    )
    title = models.CharField(max_length=240)
    why = models.TextField()
    action = models.TextField()
    unknown = models.TextField(blank=True)
    evidence = models.JSONField(default=list)
    status = models.CharField(max_length=20, choices=STATUSES, default="not_reviewed")
    note = models.TextField(blank=True)
    revision = models.PositiveIntegerField(default=0)
    rank = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["rank", "id"]


class Event(models.Model):
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name="events")
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    finding = models.ForeignKey(Finding, null=True, on_delete=models.CASCADE)
    kind = models.CharField(max_length=30)
    payload = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)


class Message(models.Model):
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name="messages")
    finding = models.ForeignKey(Finding, null=True, on_delete=models.CASCADE)
    role = models.CharField(max_length=10)
    text = models.TextField()
    evidence = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)


class Proposal(models.Model):
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name="proposals")
    finding = models.ForeignKey(Finding, null=True, on_delete=models.CASCADE)
    base_revision = models.PositiveIntegerField(default=0)
    kind = models.CharField(max_length=20, default="clarification")
    payload = models.JSONField(default=dict)
    state = models.CharField(max_length=12, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
