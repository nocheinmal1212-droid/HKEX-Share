"""Strict serialization and immutable artifact I/O."""
import hashlib
import json
import math
import os
from pathlib import Path
import tempfile

VERSION = "2.0.0"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def unique(pairs):
    result = {}
    for k, v in pairs:
        require(k not in result, f"duplicate JSON key: {k}")
        result[k] = v
    return result


def finite(value):
    if isinstance(value, float):
        require(math.isfinite(value), "non-finite JSON number")
    elif isinstance(value, dict):
        for v in value.values():
            finite(v)
    elif isinstance(value, list):
        for v in value:
            finite(v)
    return value


def loads(text):
    def bad(value):
        raise ValueError(f"non-finite JSON number: {value}")
    return finite(json.loads(text, object_pairs_hook=unique, parse_constant=bad))


def read(path):
    return loads(Path(path).read_text(encoding="utf-8"))


def lines(path):
    raw = Path(path).read_text(encoding="utf-8")
    require(bool(raw.strip()), f"empty JSONL: {path}")
    result = []
    for n, line in enumerate(raw.rstrip("\n").split("\n"), 1):
        require(bool(line.strip()), f"blank JSONL line: {n}")
        obj = loads(line)
        require(isinstance(obj, dict), f"JSONL line {n} must be an object")
        result.append(obj)
    return result


def encoded(obj):
    return (json.dumps(finite(obj), ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode()


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def fingerprint(obj):
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def relative(root, path):
    return Path(path).resolve().relative_to(Path(root).resolve()).as_posix()


def within(root, path):
    candidate = (Path(root) / path).resolve()
    require(candidate.is_relative_to(Path(root).resolve()), f"path escapes root: {path}")
    return candidate


def write_once(path, content):
    """Idempotent immutable output. Changed artifacts require a new revision path."""
    path = Path(path)
    require("corpus" not in path.resolve().parts, "cannot write raw corpus")
    data = content if isinstance(content, bytes) else encoded(content)
    if path.exists():
        require(path.read_bytes() == data, f"immutable artifact differs: {path}; use a new revision path")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    # Link into place without replacing a concurrent writer's artifact.
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as out:
        temp = Path(out.name)
        out.write(data)
        out.flush()
        os.fsync(out.fileno())
    try:
        os.link(temp, path)
    finally:
        temp.unlink()
