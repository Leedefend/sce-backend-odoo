#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
from pathlib import Path

from intent_smoke_utils import require_ok
from python_http_smoke_utils import get_base_url, http_post_json


ROOT = Path(__file__).resolve().parents[2]
BASELINE_JSON = ROOT / "scripts" / "verify" / "baselines" / "role_capability_floor_prod_like.json"
OUT_JSON = ROOT / "artifacts" / "backend" / "project_dashboard_role_runtime_guard.json"
OUT_MD = ROOT / "artifacts" / "backend" / "project_dashboard_role_runtime_guard.md"

REQUIRED_ZONES = {"header", "metrics", "progress", "contract", "cost", "finance", "risk"}
TARGET_ROLES = {"pm", "finance", "project_member", "contract_admin"}


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _login_token(intent_url: str, db_name: str, login: str, password: str) -> str:
    status, resp = http_post_json(
        intent_url,
        {"intent": "login", "params": {"db": db_name, "login": login, "password": password}},
        headers={"X-Anonymous-Intent": "1"},
    )
    require_ok(status, resp, f"login({login})")
    data = resp.get("data") if isinstance(resp.get("data"), dict) else {}
    token = str(data.get("token") or "").strip()
    if not token:
        raise RuntimeError(f"login({login}) missing token")
    return token


def _call_project_dashboard(intent_url: str, token: str) -> dict:
    status, resp = http_post_json(
        intent_url,
        {"intent": "project.dashboard", "params": {}},
        headers={"Authorization": f"Bearer {token}"},
    )
    require_ok(status, resp, "project.dashboard")
    data = resp.get("data") if isinstance(resp.get("data"), dict) else {}
    return data


def main() -> int:
    errors: list[str] = []
    baseline = _load_json(BASELINE_JSON)
    fixtures = baseline.get("fixtures") if isinstance(baseline.get("fixtures"), list) else []
    fixture_password = str(os.getenv("E2E_PROD_LIKE_PASSWORD") or baseline.get("fixture_password") or "prod_like").strip()

    selected = []
    for row in fixtures:
        if not isinstance(row, dict):
            continue
        role = str(row.get("role") or "").strip()
        if role in TARGET_ROLES:
            selected.append({"role": role, "login": str(row.get("login") or "").strip()})
    if not selected:
        print("[project_dashboard_role_runtime_guard] FAIL")
        print("no target role fixtures found")
        return 1

    db_name = str(os.getenv("E2E_DB") or os.getenv("DB_NAME") or "").strip()
    intent_url = f"{get_base_url()}/api/v1/intent"
    role_rows = []

    for item in selected:
        role = item["role"]
        login = item["login"]
        row = {
            "role": role,
            "login": login,
            "ok": False,
            "zone_count": 0,
            "missing_zones": [],
            "forbidden_block_count": 0,
            "readonly_contract_ok": True,
            "failure_reason": "",
        }
        try:
            token = _login_token(intent_url, db_name, login, fixture_password)
            payload = _call_project_dashboard(intent_url, token)
            zones = payload.get("zones") if isinstance(payload.get("zones"), dict) else {}
            zone_keys = set(str(k).strip() for k in zones.keys() if str(k).strip())
            missing = sorted(REQUIRED_ZONES - zone_keys)
            if missing:
                raise RuntimeError(f"missing required zones: {missing}")

            forbidden = 0
            readonly_ok = True
            for key in sorted(REQUIRED_ZONES):
                zone = zones.get(key) if isinstance(zones.get(key), dict) else {}
                blocks = zone.get("blocks") if isinstance(zone.get("blocks"), list) else []
                if len(blocks) != 1:
                    raise RuntimeError(f"zone `{key}` block size must be 1")
                block = blocks[0] if isinstance(blocks[0], dict) else {}
                visibility = block.get("visibility") if isinstance(block.get("visibility"), dict) else {}
                if not isinstance(visibility.get("allowed"), bool):
                    raise RuntimeError(f"zone `{key}` visibility.allowed must be bool")
                reason_code = str(visibility.get("reason_code") or "").strip()
                if not reason_code:
                    raise RuntimeError(f"zone `{key}` visibility.reason_code is empty")
                if visibility.get("allowed") is False:
                    forbidden += 1
                    if reason_code != "PERMISSION_DENIED":
                        raise RuntimeError(f"zone `{key}` forbidden reason_code={reason_code!r} != PERMISSION_DENIED")
                if any(k in block for k in ("write_intent", "execute_intent", "editable")):
                    readonly_ok = False

            row.update(
                {
                    "ok": True,
                    "zone_count": len(zone_keys),
                    "missing_zones": missing,
                    "forbidden_block_count": forbidden,
                    "readonly_contract_ok": readonly_ok,
                }
            )
            if not readonly_ok:
                raise RuntimeError("dashboard contract exposes mutable keys")
        except Exception as exc:
            row["failure_reason"] = str(exc)
            errors.append(f"{role}: {exc}")
        role_rows.append(row)

    if sum(int(r.get("forbidden_block_count") or 0) for r in role_rows) <= 0:
        errors.append("no forbidden blocks observed across target roles")

    report = {
        "ok": len(errors) == 0,
        "summary": {
            "role_count": len(role_rows),
            "required_zone_count": len(REQUIRED_ZONES),
            "forbidden_block_total": sum(int(r.get("forbidden_block_count") or 0) for r in role_rows),
            "error_count": len(errors),
        },
        "roles": role_rows,
        "errors": errors,
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Project Dashboard Role Runtime Guard",
        "",
        f"- status: {'PASS' if report['ok'] else 'FAIL'}",
        f"- role_count: {report['summary']['role_count']}",
        f"- required_zone_count: {report['summary']['required_zone_count']}",
        f"- forbidden_block_total: {report['summary']['forbidden_block_total']}",
        f"- error_count: {report['summary']['error_count']}",
        "",
        "## Roles",
        "",
    ]
    for row in role_rows:
        lines.append(
            f"- {row['role']} ({row['login']}): {'PASS' if row.get('ok') else 'FAIL'} "
            f"zones={row.get('zone_count')} forbidden={row.get('forbidden_block_count')} "
            f"readonly={row.get('readonly_contract_ok')} reason={row.get('failure_reason') or 'ok'}"
        )
    if errors:
        lines.extend(["", "## Errors", ""])
        for item in errors:
            lines.append(f"- {item}")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(OUT_JSON))
    print(str(OUT_MD))
    if errors:
        print("[project_dashboard_role_runtime_guard] FAIL")
        return 1
    print("[project_dashboard_role_runtime_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

