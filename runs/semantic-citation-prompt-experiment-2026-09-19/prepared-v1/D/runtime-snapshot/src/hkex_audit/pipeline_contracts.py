"""Validate downstream fixture interfaces, without executing checks or semantics."""
from decimal import Decimal
from .artifacts import require
from .contracts import validate
from .evidence import validate_evidence


def validate_bundle(evidence, annotations=(), plans=(), checks=(), findings=(), *, category_codes=(), permitted_labels=None):
    validate_evidence(evidence)
    nodes = {n["id"]: n for n in evidence["nodes"]}
    groups = [("annotation", annotations, "annotation_id"), ("plan", plans, "plan_id"),
              ("check", checks, "check_id"), ("finding", findings, "finding_id")]
    indexes = {}
    ids = set(nodes)
    for kind, records, key in groups:
        indexes[kind] = {}
        for record in records:
            validate("pipeline_artifacts", record, kind)
            require(record[key] not in ids, "duplicate downstream identity")
            ids.add(record[key]); indexes[kind][record[key]] = record
            require(all(record[k] == evidence["document"][k] for k in ("doc_id", "variant_id")), "foreign downstream document")
            require(all(ref in nodes for ref in record["evidence_refs"]), "unknown downstream evidence")
            if "category_code" in record:
                require(record["category_code"] in category_codes, "unknown taxonomy category")
                location = record["location"]
                require(location["table_id"] is not None or location["section_id"] is not None, "container location required")
                container = location["table_id"] or location["section_id"]
                require(container in nodes and nodes[container]["page_index"] == location["page_index"], "invalid location")
    for a in annotations:
        for label in a["labels"]:
            require(all(ref in nodes for ref in label["support_refs"]), "unknown label support")
            if a["method"] == "model":
                require(permitted_labels is not None and label["label"] in permitted_labels.get(label["dimension"], ()), "model label outside permitted vocabulary")
        for link in a["links"]:
            require(link["target_id"] in nodes and all(ref in nodes for ref in link["support_refs"]), "invalid semantic link")
    for p in plans:
        require(all(ref in indexes["annotation"] for ref in p["annotation_refs"]), "unknown plan annotation")
        require(all(ref in nodes for ref in p["justification_refs"]), "unknown plan justification")
        require(len({o["evidence_id"] for o in p["operands"]}) == len(p["operands"]), "duplicate operand")
        require(all(o["evidence_id"] in nodes and Decimal(o["coefficient"]) != 0 for o in p["operands"]), "invalid plan operand")
        if p["operation"] == "equality":
            require(len(p["operands"]) == 2, "equality requires two operands")
    for c in checks:
        require(c["plan_id"] is None or c["plan_id"] in indexes["plan"], "unknown check plan")
        require(bool(c["finding_ids"]) == (c["state"] == "failed"), "check/finding state mismatch")
        require(all(f in indexes["finding"] and indexes["finding"][f]["check_id"] == c["check_id"] for f in c["finding_ids"]), "broken finding link")
    for f in findings:
        require(f["check_id"] in indexes["check"] and indexes["check"][f["check_id"]]["state"] == "failed", "finding requires failed check")
        require(f["plan_id"] == indexes["check"][f["check_id"]]["plan_id"], "check/finding plan mismatch")
        require(f["finding_id"] in indexes["check"][f["check_id"]]["finding_ids"], "finding must be linked by check")
        require(all(ref in nodes for ref in f["claim"]["operand_refs"]), "unknown claim operand")
        for span in f["claim"]["span_refs"]:
            require(span["evidence_id"] in nodes, "unknown claim span")
            text = nodes[span["evidence_id"]]["text"]
            require(text is not None and 0 <= span["start"] < span["end"] <= len(text), "invalid claim span")
        require(bool(f["claim"]["operand_refs"] or f["claim"]["span_refs"]), "empty finding claim")
        if f["claim"]["kind"] == "numerical":
            require(f["plan_id"] in indexes["plan"] and f["calculation"] is not None, "numerical finding requires plan/calculation")
            require(Decimal(f["calculation"]["tolerance"]) >= 0, "negative tolerance")
        else:
            require(f["calculation"] is None, "non-numerical finding contains calculation")
    return True
