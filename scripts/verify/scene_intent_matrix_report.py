#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import json
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCENE_REGISTRY = ROOT / "addons" / "smart_construction_scene" / "scene_registry.py"
SCENE_TILES_XML = ROOT / "addons" / "smart_construction_scene" / "data" / "sc_scene_tiles.xml"
SCENE_CATALOG_JSON = ROOT / "docs" / "contract" / "exports" / "scene_catalog.json"
INTENT_ENRICHED_JSON = ROOT / "docs" / "contract" / "exports" / "intent_catalog_enriched.json"
CAPABILITY_REGISTRY = ROOT / "addons" / "smart_construction_core" / "services" / "capability_registry.py"
SCENE_MATRIX_JSON = ROOT / "artifacts" / "backend" / "scene_capability_matrix_report.json"
REPORT_MD = ROOT / "docs" / "ops" / "audit" / "scene_intent_matrix.md"


def _safe_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


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
        kv = {}
        for k, v in zip(node.keys, node.values):
            if isinstance(k, ast.Constant) and isinstance(k.value, str):
                kv[k.value] = v
        code_node = kv.get("code")
        if isinstance(code_node, ast.Constant) and isinstance(code_node.value, str):
            code = code_node.value.strip()
            if code:
                out.add(code)
    return out


def _extract_registry_capability_rows() -> list[dict]:
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
        if len(node.args) < 5:
            continue
        key_node = node.args[0]
        scene_node = node.args[4]
        if isinstance(key_node, ast.Constant) and isinstance(key_node.value, str):
            cap_key = key_node.value.strip()
            if cap_key:
                scene_key = ""
                if isinstance(scene_node, ast.Constant) and isinstance(scene_node.value, str):
                    scene_key = scene_node.value.strip()
                intent = "ui.contract"
                for kw in node.keywords:
                    if kw.arg == "intent" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                        intent = kw.value.value.strip() or "ui.contract"
                out.append({"capability": cap_key, "scene_key": scene_key, "intent": intent})
    return out


def _extract_tiles_scene_capabilities() -> dict[str, set[str]]:
    scene_caps: dict[str, set[str]] = {}
    if not SCENE_TILES_XML.is_file():
        return scene_caps
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
        bucket = scene_caps.setdefault(scene_key, set())
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
    return scene_caps


def _intent_bucket(intent: str) -> str:
    low = intent.lower()
    if any(x in low for x in ("write", "create", "unlink", "delete", "upload", "submit", "approve", "reject", "cancel", "execute", "batch", "import", "rollback", "pin", "set")):
        if "execute" in low or "button" in low:
            return "execute"
        return "write"
    return "read"


def main() -> int:
    scene_codes = _extract_scene_codes_from_registry()
    scene_caps = _extract_tiles_scene_capabilities()
    cap_intent: dict[str, str] = {}
    for row in _extract_registry_capability_rows():
        cap_key = str(row.get("capability") or "").strip()
        if not cap_key:
            continue
        cap_intent[cap_key] = str(row.get("intent") or "ui.contract")
        scene_key = str(row.get("scene_key") or "").strip()
        if scene_key:
            scene_codes.add(scene_key)
            scene_caps.setdefault(scene_key, set()).add(cap_key)

    catalog = _safe_json(SCENE_CATALOG_JSON)
    for row in catalog.get("scenes") or []:
        if not isinstance(row, dict):
            continue
        scene_key = str(row.get("scene_key") or row.get("code") or "").strip()
        if scene_key:
            scene_codes.add(scene_key)
            access = row.get("access") if isinstance(row.get("access"), dict) else {}
            req = access.get("required_capabilities") if isinstance(access.get("required_capabilities"), list) else []
            if req:
                scene_caps.setdefault(scene_key, set()).update(str(x).strip() for x in req if str(x).strip())

    scene_matrix = _safe_json(SCENE_MATRIX_JSON)
    for scene_key in scene_matrix.get("scene_keys") or []:
        text = str(scene_key or "").strip()
        if text:
            scene_codes.add(text)
    for row in scene_matrix.get("matrix") or []:
        if not isinstance(row, dict):
            continue
        scene_key = str(row.get("scene_key") or "").strip()
        if not scene_key:
            continue
        scene_codes.add(scene_key)
        caps = []
        for field in ("declared_capabilities", "required_capabilities", "all_capabilities"):
            vals = row.get(field)
            if isinstance(vals, list):
                caps.extend(vals)
        if caps:
            scene_caps.setdefault(scene_key, set()).update(str(x).strip() for x in caps if str(x).strip())

    enriched = _safe_json(INTENT_ENRICHED_JSON)
    known_intents = {str(x.get("intent_type") or "").strip() for x in (enriched.get("intents") or []) if isinstance(x, dict)}
    known_intents.discard("")

    missing_intent_refs_by_scene: dict[str, list[str]] = {}
    lines = [
        "# Scene Intent Matrix",
        "",
        f"- scene_count: {len(scene_codes)}",
        f"- scene_with_capability_binding: {sum(1 for k in scene_codes if scene_caps.get(k))}",
        "",
        "| scene_key | read intents | write intents | execute intents | 未覆盖 intent | 孤立 scene | capability_refs |",
        "|---|---|---|---|---|---:|---:|",
    ]

    used_intents: set[str] = set()
    uncovered_scenes: list[str] = []
    no_write_scenes: list[str] = []
    for scene_key in sorted(scene_codes):
        refs = sorted(scene_caps.get(scene_key) or [])
        intents = sorted({cap_intent.get(cap, "ui.contract") for cap in refs})
        read = sorted(x for x in intents if _intent_bucket(x) == "read")
        write = sorted(x for x in intents if _intent_bucket(x) == "write")
        execute = sorted(x for x in intents if _intent_bucket(x) == "execute")
        missing_intents = sorted(x for x in intents if x not in known_intents)
        if not intents:
            uncovered_scenes.append(scene_key)
        if intents and not write and not execute:
            no_write_scenes.append(scene_key)
        if missing_intents:
            missing_intent_refs_by_scene[scene_key] = missing_intents
        used_intents.update(intents)
        lines.append(
            f"| {scene_key} | {', '.join(read) if read else '-'} | "
            f"{', '.join(write) if write else '-'} | {', '.join(execute) if execute else '-'} | "
            f"{', '.join(missing_intents) if missing_intents else '-'} | "
            f"{'Y' if not intents else 'N'} | {len(refs)} |"
        )

    orphan_intents = sorted(known_intents - used_intents)
    lines.extend(["", "## Orphan Intents", ""])
    if orphan_intents:
        for intent in orphan_intents:
            lines.append(f"- `{intent}`")
    else:
        lines.append("- none")

    lines.extend(["", "## Uncovered Scenes", ""])
    if uncovered_scenes:
        for scene in uncovered_scenes:
            lines.append(f"- `{scene}`")
    else:
        lines.append("- none")

    lines.extend(["", "## No Write/Execute Scenes", ""])
    if no_write_scenes:
        for scene in sorted(no_write_scenes):
            lines.append(f"- `{scene}`")
    else:
        lines.append("- none")

    lines.extend(["", "## Scene Missing Intent Refs", ""])
    if missing_intent_refs_by_scene:
        for scene in sorted(missing_intent_refs_by_scene.keys()):
            lines.append(f"- `{scene}`: {', '.join(missing_intent_refs_by_scene[scene])}")
    else:
        lines.append("- none")

    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(str(REPORT_MD))
    print("[scene_intent_matrix_report] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
