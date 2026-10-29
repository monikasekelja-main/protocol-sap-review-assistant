"""Apply reviewed, source-anchored edits without rebuilding the original DOCX package."""

import copy
import hashlib
import io
import zipfile
from datetime import datetime, timezone

from docx import Document as WordDocument
from docx.table import Table
from lxml import etree

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
REL = "http://schemas.openxmlformats.org/package/2006/relationships"
CT = "http://schemas.openxmlformats.org/package/2006/content-types"
NS = {"w": W}
COMMENT_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments"
PARSER = etree.XMLParser(resolve_entities=False, no_network=True)


def tag(name):
    return f"{{{W}}}{name}"


def original_bytes(document):
    with document.file.open("rb") as file:
        content = file.read()
    if hashlib.sha256(content).hexdigest() != document.sha256:
        raise ValueError(
            "The original file no longer matches this review. Upload it as a new review."
        )
    return content


def locations(content):
    doc = WordDocument(io.BytesIO(content))
    result = {}

    def walk(container, path):
        for i, element in enumerate(container.iter_inner_content(), 1):
            location = f"{path} / block {i}"
            if isinstance(element, Table):
                for r, row in enumerate(element.rows, 1):
                    result[f"{location} / table row {r}"] = (
                        row._tr,
                        " | ".join(c.text for c in row.cells),
                        False,
                    )
                    seen = set()
                    for c, cell in enumerate(row.cells, 1):
                        if cell._tc in seen:
                            continue
                        seen.add(cell._tc)
                        if cell.tables:
                            walk(cell, f"{location} / row {r} / cell {c}")
            else:
                simple = all(child.tag in (tag("pPr"), tag("r")) for child in element._p)
                simple = simple and all(
                    child.tag in (tag("rPr"), tag("t"))
                    for run in element._p.findall(tag("r"))
                    for child in run
                )
                result[location] = (element._p, element.text, simple)

    walk(doc, "DOCX body")
    # Use paths relative to the XML root, never a model-provided XPath.
    return {
        key: {"path": node.getroottree().getpath(node), "text": text, "editable": simple}
        for key, (node, text, simple) in result.items()
    }


def source_target(review, evidence, maps=None):
    document = review.documents.filter(pk=evidence.get("document_id")).first()
    if not document or not document.name.lower().endswith(".docx"):
        raise ValueError("An original DOCX is needed to edit this passage.")
    prefix = f"d{document.pk}:"
    if not evidence.get("block_id", "").startswith(prefix):
        raise ValueError("This passage belongs to another source version.")
    block_id = evidence["block_id"][len(prefix) :]
    block = next((b for b in document.blocks if b["id"] == block_id), None)
    if not block:
        raise ValueError("The source passage could not be located.")
    maps = maps if maps is not None else {}
    if document.pk not in maps:
        maps[document.pk] = locations(original_bytes(document))
    target = maps[document.pk].get(block["location"])
    if not target or target["text"] != block["text"]:
        raise ValueError(
            "The original passage differs from the extracted source. Start a new review."
        )
    start, end = evidence.get("start"), evidence.get("end")
    if (
        not isinstance(start, int)
        or not isinstance(end, int)
        or start < 0
        or end <= start
        or block["text"][start:end] != evidence.get("quote")
    ):
        raise ValueError("The quoted source range no longer matches.")
    return document, block, target


def editing_options(finding, maps=None):
    options = []
    maps = maps if maps is not None else {}
    saved = {
        e["block_id"]: e for e in getattr(getattr(finding, "edit_decision", None), "edits", [])
    }
    documents = {d.pk: d for d in finding.review.documents.all()}
    for index, evidence in enumerate(finding.evidence):
        error, editable, after = "", False, ""
        try:
            _, _, target = source_target(finding.review, evidence, maps)
            editable = target["editable"]
            if not editable:
                error = "This table or formatted passage can receive a Word comment; its text cannot be changed safely here."
        except ValueError as exc:
            error = str(exc)
        if finding.kind == "discrepancy" and len(finding.evidence) == 2:
            other = finding.evidence[1 - index]
            if other["quote"] != evidence["quote"]:
                after = other["quote"]
        if evidence["block_id"] in saved:
            after = saved[evidence["block_id"]]["after"]
        options.append(
            {
                "role": documents[evidence["document_id"]].get_role_display()
                if evidence["document_id"] in documents
                else "Source document",
                "index": index,
                "evidence": evidence,
                "editable": editable,
                "error": error,
                "after": after,
                "selected": evidence["block_id"] in saved,
            }
        )
    return options


def validate_edits(review, edits, excluding=None):
    combined = []
    for decision in (
        review.findings.filter(edit_decision__choice="accepted")
        .exclude(pk=excluding)
        .select_related("edit_decision")
    ):
        combined.extend(decision.edit_decision.edits)
    combined += edits
    maps, occupied = {}, []
    for edit in combined:
        _, _, target = source_target(review, edit, maps)
        if not target["editable"]:
            raise ValueError(
                "This source passage cannot be edited safely. Add a Word comment instead."
            )
        if (
            not isinstance(edit.get("after"), str)
            or not edit["after"].strip()
            or len(edit["after"]) > 6000
        ):
            raise ValueError("Enter replacement text between 1 and 6,000 characters.")
        if any(ord(c) < 32 and c not in "\n\t" for c in edit["after"]):
            raise ValueError("Replacement text contains unsupported control characters.")
        try:
            etree.Element(tag("t")).text = edit["after"]
        except ValueError as exc:
            raise ValueError("Replacement text contains a character Word cannot store.") from exc
        if edit["after"] == edit["quote"]:
            raise ValueError(
                "Replacement text is unchanged. Edit it, reject this suggestion, or add a comment."
            )
        for previous in occupied:
            if (
                previous["block_id"] == edit["block_id"]
                and edit["start"] < previous["end"]
                and previous["start"] < edit["end"]
            ):
                raise ValueError(
                    "Two accepted edits overlap in this passage. Revisit the earlier decision before accepting this one."
                )
        occupied.append(edit)
    return True


def run_fragment(run, text, deleted=False):
    result = etree.Element(tag("r"))
    properties = run.find(tag("rPr"))
    if properties is not None:
        result.append(copy.deepcopy(properties))
    # Preserve meaningful whitespace; split literal newlines/tabs into native Word elements.
    parts = text.split("\n") if not deleted else [text]
    for i, line in enumerate(parts):
        if i:
            etree.SubElement(result, tag("br"))
        for j, part in enumerate(line.split("\t") if not deleted else [line]):
            if j:
                etree.SubElement(result, tag("tab"))
            node = etree.SubElement(result, tag("delText" if deleted else "t"))
            node.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
            node.text = part
    return result


def replace_range(paragraph, edit, tracked, next_id, author, date):
    runs = paragraph.findall(tag("r"))
    cursor, affected = 0, []
    for run in runs:
        text = "".join(node.text or "" for node in run.findall(tag("t")))
        # Replacement runs created earlier may contain breaks; they are always to the right
        # because edits are applied in descending original-offset order.
        length = len(text) + len(run.findall(tag("br"))) + len(run.findall(tag("tab")))
        if cursor < edit["end"] and cursor + length > edit["start"]:
            affected.append((run, text, cursor))
        cursor += length
    if not affected:
        raise ValueError("The edit could not be anchored in the original document.")
    first, first_text, first_start = affected[0]
    last, last_text, last_start = affected[-1]
    position = paragraph.index(first)
    before = first_text[: edit["start"] - first_start]
    after = last_text[edit["end"] - last_start :]
    replacement = []
    if before:
        replacement.append(run_fragment(first, before))
    if tracked:
        deletion = etree.Element(
            tag("del"), {tag("id"): str(next_id()), tag("author"): author, tag("date"): date}
        )
        for run, text, start in affected:
            selected = text[max(0, edit["start"] - start) : min(len(text), edit["end"] - start)]
            deletion.append(run_fragment(run, selected, deleted=True))
        insertion = etree.Element(
            tag("ins"), {tag("id"): str(next_id()), tag("author"): author, tag("date"): date}
        )
        insertion.append(run_fragment(first, edit["after"]))
        replacement.extend([deletion, insertion])
    else:
        replacement.append(run_fragment(first, edit["after"]))
    if after:
        replacement.append(run_fragment(last, after))
    for run, _, _ in affected:
        paragraph.remove(run)
    for node in reversed(replacement):
        paragraph.insert(position, node)


def build_document(review, document, *, tracked=False, reference=None):
    """Clean copy applies accepted edits; Word review copy also annotates pending issues."""
    content = original_bytes(document)
    maps = locations(content)
    with zipfile.ZipFile(io.BytesIO(content)) as source:
        entries = {item.filename: source.read(item.filename) for item in source.infolist()}
        infos = source.infolist()
    xml = etree.fromstring(entries["word/document.xml"], PARSER)
    ids = [int(value) for value in xml.xpath("//@w:id", namespaces=NS) if str(value).isdigit()]
    counter = max(ids, default=0)

    def next_id():
        nonlocal counter
        counter += 1
        return counter

    date = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    decisions = {
        f.pk: f.edit_decision
        for f in review.findings.select_related("edit_decision")
        if hasattr(f, "edit_decision")
    }
    edits = [
        edit
        for d in decisions.values()
        if d.choice == "accepted"
        for edit in d.edits
        if edit["document_id"] == document.pk
    ]
    validate_edits(review, [])
    proposed_findings = set()
    proposed_edits = []
    if tracked and reference and reference != document.role:
        if (
            reference not in ("protocol", "sap")
            or not review.documents.filter(role=reference).exists()
        ):
            raise ValueError("Choose an available reference document.")
        reference_ids = set(review.documents.filter(role=reference).values_list("pk", flat=True))
        for finding in review.findings.all():
            if finding.pk in decisions or finding.kind != "discrepancy":
                continue
            reference_quotes = {
                e["quote"] for e in finding.evidence if e["document_id"] in reference_ids
            }
            targets = [e for e in finding.evidence if e["document_id"] == document.pk]
            if len(reference_quotes) != 1 or len(targets) != 1:
                continue
            candidate = {**targets[0], "after": next(iter(reference_quotes))}
            try:
                # Suggestions remain in the export only. No saved decision is created.
                validate_edits(review, [*proposed_edits, candidate])
            except ValueError:
                continue
            edits.append(candidate)
            proposed_edits.append(candidate)
            proposed_findings.add(finding.pk)
    for edit in sorted(edits, key=lambda e: (e["block_id"], -e["start"])):
        block = next(b for b in document.blocks if f"d{document.pk}:{b['id']}" == edit["block_id"])
        target = maps[block["location"]]
        paragraph = xml.xpath(target["path"], namespaces=NS)[0]
        replace_range(paragraph, edit, tracked, next_id, "Trialwork reviewed edit", date)
    comments = (
        etree.fromstring(entries["word/comments.xml"], PARSER)
        if "word/comments.xml" in entries
        else etree.Element(tag("comments"), nsmap={"w": W})
    )
    comment_ids = [int(c.get(tag("id"))) for c in comments if c.get(tag("id"), "").isdigit()]
    counter = max(counter, max(comment_ids, default=0))
    comment_id = next_id()
    added_comments = False
    for finding in review.findings.all():
        decision = decisions.get(finding.pk)
        if decision and decision.choice == "rejected":
            continue
        if not tracked and (not decision or decision.choice != "commented"):
            continue
        # Anchor contextual comments in every affected source, including questions with no safe edit.
        source_evidence = [e for e in finding.evidence if e["document_id"] == document.pk]
        for evidence in source_evidence:
            _, block, target = source_target(review, evidence, {document.pk: maps})
            node = xml.xpath(target["path"], namespaces=NS)[0]
            paragraph = node if node.tag == tag("p") else node.find(".//" + tag("p"))
            if paragraph is None:
                raise ValueError("A comment could not be anchored to the original passage.")
            start = etree.Element(tag("commentRangeStart"), {tag("id"): str(comment_id)})
            paragraph.insert(1 if paragraph.find(tag("pPr")) is not None else 0, start)
            paragraph.append(etree.Element(tag("commentRangeEnd"), {tag("id"): str(comment_id)}))
            comment_run = etree.SubElement(paragraph, tag("r"))
            etree.SubElement(comment_run, tag("commentReference"), {tag("id"): str(comment_id)})
            comment = etree.SubElement(
                comments,
                tag("comment"),
                {tag("id"): str(comment_id), tag("author"): "Trialwork review", tag("date"): date},
            )
            p = etree.SubElement(comment, tag("p"))
            r = etree.SubElement(p, tag("r"))
            text = etree.SubElement(r, tag("t"))
            text.text = f"{finding.title}\n{finding.why}\nSuggested next step: {finding.action}"
            if decision:
                text.text += f"\nUser review: {decision.get_choice_display()}. {decision.note}"
            elif finding.pk in proposed_findings:
                text.text += f"\nProposed alignment using the {reference.upper()} as the reference you selected. Review this tracked edit in Word; no decision has been saved in the application."
            else:
                text.text += "\nOpen question: no edit direction has been selected. Confirm the intended wording before changing this passage."
            text.text += f"\nOriginal source: {block['text']}"
            comment_id = next_id()
            added_comments = True

    def serialize(root):
        return etree.tostring(root, encoding="UTF-8", xml_declaration=True, standalone=True)

    entries["word/document.xml"] = serialize(xml)
    if tracked:
        settings = etree.fromstring(entries["word/settings.xml"], PARSER)
        tracking = settings.find(tag("trackRevisions"))
        if tracking is None:
            tracking = etree.SubElement(settings, tag("trackRevisions"))
        tracking.set(tag("val"), "true")
        view = settings.find(tag("revisionView"))
        if view is None:
            view = etree.SubElement(settings, tag("revisionView"))
        for option in ("markup", "comments", "insDel", "formatting"):
            view.set(tag(option), "true")
        entries["word/settings.xml"] = serialize(settings)
    if added_comments:
        entries["word/comments.xml"] = serialize(comments)
        rels = etree.fromstring(entries["word/_rels/document.xml.rels"], PARSER)
        if not any(rel.get("Type") == COMMENT_REL for rel in rels):
            used = {rel.get("Id") for rel in rels}
            i = 1
            while f"rId{i}" in used:
                i += 1
            etree.SubElement(
                rels,
                f"{{{REL}}}Relationship",
                Id=f"rId{i}",
                Type=COMMENT_REL,
                Target="comments.xml",
            )
        entries["word/_rels/document.xml.rels"] = serialize(rels)
        types = etree.fromstring(entries["[Content_Types].xml"], PARSER)
        if not any(item.get("PartName") == "/word/comments.xml" for item in types):
            etree.SubElement(
                types,
                f"{{{CT}}}Override",
                PartName="/word/comments.xml",
                ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml",
            )
        entries["[Content_Types].xml"] = serialize(types)
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as target:
        for info in infos:
            target.writestr(info, entries.pop(info.filename))
        for name, data in entries.items():
            target.writestr(name, data)
    output.seek(0)
    return output
