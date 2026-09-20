"""Offline schema validation; schemas are loaded before the access guard."""
from pathlib import Path
from jsonschema import Draft202012Validator
from referencing import Registry
from .artifacts import read, sha, require

VERSION = "1.0.0"
NAMES = ("evidence", "evidence_manifest", "audit_input", "pipeline_artifacts")
SCHEMAS = {}
HASHES = {}


def preload():
    if SCHEMAS:
        return
    source = Path(__file__).resolve().parents[2] / "schemas"
    directory = source if (source / "evidence.schema.json").is_file() else Path(__file__).parent / "schemas"
    for name in NAMES:
        path = directory / (name + ".schema.json")
        schema = read(path)
        Draft202012Validator.check_schema(schema)
        SCHEMAS[name] = schema
        HASHES[name] = sha(path.read_bytes())


def validate(name, value, definition=None):
    preload()
    schema = SCHEMAS[name]
    if definition:
        schema = {**schema, "$ref": "#/$defs/" + definition}
    errors = sorted(Draft202012Validator(schema, registry=Registry()).iter_errors(value), key=lambda e: str(list(e.path)))
    require(not errors, "schema violation: " + (str(list(errors[0].path)) + " " + errors[0].validator if errors else ""))
