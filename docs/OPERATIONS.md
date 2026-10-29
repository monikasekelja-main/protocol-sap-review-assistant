# Implementation status and operations

## Delivered preview

The application implements the core workflow as a Django monolith with a separate worker. Dependency versions are locked in `uv.lock`. SQLite supports development; `DATABASE_URL` selects PostgreSQL. Storage is a private filesystem shared by web/worker, never a public media route. This is an explicit pilot simplification from the proposed S3 design; managed object-storage integration is still outstanding.

The supported scope remains the PRD's narrow trial type. Automatic scope checks reject some clearly unsupported design/endpoint phrases; the user must inspect extracted protocol text and explicitly confirm every eligibility criterion. Word matches and confirmation are not validated automatic clinical classification. Partner confirmation and a representative corpus remain required before a real pilot.

Local checks cover only three narrow assertion patterns. Contextual AI provides the eight-area review when configured. Coverage is conservative, and schedule checks remain partial where table interpretation is uncertain. Every displayed quote is checked as an exact substring of a version-specific extracted block. This proves quotation provenance, not semantic correctness or faithful visual reconstruction of the original.

Originals and extraction results are immutable per review run after confirmation. The confirm step records user-supplied metadata without changing source bytes. Each rerun copies source references into a new run; it never migrates old decisions. Parser, catalogue, prompt, schema and model versions are recorded; bump `reviews.pipeline.VERSION` whenever their behavior changes.

## Guided document editing

The default entry point is now a direct document upload followed by a guided issue queue. `EditDecision` stores an explicit accepted/rejected/commented decision, exact original source ranges, replacement text, actor and note. These editing decisions are separate from the older finding-status fields. Original uploads remain immutable. Review reports include the editing decisions and notes.

DOCX editing resolves extracted block locations against the actual original package and verifies its SHA-256. Simple paragraphs can receive source-range replacements, including text spanning multiple formatted runs. Unchanged runs and package members are retained. Overlapping edits, stale decisions, incorrect source hashes and unsupported structures are blocked. Table rows, hyperlinks, fields and existing annotated paragraphs are comment-only when safe replacement cannot be established. This is deliberately not a complete Word editor.

For discrepancies, alternative wording is taken from the compared passage. The user explicitly chooses one replacement direction and can edit it. The application does not infer which scientific statement is authoritative, automatically update every related definition, or verify that the resulting study design is coherent. Pending issues become comments in neutral Word review copies. Alternatively, a user can explicitly choose a reference document for export-only cross-document proposals. Unreviewed discrepancies with a single unambiguous compared quote can then become tracked edits in the other document. These proposals are validated against source locations and overlaps, do not create saved decisions, and remain subject to acceptance in Word. Unsafe or ambiguous replacements remain comments.

A final approval requires every issue to have an editing decision and every accepted edit to remain valid. Approval is bound to the review revision. Updated downloads are blocked before approval and after any subsequent record change until reapproval. Word review copies can be downloaded earlier. Updated copies apply accepted edits and retain questions chosen as comments; Word review copies encode selected edits as native `w:ins`/`w:del` revisions and anchor open questions through comments relationships and ranges. Existing comments and unrelated package parts are preserved. No working draft or download cache is stored on the server; generated copies are built in memory and deletion of a project cascades to editing decisions.

PDF uploads remain review-only for source editing. PDF notes are retained in the separate report; they cannot be embedded into an original DOCX that was never supplied. Revised-document re-import with unresolved tracked changes remains unsupported. Accept or reject revisions in Word before submitting the revised document as a new run.

The original PRD excluded source editing; this workflow implements the user's subsequent scope change. Expert evaluation and usability release gates still apply, and the revised workflow has not been tested with real clinical users.

## Processes and recovery

The development `runserver` command starts and stops its own worker (use `--no-worker` if managing one separately). Production web servers do not. Run the production web process and `python manage.py review_worker` against the same database and private filesystem. One SQLite worker only. PostgreSQL workers claim with `SELECT FOR UPDATE SKIP LOCKED`, then compare-and-set the queued state. Jobs have a ten-minute lease and fence publication with a unique token. Parsing and model requests have shorter bounded timeouts. An expired job is marked failed when a worker polls; retry from the UI starts a new run. There is no automatic repeated provider billing or infinite retry loop.

Parsing runs in a child process with a minimal environment, a 45-second CPU limit and 60-second parent timeout. Linux additionally applies a 1.5 GB address-space cap. macOS rejects address-space limits, so enforce memory at the container/host boundary for hosted use. A subprocess is **not** a complete security sandbox: isolate parser egress and filesystem access at the host/container layer before accepting external partner files.

Known parse failures have safe user-facing explanations. Unexpected exceptions expose only a generic failure, preserving earlier reviews and decisions. Processing errors do not log source or model payloads. Operational metrics currently include persisted provider token usage and timestamps; production monitoring, spend dashboards and alerts are not implemented.

## Accounts and access

There is no public registration. Create an administrator using `createsuperuser`, then create accounts in Django admin. Project owners can add existing active accounts. All source, review, decision, report and discussion queries are membership-scoped. Only owners delete projects or add members. This is not a full invitation/email or enterprise access-management system.

Development uses secure Django session/CSRF defaults appropriate for loopback HTTP. `DEBUG=0` requires a supplied secret and turns on HTTPS redirect, secure cookies and HSTS. Do not enable forwarded-header trust without a correctly configured proxy. Add perimeter login throttling and shared rate limiting before internet exposure; the preview's per-review discussion cap is not an account-wide spend control.

## AI configuration

Set an Anthropic API key and model in both web and worker environments. The adapter calls only `https://api.anthropic.com/v1/messages`, with a 90-second timeout and schema-constrained output, then validates with Pydantic. No browsing/execution tools are provided. Review context is bounded to 100,000 extracted characters; omissions downgrade coverage. Citation verification uses only blocks actually supplied to the model. Discussion retrieves up to 16 relevant blocks using source IDs and keyword overlap, with exact citation validation. It is deliberately simple retrieval; it cannot establish whole-document absence.

Uploaded text and user statements remain untrusted context. An LLM cannot directly write to a finding. Its proposed update is stored pending, then a membership-checked transaction validates evidence/revision and requires explicit acceptance. Quotes and messages are escaped in HTML. Prompt-injection resistance and clinically meaningful precision require empirical evaluation; exact citation checks alone do not establish either.

The live provider path has not been tested against a real API key in this implementation session. Provider behavior, selected model support, token costs and retention terms need verification before partner use. Reference: [Messages API](https://platform.claude.com/docs/en/api/messages/create), [structured outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs).

## Retention and deletion

A project owner can delete the project from its settings. The application first revokes access and fences active workers, removes source files, then cascades deletion of documents/extractions, runs, findings, notes, audit payloads, conversations and proposals. File-removal failure leaves an owner-visible retry action and access revoked. Reruns share immutable originals within their project; removing an already-removed shared file is idempotent. Export is generated in memory from a locked snapshot and is not cached on the server.

Retention is manual in this preview. No automatic retention schedule, backup lifecycle, provider-side deletion integration, or orphan-file sweeper is implemented. A hard process crash between file write and database commit can leave an unreferenced file. Operators must reconcile storage and set a documented retention policy before hosted use. Downloaded originals/reports on users' devices are outside server deletion. Backups must have an agreed expiry; the application does not claim instant backup erasure.

## Before a confidential or active-draft pilot

Confirm partner trial scope and document authorisation. Integrate private managed storage and verified encryption, TLS, regional hosting and backups. Confirm provider processing/retention terms. Establish numeric latency/spend limits and rate limits. Test PostgreSQL concurrency, restore and deletion on the deployed infrastructure. Restrict parser egress and resources. Complete the held-out expert evaluation and unaided usability tasks in the original PRD, reporting sample sizes and uncertainty. These are release gates, not claims that this preview has already passed.
