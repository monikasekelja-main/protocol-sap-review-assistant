"""Review criteria and conservative combination of local and contextual coverage."""

from .schemas import CHECKS, verify_evidence

RUBRIC = {
    "trial_question": "Compare the intended population, treatment/comparator and primary outcome across objective, synopsis, endpoint and SAP. Flag a conflicting trial question only when the same context is established; equivalent wording is not an issue.",
    "endpoint": "Compare primary endpoint definition, instrument/measure, calculation, assessment time and time origin across sections and documents. Separate primary from secondary outcomes. Week 12 and Day 84 are equivalent only with the same origin. Do not duplicate an existing timing finding.",
    "schedule": "Locate the primary assessment and baseline in the schedule, interpreting row labels, visit headers, required/optional cells and visit windows together. Cite endpoint, table headers and relevant row. A readable extracted row does not prove complete schedule extraction. Abstain if measure identity or table structure is uncertain.",
    "population": "Compare the primary analysis population, inclusion/exclusion rules, treatment assignment and relevant definitions. Distinguish randomised, treated, evaluable and per-protocol participants; do not infer equivalence from an acronym alone. Explain consequential contradictions in exclusions.",
    "analysis": "Check whether the primary analysis names the same endpoint, population, treatment comparison and time point. Identify contradictory methods or undefined dependencies from supplied evidence. Do not choose a model, prescribe an analysis, or certify statistical appropriateness.",
    "missing": "Compare missing-observation assumptions and handling, and collection/inclusion after treatment discontinuation, rescue treatment or withdrawal. Distinguish stopping treatment from withdrawing follow-up or consent. An explicit contradiction needs both passages; unclear dependencies require a specific question tied to evidence.",
    "sample_size": "Compare planned randomised totals, per-arm counts, allocation ratio and the endpoint/time named in the justification. Distinguish randomised from evaluable totals and account for attrition and unequal allocation. Check stated consistency, not independent power or sample-size adequacy.",
    "operations": "Identify specific unresolved responsibilities, availability or procedures needed to collect the primary outcome. Name the affected assessment and practical dependency. Acknowledge procedures delegated to an external manual; do not declare them absent or create generic staffing/burden recommendations.",
}
LOCAL_REASONS = {
    "trial_question": "Requires contextual comparison of population, treatment comparison and outcome; local rules do not assess their coherence.",
    "endpoint": "Compares explicit single-time primary endpoint statements only when the surrounding wording matches; normalises weeks and days. Does not assess instrument, calculation or time-origin definitions.",
    "schedule": "Requires interpretation of the primary endpoint against schedule rows, visit headers and windows; local rules do not interpret schedule tables.",
    "population": "Compares explicitly named primary analysis populations. Does not assess eligibility, exclusion rules or treatment-assignment definitions.",
    "analysis": "Requires alignment of the analysis with the endpoint, population and time point; local rules do not assess the analysis specification.",
    "missing": "Requires interpretation of collection and analysis after missing observations or treatment changes; local rules do not assess these policies.",
    "sample_size": "Compares explicitly stated totals to be randomised. Does not assess per-arm allocation, attrition assumptions, endpoint justification or statistical power.",
    "operations": "Requires contextual evidence of an unresolved dependency affecting primary-outcome collection; local rules do not assess responsibilities or delegated procedures.",
}


def combine_coverage(local, contextual, blocks, *, incomplete=False, withheld=()):
    """Keep deterministic coverage when AI abstains; never accept ungrounded AI coverage."""
    output = []
    for base in local:
        key = base["check"]
        matches = [entry for entry in contextual if entry["check"] == key]
        ai = {
            "state": "not_assessed",
            "reason": "No contextual AI assessment was returned for this area.",
            "evidence": [],
        }
        if len(matches) == 1:
            ai = {k: matches[0][k] for k in ("state", "reason", "evidence")}
            try:
                ai["evidence"] = verify_evidence(ai["evidence"], blocks)
                if ai["state"] in ("assessed", "partial") and not ai["evidence"]:
                    raise ValueError("Coverage needs evidence")
                if ai["state"] == "not_applicable":
                    raise ValueError("All eight checks apply within the supported trial scope")
            except ValueError:
                ai = {
                    "state": "not_assessed",
                    "reason": "The contextual coverage claim could not be verified; no assessment is credited.",
                    "evidence": [],
                }
        elif len(matches) > 1:
            ai["reason"] = "Conflicting duplicate contextual coverage entries were withheld."
        if incomplete and ai["state"] == "assessed":
            ai["state"] = "partial"
            ai["reason"] += " Extraction or context limitations prevent complete coverage."
        if key in withheld and ai["state"] in ("assessed", "partial"):
            ai["state"] = "partial"
            ai["reason"] += " An unverifiable finding in this area was withheld."
        state = ai["state"]
        if base["state"] == "partial" and state != "assessed":
            state = "partial"
        output.append(
            {
                "check": key,
                "label": CHECKS[key],
                "state": state,
                "reason": f"Local checks: {base['reason']} Contextual AI: {ai['reason']}",
                "local": base,
                "contextual": ai,
                "evidence": ai["evidence"] or base.get("evidence", []),
            }
        )
    return output
