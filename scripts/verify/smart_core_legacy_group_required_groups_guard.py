#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
HANDLERS_DIR = ROOT / "addons" / "smart_core" / "handlers"
OUT_JSON = ROOT / "artifacts" / "backend" / "smart_core_legacy_group_required_groups_guard.json"
OUT_MD = ROOT / "docs" / "ops" / "audit" / "smart_core_legacy_group_required_groups_guard.md"

LEGACY_TOKEN = ".group_sc_"
INDUSTRY_PREFIX = "smart_construction_core."


def _literal_str(node: ast.AST | None) -> str:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return str(node.value).strip()
    return ""


def _literal_str_list(node: ast.AST | None) -> list[str]:
    if not isinstance(node, (ast.List, ast.Tuple)):
        return []
    values: list[str] = []
    for item in node.elts:
        text = _literal_str(item)
        if text:
            values.append(text)
    return values


def _extract_violations(path: Path) -> dict[str, Any]:
    payload: dict[str, Any] = {"violations": [], "parse_errors": []}
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except Exception as exc:
        payload["parse_errors"].append(f"parse_error:{path.name}:{exc}")
        return payload

    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        for stmt in node.body:
            if not isinstance(stmt, ast.Assign) or len(stmt.targets) != 1:
                continue
            target = stmt.targets[0]
            if not isinstance(target, ast.Name) or target.id != "REQUIRED_GROUPS":
                continue
            groups = _literal_str_list(stmt.value)
            for group in groups:
                marker = group.lower()
                if LEGACY_TOKEN in marker or marker.startswith(INDUSTRY_PREFIX):
                    payload["violations"].append(
                        {
                            "file": str(path.relative_to(ROOT)),
                            "class": node.name,
                            "group": group,
                            "reason": "legacy_or_industry_group_in_required_groups",
                        }
                    )

    return payload


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> int:
    violations: list[dict[str, str]] = []
    parse_errors: list[str] = []

    for file in sorted(HANDLERS_DIR.glob("*.py")):
        if file.name.startswith("__"):
            continue
        extracted = _extract_violations(file)
        violations.extend(extracted["violations"])
        parse_errors.extend(extracted["parse_errors"])

    report = {
        "status": "PASS" if not (violations or parse_errors) else "FAIL",
        "legacy_token": LEGACY_TOKEN,
        "industry_prefix": INDUSTRY_PREFIX,
        "violations": violations,
        "parse_errors": parse_errors,
    }
    _write(OUT_JSON, json.dumps(report, ensure_ascii=False, indent=2) + "\n")

    lines = [
        "# Smart Core Legacy Group Required Groups Guard",
        "",
        f"- status: {report['status']}",
        f"- legacy_token: {LEGACY_TOKEN}",
        f"- industry_prefix: {INDUSTRY_PREFIX}",
        f"- violation_count: {len(violations)}",
        f"- parse_errors: {', '.join(parse_errors) if parse_errors else '(none)'}",
        "",
        "## Violations",
    ]
    if violations:
        for row in violations:
            lines.append(
                f"- {row['file']}::{row['class']} -> {row['group']} ({row['reason']})"
            )
    else:
        lines.append("- (none)")
    _write(OUT_MD, "\n".join(lines) + "\n")

    if report["status"] != "PASS":
        print("[smart_core_legacy_group_required_groups_guard] FAIL")
        return 1
    print("[smart_core_legacy_group_required_groups_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())

