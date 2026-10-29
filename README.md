# Protocol and SAP Review Assistant

A practical second look at your clinical trial documents.

A protocol says **Week 12**. The statistical analysis plan says **Week 24**. Which one does the team intend?

This application helps trial managers, investigators and statisticians find those conflicting details, read the evidence side by side, and keep a record of what they decide. Upload a protocol and an optional statistical analysis plan (SAP), review the findings, and export a report for your team.

![Findings alongside the protocol and SAP passages that support them](docs/images/review-workspace.png)

**Research preview.** You can try the complete workflow with synthetic documents and no API key. Broader AI review is optional. Use public, synthetic or explicitly authorised redacted documents; confidential partner material and patient-level records are outside this preview.

## From documents to decisions

1. **Upload and confirm.** Add a DOCX or text-based PDF protocol, plus a SAP if you have one. Check the detected document versions and trial scope.
2. **Review the findings.** Start with up to five prioritised issues. Each includes source passages, why it matters, and a suggested next step.
3. **Inspect and discuss.** Follow a quotation back to its source location or ask about the selected finding. AI discussion requires provider configuration.
4. **Record a decision.** Mark a finding *Action needed*, *Needs discussion* or *Dismissed*, and add a team note. Proposed changes from discussion require explicit acceptance.
5. **Take the record with you.** Export a DOCX report containing the summary, findings, evidence, decisions and coverage limitations.

Your original documents stay unchanged. A new review run keeps earlier findings and decisions intact.

## Try it locally

You need **Python 3.12+** and [uv](https://docs.astral.sh/uv/getting-started/installation/). From the repository directory:

```sh
uv sync --frozen
uv run python manage.py migrate
uv run python manage.py seed_demo
uv run python manage.py review_worker --once
uv run python manage.py runserver 127.0.0.1:8000
```

Open **[localhost:8000](http://127.0.0.1:8000)**. Sign in as `demo` using the generated password printed by `seed_demo`. The demo includes a synthetic study with three deliberate discrepancies.

To process uploads and new runs, leave the worker running in a **second terminal**:

```sh
uv run python manage.py review_worker
```

Local development uses SQLite and one worker. Running `seed_demo` again preserves the existing account and review. To reset its password:

```sh
uv run python manage.py changepassword demo
```

## Documents to test with

[Download the example pack](examples/pipeline-test-pack.zip) or read the [case guide and expected results](examples/pipeline-test-pack/README.md).

It contains **13 DOCX files and 3 PDFs**, covering matching documents, deliberate discrepancies, equivalent wording, a protocol-only review, contextual questions, embedded instructions and unsupported inputs.

Start with the pair in **`02_discrepancies`**. Local mode should flag:

- A primary assessment at Week 12 versus Week 24.
- Intention-to-treat versus per-protocol primary analysis populations.
- A planned randomised total of 120 versus 100 participants.

Unzip the pack and upload one case at a time. The answer key separates local-check expectations from cases that need AI review.

## Choose the review mode

| | Local checks | AI review |
| --- | --- | --- |
| Setup | No API key needed | Anthropic API key and model required |
| Checks | Three narrow patterns: explicit primary endpoint timing, named primary analysis populations and stated randomised totals | Contextual review across the eight check areas in the PRD |
| Discussion | Retrieves passages and explains existing findings | Answers questions using retrieved source evidence and recorded context |
| Limits | Other check areas are marked unassessed | Bounded document context, extraction limitations and model uncertainty still apply |

To enable AI, export `ANTHROPIC_API_KEY` and `ANTHROPIC_MODEL` in **both** the web and worker environments, then start a new review run. Choose a model that supports structured outputs. The provider receives extracted text and selected discussion context, so check your authorisation and its processing terms first.

See [.env.example](.env.example) for configuration. Django does not automatically load `.env`; Docker Compose does.

## What it is designed to review

The current scope is English-language, two-arm parallel-group randomised superiority trials with a continuous primary endpoint at a fixed time point. Files can be DOCX or text-based PDF, up to 25 MB each and 250 PDF pages. Scans and unresolved tracked changes are unsupported.

Findings are issues and questions for your team, not a verdict on the trial. Quotations are checked against extracted source text, and incomplete checks are disclosed. No findings does **not** mean a trial has passed review.

The preview has not completed the PRD's expert evaluation or unaided usability release gates. Live AI calls are mocked in automated tests. See [operations and remaining work](docs/OPERATIONS.md) for the practical limits.

## Development and setup

The application uses **Django**, server-rendered pages, a separate background worker and private file storage. SQLite makes local setup easy; PostgreSQL is supported for shared environments.

Run the checks:

```sh
uv run ruff check .
uv run ruff format --check .
uv run python manage.py makemigrations --check --dry-run
uv run python manage.py test
```

GitHub CI runs the tests on SQLite and PostgreSQL and checks deployment settings. The test suite includes the upload-ready example documents.

There is no public signup. Create an administrator with `uv run python manage.py createsuperuser`, then manage accounts at `/admin/`. Project owners can grant or revoke access for existing accounts and delete their project's files and review records.

<details>
<summary><strong>Run with Docker Compose</strong></summary>

Create a local `.env` with a strong `SECRET_KEY` and a URL-safe `POSTGRES_PASSWORD`, then run:

```sh
docker compose build
docker compose run --rm web .venv/bin/python manage.py migrate
docker compose run --rm web .venv/bin/python manage.py seed_demo
docker compose up
```

Compose runs a local web server, worker and PostgreSQL database, with persistent volumes for the database and private files. It binds the web server to loopback. Hosted deployment needs TLS, static-file serving and the data controls described in the [operations guide](docs/OPERATIONS.md).

</details>

## Project notes

- [Product requirements](docs/PRD.md) — the intended experience and release gates.
- [PRD review](docs/PRD-REVIEW.md) — assumptions and decisions to confirm.
- [Build plan](docs/BUILD-PLAN.md) — architecture and implementation approach.
- [Delivery backlog](docs/BACKLOG.md) — milestones and acceptance criteria.
- [Operations guide](docs/OPERATIONS.md) — current behavior, configuration and remaining work.
