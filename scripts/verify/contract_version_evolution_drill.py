#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
import re
from pathlib import Path

from python_http_smoke_utils import get_base_url, http_post_json


ROOT = Path(__file__).resolve().parents[2]
BASELINE_JSON = ROOT / "scripts" / "verify" / "baselines" / "contract_version_evolution.json"
VERSION_RULES = ROOT / "docs" / "contract" / "versioning_rules.md"
REPORT_MD = ROOT / "docs" / "ops" / "audit" / "contract_version_evolution_report.md"
REPORT_JSON = ROOT / "artifacts" / "backend" / "contract_version_evolution_report.json"


def _load_baseline() -> dict:
    if not BASELINE_JSON.is_file():
        return {}
    try:
        payload = json.loads(BASELINE_JSON.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _ver_tuple(raw: str) -> tuple[int, ...]:
    text = str(raw or "").strip().lower()
    if text.startswith("v"):
        text = text[1:]
    out = []
    for p in text.split("."):
        try:
            out.append(int(p))
        except Exception:
            out.append(0)
    return tuple(out) if out else (0,)


def _login(intent_url: str, db_name: str, login: str, password: str) -> tuple[bool, str]:
    status, payload = http_post_json(
        intent_url,
        {"intent": "login", "params": {"db": db_name, "login": login, "password": password}},
        headers={"X-Anonymous-Intent": "1"},
    )
    if status >= 400 or not isinstance(payload, dict) or payload.get("ok") is not True:
        return False, ""
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    session = data.get("session") if isinstance(data.get("session"), dict) else {}
    token = str(session.get("token") or data.get("token") or "").strip()
    return bool(token), token


def _intent(intent_url: str, token: str, intent: str, params: dict) -> tuple[int, dict]:
    return http_post_json(
        intent_url,
        {"intent": intent, "params": params},
        headers={"Authorization": f"Bearer {token}"},
    )


def _ensure_keys(obj: dict, keys: list[str], missing: list[str], prefix: str):
    for k in keys:
        if k not in obj:
            missing.append(f"{prefix}.{k}")


_SEMVER_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")


def _is_semver(value: str) -> bool:
    return bool(_SEMVER_RE.match(str(value or "").strip()))


def main() -> int:
    baseline = _load_baseline()
    errors: list[str] = []
    warnings: list[str] = []
    missing: list[str] = []

    if not VERSION_RULES.is_file():
        errors.append("missing docs/contract/versioning_rules.md")

    base_url = get_base_url()
    intent_url = f"{base_url}/api/v1/intent"
    db_name = str(os.getenv("DB_NAME") or os.getenv("ODOO_DB") or "sc_dev").strip()
    login = str(os.getenv("E2E_LOGIN") or "admin").strip()
    password = str(os.getenv("E2E_PASSWORD") or os.getenv("ADMIN_PASSWD") or "admin").strip()

    ok, token = _login(intent_url, db_name, login, password)
    if not ok:
        errors.append("login failed for contract version drill")
        token = ""

    login_payload = {}
    system_payload = {}
    ui_payload = {}
    login_status, login_resp = http_post_json(
        intent_url,
        {"intent": "login", "params": {"db": db_name, "login": login, "password": password}},
        headers={"X-Anonymous-Intent": "1"},
    )
    if login_status >= 400 or not isinstance(login_resp, dict):
        errors.append("login unavailable for evolution drill")
    else:
        login_payload = login_resp

    if token:
        st_a, p_a = _intent(intent_url, token, "system.init", {"contract_mode": "user"})
        st_b, p_b = _intent(
            intent_url, token, "ui.contract", {"op": "model", "model": "project.project", "view_type": "form"}
        )
        if st_a >= 400 or not isinstance(p_a, dict):
            errors.append("system.init unavailable for evolution drill")
        else:
            system_payload = p_a
        if st_b >= 400 or not isinstance(p_b, dict):
            errors.append("ui.contract unavailable for evolution drill")
        else:
            ui_payload = p_b

    required_env = baseline.get("required_envelope_keys") if isinstance(baseline.get("required_envelope_keys"), list) else []
    required_meta = baseline.get("required_meta_keys") if isinstance(baseline.get("required_meta_keys"), list) else []
    semver_meta_keys = baseline.get("semver_meta_keys") if isinstance(baseline.get("semver_meta_keys"), list) else []
    sys_keys = baseline.get("required_system_init_data_keys") if isinstance(baseline.get("required_system_init_data_keys"), list) else []
    ui_keys = baseline.get("required_ui_contract_data_keys") if isinstance(baseline.get("required_ui_contract_data_keys"), list) else []

    if login_payload:
        _ensure_keys(login_payload, required_env, missing, "login")
        login_meta = login_payload.get("meta") if isinstance(login_payload.get("meta"), dict) else {}
        _ensure_keys(login_meta, required_meta, missing, "login.meta")
        for key in semver_meta_keys:
            if not _is_semver(str(login_meta.get(key) or "")):
                errors.append(f"login.meta.{key} not semver: {login_meta.get(key)!r}")

    if system_payload:
        _ensure_keys(system_payload, required_env, missing, "system.init")
        meta = system_payload.get("meta") if isinstance(system_payload.get("meta"), dict) else {}
        _ensure_keys(meta, required_meta, missing, "system.init.meta")
        for key in semver_meta_keys:
            if not _is_semver(str(meta.get(key) or "")):
                errors.append(f"system.init.meta.{key} not semver: {meta.get(key)!r}")
        data = system_payload.get("data") if isinstance(system_payload.get("data"), dict) else {}
        if isinstance(data.get("data"), dict):
            data = data.get("data")
        _ensure_keys(data, sys_keys, missing, "system.init.data")

    if ui_payload:
        _ensure_keys(ui_payload, required_env, missing, "ui.contract")
        meta = ui_payload.get("meta") if isinstance(ui_payload.get("meta"), dict) else {}
        _ensure_keys(meta, required_meta + ["response_schema_version"], missing, "ui.contract.meta")
        for key in semver_meta_keys:
            if not _is_semver(str(meta.get(key) or "")):
                errors.append(f"ui.contract.meta.{key} not semver: {meta.get(key)!r}")
        data = ui_payload.get("data") if isinstance(ui_payload.get("data"), dict) else {}
        _ensure_keys(data, ui_keys, missing, "ui.contract.data")

    if missing:
        errors.append(f"required keys missing: {len(missing)}")

    min_api = str(baseline.get("min_api_version") or "v1")
    min_contract = str(baseline.get("min_contract_version") or "1.0.0")
    api_ver = ""
    contract_ver = ""
    if ui_payload and isinstance(ui_payload.get("meta"), dict):
        api_ver = str(ui_payload["meta"].get("api_version") or "")
        contract_ver = str(ui_payload["meta"].get("contract_version") or "")
    if api_ver and _ver_tuple(api_ver) < _ver_tuple(min_api):
        errors.append(f"api_version regressed: {api_ver} < {min_api}")
    if contract_ver and _ver_tuple(contract_ver) < _ver_tuple(min_contract):
        errors.append(f"contract_version regressed: {contract_ver} < {min_contract}")

    payload = {
        "ok": len(errors) == 0,
        "summary": {
            "api_version": api_ver,
            "contract_version": contract_ver,
            "missing_key_count": len(missing),
            "error_count": len(errors),
            "warning_count": len(warnings),
        },
        "missing_keys": missing,
        "errors": errors,
        "warnings": warnings,
    }
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Contract Version Evolution Report",
        "",
        f"- api_version: {api_ver or '-'}",
        f"- contract_version: {contract_ver or '-'}",
        f"- missing_key_count: {len(missing)}",
        f"- error_count: {len(errors)}",
        f"- warning_count: {len(warnings)}",
        "",
        "## Errors",
        "",
    ]
    if errors:
        for item in errors:
            lines.append(f"- {item}")
    else:
        lines.append("- none")
    lines.extend(["", "## Missing Keys", ""])
    if missing:
        for item in missing:
            lines.append(f"- {item}")
    else:
        lines.append("- none")
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(REPORT_MD))
    print(str(REPORT_JSON))
    if errors:
        print("[contract_version_evolution_drill] FAIL")
        return 2
    print("[contract_version_evolution_drill] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
