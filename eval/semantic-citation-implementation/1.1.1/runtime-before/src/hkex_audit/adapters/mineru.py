"""Translate the observed middle-JSON profile; no OCR or accounting inference."""
from ..artifacts import encode, identity, require, sha
from ..evidence import document_id, node_id, validate_evidence
from .html_table import parse, MAX_HTML_CHARS, MAX_CELLS, MAX_GRID_SLOTS

CONFIGURATION = {"max_json_bytes": 64 * 1024 * 1024, "max_html_chars": MAX_HTML_CHARS,
                 "max_cells": MAX_CELLS, "max_grid_slots": MAX_GRID_SLOTS,
                 "max_native_depth": 64, "source_view": "page_local_preprocessed"}
TEXT_TYPES = {"text", "title", "header", "footer", "page_number", "page_footnote", "aside_text",
              "image_caption", "image_footnote", "table_caption", "table_footnote", "chart_caption", "chart_footnote"}
CONTAINERS = {"table", "table_body", "list", "image", "image_body", "chart", "chart_body", "line"}


def adapt(native, document, digest):
    require(isinstance(native, dict) and isinstance(native.get("pdf_info"), list) and native["pdf_info"], "native page inventory missing")
    require(native.get("_backend") == "vlm" and native.get("_version_name") == "3.2.2", "unsupported native profile; review before adding support")
    artifact = "sha256-" + digest
    doc = document_id(document, [artifact])
    evidence = {"schema_version": "1.0.0", "identity_policy": "1", "id": doc, "document": document,
                "artifact_ids": [artifact], "pages": [], "nodes": [], "sources": [], "capabilities": [], "limitations": []}

    def limitation(region, code, reason):
        issue = {"id": identity("limitation", region, code), "region_id": region, "code": code, "reason": reason}
        if issue not in evidence["limitations"]:
            evidence["limitations"].append(issue)

    def source(ptr, text, fmt="text"):
        require(isinstance(text, str), "source content is not text")
        s = {"id": identity("source", artifact, ptr), "artifact_id": artifact, "pointer": ptr,
             "text": text, "format": fmt, "sha256": sha(text.encode("utf-8"))}
        evidence["sources"].append(s)
        return s

    def make_node(kind, ptr, page, parent, raw, ordinal=None):
        box = raw.get("bbox")
        valid_box = isinstance(box, list) and len(box) == 4 and all(isinstance(v, (float, int)) and not isinstance(v, bool) for v in box) and box[0] <= box[2] and box[1] <= box[3]
        node = {"id": node_id(doc, kind, ptr, ordinal), "kind": kind, "page_index": page,
                "parent_id": parent, "native_pointer": ptr, "ordinal": ordinal,
                "native_type": str(raw.get("type", "unknown")), "native_index": raw.get("index"),
                "native_angle": raw.get("angle"), "merge_hint": raw.get("cell_merge", raw.get("merge_prev")),
                "bbox": box if valid_box else None, "text": None, "fragments": [], "source_span": None, "content_state": "missing",
                "row": None, "column": None, "row_span": None, "column_span": None,
                "row_count": None, "column_count": None, "grid_state": None}
        evidence["nodes"].append(node)
        if box is not None and not valid_box:
            limitation(node["id"], "invalid_native_geometry", "Native rectangle was retained in source but cannot be used as geometry.")
        return node

    def attach(node, s):
        f = {"source_id": s["id"], "start": 0, "end": len(s["text"]), "encoding": "literal"}
        node["fragments"].append(f)
        node["text"] = (node["text"] or "") + s["text"]
        node["content_state"] = "text" if node["text"] else "blank"

    def visit(raw, ptr, page, parent=None, table=None, depth=0):
        require(depth <= CONFIGURATION["max_native_depth"], "native nesting limit")
        require(isinstance(raw, dict), "invalid native region")
        typ = raw.get("type", "line" if "spans" in raw else "unknown")
        kind = "table" if typ == "table" and "blocks" in raw else "figure" if typ in {"image", "chart"} else "block"
        if "content" in raw and typ in {"image", "chart"}:
            kind = "description"
        elif typ in {"inline_equation", "interline_equation"}:
            kind = "formula"
        node = make_node(kind, ptr, page, parent, raw)
        if kind == "table":
            table = node
            node.update(row_count=0, column_count=0, grid_state="unresolved")
        if typ not in TEXT_TYPES | CONTAINERS:
            node["content_state"] = "unsupported"
            limitation(node["id"], "unsupported_native_kind", "Native region is retained without interpreting its content.")
            source(ptr, encode(raw).decode("utf-8"), "json")
        if kind in {"figure", "description", "formula"}:
            limitation(node["id"], "non_verbatim_or_visual_content", "Visual content or generated description is not certified literal source text.")
        if "content" in raw:
            if isinstance(raw["content"], str):
                attach(node, source(ptr + "/content", raw["content"]))
            else:
                source(ptr + "/content", encode(raw["content"]).decode("utf-8"), "json")
                limitation(node["id"], "non_text_content", "Native content is not a literal string.")
        if kind in {"description", "formula", "figure"}:
            node["content_state"] = "unsupported"
        if "html" in raw:
            s = source(ptr + "/html", raw["html"], "html")
            if table is None:
                limitation(node["id"], "unattached_table_html", "HTML has no native table container.")
            else:
                result = parse(raw["html"])
                if table["grid_state"] != "unresolved" or table["row_count"]:
                    limitation(table["id"], "multiple_html_bodies", "Multiple HTML bodies cannot be assigned to one grid.")
                    table["grid_state"] = "partial"
                else:
                    table.update(row_count=result["rows"], column_count=result["columns"], grid_state=result["state"])
                    for ordinal, cell in enumerate(result["cells"]):
                        n = make_node("cell", ptr + "/html", page, table["id"], {"type": "html_cell"}, ordinal)
                        n.update({k: cell[k] for k in ("row", "column", "row_span", "column_span", "text")})
                        n["fragments"] = [{**f, "source_id": s["id"]} for f in cell["fragments"]]
                        n["source_span"] = {"source_id": s["id"], "start": cell["start"], "end": cell["end"]}
                        n["content_state"] = "unsupported" if cell["unsupported"] else "text" if cell["text"] else "blank"
                        if cell["unsupported"]:
                            limitation(n["id"], "unsupported_cell_content", "Cell contains non-text or unsupported inline markup; raw HTML is preserved.")
                    for code in result["issues"]:
                        limitation(table["id"], code, "HTML grid recovery limitation; inspect the retained source fragment.")
        for field in ("blocks", "lines", "spans"):
            if field in raw:
                if not isinstance(raw[field], list):
                    limitation(node["id"], "malformed_children", "Native child collection is not an array.")
                    source(ptr + "/" + field, encode(raw[field]).decode("utf-8"), "json")
                else:
                    for i, child in enumerate(raw[field]):
                        if isinstance(child, dict):
                            visit(child, ptr + "/" + field + "/" + str(i), page, node["id"], table, depth + 1)
                        else:
                            source(ptr + "/" + field + "/" + str(i), encode(child).decode("utf-8"), "json")
                            limitation(node["id"], "malformed_child", "A native child is not an object.")
        if kind == "table" and node["grid_state"] == "unresolved":
            limitation(node["id"], "unresolved_grid", "No accepted grid is available for this inventoried table.")
        return node

    for i, p in enumerate(native["pdf_info"]):
        require(isinstance(p, dict) and type(p.get("page_idx")) is int and p["page_idx"] == i, "invalid physical page identity")
        ptr = "/pdf_info/" + str(i)
        size = p.get("page_size")
        valid_size = isinstance(size, list) and len(size) == 2 and all(type(v) in {int, float} and v > 0 for v in size)
        page = {"id": node_id(doc, "page", ptr), "page_index": i, "native_pointer": ptr,
                "width": size[0] if valid_size else None, "height": size[1] if valid_size else None,
                "coordinate_frame": "native_page", "units": None, "origin": None, "rotation": None,
                "coordinate_reason": "Native coordinates retained; exact units, origin and page rotation are unverified.", "printed_label_refs": []}
        evidence["pages"].append(page)
        for field in ("preproc_blocks", "discarded_blocks"):
            if not isinstance(p.get(field), list):
                limitation(page["id"], "missing_" + field, "Native page region collection is missing or invalid.")
                continue
            for j, raw in enumerate(p[field]):
                node = visit(raw, ptr + "/" + field + "/" + str(j), i)
                if raw.get("type") == "page_number":
                    descendants = {node["id"]}
                    for child in evidence["nodes"]:
                        if child["parent_id"] in descendants:
                            descendants.add(child["id"])
                            if child["text"] is not None:
                                page["printed_label_refs"].append(child["id"])
        if "para_blocks" in p and p["para_blocks"] != p.get("preproc_blocks"):
            limitation(page["id"], "alternate_view_differs", "Alternate paragraph view differs; page-local fragments are retained without inferring continuation.")
    for name, state, reason in [
        ("literal_native_text", "available", "Selected native strings and source offsets are retained."),
        ("logical_cells", "available", "Per-table grid states qualify recovered cells."),
        ("cell_geometry", "unavailable", "This native profile supplies no cell boxes."),
        ("character_geometry", "unavailable", "Native spans are not character geometry."),
        ("fonts", "unavailable", "No font evidence is supplied by this profile."),
        ("pdf_fidelity", "unknown", "Adapter has no PDF access; schema validity does not establish fidelity."),
        ("accounting_completeness", "unknown", "Relationships are not interpreted by the adapter."),
        ("semantic_headers", "unknown", "HTML cell positions do not establish accounting roles.")]:
        evidence["capabilities"].append({"name": name, "scope_id": doc, "state": state, "reason": reason, "evidence_refs": []})
    validate_evidence(evidence, native)
    return evidence
