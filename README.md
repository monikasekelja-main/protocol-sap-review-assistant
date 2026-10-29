# Protocol and SAP Review Assistant

Planning repository for an evidence-linked review assistant for clinical trial protocols and statistical analysis plans (SAPs).

**Current status:** PRD reviewed and implementation planned. No application has been implemented or deployed. Proposed GitHub owner: `monikasekelja-main`; proposed repository: `test-repo`, matching this workspace.

The product helps a trial team identify consequential inconsistencies, inspect supporting passages, discuss findings, record decisions, and export a DOCX report. It does not establish scientific, statistical, safety, or regulatory adequacy.

- [Original PRD](docs/PRD.md)
- [PRD review and decisions needed](docs/PRD-REVIEW.md)
- [Architecture and implementation plan](docs/BUILD-PLAN.md)
- [Delivery backlog and acceptance criteria](docs/BACKLOG.md)

Start with the extraction and evidence milestone in the backlog. Confirm the narrow trial scope with a pilot partner before implementing the review engine. Use synthetic, public, or explicitly authorised redacted documents during development; keep real study files, extracted content, conversations, and secrets out of Git.
