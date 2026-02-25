#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import json
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CAPABILITY_REGISTRY = ROOT / "addons" / "smart_construction_core" / "services" / "capability_registry.py"
SCENE_TILES_XML = ROOT / "addons" / "smart_construction_scene" / "data" / "sc_scene_tiles.xml"
INTENT_ENRICHED_JSON = ROOT / "docs" / "contract" / "exports" / "intent_catalog_enriched.json"
REPORT_MD = ROOT / "docs" / "ops" / "audit" / "capability_scene_matrix.md"
REPORT_JSON = ROOT / "artifacts" / "backend" / "capability_scene_matrix.json"


def _safe_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _extract_capability_registry() -> dict[str, dict]:
    out: dict[str, dict] = {}
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
        if len(node.args) < 5:
            continue
        if not (isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str)):
            continue
        cap_key = node.args[0].value.strip()
        if not cap_key:
            continue
        scene_key = ""
        if isinstance(node.args[4], ast.Constant) and isinstance(node.args[4].value, str):
            scene_key = node.args[4].value.strip()
        intent = "ui.contract"
        for kw in node.keywords:
            if kw.arg == "intent" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                intent = kw.value.value.strip() or "ui.contract"
                break
        out[cap_key] = {"scene_key": scene_key, "intent": intent}
    return out


def _extract_scene_refs() -> dict[str, set[str]]:
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


def main() -> int:
    registry = _extract_capability_registry()
    scene_refs = _extract_scene_refs()
    known_intents = {
        str(row.get("intent_type") or "").strip()
        for row in (_safe_json(INTENT_ENRICHED_JSON).get("intents") or [])
        if isinstance(row, dict) and str(row.get("intent_type") or "").strip()
    }

    registry_keys = sorted(registry.keys())
    scene_ref_keys = sorted({cap for caps in scene_refs.values() for cap in caps})
    consumed_capabilities = sorted([key for key in registry_keys if key in scene_ref_keys])
    unused_capabilities = sorted([key for key in registry_keys if key not in scene_ref_keys])
    scene_missing_capabilities = sorted([key for key in scene_ref_keys if key not in registry])
    capabilities_without_intent = sorted(
        [key for key, row in registry.items() if str(row.get("intent") or "").strip() not in known_intents]
    )

    summary = {
        "registry_capability_count": len(registry_keys),
        "scene_ref_capability_count": len(scene_ref_keys),
        "consumed_capability_count": len(consumed_capabilities),
        "unused_capability_count": len(unused_capabilities),
        "scene_missing_capability_count": len(scene_missing_capabilities),
        "capability_without_intent_count": len(capabilities_without_intent),
    }
    payload = {
        "ok": True,
        "summary": summary,
        "registry_capabilities": registry_keys,
        "scene_ref_capabilities": scene_ref_keys,
        "unused_capabilities": unused_capabilities,
        "scene_missing_capabilities": scene_missing_capabilities,
        "capabilities_without_intent": capabilities_without_intent,
        "scene_ref_matrix": {
            scene: sorted(caps)
            for scene, caps in sorted(scene_refs.items(), key=lambda item: item[0])
        },
    }
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Capability Scene Matrix",
        "",
        f"- registry_capability_count: {summary['registry_capability_count']}",
        f"- scene_ref_capability_count: {summary['scene_ref_capability_count']}",
        f"- consumed_capability_count: {summary['consumed_capability_count']}",
        f"- unused_capability_count: {summary['unused_capability_count']}",
        f"- scene_missing_capability_count: {summary['scene_missing_capability_count']}",
        f"- capability_without_intent_count: {summary['capability_without_intent_count']}",
        "",
        "## Unused Capabilities",
        "",
    ]
    if unused_capabilities:
        for key in unused_capabilities:
            lines.append(f"- `{key}`")
    else:
        lines.append("- none")

    lines.extend(["", "## Scene Missing Capabilities", ""])
    if scene_missing_capabilities:
        for key in scene_missing_capabilities:
            lines.append(f"- `{key}`")
    else:
        lines.append("- none")

    lines.extend(["", "## Capabilities Without Intent", ""])
    if capabilities_without_intent:
        for key in capabilities_without_intent:
            lines.append(f"- `{key}`")
    else:
        lines.append("- none")

    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(str(REPORT_MD))
    print(str(REPORT_JSON))
    print("[capability_scene_matrix_report] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
