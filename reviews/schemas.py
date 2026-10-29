from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

CHECKS = {
    "trial_question": "Trial question",
    "endpoint": "Primary endpoint",
    "schedule": "Assessment schedule",
    "population": "Analysis population",
    "analysis": "Primary analysis",
    "missing": "Missing observations and treatment changes",
    "sample_size": "Sample size",
    "operations": "Essential operational requirements",
}
Check = Literal[
    "trial_question",
    "endpoint",
    "schedule",
    "population",
    "analysis",
    "missing",
    "sample_size",
    "operations",
]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Citation(StrictModel):
    block_id: str
    quote: str = Field(min_length=1, max_length=6000)


class Candidate(StrictModel):
    check: Check
    kind: Literal["discrepancy", "question"]
    priority: Literal["high", "medium", "low"]
    title: str = Field(min_length=1, max_length=240)
    why: str = Field(min_length=1, max_length=2000)
    action: str = Field(min_length=1, max_length=2000)
    unknown: str = Field(max_length=2000)
    evidence: list[Citation] = Field(min_length=1, max_length=6)


class SummaryField(StrictModel):
    field: Literal[
        "Trial question",
        "Population",
        "Treatment comparison",
        "Primary outcome",
        "Primary analysis",
    ]
    text: str = Field(max_length=1500)
    evidence: list[Citation] = Field(max_length=5)


class Coverage(StrictModel):
    check: Check
    state: Literal["assessed", "partial", "not_assessed", "not_applicable"]
    reason: str = Field(min_length=1, max_length=1500)


class ReviewOutput(StrictModel):
    summary: list[SummaryField] = Field(max_length=5)
    findings: list[Candidate] = Field(max_length=40)
    coverage: list[Coverage] = Field(max_length=8)


def verify_evidence(citations, blocks):
    verified = []
    for citation in citations:
        item = citation.model_dump() if isinstance(citation, Citation) else citation
        block = blocks.get(item["block_id"])
        if block is None or item["quote"] not in block["text"] or not item["quote"].strip():
            raise ValueError("Unverifiable source evidence")
        start = block["text"].index(item["quote"])
        verified.append(
            {
                "block_id": item["block_id"],
                "document_id": block["document_id"],
                "name": block["name"],
                "version": block["version"],
                "location": block["location"],
                "start": start,
                "end": start + len(item["quote"]),
                "quote": block["text"][start : start + len(item["quote"])],
            }
        )
    return verified


def validate_finding(candidate, blocks):
    evidence = verify_evidence(candidate.evidence, blocks)
    if (
        candidate.kind == "discrepancy"
        and len({(e["block_id"], e["start"], e["end"]) for e in evidence}) < 2
    ):
        raise ValueError("A discrepancy requires two different source passages")
    if candidate.kind == "question" and not candidate.unknown.strip():
        raise ValueError("A question must identify what remains unknown")
    result = candidate.model_dump()
    result["evidence"] = evidence
    return result


class ChatProposal(StrictModel):
    kind: Literal["clarification", "decision", "new_finding"]
    note: str = Field(min_length=1, max_length=2000)
    status: Literal["not_reviewed", "action_needed", "needs_discussion", "dismissed"]
    finding: Candidate | None


class DiscussionOutput(StrictModel):
    answer: str = Field(min_length=1, max_length=6000)
    evidence: list[Citation] = Field(max_length=8)
    proposal: ChatProposal | None
