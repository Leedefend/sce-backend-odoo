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


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _resolve_artifacts_dir() -> Path:
    for raw in (os.getenv("ARTIFACTS_DIR"), "/mnt/artifacts", str(ROOT / "artifacts")):
        p = Path(str(raw or "").strip())
        if not str(p):
            continue
        try:
            p.mkdir(parents=True, exist_ok=True)
            return p
        except Exception:
            continue
    raise RuntimeError("no writable artifacts dir available")


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


def _request_user_surface(intent_url: str, token: str) -> tuple[dict, dict]:
    status, resp = http_post_json(
        intent_url,
        {
            "intent": "ui.contract",
            "params": {
                "op": "model",
                "model": "project.project",
                "view_type": "form",
                "contract_surface": "user",
                "source_mode": "governance_pipeline",
            },
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    require_ok(status, resp, "ui.contract.user_surface")
    data = resp.get("data") if isinstance(resp.get("data"), dict) else {}
    meta = resp.get("meta") if isinstance(resp.get("meta"), dict) else {}
    return data, meta


def _collect_fields(row: dict) -> list[str]:
    fields = row.get("fields") if isinstance(row.get("fields"), dict) else {}
    return [str(name).strip() for name in fields.keys() if str(name).strip()]


def main() -> int:
    baseline = _load_json(BASELINE_JSON)
    if not baseline:
        print("[governed_surface_policy_guard] FAIL")
        print(f"invalid baseline: {BASELINE_JSON.relative_to(ROOT).as_posix()}")
        return 1

    db_name = str(os.getenv("E2E_DB") or os.getenv("DB_NAME") or "").strip()
    fixture_password = str(os.getenv("E2E_PROD_LIKE_PASSWORD") or baseline.get("fixture_password") or "prod_like").strip()
    roles = baseline.get("roles") if isinstance(baseline.get("roles"), list) else []
    max_user_fields = int(baseline.get("max_user_fields") or 25)
    forbidden_user_fields = [str(x).strip() for x in (baseline.get("forbidden_user_fields") or []) if str(x).strip()]
    env_name = str(os.getenv("ENV") or "").strip().lower()
    strict_surface = env_name not in {"dev", "test", "local"}
    if not strict_surface:
        max_user_fields = max(max_user_fields, 10000)
        forbidden_user_fields = []

    base_url = get_base_url()
    intent_url = f"{base_url}/api/v1/intent"
    artifacts_dir = _resolve_artifacts_dir() / "backend"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    artifact_json = artifacts_dir / "governed_surface_policy_guard.json"
    artifact_md = artifacts_dir / "governed_surface_policy_guard.md"

    role_reports: list[dict] = []
    errors: list[str] = []

    for role_cfg in roles:
        role = str(role_cfg.get("role") or "").strip()
        login = str(role_cfg.get("login") or "").strip()
        row = {"role": role, "login": login, "ok": False, "reason": ""}
        try:
            token = _login_token(intent_url, db_name, login, fixture_password)
            data, meta = _request_user_surface(intent_url, token)
            fields = _collect_fields(data)
            forbidden_hits = sorted([name for name in fields if name in set(forbidden_user_fields)])

            mapping = data.get("surface_mapping") if isinstance(data.get("surface_mapping"), dict) else {}
            native_mapping = mapping.get("native_to_governed") if isinstance(mapping.get("native_to_governed"), dict) else {}
            fields_mapping = native_mapping.get("fields") if isinstance(native_mapping.get("fields"), dict) else {}
            removed_fields = fields_mapping.get("removed") if isinstance(fields_mapping.get("removed"), list) else []

            checks = [
                str(data.get("contract_surface") or "").strip().lower() == "user",
                str(meta.get("contract_surface") or "").strip().lower() == "user",
                str(data.get("render_mode") or "").strip().lower() == "governed",
                str(data.get("source_mode") or "").strip().lower() == "governance_pipeline",
                data.get("governed_from_native") is True,
                isinstance(native_mapping, dict),
                isinstance(removed_fields, list),
                (len(fields) <= max_user_fields) if strict_surface else True,
                (len(forbidden_hits) == 0) if strict_surface else True,
            ]
            if all(checks):
                row["ok"] = True
            else:
                row["reason"] = f"user surface policy failed forbidden={forbidden_hits[:5]} field_count={len(fields)}"
        except Exception as exc:
            row["ok"] = False
            row["reason"] = str(exc)
        if not row["ok"]:
            errors.append(f"{role}:{row['reason']}")
        role_reports.append(row)

    payload = {
        "ok": not errors,
        "summary": {
            "role_count": len(role_reports),
            "passed_role_count": sum(1 for x in role_reports if x.get("ok")),
            "failed_role_count": sum(1 for x in role_reports if not x.get("ok")),
            "error_count": len(errors),
            "artifacts_dir": str(artifacts_dir),
        },
        "roles": role_reports,
        "errors": errors,
    }
    artifact_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# Governed Surface Policy Guard",
        "",
        f"- status: {'PASS' if payload['ok'] else 'FAIL'}",
        f"- role_count: {payload['summary']['role_count']}",
        f"- error_count: {payload['summary']['error_count']}",
        "",
        "## Roles",
        "",
    ]
    for row in role_reports:
        lines.append(f"- {row['role']} ({row['login']}): {'PASS' if row['ok'] else 'FAIL'}")
    artifact_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(artifact_json))
    print(str(artifact_md))
    if payload["ok"]:
        print("[governed_surface_policy_guard] PASS")
        return 0
    print("[governed_surface_policy_guard] FAIL")
    for err in errors:
        print(f"- {err}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
