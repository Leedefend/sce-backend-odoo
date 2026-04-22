#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SCENE_REGISTRY = ROOT / "addons/smart_construction_scene/profiles/scene_registry_content.py"
OUT_JSON = ROOT / "artifacts" / "backend" / "backend_scene_authority_guard.json"
OUT_MD = ROOT / "artifacts" / "backend" / "backend_scene_authority_guard.md"


BASELINE = [
    {
        "code": "projects.list",
        "family": "projects",
        "phase": "frozen",
        "required": {
            "route": "/s/projects.list",
            "menu_xmlid": "smart_construction_core.menu_sc_root",
            "action_xmlid": "smart_construction_core.action_sc_project_list",
        },
        "required_missing": [],
        "known_gap": "route authority is now frozen while native menu/action parity remains intentional",
    },
    {
        "code": "projects.ledger",
        "family": "projects",
        "phase": "frozen",
        "required": {
            "route": "/s/projects.ledger",
            "menu_xmlid": "smart_construction_core.menu_sc_project_project",
            "action_xmlid": "smart_construction_core.action_sc_project_kanban_lifecycle",
        },
        "required_missing": [],
        "known_gap": "ledger/detail still share native action semantics outside canonical route split",
    },
    {
        "code": "projects.intake",
        "family": "projects",
        "phase": "frozen",
        "required": {
            "route": "/s/projects.intake",
            "menu_xmlid": "smart_construction_core.menu_sc_project_initiation",
            "action_xmlid": "smart_construction_core.action_project_initiation",
        },
        "required_missing": [],
        "known_gap": "project.initiation remains as compatibility alias route only",
    },
    {
        "code": "projects.detail",
        "family": "projects",
        "phase": "frozen",
        "required": {
            "route": "/s/projects.detail",
            "menu_xmlid": "smart_construction_core.menu_sc_project_project",
        },
        "required_missing": ["action_xmlid"],
        "known_gap": "projects.detail is frozen as route-plus-menu authority and no longer co-owns the shared ledger native action",
    },
    {
        "code": "task.center",
        "family": "tasks",
        "phase": "frozen",
        "required": {
            "route": "/s/task.center",
            "action_xmlid": "project.action_view_all_task",
        },
        "required_missing": ["menu_xmlid"],
        "known_gap": "task.center is a declared action-only stable slice and intentionally has no dedicated menu authority",
    },
    {
        "code": "task.board",
        "family": "tasks",
        "phase": "frozen",
        "required": {
            "route": "/s/task.board",
        },
        "required_missing": ["menu_xmlid", "action_xmlid"],
        "known_gap": "task.board is a route-only compat scene and intentionally has no native menu/action authority",
    },
    {
        "code": "finance.center",
        "family": "finance_center",
        "phase": "frozen",
        "required": {
            "route": "/s/finance.center",
            "menu_xmlid": "smart_construction_core.menu_sc_finance_center",
            "action_xmlid": "smart_construction_core.action_sc_finance_dashboard",
        },
        "required_missing": [],
        "known_gap": "keeps the finance root menu/action as the canonical root owner",
    },
    {
        "code": "finance.workspace",
        "family": "finance_center",
        "phase": "frozen",
        "required": {
            "route": "/s/finance.workspace",
            "menu_xmlid": "smart_construction_core.menu_sc_finance_center",
        },
        "required_missing": ["action_xmlid"],
        "known_gap": "finance.workspace is frozen as route-plus-menu authority and no longer co-owns the finance root action",
    },
    {
        "code": "finance.payment_requests",
        "family": "payment_entry",
        "phase": "frozen",
        "required": {
            "route": "/s/finance.payment_requests",
            "menu_xmlid": "smart_construction_core.menu_payment_request",
            "action_xmlid": "smart_construction_core.action_payment_request_my",
        },
        "required_missing": [],
        "known_gap": "native compatibility menu still points to the generic payment list family",
    },
    {
        "code": "payments.approval",
        "family": "payment_approval",
        "phase": "frozen",
        "required": {
            "route": "/s/payments.approval",
            "menu_xmlid": "smart_construction_core.menu_sc_tier_review_my_payment_request",
            "action_xmlid": "smart_construction_core.action_sc_tier_review_my_payment_request",
        },
        "required_missing": [],
        "known_gap": "uses the native approval menu while keeping approval action authority distinct from finance.payment_requests",
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


def _build_report() -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    known_gaps: list[str] = []

    module = _load_module(SCENE_REGISTRY, "backend_scene_authority_guard_scene_registry")
    loader = getattr(module, "list_scene_entries", None)
    if not callable(loader):
        raise RuntimeError("scene_registry_content.py missing list_scene_entries()")

    rows = loader()
    if not isinstance(rows, list):
        raise RuntimeError("list_scene_entries() must return a list")

    code_counts: dict[str, int] = {}
    indexed_rows: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        code = _clean_text(row.get("code"))
        if not code:
            continue
        code_counts[code] = code_counts.get(code, 0) + 1
        indexed_rows.setdefault(code, row)

    for code, count in sorted(code_counts.items()):
        if count > 1:
            errors.append(f"duplicate scene code in registry: {code} ({count})")

    scene_reports: list[dict[str, Any]] = []
    for spec in BASELINE:
        code = spec["code"]
        row = indexed_rows.get(code)
        if not row:
            errors.append(f"missing baseline scene: {code}")
            continue
        target = row.get("target") if isinstance(row.get("target"), dict) else {}
        required = dict(spec.get("required") or {})
        required_missing = list(spec.get("required_missing") or [])

        mismatches: list[str] = []
        for field, expected in required.items():
            actual = _clean_text(target.get(field))
            if actual != expected:
                mismatches.append(f"{field}: expected {expected}, got {actual or '(missing)'}")

        for field in required_missing:
            actual = _clean_text(target.get(field))
            if actual:
                mismatches.append(f"{field}: expected missing, got {actual}")

        if mismatches:
            errors.append(f"{code} authority mismatch")
            errors.extend([f"{code}: {item}" for item in mismatches])
        else:
            known_gap = _clean_text(spec.get("known_gap"))
            if known_gap:
                known_gaps.append(f"{code}: {known_gap}")

        scene_reports.append(
            {
                "code": code,
                "family": spec["family"],
                "phase": spec["phase"],
                "required": required,
                "required_missing": required_missing,
                "actual": {
                    "route": _clean_text(target.get("route")),
                    "menu_xmlid": _clean_text(target.get("menu_xmlid")),
                    "action_xmlid": _clean_text(target.get("action_xmlid")),
                },
                "mismatches": mismatches,
            }
        )

    payment_requests = indexed_rows.get("finance.payment_requests", {})
    approval = indexed_rows.get("payments.approval", {})
    finance_center = indexed_rows.get("finance.center", {})
    finance_workspace = indexed_rows.get("finance.workspace", {})

    payment_requests_target = payment_requests.get("target") if isinstance(payment_requests.get("target"), dict) else {}
    approval_target = approval.get("target") if isinstance(approval.get("target"), dict) else {}
    finance_center_target = finance_center.get("target") if isinstance(finance_center.get("target"), dict) else {}
    finance_workspace_target = finance_workspace.get("target") if isinstance(finance_workspace.get("target"), dict) else {}

    if _clean_text(payment_requests_target.get("menu_xmlid")) == _clean_text(approval_target.get("menu_xmlid")):
        errors.append("finance.payment_requests and payments.approval must keep distinct native menus")
    if _clean_text(payment_requests_target.get("action_xmlid")) == _clean_text(approval_target.get("action_xmlid")):
        errors.append("finance.payment_requests and payments.approval must keep distinct canonical actions")

    if _clean_text(finance_center_target.get("menu_xmlid")) != _clean_text(finance_workspace_target.get("menu_xmlid")):
        errors.append("finance.center and finance.workspace must keep the same native root menu")
    if not _clean_text(finance_workspace_target.get("route")):
        errors.append("finance.workspace must keep an explicit canonical route")

    report = {
        "status": "PASS" if not errors else "FAIL",
        "baseline_scene_count": len(BASELINE),
        "checked_registry_path": SCENE_REGISTRY.relative_to(ROOT).as_posix(),
        "scenes": scene_reports,
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
        "# Backend Scene Authority Guard",
        "",
        f"- status: {report.get('status', 'FAIL')}",
        f"- baseline_scene_count: {report.get('baseline_scene_count', 0)}",
        f"- checked_registry_path: {report.get('checked_registry_path', '') or '(unknown)'}",
    ]
    known_gaps = report.get("known_gaps") if isinstance(report.get("known_gaps"), list) else []
    if known_gaps:
        lines.extend(["", "## Known Gaps"])
        lines.extend([f"- {item}" for item in known_gaps])
    if errors:
        lines.extend(["", "## Errors"])
        lines.extend([f"- {item}" for item in errors])
    _write(OUT_MD, "\n".join(lines) + "\n")

    if errors:
        print("[backend_scene_authority_guard] FAIL")
        for item in errors:
            print(f"- {item}")
        return 1

    print("[backend_scene_authority_guard] PASS")
    print(f"known_gaps={len(known_gaps)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
