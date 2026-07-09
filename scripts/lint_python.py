#!/usr/bin/env python3
from __future__ import annotations

import ast
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKIP_PARTS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".venv",
    "__pycache__",
    "node_modules",
    "venv",
}


def iter_python_files():
    for path in sorted(ROOT.rglob("*.py")):
        relative = path.relative_to(ROOT)
        if any(part in SKIP_PARTS for part in relative.parts):
            continue
        yield path, relative


def main():
    failures = []
    checked = 0
    for path, relative in iter_python_files():
        checked += 1
        text = path.read_text(encoding="utf-8")
        try:
            ast.parse(text, filename=str(relative))
        except SyntaxError as exc:
            failures.append(f"{relative}:{exc.lineno}:{exc.offset}: {exc.msg}")

        for line_number, line in enumerate(text.splitlines(), start=1):
            if line.rstrip(" \t") != line:
                failures.append(f"{relative}:{line_number}: trailing whitespace")
            indent = line[: len(line) - len(line.lstrip(" \t"))]
            if "\t" in indent:
                failures.append(f"{relative}:{line_number}: tab indentation")

        if text and not text.endswith("\n"):
            failures.append(f"{relative}: missing final newline")

    if failures:
        print("Python lint failed:", file=sys.stderr)
        print("\n".join(failures), file=sys.stderr)
        return 1

    print(f"Python lint passed ({checked} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
