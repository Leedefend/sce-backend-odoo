#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ROLE_FLOOR_JSON = ROOT / "artifacts" / "backend" / "role_capability_floor_prod_like.json"
OUT_JSON = ROOT / "artifacts" / "backend" / "project_member_unification_guard.json"
OUT_MD = ROOT / "artifacts" / "backend" / "project_member_unification_guard.md"


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def main() -> int:
    floor = _load_json(ROLE_FLOOR_JSON)
    errors: list[str] = []
    summary: dict = {
        "project_member_found": False,
        "project_member_login": "",
        "project_member_ok": False,
        "project_member_capability_count": 0,
        "has_material_group": False,
        "has_cost_group": False,
    }

    if not floor:
        errors.append(f"missing role floor artifact: {ROLE_FLOOR_JSON.as_posix()}")
    roles = floor.get("roles") if isinstance(floor.get("roles"), list) else []
    project_member = None
    for row in roles:
        if not isinstance(row, dict):
            continue
        if str(row.get("role") or "").strip() == "project_member":
            project_member = row
            break

    if not isinstance(project_member, dict):
        errors.append("project_member fixture not found in role floor artifact")
    else:
        summary["project_member_found"] = True
        summary["project_member_login"] = str(project_member.get("login") or "").strip()
        summary["project_member_ok"] = bool(project_member.get("ok"))
        summary["project_member_capability_count"] = int(project_member.get("capability_count") or 0)
        groups = {
            str(x).strip()
            for x in (project_member.get("groups_xmlids") or [])
            if str(x).strip()
        }
        summary["has_material_group"] = "smart_construction_core.group_sc_role_material_user" in groups
        summary["has_cost_group"] = "smart_construction_core.group_sc_role_cost_user" in groups

        if not summary["project_member_ok"]:
            errors.append("project_member runtime floor check failed")
        if summary["project_member_capability_count"] < 1:
            errors.append("project_member capability_count must be >= 1")
        if not summary["has_material_group"]:
            errors.append("project_member missing material_user group mapping")
        if not summary["has_cost_group"]:
            errors.append("project_member missing cost_user group mapping")

    report = {
        "ok": len(errors) == 0,
        "summary": summary,
        "errors": errors,
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Project Member Unification Guard",
        "",
        f"- status: {'PASS' if report['ok'] else 'FAIL'}",
        f"- project_member_found: {summary['project_member_found']}",
        f"- project_member_login: {summary['project_member_login'] or '-'}",
        f"- project_member_ok: {summary['project_member_ok']}",
        f"- project_member_capability_count: {summary['project_member_capability_count']}",
        f"- has_material_group: {summary['has_material_group']}",
        f"- has_cost_group: {summary['has_cost_group']}",
        f"- error_count: {len(errors)}",
    ]
    if errors:
        lines.extend(["", "## Errors", ""])
        for item in errors:
            lines.append(f"- {item}")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(OUT_JSON))
    print(str(OUT_MD))
    if errors:
        print("[project_member_unification_guard] FAIL")
        return 1
    print("[project_member_unification_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

