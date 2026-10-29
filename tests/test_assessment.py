import io
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.urls import reverse
from docx import Document as WordDocument

from reviews.assessment import RUBRIC
from reviews.pipeline import local_review, run_review, source_blocks
from reviews.provider import ProviderError
from reviews.schemas import CHECKS, ReviewOutput, SummaryField
from tests.test_application import ReviewFixture


@override_settings(AI_ENABLED=True)
class AssessmentTests(ReviewFixture, TestCase):
    def response(self, *, evidence=True):
        blocks = source_blocks(self.review)
        block = next(iter(blocks.values()))
        return ReviewOutput(
            summary=[],
            findings=[],
            coverage=[
                {
                    "check": check,
                    "state": "assessed",
                    "reason": "Compared supplied definitions.",
                    "evidence": [{"block_id": block["id"], "quote": block["text"]}]
                    if evidence
                    else [],
                }
                for check in CHECKS
            ],
        )

    def run_ai(self, result):
        with patch("reviews.pipeline.generate", return_value=(result, {})) as generate:
            output = run_review(self.review)
        return output, generate.call_args.args[1]

    def test_hybrid_retains_local_findings_and_supplies_eight_area_rubric(self):
        output, context = self.run_ai(self.response())
        self.assertEqual(output["mode"], "hybrid")
        self.assertCountEqual(
            [f["check"] for f in output["findings"]], ["endpoint", "population", "sample_size"]
        )
        self.assertEqual(set(context["assessment_rubric"]), set(CHECKS))
        self.assertEqual(len(context["local_findings"]), 3)
        self.assertIn("time origin", RUBRIC["endpoint"])
        for entry in output["coverage"]:
            self.assertEqual(
                entry["contextual"]["state"], "partial"
            )  # Fixture has extraction limits.
            self.assertTrue(entry["contextual"]["evidence"][0]["document_id"])
            self.assertIn("local", entry)

    def test_no_assessed_coverage_without_source_evidence(self):
        for fabricated in (False, True):
            result = self.response(evidence=fabricated)
            if fabricated:
                for entry in result.coverage:
                    entry.evidence[0].quote = "This quotation was invented."
            output, _ = self.run_ai(result)
            self.assertTrue(
                all(e["contextual"]["state"] == "not_assessed" for e in output["coverage"])
            )
            self.assertTrue(all(not e["contextual"]["evidence"] for e in output["coverage"]))
            self.assertEqual(
                next(e for e in output["coverage"] if e["check"] == "endpoint")["state"], "partial"
            )

    def test_duplicate_or_missing_area_does_not_hide_local_checks(self):
        result = self.response()
        result.coverage = [result.coverage[1], result.coverage[1]]
        output, _ = self.run_ai(result)
        self.assertEqual(len(output["coverage"]), 8)
        endpoint = next(e for e in output["coverage"] if e["check"] == "endpoint")
        self.assertEqual(endpoint["state"], "partial")
        self.assertEqual(endpoint["contextual"]["state"], "not_assessed")
        self.assertEqual(endpoint["local"]["state"], "partial")

    def test_ai_failure_preserves_local_results_and_discloses_failure(self):
        with patch("reviews.pipeline.generate", side_effect=ProviderError("Unavailable")):
            output = run_review(self.review)
        self.assertEqual(output["mode"], "local_fallback")
        self.assertEqual(len(output["findings"]), 3)
        self.assertTrue(all(e["contextual"]["state"] == "not_assessed" for e in output["coverage"]))
        self.assertTrue(any("did not complete" in text for text in output["limitations"]))
        self.assertTrue(output["summary"]["Trial question"]["evidence"])

    def test_omitted_context_cannot_support_ai_coverage(self):
        document = self.review.documents.get(role="sap")
        text = "Outside model context " + "z" * 100001
        document.blocks.append(
            {"id": "oversized", "text": text, "location": "body", "kind": "paragraph"}
        )
        document.save()
        result = self.response()
        for entry in result.coverage:
            entry.evidence[0].block_id = f"d{document.pk}:oversized"
            entry.evidence[0].quote = "Outside model context"
        result.summary = [
            SummaryField(
                field="Trial question",
                text="Outside model context",
                evidence=[
                    {"block_id": f"d{document.pk}:oversized", "quote": "Outside model context"}
                ],
            )
        ]
        output, context = self.run_ai(result)
        self.assertNotEqual(output["summary"]["Trial question"]["text"], "Outside model context")
        self.assertFalse(any(b["id"].endswith(":oversized") for b in context["blocks"]))
        self.assertTrue(all(e["contextual"]["state"] == "not_assessed" for e in output["coverage"]))
        self.assertTrue(any("context limit" in message for message in output["limitations"]))

    def test_not_applicable_cannot_bypass_supported_check(self):
        result = self.response()
        for entry in result.coverage:
            entry.state = "not_applicable"
        output, _ = self.run_ai(result)
        self.assertTrue(all(e["contextual"]["state"] == "not_assessed" for e in output["coverage"]))

    def test_local_coverage_depends_on_comparable_evidence(self):
        _, _, coverage = local_review(source_blocks(self.review))
        self.assertEqual(len({c["reason"] for c in coverage}), 8)
        self.assertEqual(sum(c["state"] == "partial" for c in coverage), 3)
        self.review.documents.filter(role="sap").delete()
        _, _, coverage = local_review(source_blocks(self.review))
        self.assertTrue(all(c["state"] == "not_assessed" for c in coverage))

    def test_failed_contextual_run_shows_banner_and_evidence_in_guided_coverage(self):
        with patch("reviews.pipeline.generate", side_effect=ProviderError("Unavailable")):
            self.ready()
        page = self.client.get(reverse("guide", args=[self.review.pk]) + "?step=3")
        self.assertContains(page, "Contextual AI review did not complete")
        self.assertContains(page, "Passages compared by local rules")
        self.assertContains(page, "Contextual AI · not_assessed")
        report = self.client.get(reverse("report", args=[self.review.pk]))
        self.assertEqual(report.status_code, 200)
        doc = WordDocument(io.BytesIO(b"".join(report.streaming_content)))
        text = "\n".join(p.text for p in doc.paragraphs)
        self.assertIn("Local checks: partial", text)
        self.assertIn("Contextual AI: not assessed", text)
        self.assertIn("start a new run to retry", text)
