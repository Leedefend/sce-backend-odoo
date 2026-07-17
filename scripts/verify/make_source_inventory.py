#!/usr/bin/env python3
"""Resolve repository Make includes for verification guards."""

from __future__ import annotations

import re
import shlex
from pathlib import Path


INCLUDE_PATTERN = re.compile(r"^\s*-?include\s+(?P<paths>[^#\n]+)", re.MULTILINE)


def collect_make_sources(root: Path) -> list[Path]:
    """Return the root Makefile and every statically resolvable included file."""
    pending = [root / "Makefile"]
    sources: list[Path] = []
    seen: set[Path] = set()
    while pending:
        path = pending.pop(0).resolve()
        if path in seen or not path.is_file():
            continue
        seen.add(path)
        sources.append(path)
        text = path.read_text(encoding="utf-8")
        for match in INCLUDE_PATTERN.finditer(text):
            for token in shlex.split(match.group("paths")):
                if "$" in token or "%" in token:
                    continue
                candidate = (root / token).resolve()
                if candidate.is_file() and candidate not in seen:
                    pending.append(candidate)
    return sources


def combined_make_source(root: Path) -> tuple[str, list[Path]]:
    sources = collect_make_sources(root)
    chunks = [
        f"# source: {path.relative_to(root).as_posix()}\n{path.read_text(encoding='utf-8')}"
        for path in sources
    ]
    return "\n\n".join(chunks), sources


def make_logical_lines(text: str) -> list[str]:
    """Join Make continuation lines without changing recipe bodies."""
    logical: list[str] = []
    buffer = ""
    for line in text.splitlines():
        stripped = line.rstrip()
        buffer = f"{buffer} {stripped.lstrip()}".strip() if buffer else stripped
        if buffer.endswith("\\"):
            buffer = buffer[:-1].rstrip()
            continue
        logical.append(buffer)
        buffer = ""
    if buffer:
        logical.append(buffer)
    return logical
