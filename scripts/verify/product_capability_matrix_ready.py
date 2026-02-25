#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MATRIX_JSON = ROOT / "docs" / "product" / "capability_matrix_v1.json"
REPORT_MD = ROOT / "docs" / "ops" / "audit" / "product_capability_matrix_report.md"
REPORT_JSON = ROOT / "artifacts" / "backend" / "product_capability_matrix_report.json"


def _load_matrix() -> dict:
    if not MATRIX_JSON.is_file():
        return {}
    try:
        payload = json.loads(MATRIX_JSON.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _collect_intents() -> set[str]:
    intents: set[str] = set()
    for path in ROOT.glob("addons/*/handlers/*.py"):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except Exception:
            continue
        for node in tree.body:
            if not isinstance(node, ast.ClassDef):
                continue
            for stmt in node.body:
                if not isinstance(stmt, ast.Assign):
                    continue
                names = [t.id for t in stmt.targets if isinstance(t, ast.Name)]
                if "INTENT_TYPE" not in names:
                    continue
                try:
                    value = ast.literal_eval(stmt.value)
                except Exception:
                    continue
                if isinstance(value, str) and value.strip():
                    intents.add(value.strip())
            for stmt in node.body:
                if not isinstance(stmt, ast.Assign):
                    continue
                names = [t.id for t in stmt.targets if isinstance(t, ast.Name)]
                if "ALIASES" not in names:
                    continue
                try:
                    aliases = ast.literal_eval(stmt.value)
                except Exception:
                    continue
                if isinstance(aliases, list):
                    for item in aliases:
                        if isinstance(item, str) and item.strip():
                            intents.add(item.strip())
    return intents


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []
    matrix = _load_matrix()
    if not matrix:
        errors.append("missing docs/product/capability_matrix_v1.json")
    caps = matrix.get("capabilities") if isinstance(matrix.get("capabilities"), list) else []
    if not caps:
        errors.append("capability matrix is empty")
    if len(caps) > 20:
        errors.append(f"capability matrix exceeds v1 limit: {len(caps)} > 20")

    catalog_intents = _collect_intents()
    unique_intents: set[str] = set()
    unique_scenes: set[str] = set()
    unresolved_intents: list[str] = []

    for idx, item in enumerate(caps):
        if not isinstance(item, dict):
            errors.append(f"capability item #{idx + 1} invalid")
            continue
        name = str(item.get("name") or "").strip()
        product_key = str(item.get("product_key") or "").strip()
        intents = item.get("intents") if isinstance(item.get("intents"), list) else []
        scenes = item.get("scenes") if isinstance(item.get("scenes"), list) else []
        roles = item.get("roles") if isinstance(item.get("roles"), list) else []
        if not name or not product_key:
            errors.append(f"capability item #{idx + 1} missing name/product_key")
        if not intents:
            errors.append(f"{product_key or name}: intents empty")
        if not scenes:
            errors.append(f"{product_key or name}: scenes empty")
        if not roles:
            errors.append(f"{product_key or name}: roles empty")
        for intent in intents:
            key = str(intent or "").strip()
            if not key:
                continue
            unique_intents.add(key)
            if key not in catalog_intents:
                unresolved_intents.append(f"{product_key}:{key}")
        for scene in scenes:
            key = str(scene or "").strip()
            if key:
                unique_scenes.add(key)

    if unresolved_intents:
        errors.append(f"unresolved intents in product matrix: {len(unresolved_intents)}")

    payload = {
        "ok": len(errors) == 0,
        "summary": {
            "capability_count": len(caps),
            "mapped_intent_count": len(unique_intents),
            "mapped_scene_count": len(unique_scenes),
            "unresolved_intent_count": len(unresolved_intents),
            "error_count": len(errors),
            "warning_count": len(warnings),
        },
        "unresolved_intents": unresolved_intents,
        "errors": errors,
        "warnings": warnings,
    }
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Product Capability Matrix Report",
        "",
        f"- capability_count: {len(caps)}",
        f"- mapped_intent_count: {len(unique_intents)}",
        f"- mapped_scene_count: {len(unique_scenes)}",
        f"- unresolved_intent_count: {len(unresolved_intents)}",
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
    lines.extend(["", "## Unresolved Intents", ""])
    if unresolved_intents:
        for item in unresolved_intents:
            lines.append(f"- {item}")
    else:
        lines.append("- none")
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(REPORT_MD))
    print(str(REPORT_JSON))
    if errors:
        print("[product_capability_matrix_ready] FAIL")
        return 2
    print("[product_capability_matrix_ready] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
