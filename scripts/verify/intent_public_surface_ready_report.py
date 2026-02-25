#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SURFACE_JSON = ROOT / "docs" / "contract" / "intent_public_surface.json"
REPORT_MD = ROOT / "docs" / "ops" / "audit" / "intent_public_surface_report.md"
REPORT_JSON = ROOT / "artifacts" / "backend" / "intent_public_surface_report.json"


def _load_surface() -> dict:
    if not SURFACE_JSON.is_file():
        return {}
    try:
        payload = json.loads(SURFACE_JSON.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _collect_internal_intents() -> set[str]:
    intents: set[str] = set()
    for path in ROOT.glob("addons/*/handlers/*.py"):
        if path.name.startswith("_"):
            continue
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
    return intents


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []
    surface = _load_surface()
    internal_intents = _collect_internal_intents()

    if not surface:
        errors.append("missing or invalid docs/contract/intent_public_surface.json")

    public_intents = surface.get("public_intents") if isinstance(surface.get("public_intents"), list) else []
    seen_public: set[str] = set()
    unresolved: list[str] = []
    governance_exposed: list[str] = []
    mapped_count = 0

    for item in public_intents:
        if not isinstance(item, dict):
            continue
        key = str(item.get("key") or "").strip()
        layer = str(item.get("layer") or "").strip().lower()
        internal = item.get("internal_intents") if isinstance(item.get("internal_intents"), list) else []
        if not key:
            errors.append("public intent entry missing key")
            continue
        if key in seen_public:
            errors.append(f"duplicate public intent key: {key}")
        seen_public.add(key)
        if layer not in {"core", "domain", "governance"}:
            errors.append(f"public intent layer invalid: {key} -> {layer}")
        if not internal:
            errors.append(f"public intent has empty internal mapping: {key}")
            continue
        mapped_count += len(internal)
        for intent in internal:
            ii = str(intent or "").strip()
            if not ii:
                continue
            if ii.startswith("scene.governance.") and layer != "governance":
                governance_exposed.append(f"{key}:{ii}")
            if ii not in internal_intents:
                unresolved.append(f"{key}:{ii}")

    if unresolved:
        errors.append(f"unresolved internal intents: {len(unresolved)}")
    if governance_exposed:
        errors.append("governance intents mapped outside governance layer")

    payload = {
        "ok": len(errors) == 0,
        "summary": {
            "public_intent_count": len(seen_public),
            "internal_intent_catalog_count": len(internal_intents),
            "mapped_internal_count": mapped_count,
            "unresolved_count": len(unresolved),
            "error_count": len(errors),
            "warning_count": len(warnings),
        },
        "unresolved": unresolved,
        "governance_exposed": governance_exposed,
        "errors": errors,
        "warnings": warnings,
    }
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Intent Public Surface Report",
        "",
        f"- public_intent_count: {payload['summary']['public_intent_count']}",
        f"- internal_intent_catalog_count: {payload['summary']['internal_intent_catalog_count']}",
        f"- mapped_internal_count: {payload['summary']['mapped_internal_count']}",
        f"- unresolved_count: {payload['summary']['unresolved_count']}",
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
    lines.extend(["", "## Unresolved", ""])
    if unresolved:
        for item in unresolved:
            lines.append(f"- {item}")
    else:
        lines.append("- none")
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(REPORT_MD))
    print(str(REPORT_JSON))
    if errors:
        print("[intent_public_surface_ready_report] FAIL")
        return 2
    print("[intent_public_surface_ready_report] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
