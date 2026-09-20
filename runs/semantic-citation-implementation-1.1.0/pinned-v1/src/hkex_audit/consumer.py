"""IR-only downstream inventory. Does not import an adapter."""
from collections import Counter
from .artifacts import require, fingerprint
from .contracts import validate
from .evidence import validate_evidence
from .evidence_context import build_context, MAX_CONTEXT_BYTES


def inspect(evidence, manifest):
    validate("evidence_manifest", manifest)
    validate_evidence(evidence)
    require(manifest["evidence_id"] == evidence["id"] and manifest["document"] == evidence["document"], "manifest identity mismatch")
    require(manifest["evidence_sha256"] == fingerprint(evidence), "manifest evidence content hash mismatch")
    require(manifest["configuration_sha256"] == fingerprint(manifest["configuration"]), "configuration hash mismatch")
    require([x["artifact_id"] for x in manifest["inputs"]] == evidence["artifact_ids"], "manifest source inventory mismatch")
    require(all(x["artifact_id"] == "sha256-" + x["sha256"] for x in manifest["inputs"]), "invalid manifest artifact identity")
    tables = [n for n in evidence["nodes"] if n["kind"] == "table"]
    summary = {"evidence_id": evidence["id"], "pages": len(evidence["pages"]), "table_regions": len(tables),
               "tables_by_grid_state": dict(sorted(Counter(n["grid_state"] for n in tables).items())),
               "cells": sum(n["kind"] == "cell" for n in evidence["nodes"]),
               "source_fragments": len(evidence["sources"]), "unresolved_regions": len({x["region_id"] for x in evidence["limitations"]}),
               "limitations_by_code": dict(sorted(Counter(x["code"] for x in evidence["limitations"]).items())),
               "structural_validity": "valid", "native_fidelity": "not_reattested", "pdf_fidelity": "unverified",
               "detector_performance": "not_executed"}
    candidates = [n["id"] for n in evidence["nodes"] if n["kind"] in {"cell", "block"} and n["text"] is not None
                  and n["content_state"] in {"text", "blank"} and len(n["text"].encode("utf-8")) < MAX_CONTEXT_BYTES // 4]
    context = build_context(evidence, candidates[:1]) if candidates else {"evidence_id": evidence["id"], "items": []}
    return summary, context
