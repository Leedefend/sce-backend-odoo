#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
from pathlib import Path

from intent_smoke_utils import require_ok
from python_http_smoke_utils import get_base_url, http_post_json


ROOT = Path(__file__).resolve().parents[2]
BASELINE_JSON = ROOT / "scripts" / "verify" / "baselines" / "capability_core_health_report.json"
PROD_LIKE_BASELINE_JSON = ROOT / "scripts" / "verify" / "baselines" / "role_capability_floor_prod_like.json"

VALID_CAPABILITY_STATES = {"allow", "readonly", "deny", "pending", "coming_soon"}
VALID_STATES = {"READY", "LOCKED", "PREVIEW"}


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


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


def _load_prod_like_logins() -> list[str]:
    baseline = _load_json(PROD_LIKE_BASELINE_JSON)
    fixtures = baseline.get("fixtures") if isinstance(baseline.get("fixtures"), list) else []
    out: list[str] = []
    for item in fixtures:
        if not isinstance(item, dict):
            continue
        login = str(item.get("login") or "").strip()
        if login and login not in out:
            out.append(login)
    return out


def _login(intent_url: str, db_name: str, login: str, password: str) -> str:
    status, resp = http_post_json(
        intent_url,
        {"intent": "login", "params": {"db": db_name, "login": login, "password": password}},
        headers={"X-Anonymous-Intent": "1"},
    )
    if status != 200:
        return ""
    data = resp.get("data") if isinstance(resp.get("data"), dict) else {}
    return str(data.get("token") or "").strip()


def _system_init(intent_url: str, token: str, contract_mode: str) -> dict:
    status, resp = http_post_json(
        intent_url,
        {"intent": "system.init", "params": {"contract_mode": contract_mode}},
        headers={"Authorization": f"Bearer {token}"},
    )
    require_ok(status, resp, f"system.init[{contract_mode}]")
    data = resp.get("data") if isinstance(resp.get("data"), dict) else {}
    if isinstance(data.get("data"), dict):
        data = data.get("data") or data
    return data


def _check_capability(cap: dict, path: str, warnings: list[str]) -> None:
    group_key = str(cap.get("group_key") or "").strip()
    group_label = str(cap.get("group_label") or "").strip()
    state = str(cap.get("state") or "").strip().upper()
    capability_state = str(cap.get("capability_state") or "").strip().lower()

    if not group_key:
        warnings.append(f"{path} missing group_key")
    if not group_label:
        warnings.append(f"{path} missing group_label")
    if state not in VALID_STATES:
        warnings.append(f"{path} invalid state={state!r}")
    if capability_state not in VALID_CAPABILITY_STATES:
        warnings.append(f"{path} invalid capability_state={capability_state!r}")
    if "capability_state_reason" not in cap:
        warnings.append(f"{path} missing capability_state_reason")


def _check_tile(tile: dict, path: str, warnings: list[str]) -> None:
    state = str(tile.get("capability_state") or "").strip().lower()
    if state and state not in VALID_CAPABILITY_STATES:
        warnings.append(f"{path} invalid capability_state={state!r}")
    if state and "capability_state_reason" not in tile:
        warnings.append(f"{path} missing capability_state_reason")


def main() -> int:
    baseline = {
        "min_role_samples": 2,
        "min_capability_count_per_role": 1,
        "max_errors": 0,
    }
    baseline.update(_load_json(BASELINE_JSON))

    base_url = get_base_url()
    intent_url = f"{base_url}/api/v1/intent"
    db_name = str(os.getenv("E2E_DB") or os.getenv("DB_NAME") or "").strip()
    admin_login = str(os.getenv("E2E_LOGIN") or "admin").strip()
    admin_password = str(os.getenv("E2E_PASSWORD") or os.getenv("ADMIN_PASSWD") or "admin").strip()
    prod_like_password = str(os.getenv("E2E_PROD_LIKE_PASSWORD") or "prod_like").strip()
    demo_password = str(os.getenv("E2E_ROLE_MATRIX_DEFAULT_PASSWORD") or "demo").strip()

    logins = _load_prod_like_logins()
    if admin_login and admin_login not in logins:
        logins.append(admin_login)
    for fallback in ("demo_pm", "demo_finance", "demo_role_executive"):
        if fallback not in logins:
            logins.append(fallback)

    role_reports: list[dict] = []
    errors: list[str] = []
    warnings: list[str] = []
    login_failures: list[str] = []

    for login in logins:
        if login == "admin" or login == admin_login:
            pwd = admin_password
        elif login.startswith("sc_fx_"):
            pwd = prod_like_password
        else:
            pwd = demo_password
        token = _login(intent_url, db_name, login, pwd)
        if not token:
            login_failures.append(login)
            continue
        role_row = {
            "login": login,
            "user_mode": {"capability_count": 0, "group_count": 0, "scene_count": 0, "error_count": 0},
            "hud_mode": {"capability_count": 0, "group_count": 0, "scene_count": 0, "error_count": 0},
        }
        for mode in ("user", "hud"):
            payload = _system_init(intent_url, token, mode)
            caps = payload.get("capabilities") if isinstance(payload.get("capabilities"), list) else []
            scenes = payload.get("scenes") if isinstance(payload.get("scenes"), list) else []
            groups = payload.get("capability_groups") if isinstance(payload.get("capability_groups"), list) else []
            mode_errors: list[str] = []
            mode_warnings: list[str] = []
            for idx, cap in enumerate(caps):
                if not isinstance(cap, dict):
                    mode_errors.append(f"{login}.{mode}.capabilities[{idx}] invalid object")
                    continue
                _check_capability(cap, f"{login}.{mode}.capabilities[{idx}]", mode_warnings)
            for s_idx, scene in enumerate(scenes):
                if not isinstance(scene, dict):
                    continue
                tiles = scene.get("tiles") if isinstance(scene.get("tiles"), list) else []
                for t_idx, tile in enumerate(tiles):
                    if not isinstance(tile, dict):
                        continue
                    _check_tile(tile, f"{login}.{mode}.scenes[{s_idx}].tiles[{t_idx}]", mode_warnings)

            if len(caps) < int(baseline.get("min_capability_count_per_role") or 1):
                mode_errors.append(
                    f"{login}.{mode}.capability_count below baseline: {len(caps)} < "
                    f"{int(baseline.get('min_capability_count_per_role') or 1)}"
                )

            role_row[f"{mode}_mode"] = {
                "capability_count": len(caps),
                "group_count": len(groups),
                "scene_count": len(scenes),
                "error_count": len(mode_errors),
                "warning_count": len(mode_warnings),
            }
            errors.extend(mode_errors)
            warnings.extend(mode_warnings)
        role_reports.append(role_row)

    if len(role_reports) < int(baseline.get("min_role_samples") or 2):
        errors.append(f"role_samples below baseline: {len(role_reports)} < {int(baseline.get('min_role_samples') or 2)}")

    report = {
        "ok": len(errors) <= int(baseline.get("max_errors") or 0),
        "baseline": baseline,
        "summary": {
            "role_sample_count": len(role_reports),
            "login_failure_count": len(login_failures),
            "error_count": len(errors),
            "warning_count": len(warnings),
        },
        "roles": sorted(role_reports, key=lambda row: str(row.get("login") or "")),
        "login_failures": sorted(login_failures),
        "errors": sorted(errors),
        "warnings": sorted(warnings),
    }

    artifacts_root = _resolve_artifacts_dir()
    artifact_json = artifacts_root / "backend" / "capability_core_health_report.json"
    artifact_md = artifacts_root / "backend" / "capability_core_health_report.md"
    artifact_json.parent.mkdir(parents=True, exist_ok=True)
    artifact_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Capability Core Health Report",
        "",
        f"- status: {'PASS' if report['ok'] else 'FAIL'}",
        f"- role_sample_count: {report['summary']['role_sample_count']}",
        f"- login_failure_count: {report['summary']['login_failure_count']}",
        f"- error_count: {report['summary']['error_count']}",
        f"- warning_count: {report['summary']['warning_count']}",
    ]
    if report["errors"]:
        lines.extend(["", "## Errors", ""])
        for item in report["errors"][:200]:
            lines.append(f"- {item}")
    if report["warnings"]:
        lines.extend(["", "## Warnings", ""])
        for item in report["warnings"][:200]:
            lines.append(f"- {item}")
    artifact_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(artifact_json))
    print(str(artifact_md))
    if not report["ok"]:
        print("[capability_core_health_report] FAIL")
        return 1
    print("[capability_core_health_report] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
