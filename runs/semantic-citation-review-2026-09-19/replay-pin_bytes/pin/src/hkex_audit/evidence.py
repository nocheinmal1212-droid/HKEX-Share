"""Producer-neutral evidence identities, references and source validation."""
from html import unescape
import re
from .artifacts import fingerprint, identity, require, sha, pointer
from .contracts import validate


def document_id(document, artifacts):
    return identity("document", "1", document, artifacts)


def node_id(document, kind, native_pointer, ordinal=None):
    return identity(kind, "1", document, native_pointer, ordinal)


def validate_evidence(evidence, native=None):
    validate("evidence", evidence)
    doc = evidence["id"]
    require(doc == document_id(evidence["document"], evidence["artifact_ids"]), "document identity mismatch")
    nodes = {n["id"]: n for n in evidence["nodes"]}
    sources = {s["id"]: s for s in evidence["sources"]}
    pages = {p["page_index"]: p for p in evidence["pages"]}
    all_ids = [doc] + [x["id"] for group in (evidence["nodes"], evidence["sources"], evidence["pages"], evidence["limitations"]) for x in group]
    require(len(all_ids) == len(set(all_ids)), "duplicate evidence identity")
    require(len(pages) == len(evidence["pages"]) and sorted(pages) == list(range(len(pages))), "page inventory is not contiguous")
    for page in evidence["pages"]:
        require(page["id"] == node_id(doc, "page", page["native_pointer"]), "page identity mismatch")
        require((page["width"] is None and page["height"] is None) or
                (page["width"] is not None and page["height"] is not None and page["width"] > 0 and page["height"] > 0), "invalid page dimensions")
        for ref in page["printed_label_refs"]:
            require(ref in nodes and nodes[ref]["page_index"] == page["page_index"], "invalid printed label reference")
    for source in sources.values():
        require(source["artifact_id"] in evidence["artifact_ids"], "foreign source artifact")
        require(source["id"] == identity("source", source["artifact_id"], source["pointer"]), "source identity mismatch")
        require(sha(source["text"].encode("utf-8")) == source["sha256"], "source text hash mismatch")
        if native is not None:
            raw = pointer(native, source["pointer"])
            if source["format"] == "json":
                from .artifacts import encode
                raw = encode(raw).decode("utf-8")
            require(raw == source["text"], "literal native source differs")
    for node in nodes.values():
        require(node["id"] == node_id(doc, node["kind"], node["native_pointer"], node["ordinal"]), "occurrence identity mismatch")
        if native is not None:
            pointer(native, node["native_pointer"])
        require(node["page_index"] in pages, "unknown page")
        require(node["native_pointer"].startswith(pages[node["page_index"]]["native_pointer"] + "/"), "occurrence pointer escapes page")
        parent = node["parent_id"]
        if parent is not None:
            require(parent in nodes and nodes[parent]["page_index"] == node["page_index"], "foreign or missing parent")
            visited = {node["id"]}
            while parent is not None:
                require(parent not in visited and parent in nodes, "cyclic or broken parent chain")
                visited.add(parent)
                parent = nodes[parent]["parent_id"]
        if node["bbox"] is not None:
            x0, y0, x1, y1 = node["bbox"]
            require(x0 <= x1 and y0 <= y1, "inverted rectangle")
        parts = []
        for f in node["fragments"]:
            require(f["source_id"] in sources, "unknown text source")
            s = sources[f["source_id"]]
            require(0 <= f["start"] <= f["end"] <= len(s["text"]), "invalid text span")
            text = s["text"][f["start"]:f["end"]]
            require(f["encoding"] != "html_entity" or (s["format"] == "html" and text.startswith("&")), "invalid entity span")
            parts.append(unescape(text) if f["encoding"] == "html_entity" else text)
        require(node["text"] is None or node["text"] == "".join(parts), "decoded text/span mismatch")
        require(node["content_state"] != "blank" or node["text"] == "", "blank state requires literal empty text")
        if node["kind"] == "cell":
            require(node["parent_id"] in nodes and nodes[node["parent_id"]]["kind"] == "table", "cell requires table parent")
            require(node["native_pointer"].startswith(nodes[node["parent_id"]]["native_pointer"] + "/"), "cell source escapes table")
            require(all(node[k] is not None for k in ("row", "column", "row_span", "column_span")), "missing cell coordinates")
            span = node["source_span"]
            require(span is not None and span["source_id"] in sources, "missing cell source span")
            raw = sources[span["source_id"]]
            require(raw["format"] == "html" and raw["pointer"] == node["native_pointer"] and
                    0 <= span["start"] < span["end"] <= len(raw["text"]), "invalid cell source anchor")
            cell_html = raw["text"][span["start"]:span["end"]].lower()
            require(re.match(r"<t[dh](?:\s|>)", cell_html) and re.search(r"</t[dh]\s*>$", cell_html), "cell anchor does not delimit explicit markup")
            require(all(f["source_id"] == span["source_id"] and span["start"] <= f["start"] <= f["end"] <= span["end"] for f in node["fragments"]), "cell fragments escape source anchor")
        else:
            require(all(node[k] is None for k in ("row", "column", "row_span", "column_span")), "cell coordinates on non-cell")
            require(node["source_span"] is None, "unexpected cell anchor")
            require(all(sources[f["source_id"]]["pointer"] == node["native_pointer"] + "/content" for f in node["fragments"]), "text fragment belongs to a different occurrence")
    for table in (n for n in nodes.values() if n["kind"] == "table"):
        require(all(table[k] is not None for k in ("row_count", "column_count", "grid_state")), "missing grid assessment")
        occupied = set()
        source_ends = {}
        for cell in (n for n in nodes.values() if n["kind"] == "cell" and n["parent_id"] == table["id"]):
            span = cell["source_span"]
            require(span["start"] >= source_ends.get(span["source_id"], 0), "cell source anchors overlap or reorder")
            source_ends[span["source_id"]] = span["end"]
            require(cell["row_span"] * cell["column_span"] + len(occupied) <= 500_000, "grid limit")
            for r in range(cell["row"], cell["row"] + cell["row_span"]):
                for c in range(cell["column"], cell["column"] + cell["column_span"]):
                    require(r < table["row_count"] and c < table["column_count"] and (r, c) not in occupied, "invalid grid occupancy")
                    occupied.add((r, c))
        if table["grid_state"] == "resolved":
            require(len(occupied) == table["row_count"] * table["column_count"], "complete grid contains holes")
    for issue in evidence["limitations"]:
        require(issue["region_id"] in nodes or issue["region_id"] in {p["id"] for p in pages.values()} or issue["region_id"] == doc, "unknown limitation region")
    for cap in evidence["capabilities"]:
        require(cap["scope_id"] in all_ids and all(ref in all_ids for ref in cap["evidence_refs"]), "invalid capability references")
    return evidence
