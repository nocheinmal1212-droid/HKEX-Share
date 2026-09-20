"""Launch isolated native/IR workers with explicit, immutable artifact outputs."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from . import __version__
from .artifacts import read, read_bytes, loads, encode, sha, fingerprint, require, write_new
from .contracts import preload, validate, HASHES
from .consumer import inspect
from audit_inputs import selected_files, descriptors
from audit_inputs.guard import install

OUTPUTS = ("evidence.json", "manifest.json", "inventory.json", "context.json", "run.json", "stage-failure.json")
CODE_FILES = ("__init__.py", "artifacts.py", "contracts.py", "evidence.py", "adapters/mineru.py", "adapters/html_table.py")


def worker(payload):
    preload()
    selection = payload["selection"]
    validate("audit_input", selection)
    paths = selected_files(selection)
    output = Path(payload["output"])
    native_mode = selection["mode"] == "native"
    if native_mode:
        from .adapters.mineru import adapt, CONFIGURATION
        code_hash = fingerprint({name: sha((Path(__file__).parent / name).read_bytes()) for name in CODE_FILES})
    runtime_names = ("__init__.py", "artifacts.py", "contracts.py", "evidence.py", "consumer.py", "evidence_context.py", "cli.py")
    runtime_hash = fingerprint({name: sha((Path(__file__).parent / name).read_bytes()) for name in runtime_names} |
                               {"audit_inputs/" + name: sha((Path(__file__).parents[1] / "audit_inputs" / name).read_bytes()) for name in ("__init__.py", "guard.py")})
    # Import and warm-up dependencies before installing the guard. No corpus/evaluation
    # reads occur in this bootstrap; all source files are read below under the guard.
    attempts = install(paths, [output / name for name in OUTPUTS])
    started = time.monotonic()
    stage = "adapter" if native_mode else "consumer"
    try:
        raw_files = [read_bytes(p) for p in paths]
        for d, raw in zip(descriptors(selection), raw_files):
            require(sha(raw) == d["sha256"], "selected artifact hash mismatch")
            require(not raw.lstrip().startswith(b"%PDF"), "renamed PDF content is forbidden")
        if native_mode:
            native = loads(raw_files[0])
            evidence = adapt(native, selection["document"], sha(raw_files[0]))
            manifest = {"schema_version": "1.0.0", "identity_policy": "1", "document": selection["document"],
                        "evidence_id": evidence["id"], "evidence_sha256": fingerprint(evidence),
                        "inputs": [{"artifact_id": evidence["artifact_ids"][0], "sha256": sha(raw_files[0]), "role": "middle_json", "path": str(paths[0])}],
                        "producer": {"engine": "MinerU", "backend": native.get("_backend"), "version": native.get("_version_name"),
                                     "checkpoint": None, "settings": None, "unknown_reason": "Checkpoint and extraction settings were not supplied; equivalence is unverified."},
                        "adapter": {"name": "mineru_middle", "version": __version__, "code_sha256": code_hash},
                        "schema_hashes": dict(HASHES), "configuration": CONFIGURATION, "configuration_sha256": fingerprint(CONFIGURATION)}
        else:
            evidence, manifest = map(loads, raw_files)
            validate("evidence_manifest", manifest)
            require(sha(raw_files[0]) == manifest["evidence_sha256"], "evidence/manifest byte hash mismatch")
            require(manifest["document"] == selection["document"], "IR selection document/variant mismatch")
            require(manifest["schema_hashes"] == HASHES, "schema definition hashes differ; explicit compatibility migration required")
        summary, context = inspect(evidence, manifest)
        if native_mode:
            write_new(output / "evidence.json", evidence)
            write_new(output / "manifest.json", manifest)
            summary["native_fidelity"] = "literal_fragments_verified_against_selected_native"
        write_new(output / "inventory.json", summary)
        write_new(output / "context.json", context)
        write_new(output / "run.json", {"stage": stage, "status": "complete", "elapsed_seconds": time.monotonic() - started,
                                        "runtime_code_sha256": runtime_hash, "schema_hashes": dict(HASHES),
                                        "access_attempts": attempts.copy(), "adapter_imported": any(k.startswith("hkex_audit.adapters") for k in sys.modules),
                                        "limitations": ["Preloaded Python/dependency code is trusted; this is not hostile-code containment.",
                                                        "No PDF fidelity, semantic execution or detector performance claim."]})
        return 0
    except Exception as exc:
        failure = {"schema_version": "1.0.0", "stage": stage, "state": "crashed", "error_type": type(exc).__name__,
                   "reason": str(exc) if isinstance(exc, (ValueError, PermissionError)) else "Evidence stage execution failed."}
        validate("pipeline_artifacts", failure, "stage_failure")
        write_new(output / "stage-failure.json", failure)
        write_new(output / "run.json", {"stage": stage, "status": "failed", "access_attempts": attempts.copy()})
        print(json.dumps(failure), file=sys.stderr)
        return 2 if isinstance(exc, ValueError) else 1


def launch(command, selection_path, output):
    selection_path = Path(selection_path).resolve()
    selection = read(selection_path)
    require(selection.get("mode") == {"ingest": "native", "inspect": "ir"}[command], "command/input mode mismatch")
    paths = selected_files(selection, selection_path.parent)
    for desc, path in zip(descriptors(selection), paths):
        desc["path"] = str(path)
    output = Path(output).absolute()
    require(not any(p.is_symlink() for p in [output, *output.parents]), "symlink output is forbidden")
    output = output.resolve()
    require(not output.exists(), "output directory exists; select a new immutable run directory")
    require(not any(x in output.parts for x in ("corpus", "eval", ".git")), "protected output directory")
    require(output != selection_path and output not in paths, "output/input collision")
    output.mkdir(parents=True)
    package_root = str(Path(__file__).resolve().parents[1])
    bootstrap = "import sys,json;sys.path.insert(0,sys.argv[1]);from hkex_audit.cli import worker;sys.exit(worker(json.load(sys.stdin)))"
    proc = subprocess.run([sys.executable, "-I", "-B", "-c", bootstrap, package_root],
                          input=json.dumps({"selection": selection, "output": str(output)}), text=True,
                          capture_output=True, timeout=180, close_fds=True)
    if proc.stderr:
        print(proc.stderr, file=sys.stderr, end="")
    return proc.returncode


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("ingest", "inspect"))
    parser.add_argument("--selection", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        return launch(args.command, args.selection, args.output)
    except (ValueError, OSError, subprocess.TimeoutExpired) as exc:
        print("input/launch failure: " + type(exc).__name__ + ": " + str(exc), file=sys.stderr)
        return 2 if isinstance(exc, ValueError) else 1
