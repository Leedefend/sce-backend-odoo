#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import sys
import types
import xml.etree.ElementTree as ET
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SCENE_DIR = ROOT / "addons" / "smart_construction_scene"
SMART_CORE_DIR = ROOT / "addons" / "smart_core"
OUT_JSON = ROOT / "artifacts" / "backend" / "backend_scene_menu_mapping_guard.json"
OUT_MD = ROOT / "artifacts" / "backend" / "backend_scene_menu_mapping_guard.md"

MENU_FILES = [
    ROOT / "addons" / "smart_construction_core" / "views" / "menu_root.xml",
    ROOT / "addons" / "smart_construction_core" / "views" / "menu.xml",
    ROOT / "addons" / "smart_construction_core" / "views" / "menu_finance_center.xml",
    ROOT / "addons" / "smart_construction_core" / "views" / "core" / "payment_request_views.xml",
]

BASELINE_MENUS = [
    {
        "label": "projects.list",
        "menu_xmlid": "smart_construction_core.menu_sc_root",
        "action_xmlid": "smart_construction_core.action_sc_project_list",
        "expected_scene_key": "projects.list",
        "expected_route_prefix": "/s/projects.list",
        "expected_target_type": "scene",
    },
    {
        "label": "projects.ledger",
        "menu_xmlid": "smart_construction_core.menu_sc_project_project",
        "action_xmlid": "smart_construction_core.action_sc_project_kanban_lifecycle",
        "expected_scene_key": "projects.ledger",
        "expected_route_prefix": "/s/projects.ledger",
        "expected_target_type": "scene",
    },
    {
        "label": "projects.intake",
        "menu_xmlid": "smart_construction_core.menu_sc_project_initiation",
        "action_xmlid": "smart_construction_core.action_project_initiation",
        "expected_scene_key": "projects.intake",
        "expected_route_prefix": "/s/projects.intake",
        "expected_target_type": "scene",
    },
    {
        "label": "finance.center",
        "menu_xmlid": "smart_construction_core.menu_sc_finance_center",
        "action_xmlid": "smart_construction_core.action_sc_finance_dashboard",
        "expected_scene_key": "finance.center",
        "expected_route_prefix": "/s/finance.center",
        "expected_target_type": "scene",
    },
    {
        "label": "finance.payment_requests",
        "menu_xmlid": "smart_construction_core.menu_payment_request",
        "action_xmlid": "smart_construction_core.action_payment_request",
        "expected_scene_key": "finance.payment_requests",
        "expected_route_prefix": "/s/finance.payment_requests",
        "expected_target_type": "scene",
    },
    {
        "label": "payments.approval",
        "menu_xmlid": "smart_construction_core.menu_sc_tier_review_my_payment_request",
        "action_xmlid": "smart_construction_core.action_sc_tier_review_my_payment_request",
        "expected_scene_key": "payments.approval",
        "expected_route_prefix": "/s/payments.approval",
        "expected_target_type": "scene",
    },
]

ABSENT_DIRECT_MENU_SCENES = {
    "projects.detail": "detail scene still shares project ledger native menu and must not claim a dedicated menu mapping yet",
    "task.center": "task center has action-scene mapping but still must not claim a dedicated menu mapping yet",
    "finance.workspace": "finance workspace still shares finance root menu and must not replace finance.center at menu-root level",
}


def _write(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8")


def _load_module(name: str, path: Path):
    spec = spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"spec unavailable: {path.as_posix()}")
    module = module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


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


def _parse_menu_bindings() -> dict[str, dict[str, str]]:
    bindings: dict[str, dict[str, str]] = {}
    for path in MENU_FILES:
        if not path.is_file():
            raise RuntimeError(f"missing menu file: {path.relative_to(ROOT).as_posix()}")
        tree = ET.parse(path)
        root = tree.getroot()
        for node in root.iter():
            if node.tag != "menuitem":
                continue
            menu_xmlid = _normalize_xmlid(node.attrib.get("id"))
            action_xmlid = _normalize_xmlid(node.attrib.get("action"))
            if menu_xmlid:
                bindings[menu_xmlid] = {
                    "action_xmlid": action_xmlid,
                }
    return bindings


def _synthetic_id(seed: str) -> int:
    return 1000 + sum((index + 1) * ord(ch) for index, ch in enumerate(seed))


def _build_explicit_scene_map(
    *,
    nav_maps: dict[str, Any],
    registry_entries: list[dict[str, Any]],
    menu_bindings: dict[str, dict[str, str]],
) -> tuple[dict[str, Any], dict[str, int], dict[str, int]]:
    menu_id_map = {xmlid: _synthetic_id(f"menu:{xmlid}") for xmlid in menu_bindings}

    action_xmlids = {
        binding.get("action_xmlid")
        for binding in menu_bindings.values()
        if str(binding.get("action_xmlid") or "").strip()
    }
    action_xmlids.update(str(key) for key in (nav_maps.get("action_xmlid_scene_map") or {}).keys())
    action_id_map = {xmlid: _synthetic_id(f"action:{xmlid}") for xmlid in action_xmlids if xmlid}

    scene_map = {
        "menu_id_to_scene": {},
        "action_id_to_scene": {},
        "entries": [],
    }

    for menu_xmlid, scene_key in (nav_maps.get("menu_scene_map") or {}).items():
        menu_id = menu_id_map.get(str(menu_xmlid))
        if menu_id and str(scene_key or "").strip():
            scene_map["menu_id_to_scene"][str(menu_id)] = str(scene_key)

    for action_xmlid, scene_key in (nav_maps.get("action_xmlid_scene_map") or {}).items():
        action_id = action_id_map.get(str(action_xmlid))
        if action_id and str(scene_key or "").strip():
            scene_map["action_id_to_scene"][str(action_id)] = str(scene_key)

    for row in registry_entries:
        if not isinstance(row, dict):
            continue
        code = str(row.get("code") or "").strip()
        if not code:
            continue
        target = row.get("target") if isinstance(row.get("target"), dict) else {}
        menu_xmlid = str(target.get("menu_xmlid") or "").strip()
        action_xmlid = str(target.get("action_xmlid") or "").strip()
        entry = {
            "code": code,
            "target": dict(target),
        }
        if menu_xmlid in menu_id_map:
            entry["menu_id"] = menu_id_map[menu_xmlid]
            entry["target"]["menu_id"] = menu_id_map[menu_xmlid]
        if action_xmlid in action_id_map:
            entry["action_id"] = action_id_map[action_xmlid]
            entry["target"]["action_id"] = action_id_map[action_xmlid]
        scene_map["entries"].append(entry)

    return scene_map, menu_id_map, action_id_map


def _build_nav_fact(menu_id_map: dict[str, int], action_id_map: dict[str, int]) -> dict[str, Any]:
    rows = []
    for spec in BASELINE_MENUS:
        menu_xmlid = spec["menu_xmlid"]
        action_xmlid = spec["action_xmlid"]
        rows.append(
            {
                "menu_id": menu_id_map[menu_xmlid],
                "key": f"menu:{menu_id_map[menu_xmlid]}",
                "name": spec["label"],
                "has_children": False,
                "action_raw": f"ir.actions.act_window,{action_id_map[action_xmlid]}",
                "action_type": "ir.actions.act_window",
                "action_id": action_id_map[action_xmlid],
                "action_exists": True,
                "action_meta": {},
            }
        )
    return {"flat": rows, "tree": []}


def _build_report() -> tuple[dict[str, Any], list[str]]:
    _bootstrap_stub_modules()
    core_extension = _load_module(
        "odoo.addons.smart_construction_scene.core_extension",
        SCENE_DIR / "core_extension.py",
    )
    registry = _load_module(
        "odoo.addons.smart_construction_scene.profiles.scene_registry_content",
        SCENE_DIR / "profiles" / "scene_registry_content.py",
    )
    interpreter_mod = _load_module(
        "odoo.addons.smart_core.delivery.menu_target_interpreter_service",
        SMART_CORE_DIR / "delivery" / "menu_target_interpreter_service.py",
    )

    registry_entries = list(registry.list_scene_entries())
    core_extension.scene_registry.load_scene_configs = lambda env: list(registry_entries)
    nav_maps = core_extension.smart_core_nav_scene_maps(object())
    menu_bindings = _parse_menu_bindings()
    scene_map, menu_id_map, action_id_map = _build_explicit_scene_map(
        nav_maps=nav_maps,
        registry_entries=registry_entries,
        menu_bindings=menu_bindings,
    )
    nav_fact = _build_nav_fact(menu_id_map, action_id_map)
    service = interpreter_mod.MenuTargetInterpreterService(env=None)
    explained = service.interpret(nav_fact, scene_map=scene_map, policy={})

    errors: list[str] = []
    row_reports: list[dict[str, Any]] = []
    explained_rows = {
        int(row["menu_id"]): row
        for row in (explained.get("flat") or [])
        if isinstance(row, dict) and isinstance(row.get("menu_id"), int)
    }

    for spec in BASELINE_MENUS:
        menu_id = menu_id_map[spec["menu_xmlid"]]
        row = explained_rows.get(menu_id)
        mismatches: list[str] = []
        if not row:
            mismatches.append("explained row missing")
        else:
            target_type = str(row.get("target_type") or "")
            scene_key = str(((row.get("target") or {}).get("scene_key")) or "")
            route = str(row.get("route") or "")
            entry_target_type = str(((row.get("entry_target") or {}).get("type")) or "")
            entry_target_scene = str(((row.get("entry_target") or {}).get("scene_key")) or "")
            if target_type != spec["expected_target_type"]:
                mismatches.append(f"target_type: expected {spec['expected_target_type']}, got {target_type or '(missing)'}")
            if scene_key != spec["expected_scene_key"]:
                mismatches.append(f"scene_key: expected {spec['expected_scene_key']}, got {scene_key or '(missing)'}")
            if not route.startswith(spec["expected_route_prefix"]):
                mismatches.append(f"route: expected prefix {spec['expected_route_prefix']}, got {route or '(missing)'}")
            if entry_target_type != "scene":
                mismatches.append(f"entry_target.type: expected scene, got {entry_target_type or '(missing)'}")
            if entry_target_scene != spec["expected_scene_key"]:
                mismatches.append(
                    f"entry_target.scene_key: expected {spec['expected_scene_key']}, got {entry_target_scene or '(missing)'}"
                )
        if mismatches:
            errors.append(f"{spec['label']} menu mapping mismatch")
            errors.extend([f"{spec['label']}: {item}" for item in mismatches])
        row_reports.append(
            {
                "label": spec["label"],
                "menu_xmlid": spec["menu_xmlid"],
                "action_xmlid": spec["action_xmlid"],
                "menu_id": menu_id,
                "action_id": action_id_map[spec["action_xmlid"]],
                "explained": row,
                "mismatches": mismatches,
            }
        )

    known_gaps: list[str] = []
    reverse_menu_map = {str(value): str(key) for key, value in (nav_maps.get("menu_scene_map") or {}).items()}
    reverse_action_map = {str(value): str(key) for key, value in (nav_maps.get("action_xmlid_scene_map") or {}).items()}
    for scene_key, reason in ABSENT_DIRECT_MENU_SCENES.items():
        if scene_key in reverse_menu_map:
            errors.append(f"{scene_key} unexpectedly owns dedicated menu mapping: {reverse_menu_map[scene_key]}")
        else:
            known_gaps.append(f"{scene_key}: {reason}")
    task_center_action = reverse_action_map.get("task.center")
    if task_center_action:
        known_gaps.append(f"task.center: no dedicated menu mapping, but direct action scene map is already present via {task_center_action}")
    else:
        errors.append("task.center must keep its direct action scene map while menu authority remains unresolved")

    report = {
        "status": "PASS" if not errors else "FAIL",
        "checked_menu_files": [path.relative_to(ROOT).as_posix() for path in MENU_FILES],
        "rows": row_reports,
        "known_gaps": known_gaps,
        "errors": errors,
    }
    return report, errors


def main() -> int:
    try:
        report, errors = _build_report()
    except Exception as exc:
        report = {"status": "FAIL", "errors": [f"ENV_UNSTABLE: {exc}"]}
        errors = report["errors"]

    _write(OUT_JSON, json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    lines = [
        "# Backend Scene Menu Mapping Guard",
        "",
        f"- status: {report.get('status', 'FAIL')}",
    ]
    checked_menu_files = report.get("checked_menu_files") if isinstance(report.get("checked_menu_files"), list) else []
    if checked_menu_files:
        lines.extend(["", "## Checked Menu Files"])
        lines.extend([f"- {item}" for item in checked_menu_files])
    known_gaps = report.get("known_gaps") if isinstance(report.get("known_gaps"), list) else []
    if known_gaps:
        lines.extend(["", "## Known Gaps"])
        lines.extend([f"- {item}" for item in known_gaps])
    if errors:
        lines.extend(["", "## Errors"])
        lines.extend([f"- {item}" for item in errors])
    _write(OUT_MD, "\n".join(lines) + "\n")

    if errors:
        print("[backend_scene_menu_mapping_guard] FAIL")
        for item in errors:
            print(f"- {item}")
        return 1

    print("[backend_scene_menu_mapping_guard] PASS")
    print(f"known_gaps={len(known_gaps)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
