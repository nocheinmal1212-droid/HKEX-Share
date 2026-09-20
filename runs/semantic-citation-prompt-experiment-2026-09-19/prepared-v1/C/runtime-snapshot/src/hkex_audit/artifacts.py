"""Strict, bounded JSON and deterministic artifact identities."""
import hashlib
import json
import math
from pathlib import Path

MAX_BYTES = 64 * 1024 * 1024


def require(condition, message):
    if not condition:
        raise ValueError(message)


def loads(raw):
    def pairs(items):
        result = {}
        for k, v in items:
            require(k not in result, "duplicate JSON key")
            result[k] = v
        return result

    def finite(s):
        n = float(s)
        require(math.isfinite(n), "non-finite JSON number")
        return n

    def constant(_):
        raise ValueError("non-finite JSON constant")

    require(len(raw) <= MAX_BYTES, "JSON byte/character limit exceeded")
    try:
        return json.loads(raw, object_pairs_hook=pairs, parse_float=finite, parse_constant=constant)
    except (RecursionError, UnicodeDecodeError) as exc:
        raise ValueError("invalid or excessively nested JSON") from exc


def read_bytes(path):
    with open(path, "rb") as stream:
        data = stream.read(MAX_BYTES + 1)
    require(len(data) <= MAX_BYTES, "artifact byte limit exceeded")
    return data


def read(path):
    return loads(read_bytes(path))


def encode(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n").encode("utf-8")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def fingerprint(value):
    return sha(encode(value))


def identity(kind, *parts):
    return kind + "-" + fingerprint(list(parts))


def pointer(value, path):
    require(path == "" or path.startswith("/"), "invalid JSON Pointer")
    for part in path.split("/")[1:]:
        part = part.replace("~1", "/").replace("~0", "~")
        try:
            value = value[int(part)] if isinstance(value, list) else value[part]
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise ValueError("unresolved native pointer") from exc
    return value


def write_new(path, value):
    """Never replace an artifact; identical writes are idempotent."""
    path = Path(path)
    data = encode(value)
    if path.exists():
        require(read_bytes(path) == data, "existing artifact differs; select a new output directory")
        return
    with path.open("xb") as stream:
        stream.write(data)
