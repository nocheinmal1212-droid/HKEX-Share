"""Bounded literal-evidence payloads. No prompts, model calls or path dereferencing."""
from .artifacts import encode, require

MAX_IDS = 64
MAX_CONTEXT_BYTES = 24_000


def build_context(evidence, ids):
    require(isinstance(ids, list) and 0 < len(ids) <= MAX_IDS and len(ids) == len(set(ids)), "invalid context ID selection")
    nodes = {n["id"]: n for n in evidence["nodes"]}
    require(all(i in nodes for i in ids), "unknown context ID")
    result = {"evidence_id": evidence["id"], "items": []}
    for i in ids:
        n = nodes[i]
        require(n["kind"] not in {"description", "formula", "figure"} and n["content_state"] != "unsupported", "non-verbatim evidence cannot enter text context")
        result["items"].append({"id": i, "kind": n["kind"], "text": n["text"],
                                "parent_id": n["parent_id"], "page_index": n["page_index"],
                                "content_state": n["content_state"], "fragments": n["fragments"],
                                "limitations": [x for x in evidence["limitations"] if x["region_id"] in {i, n["parent_id"], evidence["id"]}]})
    require(len(encode(result)) <= MAX_CONTEXT_BYTES, "context payload limit exceeded; choose fewer/smaller fragments")
    return result
