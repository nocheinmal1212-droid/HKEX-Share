"""Pure formatting functions for taxonomy YAML and error-record JSONL."""

from __future__ import annotations

from collections.abc import Iterable
from io import StringIO
import json
import math
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq
from ruamel.yaml.scalarstring import DoubleQuotedScalarString, FoldedScalarString
from ruamel.yaml.tokens import AliasToken, AnchorToken


TAXONOMY_CATEGORY_KEYS = ("code", "revision", "name", "status", "scope", "description", "examples")
ERROR_RECORD_KEYS = (
    "schema_version", "error_id", "bundle_id", "variant_id", "doc_id", "source_ref",
    "status", "ingestion_status", "category_code", "category_revision", "scoring_status",
    "site_id", "split_group_id", "split", "location", "secondary_locations",
    "original_text", "injected_text", "original_value", "injected_value", "value_delta",
    "relation", "detectability_band", "expected_detectable", "injection_stage",
    "injector_version", "seed", "propagated", "propagation_sites", "description",
    "review_notes", "created_at", "updated_at",
)


class FormatError(ValueError):
    """Raised when a source cannot be formatted without guessing intent."""


def normalize_text(raw: bytes, *, source: str = "<memory>") -> str:
    """Apply the universal UTF-8, LF, whitespace, and final-newline rules."""

    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise FormatError(f"{source}: not valid UTF-8: {exc}") from exc

    if "\x00" in text:
        raise FormatError(f"{source}: NUL bytes are not permitted")
    if "\t" in text:
        line = text.count("\n", 0, text.index("\t")) + 1
        raise FormatError(f"{source}:{line}: tabs are forbidden")

    lines = [line.rstrip(" ") for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines) + "\n"


def _yaml() -> YAML:
    yaml = YAML(typ="rt")
    yaml.allow_unicode = True
    yaml.default_flow_style = False
    yaml.explicit_start = True
    yaml.explicit_end = False
    yaml.indent(mapping=2, sequence=4, offset=2)
    yaml.line_break = "\n"
    yaml.preserve_quotes = True
    yaml.width = 4096
    return yaml


def _reject_yaml_references(text: str, source: str) -> None:
    scanner = _yaml()
    try:
        tokens = scanner.scan(text)
        for token in tokens:
            if isinstance(token, (AnchorToken, AliasToken)):
                mark = token.start_mark
                kind = "anchor" if isinstance(token, AnchorToken) else "alias"
                raise FormatError(
                    f"{source}:{mark.line + 1}:{mark.column + 1}: YAML {kind}s are forbidden"
                )
    except FormatError:
        raise
    except Exception as exc:
        raise FormatError(f"{source}: invalid YAML: {exc}") from exc


def _order_mapping(mapping: CommentedMap, key_order: Iterable[str]) -> None:
    original_last = next(reversed(mapping), None)
    trailing_block_comment = None
    original_comment_entry = mapping.ca.items.get(original_last)
    if original_comment_entry and len(original_comment_entry) > 2:
        candidate = original_comment_entry[2]
        # ruamel represents a comment immediately above the next sequence item
        # as a post-value comment on the previous mapping's final key. Keep that
        # boundary comment final when key ordering changes.
        if candidate is not None and candidate.value.startswith("\n"):
            trailing_block_comment = candidate
            original_comment_entry[2] = None

    known = [key for key in key_order if key in mapping]
    unknown = [key for key in mapping if key not in known]
    for key in (*known, *unknown):
        mapping.move_to_end(key)

    if trailing_block_comment is not None:
        new_last = next(reversed(mapping))
        new_comment_entry = mapping.ca.items.setdefault(new_last, [None, None, None, None])
        if new_comment_entry[2] is not None:
            raise FormatError(
                f"cannot preserve comments while moving {new_last!r} to the end of a mapping"
            )
        new_comment_entry[2] = trailing_block_comment


def _quote_yaml_string(value: str) -> str:
    if ":" in value or "#" in value or value != value.strip():
        return DoubleQuotedScalarString(value)
    return str(value)


def _normalize_yaml_values(node: Any, parent_key: str | None = None) -> Any:
    if isinstance(node, CommentedMap):
        for key in list(node):
            node[key] = _normalize_yaml_values(node[key], str(key))
        return node
    if isinstance(node, CommentedSeq):
        for index in range(len(node)):
            node[index] = _normalize_yaml_values(node[index], parent_key)
        return node
    if isinstance(node, str):
        value = str(node)
        if parent_key == "description":
            if isinstance(node, FoldedScalarString):
                return node
            return FoldedScalarString(value.rstrip("\n"))
        if parent_key in {"precision_target", "recall_target"}:
            return DoubleQuotedScalarString(value)
        if "\n" in value:
            return FoldedScalarString(value.rstrip("\n"))
        return node
    return node


def format_taxonomy(raw: bytes, *, source: str = "taxonomy.yaml") -> bytes:
    """Return a deterministic, comment-preserving taxonomy YAML representation."""

    text = normalize_text(raw, source=source)
    _reject_yaml_references(text, source)
    yaml = _yaml()
    try:
        data = yaml.load(text)
    except Exception as exc:
        raise FormatError(f"{source}: invalid YAML: {exc}") from exc
    if not isinstance(data, CommentedMap):
        raise FormatError(f"{source}: document root must be a mapping")
    categories = data.get("categories")
    if not isinstance(categories, CommentedSeq):
        raise FormatError(f"{source}: categories must be a sequence")

    for category in categories:
        if not isinstance(category, CommentedMap):
            raise FormatError("category must be a mapping")
        _order_mapping(category, TAXONOMY_CATEGORY_KEYS)
    _order_mapping(data, ("spec_version", "taxonomy_version", "categories"))
    _normalize_yaml_values(data)

    stream = StringIO()
    yaml.dump(data, stream)
    return normalize_text(stream.getvalue().encode("utf-8"), source=source).encode("utf-8")


def _reject_constant(value: str) -> None:
    raise FormatError(f"non-finite JSON number {value!r} is forbidden")


def _finite_float(value: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise FormatError("non-finite JSON number is forbidden")
    return number


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise FormatError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _order_record(record: dict[str, Any]) -> dict[str, Any]:
    ordered: dict[str, Any] = {}
    for key in ERROR_RECORD_KEYS:
        if key in record:
            ordered[key] = record[key]
    for key, value in record.items():
        if key not in ordered:
            ordered[key] = value
    return ordered


def format_jsonl(
    raw: bytes, *, source: str = "<errors.jsonl>"
) -> tuple[bytes, tuple[str, ...]]:
    """Return compact, ordered JSONL plus non-fatal soft-limit warnings."""

    text = normalize_text(raw, source=source)
    lines = text[:-1].split("\n")
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(lines, start=1):
        if not line:
            raise FormatError(f"{source}:{line_number}: blank JSONL lines are forbidden")
        try:
            record = json.loads(
                line,
                parse_constant=_reject_constant,
                parse_float=_finite_float,

                object_pairs_hook=_unique_object,
            )
        except FormatError as exc:
            raise FormatError(f"{source}:{line_number}: {exc}") from exc
        except json.JSONDecodeError as exc:
            raise FormatError(f"{source}:{line_number}:{exc.colno}: invalid JSON: {exc.msg}") from exc
        if not isinstance(record, dict):
            raise FormatError(f"{source}:{line_number}: each line must be a JSON object")
        error_id = record.get("error_id")
        if not isinstance(error_id, str) or not error_id:
            raise FormatError(f"{source}:{line_number}: error_id must be a non-empty string")
        records.append(_order_record(record))

    records.sort(key=lambda record: record["error_id"])
    if len({r["error_id"] for r in records}) != len(records):
        raise FormatError("duplicate error_id in JSONL")
    output_lines = [
        json.dumps(record, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
        for record in records
    ]
    warnings: tuple[str, ...] = ()
    return ("\n".join(output_lines) + "\n").encode("utf-8"), warnings


def format_path(path: Path) -> tuple[bytes, tuple[str, ...]]:
    if "corpus" in path.resolve().parts:
        raise FormatError("raw corpus files must not be formatted")
    raw = path.read_bytes()
    if path.name == "taxonomy.yaml":
        return format_taxonomy(raw, source=str(path)), ()
    if path.suffix == ".jsonl":
        return format_jsonl(raw, source=str(path))
    raise FormatError(f"{path}: expected taxonomy.yaml or a .jsonl file")
