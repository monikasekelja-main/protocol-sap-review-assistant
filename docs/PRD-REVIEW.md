# PRD review

Reviewed 29 October 2026. This is an engineering/product assessment, not a clinical or regulatory review. The supplied PRD remains unchanged in [PRD.md](PRD.md).

## Recommendation

Proceed with a narrow retrospective pilot after confirming the supported trial type with a partner. The PRD defines a coherent workflow and unusually useful constraints: evidence for every finding, explicit record changes, durable decisions, and visible coverage limitations. Preserve those constraints throughout implementation.

The critical path is proving that source locations, table interpretation, and clinically consequential comparisons survive extraction. A polished chat interface cannot compensate for incorrect evidence or an unreadable visit schedule. Build an end-to-end evidence review first, then add discussion.

This workspace is empty: no source files, dependencies, tests, Git metadata, or project-specific AGENTS.md were found during inspection. There is no existing stack to reuse. The connected GitHub identity is `monikasekelja-main`; no accessible `monikasekelja-main/test-repo` repository was found. Architecture choices below are recommendations, not descriptions of existing software.

## Strengths to retain

- The product supports team decisions instead of offering an overall trial score.
- Discrepancies and judgment questions have different evidence requirements.
- Protocol-only review is useful without making a SAP mandatory.
- User clarification does not rewrite source evidence or automatically resolve discrepancies.
- Review completion, review decisions, and future verification of revisions are separate concepts.
- Release gates include false alarms, expert judgment, and unaided use, alongside detection quality.

## Decisions needed before implementation

| Decision | Recommended pilot default | Why it matters |
| --- | --- | --- |
| Partner and trial scope | Confirm English, two-arm parallel superiority trials with one continuous primary endpoint at a fixed time | Affects the fact schema, check catalogue, and evaluation labels; explicitly required by the PRD |
| Real-document access | Synthetic/public/authorised redacted material until confidential-data controls are verified | Avoids treating a prototype as a confidential-data service |
| Scope determination | Assess design from cited document text; ask a targeted question if uncertain; block unsupported review | A tick box alone cannot establish supported scope |
| Upload envelope | Initially propose 25 MB and 250 pages per document, two documents per run; confirm against partner examples | Bounds parser cost, request sizes, context budgets, and user expectations |
| Difficult DOCX content | Reject documents with unresolved tracked changes for the pilot; disclose unsupported text boxes/embedded content | Common document APIs omit some content; silent omissions undermine evidence |
| Re-review | New run for a changed document or explicit rerun; old decisions remain on the old run | Prevents silently carrying decisions to different evidence |
| Access model | Invite-only projects; same review permissions for project members; project owner manages access/deletion | One workspace does not mean public document access or an enterprise role system |
| Retention | Agree a concrete pilot retention period and backup expiry before confidential use; display it before upload | Deletion cannot promise immediate removal from immutable backups |
| Provider/model | Select one provider and pin a model after a representative extraction/review evaluation | No evidence yet supports a particular model's accuracy, cost, or retention suitability |
| Hosting | Select region and managed services after partner data requirements are known | Determines data location, backups, operational ownership, and cost |

These are proposed defaults and open decisions, not additional accepted PRD requirements. Planning and synthetic fixtures can proceed; partner-dependent scope decisions gate the implementation milestones identified in the backlog.

## Material gaps to close

1. **Evidence accuracy versus semantic correctness.** An exact quotation can still be from the wrong arm, secondary endpoint, historical version, or table column. Verification must check context and meaning, not just string matching. Exact-match validation is necessary but insufficient.
2. **Coverage cannot be inferred from successful parsing.** A parser can return prose while omitting a schedule table. Store per-check coverage and assessment reasons, and inspect representative source renders during the parser spike. Never turn unassessed content into an absence claim.
3. **Sample-size arithmetic needs explicit quantities.** Planned randomised, evaluable, and per-arm totals can differ legitimately. Compare only quantities with matched roles, units, and stated allocation. Do not recompute power or declare the calculation appropriate.
4. **Discontinuation language needs context.** Treatment discontinuation, study withdrawal, missing measurements, rescue therapy, and intercurrent events are not interchangeable. Retain the source terms; flag a bounded question when their relationship is unclear.
5. **Failure and retry behavior needs a contract.** Define recoverable processing states, stage retries, and atomic publication. Partial attempts must not become apparently complete reviews or erase decisions.
6. **Team decisions need conflict handling.** Even without simultaneous collaborative editing, two browser sessions can overwrite notes. Use revision checks and show a reload/compare prompt on stale writes.
7. **Evaluation denominators need definition.** Specify what counts as a unique issue, an actionable question, an eligible high-priority discrepancy, and a false alarm. Freeze labels before evaluating a release candidate.
8. **Resource and performance budgets are missing.** Record parser duration, model tokens/cost, queue wait, review latency, and export latency on the pilot corpus. Agree numerical budgets before the pilot; do not present an invented cost estimate as measured performance.

## Scope discipline

Keep the eight PRD check areas, with coverage reported independently for each. Implement them incrementally; do not call a three-check prototype the completed MVP. First demonstrate primary endpoint timing, schedule agreement, and analysis population checks, then implement and evaluate the remaining areas before the full pilot release.

Defer OCR, revised-document verification, literature search, role dashboards, automatic source edits, full drafting, autonomous agents, vector databases, and power calculations. Revisit only when the pilot supplies evidence of need.

## Release decision

Ship a retrospective pilot only after the PRD gates pass on a frozen held-out set and the three user roles complete the core workflow unaided. Report corpus size, uncertainty, false alarms, and review effort. Meeting a numerical target on a handful of seeded examples is not established real-world performance.
