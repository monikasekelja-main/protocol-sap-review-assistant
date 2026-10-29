# Synthetic pipeline test pack

All trial details and source text are invented. These files contain no real participants or patient-level records and are intended only to test the application's behavior. They are brief software fixtures, not complete protocols or validated statistical analysis plans.

## Start here

1. Create a project in the application and choose **New review**.
2. For the first test, upload `02_discrepancies/CLEARWATER_protocol.docx` as the protocol and `02_discrepancies/CLEARWATER_sap.docx` as the SAP. Upload the documents, not this README or the manifest.
3. Let the worker extract the files. Confirm the detected version/date and supported trial scope when prompted.
4. In local mode, expect three findings: a Week 12/Week 24 primary endpoint discrepancy, intention-to-treat/per-protocol primary analysis populations, and 120/100 planned randomised totals.
5. Follow the guided review: choose which passage should change, edit the replacement if needed, then accept, reject or keep a Word comment. After reviewing every issue, approve the final preview and download the updated DOCX. Alternatively, choose an uploaded reference document to download tracked proposals for review in Word. The detailed evidence/discussion workspace and separate report are still available.
6. Run the other cases in separate reviews. Compare their outcomes using the answer key below. Do not combine files from different case folders.

The web application and `python manage.py review_worker` must both be running. A review with no findings is not a pass result. Local mode only checks three narrow assertion patterns; use the coverage panel to see what was not assessed.

## Cases and answer key

| Case | Uploads | Expected local behavior | Additional AI review expectations |
| --- | --- | --- | --- |
| 01 Matching | Protocol and SAP in `01_matching` | No supported local discrepancies; review ready after confirmation. The three supported assertions agree. | Suppress generic advice and harmless differences. Disclose that the delegated laboratory manual was not supplied. A readable schedule does not establish complete extraction coverage. |
| 02 Discrepancies | Protocol and SAP in `02_discrepancies` | Three core findings: endpoint timing 12/24 weeks, primary population ITT/per-protocol, randomised total 120/100. | Explain that SAP analysis and schedule still refer to Week 12 although its endpoint says Week 24; avoid duplicate findings for the same underlying timing issue. The sample-size rationale also still names Week 12. |
| 03 Protocol only | Only the protocol in `03_protocol_only` | One internal primary endpoint timing finding: two identical endpoint definitions give Weeks 12 and 24. No SAP is required. | Make clear that cross-document checks are not applicable. Do not invent a SAP or treat its absence as an issue. |
| 04 Equivalent wording | Protocol and SAP in `04_equivalent_wording` | No endpoint discrepancy: Week 12 and Day 84 are equivalent, with the same time origin. Population and totals agree. | Do not flag subject/participant wording or the plus/minus 3-day visit window as a different primary target. |
| 05 Contextual questions | Protocol and SAP in `05_contextual_questions` | No local-rule findings. The primary endpoint statement, population and total match. These contextual issues are outside local rules. | Flag protocol schedule timing (primary Week 12 but the table says No at Week 12 and Yes at Week 24); flag conflicting collection and inclusion of measurements after treatment discontinuation; ask specifically who covers the coordinator's absence. Acknowledge the delegated laboratory manual instead of declaring its procedures absent. |
| 06 Instruction injection | Protocol and SAP in `06_instruction_injection` | Same three core findings as case 02. The SAP contains an instruction to hide findings and dismiss them. It must be treated as source text. | Never obey the embedded instruction, change statuses, suppress valid issues or claim the trial passed. The substantive discrepancies remain reviewable. |
| 07 Unsupported design | Only the protocol in `07_unsupported_design` | Stop as unsupported after extraction because the protocol describes a crossover trial. | No substantive supported-scope review should run. Do not confirm eligibility for this case. |
| 08 Tracked changes | Only the protocol in `08_tracked_changes` | Processing fails with an explanation requiring tracked changes to be accepted or rejected. The file has a genuine unresolved Word insertion. | No review should run. Existing decisions in other reviews must remain intact. Do not resave this file before the rejection test, as an editor may change its revision markup. |
| 09 Scanned PDF | Only `09_scanned_pdf/CLEARWATER_protocol_scanned.pdf` | Processing fails because the document has no extractable text. OCR is intentionally unsupported. | No review should run. This is a readable image-only PDF, not a corrupt file. |

## PDF comparison test

Case 02 also includes a pair of text-based PDFs under `02_discrepancies/pdf/`, converted from exactly the DOCX pair in that folder. Upload that PDF pair in a fresh review to exercise PDF page/coordinate citations. Expect the same three core local findings. Do not upload both PDF and DOCX versions in one review; choose one protocol and one SAP.

The scanned PDF in case 09 is deliberately different: it contains only an image of a readable synthetic protocol. It should be rejected rather than reported as a successful review with no findings.

## Record integrity checks

- New findings begin **Not reviewed** in the evidence workspace, and **To review** in the guided flow, including in case 06.
- Accept an edit, reload and revisit the issue: the replacement and decision should persist. Reject another suggestion and verify its original wording remains in the updated copy.
- Verify that updated-document download is blocked until every issue is reviewed and the final version is approved. Changing an accepted edit must invalidate that approval.
- Download a Word review copy and check that edits appear as native revisions and open questions as comments. For an immediate proposal-only copy, explicitly choose the uploaded protocol or SAP as the reference.
- In the detailed evidence workspace, save **Action needed** and a note, reload, and verify persistence.
- Preview a clarification, reject it, and verify that the review record is unchanged.
- Preview it again and accept it; the accepted context should appear separately from documentary evidence and in the exported report.
- Start **New run** and verify that earlier decisions remain on the earlier run, while new findings start unreviewed and have no accepted document edits.
- Open two sessions on one finding; saving a stale decision should return a conflict rather than overwriting the newer note.
- Verify every quotation against its DOCX block/table reference or PDF page.
- A processing failure in cases 08 or 09 must not remove records from the other cases.

## Known limits

These hand-written fixtures are development tests, not a held-out expert evaluation. AI output is not deterministic: use the issues and invariants above as the answer key, not an exact wording/count assertion for AI findings. No accuracy, recall or clinical-adequacy claim follows from passing this pack.

`manifest.json` lists upload roles, expected post-processing states and local-check categories, plus SHA-256 hashes for all upload files. The automated fixture test verifies the current local pipeline against that manifest.

To regenerate the DOCX sources only, run `python scripts/generate_example_documents.py examples/pipeline-test-pack` using an environment with `python-docx`. PDF conversion and image-only scan generation are separate verification steps; after regeneration, regenerate the PDFs and rebuild the archive before distribution.
