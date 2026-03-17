#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
from pathlib import Path

from intent_smoke_utils import require_ok
from python_http_smoke_utils import get_base_url, http_post_json


ROOT = Path(__file__).resolve().parents[2]
REPORT_JSON = ROOT / "artifacts" / "backend" / "scene_ready_strict_gap_full_audit.json"
REPORT_MD = ROOT / "docs" / "ops" / "audits" / "scene_ready_strict_gap_full_audit.md"


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _as_dict(value):
    return value if isinstance(value, dict) else {}


def _as_list(value):
    return value if isinstance(value, list) else []


def _scene_key_matches(scene_key: str, candidate: str) -> bool:
    key = str(scene_key or "").strip().lower()
    cand = str(candidate or "").strip().lower()
    if not key or not cand:
        return False
    return key in {cand, cand.replace('.', '_'), cand.replace('_', '.')}


def _missing_contract_paths(row: dict) -> list[str]:
    missing: list[str] = []
    surface = _as_dict(row.get("surface"))
    intent = _as_dict(surface.get("intent"))
    view_modes = _as_list(row.get("view_modes"))
    sections = _as_dict(row.get("sections"))
    action_surface = _as_dict(row.get("action_surface"))
    projection = _as_dict(row.get("projection"))
    group_summary = _as_dict(projection.get("group_summary"))

    if not str(surface.get("kind") or "").strip():
        missing.append("surface.kind")
    if not str(intent.get("title") or "").strip():
        missing.append("surface.intent.title")
    if not str(intent.get("summary") or "").strip():
        missing.append("surface.intent.summary")
    if not view_modes:
        missing.append("view_modes")
    if not isinstance(sections.get("quick_actions"), dict):
        missing.append("sections.quick_actions")
    if not isinstance(sections.get("group_summary"), dict):
        missing.append("sections.group_summary")
    if not isinstance(action_surface.get("primary_actions"), list):
        missing.append("action_surface.primary_actions")
    if not isinstance(action_surface.get("groups"), list):
        missing.append("action_surface.groups")
    if not str(action_surface.get("selection_mode") or "").strip():
        missing.append("action_surface.selection_mode")
    if not isinstance(projection.get("summary_items"), list):
        missing.append("projection.summary_items")
    if not isinstance(projection.get("overview_strip"), list):
        missing.append("projection.overview_strip")
    if not isinstance(group_summary.get("items"), list):
        missing.append("projection.group_summary.items")
    return missing


def _fetch_scene_ready_contract() -> dict:
    base_url = get_base_url()
    intent_url = f"{base_url}/api/v1/intent"
    db_name = os.getenv("E2E_DB") or os.getenv("DB_NAME") or ""
    login = os.getenv("E2E_LOGIN") or "admin"
    password = os.getenv("E2E_PASSWORD") or os.getenv("ADMIN_PASSWD") or "admin"

    status, login_resp = http_post_json(
        intent_url,
        {"intent": "login", "params": {"db": db_name, "login": login, "password": password}},
        headers={"X-Anonymous-Intent": "1"},
    )
    require_ok(status, login_resp, "login")
    token = ((_as_dict(login_resp.get("data"))).get("token") or "")
    if not token:
        raise RuntimeError("login response missing token")

    status, init_resp = http_post_json(
        intent_url,
        {"intent": "system.init", "params": {"contract_mode": "user"}},
        headers={"Authorization": f"Bearer {token}"},
    )
    require_ok(status, init_resp, "system.init")
    data = _as_dict(init_resp.get("data"))
    return _as_dict(data.get("scene_ready_contract_v1"))


def main() -> int:
    try:
        contract = _fetch_scene_ready_contract()
    except Exception as exc:
        print("[FAIL] scene_ready_strict_gap_full_audit")
        print(f" - fetch scene_ready_contract_v1 failed: {exc}")
        return 2

    scenes = _as_list(contract.get("scenes"))
    all_rows = []
    unresolved_all_rows = []
    strict_rows = []
    unresolved_strict_rows = []
    source_gap_rows = []

    for row in scenes:
        if not isinstance(row, dict):
            continue
        runtime_policy = _as_dict(row.get("runtime_policy"))
        meta = _as_dict(row.get("meta"))
        scene = _as_dict(row.get("scene"))
        scene_key = str(scene.get("key") or row.get("scene_key") or "").strip()
        missing_paths = _missing_contract_paths(row)
        all_report = {
            "scene_key": scene_key,
            "missing": missing_paths,
        }
        all_rows.append(all_report)
        if missing_paths:
            unresolved_all_rows.append(all_report)

        strict_mode = bool(runtime_policy.get("strict_contract_mode"))
        if not strict_mode:
            strict_mode = bool(_as_dict(meta.get("runtime_policy")).get("strict_contract_mode"))
        if not strict_mode:
            continue

        guard = _as_dict(row.get("contract_guard"))
        if not guard:
            guard = _as_dict(meta.get("contract_guard"))
        missing = [str(item).strip() for item in _as_list(guard.get("missing")) if str(item).strip()]
        source_missing = [str(item).strip() for item in _as_list(guard.get("source_missing")) if str(item).strip()]
        defaults_applied = [str(item).strip() for item in _as_list(guard.get("defaults_applied")) if str(item).strip()]
        contract_ready = bool(guard.get("contract_ready"))

        row_report = {
            "scene_key": scene_key,
            "contract_ready": contract_ready,
            "missing": missing,
            "source_missing": source_missing,
            "defaults_applied": defaults_applied,
        }
        strict_rows.append(row_report)
        if missing or not contract_ready:
            unresolved_strict_rows.append(row_report)
        if source_missing:
            source_gap_rows.append(row_report)

    required_pilot_keys = [
        "workspace.home",
        "finance.payment_requests",
        "risk.center",
        "project.management",
    ]
    strict_scene_keys = [str(row.get("scene_key") or "").strip() for row in strict_rows]
    missing_required_strict = [
        key
        for key in required_pilot_keys
        if not any(_scene_key_matches(item, key) for item in strict_scene_keys)
    ]

    errors: list[str] = []
    if len(scenes) == 0:
        errors.append("scene_ready_contract_v1.scenes is empty")
    if unresolved_all_rows:
        errors.append(f"unresolved full-scene contract gaps: {len(unresolved_all_rows)}")
    if len(strict_rows) == 0:
        errors.append("strict_scene_count is 0")
    if missing_required_strict:
        errors.append(f"required strict scenes missing: {','.join(missing_required_strict)}")
    if unresolved_strict_rows:
        errors.append(f"unresolved strict scenes: {len(unresolved_strict_rows)}")

    result = {
        "ok": len(errors) == 0,
        "scene_count": len(scenes),
        "full_unresolved_count": len(unresolved_all_rows),
        "strict_scene_count": len(strict_rows),
        "strict_unresolved_count": len(unresolved_strict_rows),
        "strict_source_gap_count": len(source_gap_rows),
        "missing_required_strict": missing_required_strict,
        "errors": errors,
        "all_rows": all_rows,
        "unresolved_all_rows": unresolved_all_rows,
        "strict_rows": strict_rows,
        "strict_unresolved_rows": unresolved_strict_rows,
        "strict_source_gap_rows": source_gap_rows,
    }
    _write(REPORT_JSON, json.dumps(result, ensure_ascii=False, indent=2) + "\n")

    lines = [
        "# Scene Ready Strict Gap Full Audit",
        "",
        f"- status: {'PASS' if result['ok'] else 'FAIL'}",
        f"- scene_count: {result['scene_count']}",
        f"- full_unresolved_count: {result['full_unresolved_count']}",
        f"- strict_scene_count: {result['strict_scene_count']}",
        f"- strict_unresolved_count: {result['strict_unresolved_count']}",
        f"- strict_source_gap_count: {result['strict_source_gap_count']}",
    ]
    if errors:
        lines.extend(["", "## Errors"])
        lines.extend([f"- {item}" for item in errors])
    if source_gap_rows:
        lines.extend(["", "## Source Gaps"])
        for row in source_gap_rows:
            lines.append(
                f"- `{row['scene_key']}` source_missing={','.join(row['source_missing']) or '-'} defaults_applied={','.join(row['defaults_applied']) or '-'}"
            )
    if unresolved_all_rows:
        lines.extend(["", "## Full Scene Unresolved"])
        for row in unresolved_all_rows:
            lines.append(
                f"- `{row['scene_key']}` missing={','.join(row['missing']) or '-'}"
            )
    if unresolved_strict_rows:
        lines.extend(["", "## Unresolved"])
        for row in unresolved_strict_rows:
            lines.append(
                f"- `{row['scene_key']}` missing={','.join(row['missing']) or '-'} contract_ready={row['contract_ready']}"
            )
    _write(REPORT_MD, "\n".join(lines) + "\n")

    if errors:
        print("[FAIL] scene_ready_strict_gap_full_audit")
        for item in errors:
            print(f" - {item}")
        print(f"report: {REPORT_JSON.relative_to(ROOT).as_posix()}")
        print(f"report_md: {REPORT_MD.relative_to(ROOT).as_posix()}")
        return 2

    print("[PASS] scene_ready_strict_gap_full_audit")
    print(
        "summary:",
        f"full_unresolved_count={len(unresolved_all_rows)}",
        f"strict_scene_count={len(strict_rows)}",
        f"source_gap_count={len(source_gap_rows)}",
        f"strict_unresolved_count={len(unresolved_strict_rows)}",
    )
    print(f"report: {REPORT_JSON.relative_to(ROOT).as_posix()}")
    print(f"report_md: {REPORT_MD.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
