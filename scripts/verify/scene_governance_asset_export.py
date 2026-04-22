#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import sys
import types
import xml.etree.ElementTree as ET
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SCENE_DIR = ROOT / "addons" / "smart_construction_scene"
SMART_CORE_DIR = ROOT / "addons" / "smart_core"
ASSET_DIR = ROOT / "docs" / "architecture" / "scene-governance" / "assets" / "generated"

AUTHORITY_CSV = ASSET_DIR / "scene_authority_matrix_current_v1.csv"
FAMILY_CSV = ASSET_DIR / "scene_family_inventory_current_v1.csv"
MENU_CSV = ASSET_DIR / "menu_scene_mapping_current_v1.csv"
PROVIDER_CSV = ASSET_DIR / "provider_completeness_current_v1.csv"
MANUAL_AUTHORITY_CSV = ROOT / "docs" / "architecture" / "scene-governance" / "assets" / "scene_authority_matrix_v1.csv"
MANUAL_FAMILY_CSV = ROOT / "docs" / "architecture" / "scene-governance" / "assets" / "scene_family_inventory_v1.csv"

MENU_FILES = [
    ROOT / "addons" / "smart_construction_core" / "views" / "menu_root.xml",
    ROOT / "addons" / "smart_construction_core" / "views" / "menu.xml",
    ROOT / "addons" / "smart_construction_core" / "views" / "menu_finance_center.xml",
    ROOT / "addons" / "smart_construction_core" / "views" / "core" / "payment_request_views.xml",
]


def _load_module(name: str, path: Path):
    spec = spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"spec unavailable: {path.as_posix()}")
    module = module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _normalize_xmlid(value: Any, module: str = "smart_construction_core") -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if "." in text:
        return text
    return f"{module}.{text}"


def _bootstrap_stub_modules() -> None:
    sys.modules.setdefault("odoo", types.ModuleType("odoo"))
    sys.modules.setdefault("odoo.addons", types.ModuleType("odoo.addons"))

    scene_pkg = sys.modules.setdefault(
        "odoo.addons.smart_construction_scene",
        types.ModuleType("odoo.addons.smart_construction_scene"),
    )
    scene_pkg.__path__ = [str(SCENE_DIR)]

    scene_registry_mod = types.ModuleType("odoo.addons.smart_construction_scene.scene_registry")
    scene_registry_mod.load_scene_configs = lambda env: []
    scene_registry_mod.load_scene_configs_with_timings = lambda env: ([], {})
    sys.modules["odoo.addons.smart_construction_scene.scene_registry"] = scene_registry_mod
    scene_pkg.scene_registry = scene_registry_mod

    smart_core_pkg = sys.modules.setdefault("odoo.addons.smart_core", types.ModuleType("odoo.addons.smart_core"))
    smart_core_pkg.__path__ = [str(SMART_CORE_DIR)]
    delivery_pkg = sys.modules.setdefault(
        "odoo.addons.smart_core.delivery",
        types.ModuleType("odoo.addons.smart_core.delivery"),
    )
    delivery_pkg.__path__ = [str(SMART_CORE_DIR / "delivery")]


def _load_registry_rows() -> dict[str, dict[str, Any]]:
    registry = _load_module(
        "scene_governance_asset_export_scene_registry_content",
        SCENE_DIR / "profiles" / "scene_registry_content.py",
    )
    rows = registry.list_scene_entries()
    return {
        str(row.get("code") or "").strip(): row
        for row in rows
        if isinstance(row, dict) and str(row.get("code") or "").strip()
    }


def _load_authority_baseline() -> list[dict[str, Any]]:
    module = _load_module(
        "scene_governance_asset_export_backend_scene_authority_guard",
        ROOT / "scripts" / "verify" / "backend_scene_authority_guard.py",
    )
    baseline = getattr(module, "BASELINE", None)
    if not isinstance(baseline, list):
        raise RuntimeError("backend_scene_authority_guard.BASELINE missing")
    return list(baseline)


def _load_canonical_baseline() -> dict[str, dict[str, Any]]:
    module = _load_module(
        "scene_governance_asset_export_backend_scene_canonical_entry_guard",
        ROOT / "scripts" / "verify" / "backend_scene_canonical_entry_guard.py",
    )
    baseline = getattr(module, "BASELINE", None)
    if not isinstance(baseline, list):
        raise RuntimeError("backend_scene_canonical_entry_guard.BASELINE missing")
    return {
        str(item.get("code") or "").strip(): item
        for item in baseline
        if isinstance(item, dict) and str(item.get("code") or "").strip()
    }


def _parse_menu_bindings() -> dict[str, str]:
    bindings: dict[str, str] = {}
    for path in MENU_FILES:
        tree = ET.parse(path)
        root = tree.getroot()
        for node in root.iter():
            if node.tag != "menuitem":
                continue
            menu_xmlid = _normalize_xmlid(node.attrib.get("id"))
            action_xmlid = _normalize_xmlid(node.attrib.get("action"))
            if menu_xmlid:
                bindings[menu_xmlid] = action_xmlid
    return bindings


class _DummyRegistry:
    def __init__(self) -> None:
        self.specs: list[dict[str, Any]] = []

    def register_spec(self, **kwargs) -> None:
        self.specs.append(dict(kwargs))


def _load_provider_specs() -> dict[str, dict[str, Any]]:
    module = _load_module(
        "scene_governance_asset_export_register_scene_providers",
        SCENE_DIR / "bootstrap" / "register_scene_providers.py",
    )
    registry = _DummyRegistry()
    module.register_scene_content_providers(registry, SCENE_DIR.parent)
    return {
        str(spec.get("scene_key") or "").strip(): spec
        for spec in registry.specs
        if str(spec.get("scene_key") or "").strip()
    }


def _load_manual_authority_rows() -> list[dict[str, str]]:
    return [row for row in _read_csv(MANUAL_AUTHORITY_CSV) if str(row.get("scene_key") or "").strip()]


def _load_manual_family_rows() -> dict[str, dict[str, str]]:
    return {
        str(row.get("family") or "").strip(): row
        for row in _read_csv(MANUAL_FAMILY_CSV)
        if str(row.get("family") or "").strip()
    }


def _load_menu_scene_rows(registry_rows: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    _bootstrap_stub_modules()
    core_extension = _load_module(
        "odoo.addons.smart_construction_scene.core_extension",
        SCENE_DIR / "core_extension.py",
    )
    core_extension.scene_registry.load_scene_configs = lambda env: list(registry_rows.values())
    nav_maps = core_extension.smart_core_nav_scene_maps(object())
    action_map = dict(nav_maps.get("action_xmlid_scene_map") or {})
    menu_map = dict(nav_maps.get("menu_scene_map") or {})
    menu_bindings = _parse_menu_bindings()

    rows: list[dict[str, Any]] = []
    for menu_xmlid, scene_key in sorted(menu_map.items()):
        rows.append(
            {
                "menu_xmlid": menu_xmlid,
                "native_action_xmlid": menu_bindings.get(menu_xmlid, ""),
                "resolved_scene_key": str(scene_key or ""),
                "mapping_source": "menu_scene_map",
                "compatibility_used": "false",
            }
        )
    for action_xmlid, scene_key in sorted(action_map.items()):
        rows.append(
            {
                "menu_xmlid": "",
                "native_action_xmlid": action_xmlid,
                "resolved_scene_key": str(scene_key or ""),
                "mapping_source": "action_xmlid_scene_map",
                "compatibility_used": "true",
            }
        )
    return rows


def build_exports() -> dict[str, int]:
    registry_rows = _load_registry_rows()
    authority_baseline = _load_authority_baseline()
    canonical_baseline = _load_canonical_baseline()
    provider_specs = _load_provider_specs()
    manual_authority_rows = _load_manual_authority_rows()
    manual_family_rows = _load_manual_family_rows()
    menu_rows = _load_menu_scene_rows(registry_rows)

    authority_rows: list[dict[str, Any]] = []
    family_index: dict[str, dict[str, Any]] = {}
    authority_baseline_map = {
        str(item.get("code") or "").strip(): item
        for item in authority_baseline
        if str(item.get("code") or "").strip()
    }

    for item in manual_authority_rows:
        code = str(item.get("scene_key") or "").strip()
        family = str(item.get("family") or "").strip()
        registry_row = registry_rows.get(code, {})
        target = registry_row.get("target") if isinstance(registry_row.get("target"), dict) else {}
        canonical = canonical_baseline.get(code, {})
        provider = provider_specs.get(code, {})
        authority = authority_baseline_map.get(code, {})
        authority_rows.append(
            {
                "scene_key": code,
                "family": family or str(authority.get("family") or ""),
                "registry_owner": str(item.get("registry_owner") or "scene_registry"),
                "provider_owner": str(provider.get("provider_key") or item.get("provider_owner") or ""),
                "canonical_entry": str(canonical.get("canonical_route") or item.get("canonical_entry") or ""),
                "native_fallback": str(canonical.get("compatibility_target") or item.get("native_fallback") or authority.get("known_gap") or ""),
                "menu_binding": str(target.get("menu_xmlid") or item.get("menu_binding") or ""),
                "action_binding": str(target.get("action_xmlid") or item.get("action_binding") or ""),
                "status": str(authority.get("phase") or item.get("status") or ""),
            }
        )
        family_key = family or str(authority.get("family") or "")
        manual_family = manual_family_rows.get(family_key, {})
        family_bucket = family_index.setdefault(
            family_key,
            {
                "family": family_key,
                "scene_count": 0,
                "canonical_scene": str(manual_family.get("canonical_scene") or ""),
                "native_fallback_count": 0,
                "provider_count": 0,
                "verify_status": str(manual_family.get("verify_status") or "guarded"),
                "governance_status": str(manual_family.get("governance_status") or "stage_closed"),
            },
        )
        family_bucket["scene_count"] += 1
        if not family_bucket["canonical_scene"]:
            family_bucket["canonical_scene"] = code
        if str(target.get("menu_xmlid") or "").strip() or str(target.get("action_xmlid") or "").strip():
            family_bucket["native_fallback_count"] += 1
        if provider:
            family_bucket["provider_count"] += 1

    provider_rows: list[dict[str, Any]] = []
    for code in sorted({*registry_rows.keys(), *provider_specs.keys()}):
        registry_row = registry_rows.get(code, {})
        target = registry_row.get("target") if isinstance(registry_row.get("target"), dict) else {}
        provider = provider_specs.get(code, {})
        has_fallback = any(str(target.get(key) or "").strip() for key in ("route", "menu_xmlid", "action_xmlid"))
        provider_rows.append(
            {
                "scene_key": code,
                "provider_key": str(provider.get("provider_key") or ""),
                "provider_path": str((provider.get("provider_path") or "")),
                "provider_registered": "true" if provider else "false",
                "explicit_fallback_present": "true" if has_fallback else "false",
                "completeness_status": "provider_registered" if provider else ("fallback_only" if has_fallback else "missing"),
            }
        )

    family_rows = [family_index[key] for key in sorted(family_index)]

    _write_csv(
        AUTHORITY_CSV,
        ["scene_key", "family", "registry_owner", "provider_owner", "canonical_entry", "native_fallback", "menu_binding", "action_binding", "status"],
        authority_rows,
    )
    _write_csv(
        FAMILY_CSV,
        ["family", "scene_count", "canonical_scene", "native_fallback_count", "provider_count", "verify_status", "governance_status"],
        family_rows,
    )
    _write_csv(
        MENU_CSV,
        ["menu_xmlid", "native_action_xmlid", "resolved_scene_key", "mapping_source", "compatibility_used"],
        menu_rows,
    )
    _write_csv(
        PROVIDER_CSV,
        ["scene_key", "provider_key", "provider_path", "provider_registered", "explicit_fallback_present", "completeness_status"],
        provider_rows,
    )

    return {
        "authority_rows": len(authority_rows),
        "family_rows": len(family_rows),
        "menu_rows": len(menu_rows),
        "provider_rows": len(provider_rows),
    }


def main() -> int:
    try:
        stats = build_exports()
    except Exception as exc:
        print("[scene_governance_asset_export] FAIL")
        print(f"- {exc}")
        return 1
    print("[scene_governance_asset_export] PASS")
    for key, value in stats.items():
        print(f"{key}={value}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
