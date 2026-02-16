#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
BASELINE_JSON = ROOT / "scripts/verify/baselines/intent_router_purity_guard.json"


def _iter_string_literals(tree: ast.AST):
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            yield node.value, getattr(node, "lineno", 0)
        elif isinstance(node, ast.JoinedStr):
            for part in node.values:
                if isinstance(part, ast.Constant) and isinstance(part.value, str):
                    yield part.value, getattr(part, "lineno", getattr(node, "lineno", 0))


def _load_policy() -> tuple[list[Path], list[str]]:
    payload = {}
    if BASELINE_JSON.is_file():
        payload = json.loads(BASELINE_JSON.read_text(encoding="utf-8"))
    target_files = payload.get("target_files") if isinstance(payload, dict) else None
    forbidden_keywords = payload.get("forbidden_keywords") if isinstance(payload, dict) else None
    targets = []
    for item in target_files if isinstance(target_files, list) else []:
        rel = str(item or "").strip()
        if rel:
            targets.append(ROOT / rel)
    keywords = []
    for item in forbidden_keywords if isinstance(forbidden_keywords, list) else []:
        key = str(item or "").strip().lower()
        if key:
            keywords.append(key)
    if not targets:
        raise RuntimeError("intent router purity policy missing target_files")
    if not keywords:
        raise RuntimeError("intent router purity policy missing forbidden_keywords")
    return targets, keywords


def main() -> int:
    try:
        target_files, forbidden_keywords = _load_policy()
    except Exception as exc:
        print("[intent_router_purity_guard] FAIL")
        print(f"failed to load policy: {exc}")
        return 1

    violations: list[str] = []
    for path in target_files:
        if not path.is_file():
            violations.append(f"missing file: {path.relative_to(ROOT).as_posix()}")
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        try:
            tree = ast.parse(text)
        except SyntaxError as exc:
            violations.append(f"{path.relative_to(ROOT).as_posix()}: syntax error while parsing: {exc}")
            continue
        rel = path.relative_to(ROOT).as_posix()
        for literal, lineno in _iter_string_literals(tree):
            lowered = literal.lower()
            for keyword in forbidden_keywords:
                if keyword in lowered:
                    violations.append(f"{rel}:{lineno}: forbidden industry keyword in intent layer: {keyword}")

    if violations:
        print("[intent_router_purity_guard] FAIL")
        for item in violations:
            print(item)
        return 1

    print("[intent_router_purity_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
