#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import ast
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONTROLLERS_DIR = ROOT / "addons" / "smart_core" / "controllers"
OUT = ROOT / "artifacts" / "architecture" / "controller_thin_guard_audit_v1.json"

MAX_METHOD_LINES = 80
ORM_HINTS = ["request.env[", ".search(", ".create(", ".write(", ".unlink("]


def _method_line_count(node: ast.FunctionDef | ast.AsyncFunctionDef) -> int:
    end = getattr(node, "end_lineno", None)
    start = getattr(node, "lineno", None)
    if not end or not start:
        return 0
    return max(0, end - start + 1)


def _audit_file(path: Path) -> list[dict]:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    findings: list[dict] = []

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        decorators = [ast.unparse(dec) for dec in node.decorator_list if hasattr(ast, "unparse")]
        if not any("http.route" in deco for deco in decorators):
            continue

        method_source = "\n".join(source.splitlines()[node.lineno - 1 : getattr(node, "end_lineno", node.lineno)])
        line_count = _method_line_count(node)
        orm_hits = [hint for hint in ORM_HINTS if hint in method_source]

        findings.append(
            {
                "file": str(path.relative_to(ROOT)),
                "method": node.name,
                "line_count": line_count,
                "exceeds_thin_threshold": line_count > MAX_METHOD_LINES,
                "orm_hints": orm_hits,
            }
        )

    return findings


def main() -> int:
    all_findings: list[dict] = []
    for path in sorted(CONTROLLERS_DIR.glob("*.py")):
        all_findings.extend(_audit_file(path))

    over_threshold = [item for item in all_findings if item["exceeds_thin_threshold"]]
    orm_in_controller = [item for item in all_findings if item["orm_hints"]]

    status = "PASS" if len(over_threshold) == 0 and len(orm_in_controller) == 0 else "FAIL"

    payload = {
        "status": status,
        "threshold": {"max_method_lines": MAX_METHOD_LINES},
        "summary": {
            "controller_route_method_count": len(all_findings),
            "over_threshold_count": len(over_threshold),
            "orm_hint_count": len(orm_in_controller),
        },
        "over_threshold": over_threshold,
        "orm_hints": orm_in_controller,
        "note": "strict fail-gate: any over-threshold method or ORM hint in route methods is blocking",
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    if status == "PASS":
        print(
            "[verify.arch.controller_thin_guard] PASS "
            f"methods={payload['summary']['controller_route_method_count']} "
            f"over_threshold={payload['summary']['over_threshold_count']} "
            f"orm_hints={payload['summary']['orm_hint_count']}"
        )
        return 0

    print(
        "[verify.arch.controller_thin_guard] FAIL "
        f"methods={payload['summary']['controller_route_method_count']} "
        f"over_threshold={payload['summary']['over_threshold_count']} "
        f"orm_hints={payload['summary']['orm_hint_count']}"
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
