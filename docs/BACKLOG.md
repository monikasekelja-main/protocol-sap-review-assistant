# Delivery backlog

Ordered implementation work. Estimates are engineer-days, exclude partner wait time and expert evaluation effort, and must be revised after the extraction spike. Each row can become a GitHub issue after repository publication. This planning change does not implement these tasks.

| ID | Work | Depends on | Estimate |
| --- | --- | --- | --- |
| M0 | Confirm scope, corpus, evaluation labels and data boundary | Partner | 2–3 |
| M1 | Extraction and provenance spike | M0 scope confirmation | 4–6 |
| M2 | Application foundation and immutable review runs | M1 schema | 4–6 |
| M3 | Evidence-linked summary and first three checks | M1, M2 | 5–7 |
| M4 | Remaining five check areas and coverage | M3 | 5–7 |
| M5 | Review workspace and durable decisions | M2; integrate M3/M4 | 4–6 |
| M6 | Contextual chat and explicit update proposals | M3, M5 | 4–6 |
| M7 | DOCX export, deletion and operational controls | M2, M5; integrate M6 | 4–6 |
| M8 | Held-out evaluation, usability and retrospective pilot | M4–M7 | 8–12 |

M5 UI work can start against synthetic records while M3/M4 develop. Confidential-data readiness in M7 is a separate gate from the synthetic prototype. Do not skip M4 when calling the product an MVP.

## M0 — Confirm the partner problem

- Confirm the trial design and continuous fixed-time endpoint scope with the pilot partner before implementation.
- Obtain examples of useful issues, harmless terminology differences, complex schedules and protocol-only use.
- Agree issue taxonomy, evaluation denominators, reviewer responsibilities, held-out split, proposed sample floor, retention and document authorisation.
- Identify hosting/provider constraints and the person approving confidential-data readiness.

**Done:** a recorded scope decision, authorised corpus manifest, agreed evaluation rubric and named expert reviewers. Unknown hosting/retention choices are explicitly blocking confidential intake.

## M1 — Prove extraction and evidence

- Create synthetic DOCX/text-PDF pairs with Week 12/24 mismatch, harmless rewording, merged schedule headers, footnotes, inconsistent populations, tracked changes, scans and corrupt inputs.
- Implement prototype block extraction with immutable source identifiers, PDF page/bbox and DOCX structural paths.
- Preserve source/raw text and normalized comparison values separately. Inspect source renders against extracted schedules and paragraph order.
- Record unsupported content and check-specific coverage. Reject unusable inputs with a clear recovery action.

**Done:** every displayed fixture quote resolves to the correct version and location; no known omission is silent; schedule cells retain their headers and footnotes, or affected checks are explicitly partial. Stop and revise parser/scope if this cannot be demonstrated. Produce benchmark timings and parser limitations.

## M2 — Foundation and jobs

- Scaffold Django, PostgreSQL, private storage, dependency lockfile, environment example and synthetic local setup.
- Add project membership, document versions, extractions, run/attempt records and content-free audit events.
- Implement upload validation, worker claims/leases/fencing, bounded retries, stage checkpoints and atomic publication.
- Add CI for linting, migrations and meaningful offline tests; keep real data out of fixtures and logs.

**Done:** one protocol and optional SAP enter an authorised project and complete a synthetic background run; cross-project access is denied; crash/retry does not duplicate outputs or overwrite prior reviews. Unsupported scope does not proceed to substantive review.

## M3 — First review slice

- Build five-field summary with evidence, uncertainties and stored user clarifications.
- Add endpoint definition/time, schedule alignment and analysis population checks.
- Define typed candidate schema and evidence-span verifier; require both sides for discrepancy findings.
- Deduplicate, explain consequence/priority, show top five and remaining findings.

**Done:** planted contradictions appear with correct contextual evidence; harmless wording does not trigger a discrepancy; wrong-version/incorrect-offset candidates are rejected. Protocol-only review works, and unreadable schedules disclose incomplete checks. Demonstrate the complete upload → evidence review path before chat.

## M4 — Complete supported checks

- Add trial question, primary analysis, missing observations/treatment changes, sample-size alignment and essential operations checks.
- Distinguish randomised/evaluable/per-arm counts and allocation; do not validate power.
- Account for delegated manuals and ambiguous treatment-change descriptions without making unsupported absence claims.
- Persist a result/coverage assessment for every check family, including no finding and not applicable.

**Done:** all eight PRD areas have labelled positive, harmless-difference and insufficient-evidence fixtures. Expert reviewers confirm that the catalogue implements the stated scope. Accuracy below the release targets triggers refinement rather than broader claims.

## M5 — Review workspace and decisions

- Build summary/findings/evidence panel, accessible keyboard navigation and responsive selection.
- Add Not reviewed, Action needed, Needs discussion and Dismissed; rationale notes and append-only decision history.
- Use revision checks for stale edits. Preserve discrepancy evidence when clarification changes the intended interpretation.

**Done:** a user can inspect both passages, record a decision, refresh and recover it; stale edits cannot silently overwrite notes; failures/reruns preserve old records. Coverage is visible at summary and affected-finding level. No pass badges, scores or Resolved state.

## M6 — Bounded chat

- Retrieve selected evidence and relevant sections from the run's exact versions; support document questions and explicit abstention.
- Distinguish source, user context and interpretation in responses; cite verifiable spans.
- Render proposed finding/clarification/decision updates as a before/after diff and require explicit accept/reject.
- Validate and apply accepted changes server-side exactly once, checking revision and membership.

**Done:** all PRD example interactions have useful grounded responses; rejecting a proposal changes no record; accepting a stale or invalid proposal fails safely. Malicious uploaded instructions and chat text cannot browse, execute code, access another project or mutate review state silently.

## M7 — Export and data lifecycle

- Generate DOCX from an accepted-state snapshot with summary, all findings, evidence, decisions, notes and coverage; omit full chat by default.
- Visually inspect representative report output, including long evidence, Unicode and multi-page reports.
- Implement authorised download, retention/deletion jobs, worker cancellation/fencing, backup-expiry policy and content-free logging.
- Verify storage/TLS/provider terms, environment separation, operational alerts and backup restoration before confidential intake.

**Done:** exported state matches its recorded snapshot; originals remain unchanged. Deletion removes or expires every documented data class, active workers cannot resurrect it, and failures are visible. Confidential-document upload remains disabled until the agreed readiness checklist has evidence and an owner sign-off.

## M8 — Evaluate and release

- Freeze candidate code, parser/check/model/prompt versions and held-out labels; record per-study results and expert adjudications.
- Evaluate discrepancy precision/recall separately from question usefulness, and publish counts, uncertainty and review burden.
- Run the six PRD usability tasks unaided with each of the three user roles.
- Measure latency, token spend, failures, false alarms and useful review outcomes; agree operating budgets and support responsibility.

**Done:** all PRD pilot gates are met with documented denominators and limitations; retrospective pilot is approved. Move to active drafts only after the retrospective gate. If a gate fails, record the failure and fix the affected capability; do not silently relax the target.

## First implementation pull request

After M0, implement the M1 extraction spike and synthetic fixtures only. Include a reproducible command that prints source blocks and coverage, tests evidence-location round trips, and demonstrates a known schedule failure. The reviewable result should answer whether the parser can support the product before adding model calls or UI polish.
