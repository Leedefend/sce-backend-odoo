# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path("/mnt") if Path("/mnt/scripts").exists() else Path(__file__).resolve().parents[2]
ADDONS_ROOT = ROOT / "extra-addons" if (ROOT / "extra-addons").is_dir() else ROOT / "addons"
DOCS_ROOT = ROOT / "docs"
REPORT_PATH = ROOT / "artifacts" / "backend" / "default_scene_semantic_monitor.json"
SCENE_XML_PATH = ADDONS_ROOT / "smart_construction_scene" / "data" / "sc_scene_tiles.xml"
SCENE_REGISTRY_PATH = ADDONS_ROOT / "smart_construction_scene" / "scene_registry.py"
ROLE_SOURCE_PATH = DOCS_ROOT / "product" / "delivery" / "v1" / "role_package_source_v1.json"
MODULE_SOURCE_PATH = DOCS_ROOT / "product" / "delivery" / "v1" / "module_scene_capability_source_v1.json"
SCOREBOARD_PATH = DOCS_ROOT / "product" / "delivery" / "v1" / "delivery_readiness_scoreboard_v1.md"

DEFAULT_SCENE = "default"
DEFAULT_ROUTE = "/workbench?scene=default"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _write_report(payload: dict) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _load_json(path: Path) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _load_default_xml_payload() -> dict:
    tree = ET.parse(str(SCENE_XML_PATH))
    for record in tree.findall(".//record"):
        if record.attrib.get("id") != "sc_scene_version_default_v2":
            continue
        for field in record.findall("field"):
            if field.attrib.get("name") == "payload_json":
                expr = str(field.attrib.get("eval") or "").strip()
                payload = ast.literal_eval(expr)
                return payload if isinstance(payload, dict) else {}
    return {}


def _role_defaults(role_source: dict) -> list[dict]:
    roles = role_source.get("roles") if isinstance(role_source.get("roles"), list) else []
    out: list[dict] = []
    for role in roles:
        if not isinstance(role, dict):
            continue
        out.append(
            {
                "role_key": str(role.get("role_key") or "").strip(),
                "probe_login": str(role.get("probe_login") or "").strip(),
                "default_scene": str(role.get("default_scene") or "").strip(),
            }
        )
    return out


def _module_default_refs(module_source: dict) -> dict:
    scope = module_source.get("delivery_scope") if isinstance(module_source.get("delivery_scope"), dict) else {}
    scope_scene_keys = scope.get("scene_keys") if isinstance(scope.get("scene_keys"), list) else []
    modules = module_source.get("modules") if isinstance(module_source.get("modules"), list) else []
    refs = []
    for module in modules:
        if not isinstance(module, dict):
            continue
        entry_scenes = module.get("entry_scenes") if isinstance(module.get("entry_scenes"), list) else []
        menu_hints = module.get("menu_hints") if isinstance(module.get("menu_hints"), list) else []
        if DEFAULT_SCENE in entry_scenes or DEFAULT_SCENE in menu_hints:
            refs.append(
                {
                    "module_key": str(module.get("module_key") or "").strip(),
                    "entry_scenes": entry_scenes,
                    "menu_hints": menu_hints,
                }
            )
    return {
        "scope_contains_default": DEFAULT_SCENE in scope_scene_keys,
        "module_literal_default_refs": refs,
    }


def _scoreboard_mentions_default() -> bool:
    text = SCOREBOARD_PATH.read_text(encoding="utf-8")
    return "| 主数据与工作台 |" in text and "`default`" in text


errors: list[str] = []
Scene = env["sc.scene"].sudo()  # noqa: F821
scene_records = Scene.search([("code", "=", DEFAULT_SCENE)])
scene = scene_records[:1]
version = scene.active_version_id if scene else False
db_payload = version.payload_json if version and isinstance(version.payload_json, dict) else {}
xml_payload = _load_default_xml_payload()
role_source = _load_json(ROLE_SOURCE_PATH)
module_source = _load_json(MODULE_SOURCE_PATH)
registry_text = SCENE_REGISTRY_PATH.read_text(encoding="utf-8")
registry_contains_default = "'code': 'default'" in registry_text or '"code": "default"' in registry_text
registry_contains_route = DEFAULT_ROUTE in registry_text
role_defaults = _role_defaults(role_source)
literal_default_roles = [row for row in role_defaults if row["default_scene"] == DEFAULT_SCENE]
module_refs = _module_default_refs(module_source)
db_route = (db_payload.get("target") if isinstance(db_payload.get("target"), dict) else {}).get("route")
xml_route = (xml_payload.get("target") if isinstance(xml_payload.get("target"), dict) else {}).get("route")

if len(scene_records) != 1:
    errors.append("default_scene_record_count:%s" % len(scene_records))
if not version:
    errors.append("default_scene_active_version_missing")
if db_payload.get("code") != DEFAULT_SCENE:
    errors.append("db_payload_code_mismatch")
if db_route != DEFAULT_ROUTE:
    errors.append("db_payload_route_mismatch")
if not isinstance(db_payload.get("tiles"), list) or not db_payload.get("tiles"):
    errors.append("db_payload_tiles_empty")
if xml_payload.get("code") != DEFAULT_SCENE:
    errors.append("xml_payload_code_mismatch")
if xml_route != DEFAULT_ROUTE:
    errors.append("xml_payload_route_mismatch")
if not registry_contains_default or not registry_contains_route:
    errors.append("scene_registry_default_fallback_missing")
if literal_default_roles:
    errors.append("role_default_scene_uses_literal_default")
if module_refs["scope_contains_default"] or module_refs["module_literal_default_refs"]:
    errors.append("module_source_uses_literal_default")
if not _scoreboard_mentions_default():
    errors.append("scoreboard_default_row_missing")

payload = {
    "generated_at_utc": _utc_now(),
    "ok": not errors,
    "monitor": "default_scene_semantic_monitor",
    "db": env.cr.dbname,  # noqa: F821
    "company_id": int(env.company.id),  # noqa: F821
    "placeholder_scene_key": DEFAULT_SCENE,
    "placeholder_route": DEFAULT_ROUTE,
    "db_scene": {
        "record_count": len(scene_records),
        "scene_id": int(scene.id) if scene else 0,
        "active_version_id": int(version.id) if version else 0,
        "active_version": str(version.version or "") if version else "",
        "source": str(version.source or "") if version else "",
        "payload_route": db_route or "",
        "tile_keys": [str(tile.get("key") or "") for tile in db_payload.get("tiles", []) if isinstance(tile, dict)],
    },
    "static_scene_xml": {
        "path": str(SCENE_XML_PATH.relative_to(ROOT)),
        "payload_route": xml_route or "",
        "tile_count": len(xml_payload.get("tiles") if isinstance(xml_payload.get("tiles"), list) else []),
    },
    "registry": {
        "path": str(SCENE_REGISTRY_PATH.relative_to(ROOT)),
        "fallback_contains_default": registry_contains_default,
        "fallback_contains_route": registry_contains_route,
    },
    "role_defaults": {
        "path": str(ROLE_SOURCE_PATH.relative_to(ROOT)),
        "role_count": len(role_defaults),
        "default_scenes": sorted({row["default_scene"] for row in role_defaults if row["default_scene"]}),
        "literal_default_roles": literal_default_roles,
    },
    "module_source": {
        "path": str(MODULE_SOURCE_PATH.relative_to(ROOT)),
        **module_refs,
    },
    "scoreboard": {
        "path": str(SCOREBOARD_PATH.relative_to(ROOT)),
        "mentions_default_row": _scoreboard_mentions_default(),
    },
    "errors": errors,
    "report_path": str(REPORT_PATH.relative_to(ROOT)),
}
_write_report(payload)
print(REPORT_PATH)
print("[default_scene_semantic_monitor] PASS" if payload["ok"] else "[default_scene_semantic_monitor] FAIL")
if errors:
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    raise SystemExit(1)
