#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import json
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INTENT_ENRICHED_JSON = ROOT / "docs" / "contract" / "exports" / "intent_catalog_enriched.json"
SCENE_REGISTRY = ROOT / "addons" / "smart_construction_scene" / "scene_registry.py"
SCENE_TILES_XML = ROOT / "addons" / "smart_construction_scene" / "data" / "sc_scene_tiles.xml"
CAPABILITY_REGISTRY = ROOT / "addons" / "smart_construction_core" / "services" / "capability_registry.py"
REPORT_MD = ROOT / "docs" / "ops" / "audit" / "intent_orphan_report.md"
REPORT_JSON = ROOT / "artifacts" / "backend" / "intent_orphan_report.json"

L0_CORE_INTENTS = {
    "system.init",
    "ui.contract",
    "api.data",
    "api.data.create",
    "api.data.write",
    "api.data.unlink",
    "api.data.batch",
    "execute_button",
    "permission.check",
}
GOVERNANCE_PREFIXES = ("scene.governance.", "scene.package.")
INTERNAL_PREFIXES = (
    "login",
    "bootstrap",
    "contract.",
    "meta.",
    "app.",
    "usage.",
    "scene.health",
    "scene.resolve",
)


def _safe_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _extract_registry_capability_intents() -> dict[str, str]:
    out: dict[str, str] = {}
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
        cap_key = ""
        if isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
            cap_key = node.args[0].value.strip()
        if not cap_key:
            continue
        intent = "ui.contract"
        for kw in node.keywords:
            if kw.arg == "intent" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                intent = kw.value.value.strip() or "ui.contract"
                break
        out[cap_key] = intent
    return out


def _extract_scene_capability_refs() -> dict[str, set[str]]:
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
                value = str(req or "").strip()
                if value:
                    bucket.add(value)
    return refs


def _extract_scene_codes_from_registry() -> set[str]:
    out: set[str] = set()
    if not SCENE_REGISTRY.is_file():
        return out
    try:
        tree = ast.parse(SCENE_REGISTRY.read_text(encoding="utf-8"), filename=str(SCENE_REGISTRY))
    except Exception:
        return out
    for node in ast.walk(tree):
        if not isinstance(node, ast.Dict):
            continue
        key_nodes = node.keys
        value_nodes = node.values
        for key_node, value_node in zip(key_nodes, value_nodes):
            if not (isinstance(key_node, ast.Constant) and key_node.value == "code"):
                continue
            if isinstance(value_node, ast.Constant) and isinstance(value_node.value, str):
                code = value_node.value.strip()
                if code:
                    out.add(code)
    return out


def _classify_layer(intent: str) -> str:
    low = intent.lower()
    if low in L0_CORE_INTENTS or low.startswith("file."):
        return "core"
    if low.startswith(GOVERNANCE_PREFIXES):
        return "governance"
    return "domain"


def _action_for_orphan(intent: str, layer: str) -> str:
    low = intent.lower()
    if layer in {"core", "governance"}:
        return "keep"
    if low.startswith(INTERNAL_PREFIXES):
        return "internal_only"
    return "merge_or_delete"


def main() -> int:
    enriched = _safe_json(INTENT_ENRICHED_JSON)
    intents = enriched.get("intents") if isinstance(enriched.get("intents"), list) else []
    known_intents = sorted(
        {
            str(item.get("intent_type") or "").strip()
            for item in intents
            if isinstance(item, dict) and str(item.get("intent_type") or "").strip()
        }
    )
    cap_intent = _extract_registry_capability_intents()
    scene_caps = _extract_scene_capability_refs()
    scene_codes = _extract_scene_codes_from_registry()
    scene_codes.update(scene_caps.keys())

    used_intents: set[str] = set()
    for scene_key in scene_codes:
        for cap_key in scene_caps.get(scene_key, set()):
            used_intents.add(cap_intent.get(cap_key, "ui.contract"))

    orphan_intents = sorted(set(known_intents) - used_intents)
    rows: list[dict] = []
    for intent in orphan_intents:
        layer = _classify_layer(intent)
        rows.append(
            {
                "intent": intent,
                "layer": layer,
                "action": _action_for_orphan(intent, layer),
            }
        )

    summary = {
        "known_intent_count": len(known_intents),
        "scene_count": len(scene_codes),
        "used_intent_count": len(used_intents),
        "orphan_intent_count": len(rows),
        "core_orphan_count": sum(1 for row in rows if row["layer"] == "core"),
        "governance_orphan_count": sum(1 for row in rows if row["layer"] == "governance"),
        "domain_orphan_count": sum(1 for row in rows if row["layer"] == "domain"),
        "internal_only_suggest_count": sum(1 for row in rows if row["action"] == "internal_only"),
        "merge_or_delete_suggest_count": sum(1 for row in rows if row["action"] == "merge_or_delete"),
    }
    payload = {"ok": True, "summary": summary, "rows": rows}
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Intent Orphan Report",
        "",
        f"- known_intent_count: {summary['known_intent_count']}",
        f"- scene_count: {summary['scene_count']}",
        f"- used_intent_count: {summary['used_intent_count']}",
        f"- orphan_intent_count: {summary['orphan_intent_count']}",
        f"- internal_only_suggest_count: {summary['internal_only_suggest_count']}",
        f"- merge_or_delete_suggest_count: {summary['merge_or_delete_suggest_count']}",
        "",
        "| intent | layer | action |",
        "|---|---|---|",
    ]
    for row in rows:
        lines.append(f"| {row['intent']} | {row['layer']} | {row['action']} |")

    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(REPORT_MD))
    print(str(REPORT_JSON))
    print("[intent_orphan_report] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
