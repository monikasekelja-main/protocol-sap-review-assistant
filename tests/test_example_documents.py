"""Exercise upload-ready synthetic fixtures against the real local extraction/check path."""

import hashlib
import json
from pathlib import Path

from django.test import SimpleTestCase

from reviews.extraction import ExtractionError, extract
from reviews.pipeline import local_review, scope_signals
from reviews.schemas import validate_finding

ROOT = Path(__file__).resolve().parents[1] / "examples" / "pipeline-test-pack"


class ExamplePackTests(SimpleTestCase):
    def test_manifest_files_and_expected_local_behavior(self):
        cases = json.loads((ROOT / "manifest.json").read_text())
        for case in cases:
            with self.subTest(case=case["id"]):
                blocks = {}
                rejected = False
                for index, item in enumerate(case["files"], 1):
                    path = ROOT / item["path"]
                    content = path.read_bytes()
                    self.assertEqual(hashlib.sha256(content).hexdigest(), item["sha256"])
                    try:
                        result = extract(content, path.name)
                    except ExtractionError:
                        rejected = True
                        continue
                    for block in result["blocks"]:
                        key = f"d{index}:{block['id']}"
                        blocks[key] = {
                            **block,
                            "id": key,
                            "role": item["role"],
                            "document_id": index,
                            "name": path.name,
                            "version": result["metadata"]["version"],
                        }
                if case["expected_state"] == "failed":
                    self.assertTrue(rejected)
                    continue
                self.assertFalse(rejected)
                unsupported, _ = scope_signals(blocks)
                if case["expected_state"] == "unsupported":
                    self.assertTrue(unsupported)
                    continue
                self.assertFalse(unsupported)
                _, findings, _ = local_review(blocks)
                self.assertCountEqual(
                    [finding.check for finding in findings], case["expected_local_checks"]
                )
                for finding in findings:
                    validate_finding(finding, blocks)
