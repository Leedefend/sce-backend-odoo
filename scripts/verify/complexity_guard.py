#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PUBLIC_SURFACE = ROOT / "docs" / "contract" / "intent_public_surface.json"
PRODUCT_MATRIX = ROOT / "docs" / "product" / "capability_matrix_v1.json"
REPORT_MD = ROOT / "docs" / "ops" / "audit" / "complexity_guard_report.md"
REPORT_JSON = ROOT / "artifacts" / "backend" / "complexity_guard_report.json"


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _scene_count_from_registry() -> int:
    total = 0
    for path in ROOT.glob("addons/*/services/scene_registry*.py"):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except Exception:
            continue
        for node in tree.body:
            if not isinstance(node, ast.FunctionDef):
                continue
            if not node.name.startswith("list_"):
                continue
            for stmt in node.body:
                if isinstance(stmt, ast.Return):
                    try:
                        value = ast.literal_eval(stmt.value)
                    except Exception:
                        continue
                    if isinstance(value, list):
                        total += len([x for x in value if isinstance(x, dict)])
    return total


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []
    public = _load_json(PUBLIC_SURFACE)
    matrix = _load_json(PRODUCT_MATRIX)

    public_count = len(public.get("public_intents") or [])
    capability_count = len(matrix.get("capabilities") or [])
    scene_count = _scene_count_from_registry()

    if public_count > 25:
        errors.append(f"public intent count exceeds guard: {public_count} > 25")
    if capability_count > 40:
        errors.append(f"core product capability count exceeds guard: {capability_count} > 40")
    if scene_count <= 0:
        errors.append("scene registry count invalid")
    if scene_count > 400:
        warnings.append(f"scene registry count high: {scene_count}")

    payload = {
        "ok": len(errors) == 0,
        "summary": {
            "public_intent_count": public_count,
            "core_product_capability_count": capability_count,
            "scene_registry_count": scene_count,
            "error_count": len(errors),
            "warning_count": len(warnings),
        },
        "errors": errors,
        "warnings": warnings,
    }
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Complexity Guard Report",
        "",
        f"- public_intent_count: {public_count}",
        f"- core_product_capability_count: {capability_count}",
        f"- scene_registry_count: {scene_count}",
        f"- error_count: {len(errors)}",
        f"- warning_count: {len(warnings)}",
        "",
        "## Errors",
        "",
    ]
    if errors:
        for item in errors:
            lines.append(f"- {item}")
    else:
        lines.append("- none")
    lines.extend(["", "## Warnings", ""])
    if warnings:
        for item in warnings:
            lines.append(f"- {item}")
    else:
        lines.append("- none")
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(REPORT_MD))
    print(str(REPORT_JSON))
    if errors:
        print("[complexity_guard] FAIL")
        return 2
    print("[complexity_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
