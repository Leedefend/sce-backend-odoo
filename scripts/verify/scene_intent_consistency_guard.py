#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import json
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INTENT_ENRICHED_JSON = ROOT / "docs" / "contract" / "exports" / "intent_catalog_enriched.json"
CAPABILITY_REGISTRY = ROOT / "addons" / "smart_construction_core" / "services" / "capability_registry.py"
SCENE_TILES_XML = ROOT / "addons" / "smart_construction_scene" / "data" / "sc_scene_tiles.xml"
REPORT_JSON = ROOT / "artifacts" / "backend" / "scene_intent_consistency_guard.json"
REPORT_MD = ROOT / "docs" / "ops" / "audit" / "scene_intent_consistency.md"


def _safe_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _known_intent_layer() -> dict[str, str]:
    payload = _safe_json(INTENT_ENRICHED_JSON)
    out: dict[str, str] = {}
    for row in payload.get("intents") or []:
        if not isinstance(row, dict):
            continue
        intent = str(row.get("intent_type") or "").strip()
        if not intent:
            continue
        layer = str(row.get("layer") or "domain").strip().lower()
        if layer not in {"core", "domain", "governance"}:
            layer = "domain"
        out[intent] = layer
    return out


def _capability_rows() -> list[dict]:
    out: list[dict] = []
    if not CAPABILITY_REGISTRY.is_file():
        return out
    try:
        tree = ast.parse(CAPABILITY_REGISTRY.read_text(encoding="utf-8"), filename=str(CAPABILITY_REGISTRY))
    except Exception:
        return out
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Name) or node.func.id != "_cap":
            continue
        if not node.args:
            continue
        if not (isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str)):
            continue
        cap_key = node.args[0].value.strip()
        if not cap_key:
            continue
        intent = "ui.contract"
        for kw in node.keywords:
            if kw.arg == "intent" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                intent = kw.value.value.strip() or "ui.contract"
                break
        scene_key = ""
        if len(node.args) >= 5 and isinstance(node.args[4], ast.Constant) and isinstance(node.args[4].value, str):
            scene_key = node.args[4].value.strip()
        out.append({"capability": cap_key, "intent": intent, "scene_key": scene_key})
    return out


def _scene_capability_refs() -> dict[str, set[str]]:
    refs: dict[str, set[str]] = {}
    if not SCENE_TILES_XML.is_file():
        return refs
    root = ET.fromstring(SCENE_TILES_XML.read_text(encoding="utf-8"))
    for field in root.findall(".//field[@name='payload_json']"):
        raw = field.get("eval") or ""
        if not raw.strip():
            continue
        try:
            payload = ast.literal_eval(raw)
        except Exception:
            continue
        if not isinstance(payload, dict):
            continue
        scene_key = str(payload.get("code") or payload.get("scene_key") or "").strip()
        if not scene_key:
            continue
        bucket = refs.setdefault(scene_key, set())
        for tile in payload.get("tiles") or []:
            if not isinstance(tile, dict):
                continue
            cap_key = str(tile.get("key") or "").strip()
            if cap_key:
                bucket.add(cap_key)
            for req in tile.get("required_capabilities") or []:
                text = str(req or "").strip()
                if text:
                    bucket.add(text)
    return refs


def _scene_codes_from_registry() -> set[str]:
    out: set[str] = set()
    registry_file = ROOT / "addons" / "smart_construction_scene" / "scene_registry.py"
    if not registry_file.is_file():
        return out
    try:
        tree = ast.parse(registry_file.read_text(encoding="utf-8"), filename=str(registry_file))
    except Exception:
        return out
    for node in ast.walk(tree):
        if not isinstance(node, ast.Dict):
            continue
        for k, v in zip(node.keys, node.values):
            if isinstance(k, ast.Constant) and k.value == "code":
                if isinstance(v, ast.Constant) and isinstance(v.value, str):
                    text = v.value.strip()
                    if text:
                        out.add(text)
    return out


def _is_write_intent(intent: str) -> bool:
    low = intent.lower()
    tokens = ("create", "write", "unlink", "delete", "upload", "submit", "approve", "reject", "cancel", "execute", "batch", "import", "rollback", "pin", "set")
    return any(token in low for token in tokens)


def _is_governance_scene(scene_key: str) -> bool:
    low = scene_key.lower()
    if low.startswith("portal."):
        return True
    return any(token in low for token in ("governance", "capability_matrix"))


def main() -> int:
    intent_layer = _known_intent_layer()
    cap_rows = _capability_rows()
    cap_intent = {str(row.get("capability") or ""): str(row.get("intent") or "ui.contract") for row in cap_rows}
    scene_caps = _scene_capability_refs()
    scene_codes = _scene_codes_from_registry()
    scene_codes.update(scene_caps.keys())
    for row in cap_rows:
        key = str(row.get("scene_key") or "").strip()
        if key:
            scene_codes.add(key)

    errors: list[str] = []
    warnings: list[str] = []
    rows: list[dict] = []

    for scene_key in sorted(scene_codes):
        intents = {cap_intent.get(cap, "ui.contract") for cap in scene_caps.get(scene_key, set())}
        for row in cap_rows:
            if str(row.get("scene_key") or "").strip() == scene_key:
                intents.add(str(row.get("intent") or "ui.contract"))
        intents = sorted({text for text in intents if str(text).strip()})
        missing_intents = sorted([intent for intent in intents if intent not in intent_layer])
        write_intents = sorted([intent for intent in intents if _is_write_intent(intent)])
        invalid_write_layers = sorted(
            [
                intent
                for intent in write_intents
                if intent_layer.get(intent) not in {"domain", "governance"}
            ]
        )
        governance_intents = sorted([intent for intent in intents if intent_layer.get(intent) == "governance"])

        if missing_intents:
            errors.append(f"{scene_key}: missing intents {', '.join(missing_intents)}")
        if invalid_write_layers:
            errors.append(
                f"{scene_key}: write intents must be domain/governance, got {', '.join(invalid_write_layers)}"
            )
        if governance_intents and not _is_governance_scene(scene_key):
            errors.append(
                f"{scene_key}: governance intents not allowed in business scene ({', '.join(governance_intents)})"
            )
        if not write_intents:
            warnings.append(f"{scene_key}: no write/execute intents")

        rows.append(
            {
                "scene_key": scene_key,
                "intent_count": len(intents),
                "intents": intents,
                "missing_intents": missing_intents,
                "write_intents": write_intents,
                "invalid_write_layers": invalid_write_layers,
                "governance_intents": governance_intents,
            }
        )

    payload = {
        "ok": len(errors) == 0,
        "summary": {
            "scene_count": len(rows),
            "error_count": len(errors),
            "warning_count": len(warnings),
            "no_write_scene_count": len(warnings),
        },
        "rows": rows,
        "errors": errors,
        "warnings": warnings,
    }
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Scene Intent Consistency",
        "",
        f"- scene_count: {payload['summary']['scene_count']}",
        f"- error_count: {payload['summary']['error_count']}",
        f"- warning_count: {payload['summary']['warning_count']}",
        "",
    ]
    if errors:
        lines.extend(["## Errors", ""])
        for item in errors:
            lines.append(f"- {item}")
    else:
        lines.extend(["## Errors", "", "- none"])
    if warnings:
        lines.extend(["", "## Warnings", ""])
        for item in warnings:
            lines.append(f"- {item}")
    else:
        lines.extend(["", "## Warnings", "", "- none"])
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(REPORT_MD))
    print(str(REPORT_JSON))
    if errors:
        print("[scene_intent_consistency_guard] FAIL")
        return 2
    print("[scene_intent_consistency_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
