#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
from pathlib import Path

from intent_smoke_utils import require_ok
from python_http_smoke_utils import get_base_url, http_post_json


ROOT = Path(__file__).resolve().parents[2]
BASELINE_JSON = ROOT / "scripts" / "verify" / "baselines" / "project_form_contract_surface_guard.json"


def _resolve_artifacts_dir() -> Path:
    candidates = [
        str(os.getenv("ARTIFACTS_DIR") or "").strip(),
        "/mnt/artifacts",
        str(ROOT / "artifacts"),
    ]
    for raw in candidates:
        if not raw:
            continue
        path = Path(raw)
        try:
            path.mkdir(parents=True, exist_ok=True)
            probe = path / ".probe_write"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink(missing_ok=True)
            return path
        except Exception:
            continue
    raise RuntimeError("no writable artifacts dir available")


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


def _request_form_contract(intent_url: str, token: str, contract_mode: str) -> tuple[dict, dict]:
    status, resp = http_post_json(
        intent_url,
        {
            "intent": "ui.contract",
            "params": {"op": "model", "model": "project.project", "view_type": "form", "contract_mode": contract_mode},
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    require_ok(status, resp, f"ui.contract.form.{contract_mode}")
    data = resp.get("data") if isinstance(resp.get("data"), dict) else {}
    meta = resp.get("meta") if isinstance(resp.get("meta"), dict) else {}
    return data, meta


def main() -> int:
    baseline = _load_json(BASELINE_JSON)
    if not baseline:
        print("[project_form_contract_surface_guard] FAIL")
        print(f"invalid baseline: {BASELINE_JSON.relative_to(ROOT).as_posix()}")
        return 1

    db_name = str(os.getenv("E2E_DB") or os.getenv("DB_NAME") or "").strip()
    fixture_password = str(os.getenv("E2E_PROD_LIKE_PASSWORD") or baseline.get("fixture_password") or "prod_like").strip()
    roles = baseline.get("roles") if isinstance(baseline.get("roles"), list) else []
    required_user_fields = [str(x).strip() for x in (baseline.get("required_user_fields") or []) if str(x).strip()]
    forbidden_user_fields = [str(x).strip() for x in (baseline.get("forbidden_user_fields") or []) if str(x).strip()]
    max_user_fields = int(baseline.get("max_user_fields") or 25)
    max_user_header_buttons = int(baseline.get("max_user_header_buttons") or 3)
    max_user_smart_buttons = int(baseline.get("max_user_smart_buttons") or 4)
    max_user_search_filters = int(baseline.get("max_user_search_filters") or 8)

    base_url = get_base_url()
    intent_url = f"{base_url}/api/v1/intent"
    artifacts_dir = _resolve_artifacts_dir() / "backend"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    artifact_json = artifacts_dir / "project_form_contract_surface_guard.json"
    artifact_md = artifacts_dir / "project_form_contract_surface_guard.md"

    errors: list[str] = []
    role_reports: list[dict] = []
    for role_cfg in roles:
        role = str(role_cfg.get("role") or "").strip()
        login = str(role_cfg.get("login") or "").strip()
        if not role or not login:
            errors.append(f"invalid role config: role={role!r} login={login!r}")
            continue
        row = {"role": role, "login": login, "ok": False, "failure_reason": ""}
        try:
            token = _login_token(intent_url, db_name, login, fixture_password)
            user_data, user_meta = _request_form_contract(intent_url, token, "user")
            hud_data, hud_meta = _request_form_contract(intent_url, token, "hud")

            user_fields = user_data.get("fields") if isinstance(user_data.get("fields"), dict) else {}
            hud_fields = hud_data.get("fields") if isinstance(hud_data.get("fields"), dict) else {}
            user_buttons = user_data.get("buttons") if isinstance(user_data.get("buttons"), list) else []
            user_header_buttons = [
                x for x in user_buttons if isinstance(x, dict) and str(x.get("level") or "").strip().lower() == "header"
            ]
            user_smart_buttons = [
                x
                for x in user_buttons
                if isinstance(x, dict) and str(x.get("level") or "").strip().lower() in {"smart", "row"}
            ]
            user_filters = (((user_data.get("search") or {}).get("filters")) or []) if isinstance(user_data.get("search"), dict) else []
            user_layout = (((user_data.get("views") or {}).get("form") or {}).get("layout") or []) if isinstance(user_data.get("views"), dict) else []
            user_layout_field_count = len(
                [x for x in user_layout if isinstance(x, dict) and str(x.get("type") or "").strip().lower() == "field"]
            )
            user_toolbar_header = (((user_data.get("toolbar") or {}).get("header")) or []) if isinstance(user_data.get("toolbar"), dict) else []

            row["user"] = {
                "contract_mode": user_meta.get("contract_mode"),
                "field_count": len(user_fields),
                "layout_field_count": user_layout_field_count,
                "header_button_count": len(user_header_buttons),
                "smart_button_count": len(user_smart_buttons),
                "search_filter_count": len(user_filters) if isinstance(user_filters, list) else 0,
                "toolbar_header_count": len(user_toolbar_header) if isinstance(user_toolbar_header, list) else 0,
            }
            row["hud"] = {
                "contract_mode": hud_meta.get("contract_mode"),
                "field_count": len(hud_fields),
            }

            if row["user"]["contract_mode"] != "user":
                errors.append(f"{role}.user contract_mode != user")
            if row["hud"]["contract_mode"] != "hud":
                errors.append(f"{role}.hud contract_mode != hud")
            if row["user"]["field_count"] > max_user_fields:
                errors.append(f"{role}.user field_count={row['user']['field_count']} exceeds max={max_user_fields}")
            if row["user"]["layout_field_count"] < min(row["user"]["field_count"], 12):
                errors.append(
                    f"{role}.user layout_field_count={row['user']['layout_field_count']} too low for field_count={row['user']['field_count']}"
                )
            if row["user"]["header_button_count"] > max_user_header_buttons:
                errors.append(
                    f"{role}.user header_button_count={row['user']['header_button_count']} exceeds max={max_user_header_buttons}"
                )
            if row["user"]["smart_button_count"] > max_user_smart_buttons:
                errors.append(
                    f"{role}.user smart_button_count={row['user']['smart_button_count']} exceeds max={max_user_smart_buttons}"
                )
            if row["user"]["search_filter_count"] > max_user_search_filters:
                errors.append(
                    f"{role}.user search_filter_count={row['user']['search_filter_count']} exceeds max={max_user_search_filters}"
                )
            if row["user"]["toolbar_header_count"] != 0:
                errors.append(f"{role}.user toolbar.header should be empty")
            for field in required_user_fields:
                if field not in user_fields:
                    errors.append(f"{role}.user missing required field `{field}`")
            for field in forbidden_user_fields:
                if field in user_fields:
                    errors.append(f"{role}.user includes forbidden field `{field}`")
            if len(hud_fields) < len(user_fields):
                errors.append(f"{role}.hud field_count={len(hud_fields)} should be >= user={len(user_fields)}")
            row["ok"] = True
        except Exception as exc:
            row["failure_reason"] = str(exc)
            errors.append(f"{role}: {exc}")
        role_reports.append(row)

    report = {
        "ok": len(errors) == 0,
        "summary": {
            "role_count": len(role_reports),
            "passed_role_count": sum(1 for row in role_reports if row.get("ok")),
            "failed_role_count": sum(1 for row in role_reports if not row.get("ok")),
            "error_count": len(errors),
            "artifacts_dir": str(artifacts_dir),
        },
        "baseline": baseline,
        "roles": sorted(role_reports, key=lambda row: str(row.get("role") or "")),
        "errors": sorted(errors),
    }
    artifact_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Project Form Contract Surface Guard",
        "",
        f"- status: {'PASS' if report['ok'] else 'FAIL'}",
        f"- role_count: {report['summary']['role_count']}",
        f"- error_count: {report['summary']['error_count']}",
        "",
        "## Roles",
        "",
    ]
    for row in report["roles"]:
        lines.append(f"- {row['role']} ({row['login']}): {'PASS' if row.get('ok') else 'FAIL'} {row.get('failure_reason') or ''}".strip())
    if report["errors"]:
        lines.extend(["", "## Actionable Errors", ""])
        for item in report["errors"][:200]:
            lines.append(f"- {item}")
    artifact_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(artifact_json))
    print(str(artifact_md))
    if not report["ok"]:
        print("[project_form_contract_surface_guard] FAIL")
        return 1
    print("[project_form_contract_surface_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
