#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as ET
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SCENE_REGISTRY = ROOT / "addons/smart_construction_scene/profiles/scene_registry_content.py"
OUT_JSON = ROOT / "artifacts" / "backend" / "backend_scene_canonical_entry_guard.json"
OUT_MD = ROOT / "artifacts" / "backend" / "backend_scene_canonical_entry_guard.md"

MENU_FILES = [
    ROOT / "addons/smart_construction_core/views/menu_root.xml",
    ROOT / "addons/smart_construction_core/views/menu.xml",
    ROOT / "addons/smart_construction_core/views/menu_finance_center.xml",
    ROOT / "addons/smart_construction_core/views/core/payment_request_views.xml",
]

BASELINE = [
    {
        "code": "projects.list",
        "entry_semantic": "scene_work_with_native_parity",
        "canonical_action_xmlid": "smart_construction_core.action_sc_project_list",
        "canonical_route": "/s/projects.list",
        "native_menu_xmlid": "smart_construction_core.menu_sc_root",
        "native_action_xmlid": "smart_construction_core.action_sc_project_list",
        "compatibility_target": "native menu/action",
    },
    {
        "code": "projects.ledger",
        "entry_semantic": "scene_work_with_native_parity",
        "canonical_action_xmlid": "smart_construction_core.action_sc_project_kanban_lifecycle",
        "canonical_route": "/s/projects.ledger",
        "native_menu_xmlid": "smart_construction_core.menu_sc_project_project",
        "native_action_xmlid": "smart_construction_core.action_sc_project_kanban_lifecycle",
        "compatibility_target": "native menu/action",
    },
    {
        "code": "projects.intake",
        "entry_semantic": "scene_work_with_native_parity",
        "canonical_action_xmlid": "smart_construction_core.action_project_initiation",
        "canonical_route": "/s/projects.intake",
        "native_menu_xmlid": "smart_construction_core.menu_sc_project_initiation",
        "native_action_xmlid": "smart_construction_core.action_project_initiation",
        "compatibility_target": "native create/form action",
    },
    {
        "code": "projects.detail",
        "entry_semantic": "route_with_native_menu_compat",
        "canonical_action_xmlid": "",
        "canonical_route": "/s/projects.detail",
        "native_menu_xmlid": "smart_construction_core.menu_sc_project_project",
        "native_action_xmlid": "smart_construction_core.action_sc_project_kanban_lifecycle",
        "compatibility_target": "shared project ledger native menu remains available while detail route no longer co-owns the native action",
    },
    {
        "code": "task.center",
        "entry_semantic": "action_only_scene_work",
        "canonical_action_xmlid": "project.action_view_all_task",
        "canonical_route": "/s/task.center",
        "native_menu_xmlid": "",
        "native_action_xmlid": "",
        "compatibility_target": "canonical scene route plus direct generic task action",
    },
    {
        "code": "task.board",
        "entry_semantic": "route_only_compat_scene",
        "canonical_action_xmlid": "",
        "canonical_route": "/s/task.board",
        "native_menu_xmlid": "",
        "native_action_xmlid": "",
        "compatibility_target": "dedicated board-style compat carrier without native authority",
    },
    {
        "code": "finance.center",
        "entry_semantic": "scene_work_with_shared_native_root",
        "canonical_action_xmlid": "smart_construction_core.action_sc_finance_dashboard",
        "canonical_route": "/s/finance.center",
        "native_menu_xmlid": "smart_construction_core.menu_sc_finance_center",
        "native_action_xmlid": "smart_construction_core.action_sc_finance_dashboard",
        "compatibility_target": "native root finance menu/action",
    },
    {
        "code": "finance.workspace",
        "entry_semantic": "route_with_native_menu_compat",
        "canonical_action_xmlid": "",
        "canonical_route": "/s/finance.workspace",
        "native_menu_xmlid": "smart_construction_core.menu_sc_finance_center",
        "native_action_xmlid": "smart_construction_core.action_sc_finance_dashboard",
        "compatibility_target": "shared finance root menu remains available while workspace route no longer co-owns the root action",
    },
    {
        "code": "finance.payment_requests",
        "entry_semantic": "scene_work_with_native_fallback",
        "canonical_action_xmlid": "smart_construction_core.action_payment_request_my",
        "canonical_route": "/s/finance.payment_requests",
        "native_menu_xmlid": "smart_construction_core.menu_payment_request",
        "native_action_xmlid": "smart_construction_core.action_payment_request",
        "compatibility_target": "generic payment request native list",
    },
    {
        "code": "payments.approval",
        "entry_semantic": "scene_work_with_native_parity",
        "canonical_action_xmlid": "smart_construction_core.action_sc_tier_review_my_payment_request",
        "canonical_route": "/s/payments.approval",
        "native_menu_xmlid": "smart_construction_core.menu_sc_tier_review_my_payment_request",
        "native_action_xmlid": "smart_construction_core.action_sc_tier_review_my_payment_request",
        "compatibility_target": "shared payment request source menu remains available separately",
    },
]


def _load_module(path: Path, module_name: str):
    spec = spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"spec unavailable: {path.as_posix()}")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8")


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _normalize_xmlid(value: str, module: str) -> str:
    text = _clean_text(value)
    if not text:
        return ""
    if "." in text:
        return text
    return f"{module}.{text}"


def _load_menu_map() -> dict[str, str]:
    mapping: dict[str, str] = {}
    for path in MENU_FILES:
        if not path.is_file():
            raise RuntimeError(f"missing menu file: {path.relative_to(ROOT).as_posix()}")
        tree = ET.parse(path)
        root = tree.getroot()
        for node in root.iter():
            if node.tag != "menuitem":
                continue
            menu_id = _normalize_xmlid(node.attrib.get("id"), "smart_construction_core")
            action_id = _normalize_xmlid(node.attrib.get("action"), "smart_construction_core")
            if menu_id and action_id:
                mapping[menu_id] = action_id
    return mapping


def _build_report() -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []

    registry_module = _load_module(SCENE_REGISTRY, "backend_scene_canonical_entry_guard_scene_registry")
    loader = getattr(registry_module, "list_scene_entries", None)
    if not callable(loader):
        raise RuntimeError("scene_registry_content.py missing list_scene_entries()")
    rows = loader()
    if not isinstance(rows, list):
        raise RuntimeError("list_scene_entries() must return a list")

    indexed_rows = {
        _clean_text(row.get("code")): row
        for row in rows
        if isinstance(row, dict) and _clean_text(row.get("code"))
    }
    menu_map = _load_menu_map()
    scene_reports: list[dict[str, Any]] = []

    for spec in BASELINE:
        code = spec["code"]
        row = indexed_rows.get(code)
        if not row:
            errors.append(f"missing baseline scene: {code}")
            continue
        target = row.get("target") if isinstance(row.get("target"), dict) else {}
        actual_route = _clean_text(target.get("route"))
        actual_action = _clean_text(target.get("action_xmlid"))
        actual_registry_menu = _clean_text(target.get("menu_xmlid"))

        expected_route = _clean_text(spec.get("canonical_route"))
        expected_action = _clean_text(spec.get("canonical_action_xmlid"))
        native_menu = _clean_text(spec.get("native_menu_xmlid"))
        native_action = _clean_text(spec.get("native_action_xmlid"))
        entry_semantic = _clean_text(spec.get("entry_semantic"))

        mismatches: list[str] = []
        if actual_action != expected_action:
            mismatches.append(f"canonical_action_xmlid: expected {expected_action}, got {actual_action or '(missing)'}")
        if actual_route != expected_route:
            expected_label = expected_route or "(missing)"
            mismatches.append(f"canonical_route: expected {expected_label}, got {actual_route or '(missing)'}")

        if native_menu:
            actual_native_action = menu_map.get(native_menu, "")
            if actual_native_action != native_action:
                mismatches.append(
                    f"native menu target mismatch for {native_menu}: expected {native_action}, got {actual_native_action or '(missing)'}"
                )
        else:
            actual_native_action = ""

        if entry_semantic == "scene_work_with_native_fallback":
            if not actual_route:
                mismatches.append("scene_work_with_native_fallback requires explicit canonical_route")
            if native_action and actual_action == native_action:
                mismatches.append("scene_work_with_native_fallback requires canonical_action_xmlid != native_action_xmlid")
        elif entry_semantic == "scene_work_with_native_parity":
            if not actual_route:
                mismatches.append("scene_work_with_native_parity requires explicit canonical_route")
            if native_action and actual_action != native_action:
                mismatches.append("scene_work_with_native_parity requires canonical_action_xmlid == native_action_xmlid")
        elif entry_semantic == "scene_work_with_shared_native_root":
            if not actual_route:
                mismatches.append("scene_work_with_shared_native_root requires explicit canonical_route")
            if native_action and actual_action != native_action:
                mismatches.append("scene_work_with_shared_native_root requires canonical_action_xmlid == native_action_xmlid")
        elif entry_semantic == "scene_work_with_shared_native_compat":
            if not actual_route:
                mismatches.append("scene_work_with_shared_native_compat requires explicit canonical_route")
            if native_action and actual_action != native_action:
                mismatches.append("scene_work_with_shared_native_compat requires canonical_action_xmlid == native_action_xmlid")
        elif entry_semantic == "native_only_transitional":
            if actual_route:
                mismatches.append("native_only_transitional must not freeze canonical_route yet")
            if native_action and actual_action != native_action:
                mismatches.append("native_only_transitional requires canonical_action_xmlid == native_action_xmlid")
        elif entry_semantic == "action_only_scene_work":
            if not actual_route:
                mismatches.append("action_only_scene_work requires explicit canonical_route")
            if native_menu:
                mismatches.append("action_only_scene_work must not depend on native_menu_xmlid")
        elif entry_semantic == "route_only_compat_scene":
            if not actual_route:
                mismatches.append("route_only_compat_scene requires explicit canonical_route")
            if actual_action:
                mismatches.append("route_only_compat_scene must not depend on canonical_action_xmlid")
            if native_menu:
                mismatches.append("route_only_compat_scene must not depend on native_menu_xmlid")
            if native_action:
                mismatches.append("route_only_compat_scene must not depend on native_action_xmlid")
        elif entry_semantic == "route_with_native_menu_compat":
            if not actual_route:
                mismatches.append("route_with_native_menu_compat requires explicit canonical_route")
            if actual_action:
                mismatches.append("route_with_native_menu_compat must not depend on canonical_action_xmlid")
            if not native_menu:
                mismatches.append("route_with_native_menu_compat requires native_menu_xmlid compatibility context")
            if not native_action:
                mismatches.append("route_with_native_menu_compat requires native_action_xmlid compatibility context")
        elif entry_semantic == "hybrid_root":
            if actual_route:
                mismatches.append("hybrid_root must keep route authority outside registry for now")
            if native_action and actual_action != native_action:
                mismatches.append("hybrid_root requires canonical_action_xmlid == native_action_xmlid")

        if mismatches:
            errors.append(f"{code} canonical-entry mismatch")
            errors.extend([f"{code}: {item}" for item in mismatches])

        scene_reports.append(
            {
                "code": code,
                "entry_semantic": entry_semantic,
                "compatibility_target": spec.get("compatibility_target"),
                "registry_menu_xmlid": actual_registry_menu,
                "canonical_route": actual_route,
                "canonical_action_xmlid": actual_action,
                "native_menu_xmlid": native_menu,
                "native_action_xmlid": actual_native_action,
                "mismatches": mismatches,
            }
        )

    payment_requests = next((item for item in scene_reports if item["code"] == "finance.payment_requests"), None)
    approval = next((item for item in scene_reports if item["code"] == "payments.approval"), None)
    if isinstance(payment_requests, dict) and isinstance(approval, dict):
        if payment_requests.get("canonical_action_xmlid") == approval.get("canonical_action_xmlid"):
            errors.append("finance.payment_requests and payments.approval must keep distinct canonical actions")
        if payment_requests.get("native_action_xmlid") == approval.get("canonical_action_xmlid"):
            errors.append("payments.approval canonical action must remain distinct from payment list native action")

    finance_center = next((item for item in scene_reports if item["code"] == "finance.center"), None)
    finance_workspace = next((item for item in scene_reports if item["code"] == "finance.workspace"), None)
    if isinstance(finance_center, dict) and isinstance(finance_workspace, dict):
        if finance_center.get("native_action_xmlid") != finance_workspace.get("native_action_xmlid"):
            errors.append("finance.center and finance.workspace must keep the same native finance root action")

    report = {
        "status": "PASS" if not errors else "FAIL",
        "baseline_scene_count": len(BASELINE),
        "checked_registry_path": SCENE_REGISTRY.relative_to(ROOT).as_posix(),
        "checked_menu_files": [path.relative_to(ROOT).as_posix() for path in MENU_FILES],
        "scenes": scene_reports,
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
        "# Backend Scene Canonical Entry Guard",
        "",
        f"- status: {report.get('status', 'FAIL')}",
        f"- baseline_scene_count: {report.get('baseline_scene_count', 0)}",
        f"- checked_registry_path: {report.get('checked_registry_path', '') or '(unknown)'}",
    ]
    checked_menu_files = report.get("checked_menu_files") if isinstance(report.get("checked_menu_files"), list) else []
    if checked_menu_files:
        lines.extend(["", "## Checked Menu Files"])
        lines.extend([f"- {item}" for item in checked_menu_files])
    if errors:
        lines.extend(["", "## Errors"])
        lines.extend([f"- {item}" for item in errors])
    _write(OUT_MD, "\n".join(lines) + "\n")

    if errors:
        print("[backend_scene_canonical_entry_guard] FAIL")
        for item in errors:
            print(f"- {item}")
        return 1

    print("[backend_scene_canonical_entry_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
