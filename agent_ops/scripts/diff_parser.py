#!/usr/bin/env python3
from __future__ import annotations

import re
import subprocess

from common import ROOT


def _run_git(args: list[str]) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or f"git {' '.join(args)} failed")
    return completed.stdout


def get_changed_files() -> list[str]:
    names: set[str] = set()
    output = _run_git(["status", "--short", "--untracked-files=all"])
    for line in output.splitlines():
        if not line.strip():
            continue
        path = line[3:].strip()
        if path:
            names.add(path)
    return sorted(names)


def _parse_shortstat(blob: str) -> tuple[int, int]:
    insertions = re.search(r"(\d+) insertions?\(\+\)", blob)
    deletions = re.search(r"(\d+) deletions?\(-\)", blob)
    return (
        int(insertions.group(1)) if insertions else 0,
        int(deletions.group(1)) if deletions else 0,
    )


def get_diff_stat(changed_files: list[str] | None = None) -> dict[str, int]:
    if changed_files is None:
        changed_files = get_changed_files()
    added_lines = 0
    removed_lines = 0
    modified_tracked: list[str] = []
    staged_tracked: list[str] = []

    modified_set = set(_run_git(["ls-files", "-m"]).splitlines())
    staged_set = {line.strip() for line in _run_git(["diff", "--cached", "--name-only"]).splitlines() if line.strip()}
    for path in changed_files:
        if path in modified_set:
            modified_tracked.append(path)
        if path in staged_set:
            staged_tracked.append(path)

    if modified_tracked:
        added, removed = _parse_shortstat(
            _run_git(["diff", "--shortstat", "--no-ext-diff", "--", *modified_tracked])
        )
        added_lines += added
        removed_lines += removed
    if staged_tracked:
        added, removed = _parse_shortstat(
            _run_git(["diff", "--cached", "--shortstat", "--no-ext-diff", "--", *staged_tracked])
        )
        added_lines += added
        removed_lines += removed
    for path in changed_files:
        file_path = ROOT / path
        if file_path.exists() and file_path.is_file():
            tracked = subprocess.run(
                ["git", "ls-files", "--error-unmatch", path],
                cwd=str(ROOT),
                text=True,
                capture_output=True,
                check=False,
            )
            if tracked.returncode == 0:
                continue
            try:
                added_lines += file_path.read_text(encoding="utf-8").count("\n") + 1
            except UnicodeDecodeError:
                continue

    return {
        "files": len(changed_files),
        "added_lines": added_lines,
        "removed_lines": removed_lines,
    }


def get_full_diff(changed_files: list[str] | None = None) -> str:
    if changed_files is None:
        changed_files = get_changed_files()
    if not changed_files:
        return ""
    modified_set = {line.strip() for line in _run_git(["ls-files", "-m"]).splitlines() if line.strip()}
    staged_set = {line.strip() for line in _run_git(["diff", "--cached", "--name-only"]).splitlines() if line.strip()}
    modified_tracked = [path for path in changed_files if path in modified_set]
    staged_tracked = [path for path in changed_files if path in staged_set]
    parts = [
        _run_git(["diff", "--unified=0", "--no-ext-diff", "--no-color", "HEAD", "--", *modified_tracked])
        if modified_tracked
        else "",
        _run_git(["diff", "--cached", "--unified=0", "--no-ext-diff", "--no-color", "--", *staged_tracked])
        if staged_tracked
        else "",
    ]
    for path in changed_files:
        file_path = ROOT / path
        if not file_path.exists() or not file_path.is_file():
            continue
        tracked = subprocess.run(
            ["git", "ls-files", "--error-unmatch", path],
            cwd=str(ROOT),
            text=True,
            capture_output=True,
            check=False,
        )
        if tracked.returncode == 0:
            continue
        try:
            content = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        synthetic = [f"diff --git a/{path} b/{path}", f"+++ b/{path}"]
        synthetic.extend(f"+{line}" for line in content.splitlines())
        parts.append("\n".join(synthetic))
    return "\n".join(part for part in parts if part).strip()
