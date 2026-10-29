# How the review methods work together

Local rules always run. An optional contextual AI review adds interpretation across the eight supported check areas. Neither method selects the correct trial detail, validates trial design, or changes documents without a user's decision.

| Area | Local comparison | Contextual AI assessment |
| --- | --- | --- |
| Trial question | None | Population, treatment/comparator and intended primary outcome across the objective, synopsis and SAP |
| Primary endpoint | Identical surrounding primary-endpoint wording with one explicit time; week/day normalisation | Definition, instrument, calculation, time point and time origin; primary versus secondary outcomes |
| Assessment schedule | None | Endpoint against table headers, assessment rows, required/optional cells, baseline and visit windows |
| Analysis population | Explicitly named primary analysis populations | Inclusion, exclusions, treatment assignment and definitions; distinction between randomised, treated and evaluable populations |
| Primary analysis | None | Alignment of analysis with the endpoint, population, comparison and time point; specific contradictory specifications |
| Missing observations and treatment changes | None | Missing-observation handling and collection/inclusion after treatment changes; distinguish stopping treatment from withdrawing follow-up |
| Sample size | Explicit totals to be randomised | Randomised versus evaluable totals, per-arm counts, allocation, attrition and the endpoint/time named in the justification; no independent power validation |
| Essential operational requirements | None | Specific unresolved dependencies affecting primary-outcome collection; acknowledge details delegated to manuals |

`reviews/assessment.py` contains the rubric supplied to the model. Source documents are untrusted data, not instructions. The model receives the local findings to avoid reporting the same issue again under another check.

## Reading coverage

- **Assessed**: a contextual assessment was returned with verified quotations and no recorded extraction/context limitation requiring a downgrade. This is not a pass result or proof that the interpretation is correct.
- **Partial**: a bounded local comparison ran, or contextual review has limitations. The per-method explanation states which applies.
- **Not assessed**: no comparable local pair was located, contextual review did not run, or its coverage could not be verified. This does not establish that a trial detail is absent.

All eight areas apply within the supported trial scope. A model cannot skip one by claiming it is not applicable. Missing, duplicate or ungrounded contextual coverage is not credited. Local comparison results remain visible even when contextual coverage is missing or invalid.

AI quotations are verified only against the blocks actually supplied to the model. Context omissions and extraction limitations prevent full coverage. Verification establishes quotation provenance, not semantic correctness. Findings still need users to inspect the source and decide what to do.

If AI is unavailable, the review completes with local results and an explicit contextual-review failure notice. Start a new run to retry. Earlier runs and decisions remain unchanged. Reports and final-preview coverage show both methods and their evidence; older saved reviews retain their original coverage format.

## Testing and evaluation

Automated tests exercise the local fixture pack, source verification, coverage merging, missing/duplicate entries, abstention, omitted model context, provider failure and UI/report integration. AI responses in these tests are controlled test data. They do not establish model accuracy.

For a live review evaluation, configure the Anthropic credentials and model in the server/worker environment, then use separate runs of the example pack. Case 05 is the first contextual test: look for the explicit Week 12 schedule contradiction, conflicting post-discontinuation collection/inclusion policies, and the specific coordinator-absence question. Case 01 checks restraint; case 04 checks equivalent time units/windows; case 06 checks resistance to source instructions. Do not require identical wording or an exact count of AI findings.

A trial specialist should review both correct and incorrect findings on additional held-out documents before using this workflow beyond the research preview. No live model or expert evaluation is implied by passing the automated tests.
