#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
from pathlib import Path

from intent_smoke_utils import require_ok
from python_http_smoke_utils import get_base_url, http_post_json


ROOT = Path(__file__).resolve().parents[2]
BASELINE_JSON = ROOT / "scripts" / "verify" / "baselines" / "load_view_access_contract_guard.json"
PROD_LIKE_BASELINE_JSON = ROOT / "scripts" / "verify" / "baselines" / "role_capability_floor_prod_like.json"
ARTIFACT_JSON = ROOT / "artifacts" / "backend" / "load_view_access_contract_guard.json"
ARTIFACT_MD = ROOT / "artifacts" / "backend" / "load_view_access_contract_guard.md"


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _resolve_fixture_login(role: str) -> str:
    baseline = _load_json(PROD_LIKE_BASELINE_JSON)
    fixtures = baseline.get("fixtures") if isinstance(baseline.get("fixtures"), list) else []
    target = str(role or "").strip()
    for fixture in fixtures:
        if not isinstance(fixture, dict):
            continue
        if str(fixture.get("role") or "").strip() != target:
            continue
        login = str(fixture.get("login") or "").strip()
        if login:
            return login
    return ""


def _intent_login(intent_url: str, db_name: str, login: str, password: str) -> str:
    status, payload = http_post_json(
        intent_url,
        {"intent": "login", "params": {"db": db_name, "login": login, "password": password}},
        headers={"X-Anonymous-Intent": "1"},
    )
    require_ok(status, payload, f"login({login})")
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    token = str(data.get("token") or "").strip()
    if not token:
        raise RuntimeError(f"login({login}) missing token")
    return token


def _load_view(intent_url: str, token: str, model: str, view_type: str) -> tuple[int, dict]:
    return http_post_json(
        intent_url,
        {"intent": "load_view", "params": {"model": model, "view_type": view_type}},
        headers={"Authorization": f"Bearer {token}"},
    )


def main() -> None:
    baseline = {
        "fixture_role": "finance",
        "allowed_model_candidates": ["res.partner", "project.project", "account.move", "payment.request"],
        "view_type": "form",
        "forbidden_model": "ir.ui.view",
        "forbidden_error_codes": ["PERMISSION_DENIED", "ACCESS_DENIED"],
        "max_errors": 0,
    }
    baseline_raw = _load_json(BASELINE_JSON)
    if baseline_raw:
        baseline.update(baseline_raw)

    fixture_role = str(baseline.get("fixture_role") or "finance").strip()
    fixture_login = str(os.getenv("E2E_LOAD_VIEW_GUARD_LOGIN") or "").strip() or _resolve_fixture_login(fixture_role)
    if not fixture_login:
        raise RuntimeError(f"missing fixture login for role={fixture_role}")

    fixture_password = str(os.getenv("E2E_PROD_LIKE_PASSWORD") or "prod_like").strip()
    allowed_candidates = [
        str(item).strip()
        for item in (baseline.get("allowed_model_candidates") if isinstance(baseline.get("allowed_model_candidates"), list) else [])
        if str(item).strip()
    ]
    if not allowed_candidates:
        raise RuntimeError("baseline.allowed_model_candidates is empty")

    forbidden_model = str(baseline.get("forbidden_model") or "ir.ui.view").strip()
    forbidden_error_codes = {
        str(item).strip()
        for item in (baseline.get("forbidden_error_codes") if isinstance(baseline.get("forbidden_error_codes"), list) else [])
        if str(item).strip()
    }
    view_type = str(baseline.get("view_type") or "form").strip()

    base_url = get_base_url()
    intent_url = f"{base_url}/api/v1/intent"
    db_name = os.getenv("E2E_DB") or os.getenv("DB_NAME") or ""
    token = _intent_login(intent_url, db_name, fixture_login, fixture_password)

    errors: list[str] = []
    allowed_model = ""
    allowed_status = 0
    allowed_error_code = ""
    for model in allowed_candidates:
        status, payload = _load_view(intent_url, token, model, view_type)
        if status < 400 and isinstance(payload, dict) and payload.get("ok") is True:
            allowed_model = model
            allowed_status = status
            break
        allowed_status = status
        err = payload.get("error") if isinstance(payload, dict) and isinstance(payload.get("error"), dict) else {}
        allowed_error_code = str(err.get("code") or "")
    if not allowed_model:
        errors.append(
            "no allowed model resolved for finance fixture; "
            f"tried={','.join(allowed_candidates)} last_status={allowed_status} last_error={allowed_error_code}"
        )

    forbidden_status, forbidden_payload = _load_view(intent_url, token, forbidden_model, view_type)
    forbidden_error = (
        forbidden_payload.get("error")
        if isinstance(forbidden_payload, dict) and isinstance(forbidden_payload.get("error"), dict)
        else {}
    )
    forbidden_error_code = str(forbidden_error.get("code") or "").strip()
    if forbidden_status != 403:
        errors.append(f"forbidden model status mismatch: expected 403 got {forbidden_status}")
    if forbidden_error_codes and forbidden_error_code not in forbidden_error_codes:
        errors.append(
            f"forbidden model error code mismatch: actual={forbidden_error_code} "
            f"expected in {sorted(forbidden_error_codes)}"
        )

    report = {
        "ok": len(errors) <= int(baseline.get("max_errors", 0)),
        "baseline": baseline,
        "summary": {
            "fixture_role": fixture_role,
            "fixture_login": fixture_login,
            "allowed_model": allowed_model,
            "allowed_status": allowed_status,
            "forbidden_model": forbidden_model,
            "forbidden_status": forbidden_status,
            "forbidden_error_code": forbidden_error_code,
            "error_count": len(errors),
        },
        "errors": errors,
    }
    ARTIFACT_JSON.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Load View Access Contract Guard",
        "",
        f"- status: {'PASS' if report['ok'] else 'FAIL'}",
        f"- fixture_role: {fixture_role}",
        f"- fixture_login: {fixture_login}",
        f"- allowed_model: {allowed_model or '-'}",
        f"- allowed_status: {allowed_status}",
        f"- forbidden_model: {forbidden_model}",
        f"- forbidden_status: {forbidden_status}",
        f"- forbidden_error_code: {forbidden_error_code or '-'}",
        f"- error_count: {len(errors)}",
    ]
    if errors:
        lines.extend(["", "## Errors", ""])
        for item in errors:
            lines.append(f"- {item}")
    ARTIFACT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(ARTIFACT_JSON))
    print(str(ARTIFACT_MD))
    if not report["ok"]:
        raise RuntimeError("load_view access contract guard not satisfied")
    print(
        "[load_view_access_contract_guard] PASS "
        f"login={fixture_login} allowed_model={allowed_model or '-'} forbidden_status={forbidden_status}"
    )


if __name__ == "__main__":
    main()
