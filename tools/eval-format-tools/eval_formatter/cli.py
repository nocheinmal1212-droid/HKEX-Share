"""Command-line interface for the evaluation-data formatter."""

from __future__ import annotations

import argparse
import difflib
import os
from pathlib import Path
import sys
import tempfile

from .formatting import FormatError, format_path


def _discover(arguments: list[Path]) -> list[Path]:
    discovered: set[Path] = set()
    for argument in arguments:
        path = argument.resolve()
        if path.is_file():
            discovered.add(path)
            continue
        if not path.exists():
            raise FormatError(f"{argument}: path does not exist")
        if not path.is_dir():
            raise FormatError(f"{argument}: expected a file or directory")

        if "corpus" in path.parts:
            raise FormatError("raw corpus files must not be formatted")
        taxonomy = path / "spec" / "taxonomy.yaml"
        if taxonomy.is_file():
            discovered.add(taxonomy)
        records = path / "eval" / "records"
        if records.is_dir():
            discovered.update(records.rglob("*.jsonl"))
        if "records" in path.parts:
            discovered.update(path.rglob("*.jsonl"))
    if not discovered:
        raise FormatError("no canonical files discovered")
    if any("corpus" in p.resolve().parts for p in discovered):
        raise FormatError("raw corpus files must not be formatted")
    return sorted(discovered, key=lambda candidate: candidate.as_posix())


def _atomic_write(path: Path, content: bytes) -> None:
    mode = path.stat().st_mode
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=f".{path.name}.", delete=False) as out:
            temporary_name = out.name
            out.write(content)
            out.flush()
            os.fsync(out.fileno())
        os.chmod(temporary_name, mode)
        os.replace(temporary_name, path)
    finally:
        if temporary_name is not None and os.path.exists(temporary_name):
            os.unlink(temporary_name)


def _diff(path: Path, before: bytes, after: bytes) -> str:
    before_text = before.decode("utf-8-sig", errors="replace").splitlines(keepends=True)
    after_text = after.decode("utf-8").splitlines(keepends=True)
    return "".join(
        difflib.unified_diff(
            before_text,
            after_text,
            fromfile=str(path),
            tofile=f"{path} (formatted)",
        )
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Format spec/taxonomy.yaml and eval/records/**/*.jsonl deterministically.",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        default=[Path(".")],
        help="files or bundle roots (default: current directory)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="report files that differ instead of writing them",
    )
    parser.add_argument(
        "--diff",
        action="store_true",
        help="show unified diffs (implies --check)",
    )
    parser.add_argument("--quiet", action="store_true", help="suppress normal status output")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    checking = args.check or args.diff
    try:
        paths = _discover(args.paths)
    except FormatError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    pending: list[tuple[Path, bytes, bytes]] = []
    warnings: list[str] = []
    errors: list[str] = []
    for path in paths:
        try:
            before = path.read_bytes()
            after, file_warnings = format_path(path)
            warnings.extend(file_warnings)
            if before != after:
                pending.append((path, before, after))
        except (FormatError, OSError) as exc:
            errors.append(str(exc))

    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)
    for error in errors:
        print(f"error: {error}", file=sys.stderr)
    if errors:
        print("No files were changed.", file=sys.stderr)
        return 2

    if checking:
        for path, before, after in pending:
            print(f"would reformat {path}", file=sys.stderr)
            if args.diff:
                sys.stdout.write(_diff(path, before, after))
        if not args.quiet and not pending:
            print(f"{len(paths)} file(s) already formatted")
        return 1 if pending else 0

    for path, _before, after in pending:
        _atomic_write(path, after)
        if not args.quiet:
            print(f"reformatted {path}")
    if not args.quiet:
        print(f"{len(pending)} changed; {len(paths) - len(pending)} unchanged")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
