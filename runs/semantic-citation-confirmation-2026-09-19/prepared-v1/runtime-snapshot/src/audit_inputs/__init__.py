"""Explicit native/IR file selection. No evaluation imports or discovery."""
from pathlib import Path
from hkex_audit.artifacts import require
from hkex_audit.contracts import validate


def safe_path(path, base=None):
    path = Path(path)
    if not path.is_absolute():
        require(base is not None, 'relative input requires selection-file base')
        path = Path(base) / path
    require(not any(p.is_symlink() for p in [path, *path.parents]), 'symlink input or parent is not permitted')
    resolved = path.resolve()
    require(resolved.is_file(), 'selected input is not a regular file')
    require(resolved.suffix.lower() != '.pdf', 'PDF input is forbidden')
    require('eval' not in resolved.parts and resolved.name not in {'error_detail.jsonl', 'APIKEY.txt'}, 'evaluation/credential input is forbidden')
    return resolved


def descriptors(selection):
    return selection['artifacts'] if selection['mode'] == 'native' else [selection['evidence'], selection['manifest']]


def selected_files(selection, base=None):
    validate('audit_input', selection)
    paths = tuple(safe_path(d['path'], base) for d in descriptors(selection))
    require(len(paths) == len(set(paths)), 'duplicate selected files')
    return paths
