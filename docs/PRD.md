# PRD: Protocol and SAP Review Assistant

**Status:** Proposed MVP  
**Primary users:** Clinical trial managers, investigators, and trial statisticians  
**Initial setting:** Small academic and nonprofit teams developing trials for rare and neglected diseases

## 1. Product promise

**Upload your protocol and statistical analysis plan to find conflicting details and important questions for your trial team to resolve.**

The application provides a compact study summary, prioritised findings with source evidence, and chat for discussing the review. Users record decisions and export a report.

**The goal is to help teams identify and resolve consequential issues earlier, with less review effort.**

The application supports a defined set of checks. It does not provide comprehensive scientific, statistical, operational, or regulatory assurance.

## 2. Problem

Small trial teams have limited time and specialist support. As protocols and statistical analysis plans (SAPs) evolve, important details can become inconsistent or remain unclear.

An endpoint may have different assessment times across documents. An analysis may refer to a different population. An essential assessment may be missing from the visit schedule.

Finding these issues takes careful cross-checking. Broad reviews can also produce low-value comments that distract from important decisions.

The product should help users understand an issue, verify its evidence, discuss its meaning, and decide what to do.

## 3. Primary users

| User | Main need |
|---|---|
| Trial manager | Identify unclear requirements and practical dependencies affecting essential data collection. |
| Investigator | Understand whether the documents describe a coherent trial question and what each issue could change. |
| Trial statistician | Inspect precise definitions and identify discrepancies between outcomes, populations, and planned analyses. |

All three use the same workspace. Each finding presents a short explanation and suggested action, with detailed evidence available immediately. Separate role dashboards are outside the MVP.

## 4. Intended outcome

Users should leave a review knowing:

- What the application understands the trial to be testing.
- Which issues deserve attention and why.
- What evidence supports each issue.
- What the team decided.
- What remains unassessed or uncertain.

Success means the tool produces useful clarifications or document changes without creating excessive review work.

## 5. MVP scope

Confirm the supported trial type with a pilot partner before implementation.

The proposed starting scope is:

- English-language documents.
- Two-arm, parallel-group randomised superiority trials.
- A continuous primary endpoint measured at a fixed time point.
- One protocol and one optional SAP.
- DOCX and text-based PDF.

A protocol-only review checks internal consistency. Adding a SAP enables cross-document checks.

### Outside the MVP

- Independent validation of scientific merit, treatment safety, or statistical power.
- Comprehensive statistical or regulatory review.
- Patient-level data and recruitment forecasting.
- Literature research or external browsing.
- Full protocol or SAP drafting.
- Automatic edits to source documents.
- Unsupported trial designs.
- Scanned documents requiring OCR.
- Task assignment, approval chains, and simultaneous collaborative editing.

## 6. Core experience

### Step 1: Upload

The user uploads a protocol and optional SAP.

The application displays detected titles, versions, and dates for quick confirmation. It identifies unsupported inputs before review starts.

### Step 2: Receive the review

The user sees:

- A compact study summary.
- Up to five prioritised findings.
- Specific coverage limitations.
- Access to the remaining findings.

Users do not need to approve a lengthy summary before seeing findings. The application asks targeted clarification questions only when uncertainty materially affects the review.

### Step 3: Inspect and discuss

Selecting a finding displays its supporting passages side by side, with document names, versions, and locations.

The user can select **“Discuss this finding”** to open chat with that finding and its evidence already in context.

General questions about the supplied documents are also supported.

### Step 4: Record a decision

Users select:

- **Action needed**
- **Needs discussion**
- **Dismissed**

An optional note captures the rationale or agreed next step. New findings begin as **Not reviewed**.

### Step 5: Export

The user downloads a DOCX report containing the summary, findings, evidence, decisions, and coverage limitations.

Source documents remain unchanged.

## 7. Review workspace

Use one workspace with three connected elements:

**Study summary:** A compact, expandable description of the trial.

**Findings list:** The persistent review record, showing priorities and decisions.

**Evidence and discussion panel:** Source passages and contextual chat for the selected finding.

Users should not have to search conversation history to discover outstanding issues or recorded decisions.

### Study summary

| Field | Question answered |
|---|---|
| Trial question | What is the trial trying to learn? |
| Population | Who is being studied? |
| Treatment comparison | What is being compared? |
| Primary outcome | What is measured and when? |
| Primary analysis | How is the main comparison planned, and who is included? |

Each field links to evidence. Users can expand supporting assumptions and correct an interpretation.

Corrections are stored as user clarifications. They do not replace source text or conceal discrepancies.

## 8. Findings

The main output is **“Issues and questions for your trial team.”**

Every finding includes:

- A specific title.
- Finding type and provisional priority.
- Why it matters.
- Supporting passages and locations.
- A suggested action or clarification question.
- Review status and optional team note.
- **Discuss this finding**.

### Finding types

| Type | Meaning |
|---|---|
| **Document discrepancy** | Statements in the supplied material conflict. |
| **Question for the team** | A specific ambiguity or dependency requires judgment or additional context. |

Discrepancies require both conflicting passages.

Questions must identify the relevant evidence, what remains unknown, and the decision affected. “Not found” means information was not located in assessed content; it does not prove absence.

### Priorities

- **High:** Could materially affect the primary interpretation or essential trial conduct.
- **Medium:** Creates meaningful ambiguity or a practical issue requiring clarification.
- **Low:** Limited likely impact; displayed after consequential findings.

Explain the consequence alongside the priority. Do not display numerical confidence scores, overall quality scores, compliance badges, or “trial passed” results.

## 9. Supported checks

| Area | What the MVP checks |
|---|---|
| Trial question | Conflicting descriptions of the population, comparison, and primary outcome. |
| Primary endpoint | Agreement of definition, measure, and assessment time across sections and documents. |
| Assessment schedule | Presence and consistent timing of the primary assessment. |
| Analysis population | Agreement of the stated primary population and exclusions. |
| Primary analysis | Alignment with the stated primary outcome and time point. |
| Missing observations and treatment changes | Conflicting or unclear descriptions affecting the intended primary comparison. |
| Sample size | Agreement of totals, allocation, and the endpoint named in the justification. |
| Essential operational requirements | Specific ambiguities about procedures or responsibilities needed to collect the primary outcome. |

The application checks stated information and alignment. It does not independently establish that the design or analysis is appropriate.

## 10. Rules for useful findings

Include a finding only when it:

- Has identifiable supporting evidence.
- Could affect interpretation, execution, or essential data collection.
- Leads to a concrete action or question.
- Adds something beyond existing findings.

Suppress stylistic preferences, equivalent wording, duplicates, and generic recommendations.

For example, **“Consider participant burden”** is insufficient. A useful question identifies the actual schedule requirement and asks whether the team can deliver it.

When a protocol delegates details to another manual, acknowledge that reference and ask for confirmation rather than declaring the information missing.

## 11. Chat behaviour

Chat helps users understand, challenge, and clarify the review.

### Supported interactions

- “Why did you flag this?”
- “Show the passages you compared.”
- “The protocol delegates this to the SAP. Did you account for that?”
- “Which issues should we discuss with the statistician first?”
- “We intend to include outcomes after discontinuation. What is still unclear?”

Responses must distinguish source statements, user-supplied context, and the application’s interpretation.

### Updating the review record

Chat must not silently change findings or decisions.

When discussion supports a change, show a proposed update and require the user to accept it. The same rule applies to adding a new finding.

A user clarification can resolve an interpretation question while leaving a document discrepancy outstanding. The interface must preserve that distinction.

### Boundaries

Chat uses the supplied documents and recorded context. It does not browse, edit source documents, or provide an unrestricted clinical advisory service.

The export includes accepted decisions and notes rather than the full conversation by default.

## 12. Example finding

**Primary assessment time differs between the protocol and SAP**

**Document discrepancy · High priority**

**Evidence**

- Protocol, section 6.1: “Change from baseline at Week 12.”
- SAP, section 4.2: “Change from baseline at Week 24.”

**Why it matters**

The documents specify different time points for the primary comparison.

**Suggested action**

Confirm the intended time point and align both documents and the assessment schedule.

**Status:** Action needed  
**Team note:** Week 12 confirmed; SAP requires revision.

**Discuss this finding**

*Example passages are illustrative.*

## 13. Trust and reliability

### Evidence

- Verify every quotation against extracted source text.
- Preserve PDF page references and stable DOCX section, paragraph, or table references.
- Tie findings and conversations to specific document versions.
- Keep user clarifications separate from documentary evidence.
- Abstain when evidence cannot support a claim.

### Coverage

Display specific limitations near affected findings and in the review summary.

For example:

> Assessment schedule table could not be read. Timing checks involving that table are incomplete.

Avoid relying on a generic disclaimer.

### Review integrity

- Uploaded instructions are treated as document content.
- Failed processing must not erase recorded decisions.
- New review runs must not silently overwrite earlier records.
- Use **Review ready** when processing finishes.
- Reserve **Resolved** for a future release that can verify revised documents.

## 14. Practical implementation

Use a straightforward pipeline:

1. Extract text, tables, and source locations.
2. Build the evidence-linked study summary.
3. Run deterministic consistency checks and contextual AI review.
4. Verify evidence and remove duplicates.
5. Save findings and support contextual discussion.

A single application, background worker, relational database, and private file store are sufficient for a pilot.

Record document hashes and versions of the parser, check catalogue, model, and prompts. Chat should retrieve the relevant review evidence rather than repeatedly analysing all documents.

## 15. Data handling

Start with public, synthetic, or explicitly authorised redacted documents.

Before accepting confidential partner documents, provide:

- Restricted project access.
- Encryption in transit and storage.
- Verified model-provider processing and retention terms.
- Clear retention and deletion rules.
- Deletion covering documents, extracted content, conversations, and reports.
- Logs that exclude document and conversation content.

Patient-level records are not accepted.

## 16. Evaluation

Evaluate finding quality, user understanding, and practical value.

### Expert evaluation

Use held-out protocol/SAP pairs containing genuine issues, introduced discrepancies, and harmless wording differences.

A trial manager, investigator, and statistician assess:

- Summary accuracy.
- Finding correctness and consequence.
- Whether questions are specific and useful.
- Important missed issues.
- False alarms and review burden.

Evaluate discrepancies separately from questions requiring judgment.

### Usability test

Without guidance, each primary user must be able to:

1. Identify what the application believes the trial is testing.
2. Inspect a finding and its source evidence.
3. Challenge the finding in chat.
4. Accept or reject a proposed update.
5. Record a decision.
6. Identify what was not assessed.

Use these tests to refine the workflow before adding features.

### Proposed pilot gates

| Measure | Initial target |
|---|---|
| Summary accuracy | No unresolved material misrepresentation in the held-out release evaluation. |
| Prioritised findings | At least 85% judged valid and actionable. |
| High-priority discrepancy detection | At least 80% recall within supported scope. |
| Evidence | All displayed quotations match their sources. |
| Coverage | All known extraction failures disclosed. |
| Review updates | Every chat-proposed record change requires explicit acceptance. |
| Usability | All three user types complete the core task unaided. |
| Practical value | A majority of pilot reviews produce an expert-confirmed useful clarification or document change. |

Report sample sizes, false alarms per review, review effort, and uncertainty. These are initial targets, not established performance claims.

## 17. Delivery and release

1. **Confirm the partner problem:** Select the supported trial type and examples of useful findings.
2. **Build the review workspace:** Upload, summary, findings, and evidence.
3. **Add contextual chat:** Discussion with explicit acceptance of record changes.
4. **Complete the workflow:** Decisions, export, access, and deletion.
5. **Evaluate and pilot:** Begin retrospectively; move to active drafts after meeting release gates.

The MVP is ready when users can understand the review, verify its evidence, challenge it, record decisions, and recognise its limits without guidance.

**Next likely feature:** Compare revised documents against earlier findings to verify whether requested changes were addressed.