#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
from pathlib import Path

from intent_smoke_utils import require_ok
from python_http_smoke_utils import get_base_url, http_post_json


ROOT = Path(__file__).resolve().parents[2]
CATALOG_JSON = ROOT / "docs" / "contract" / "exports" / "scene_catalog.json"
BASELINE_JSON = ROOT / "scripts" / "verify" / "baselines" / "scene_catalog_runtime_alignment.json"
ARTIFACT_JSON = ROOT / "artifacts" / "scene_catalog_runtime_alignment_guard.json"
ARTIFACT_MD = ROOT / "artifacts" / "scene_catalog_runtime_alignment_guard.md"
PROD_LIKE_BASELINE_JSON = ROOT / "scripts" / "verify" / "baselines" / "role_capability_floor_prod_like.json"


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _extract_scene_count(payload: dict) -> int:
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    if isinstance(data.get("data"), dict):  # compat nested envelope
        data = data.get("data") or data
    scenes = data.get("scenes") if isinstance(data.get("scenes"), list) else []
    return len(scenes)


def _login_token(intent_url: str, db_name: str, login: str, password: str) -> str:
    status, login_resp = http_post_json(
        intent_url,
        {"intent": "login", "params": {"db": db_name, "login": login, "password": password}},
        headers={"X-Anonymous-Intent": "1"},
    )
    require_ok(status, login_resp, "login")
    data = login_resp.get("data") if isinstance(login_resp.get("data"), dict) else {}
    token = str(data.get("token") or "").strip()
    if not token:
        raise RuntimeError("login response missing token")
    return token


def _load_prod_like_logins() -> list[str]:
    baseline = _load_json(PROD_LIKE_BASELINE_JSON)
    fixtures = baseline.get("fixtures") if isinstance(baseline.get("fixtures"), list) else []
    logins: list[str] = []
    for fixture in fixtures:
        if not isinstance(fixture, dict):
            continue
        login = str(fixture.get("login") or "").strip()
        if login and login not in logins:
            logins.append(login)
    return logins


def _login_token_with_fallback(intent_url: str, db_name: str) -> tuple[str, str, str]:
    explicit_login = str(os.getenv("E2E_LOGIN") or "").strip()
    explicit_password = str(os.getenv("E2E_PASSWORD") or os.getenv("ADMIN_PASSWD") or "").strip()
    prod_like_password = str(os.getenv("E2E_PROD_LIKE_PASSWORD") or "prod_like").strip()
    default_demo_password = str(os.getenv("E2E_ROLE_MATRIX_DEFAULT_PASSWORD") or "demo").strip()
    env_candidates = str(os.getenv("E2E_ROLE_MATRIX_LOGINS") or "").strip()
    candidates: list[str] = []
    source = "prod_like_baseline"
    if env_candidates:
        candidates = [item.strip() for item in env_candidates.split(",") if item.strip()]
        source = "env:E2E_ROLE_MATRIX_LOGINS"
    else:
        candidates.extend(_load_prod_like_logins())
        if "admin" not in candidates:
            candidates.append("admin")
        # Legacy fallback for older local DBs; last-resort only.
        for login in ("demo_pm", "demo_finance", "demo_role_executive"):
            if login not in candidates:
                candidates.append(login)
    if explicit_login:
        source = "env:E2E_LOGIN"
        candidates = [explicit_login] + [x for x in candidates if x != explicit_login]
    failures: list[str] = []
    for candidate in candidates:
        if candidate == explicit_login and explicit_password:
            candidate_pwd = explicit_password
        elif candidate == "admin":
            candidate_pwd = explicit_password or "admin"
        elif candidate.startswith("sc_fx_"):
            candidate_pwd = prod_like_password
        else:
            candidate_pwd = default_demo_password
        try:
            token = _login_token(intent_url, db_name, candidate, candidate_pwd)
            return candidate, token, source
        except Exception:
            failures.append(candidate)
    raise RuntimeError(f"all login candidates failed: {','.join(failures)}")


def main() -> None:
    baseline = {
        "min_catalog_scene_count": 1,
        "min_runtime_scene_count": 20,
        "min_catalog_runtime_ratio": 0.01,
        "max_catalog_runtime_ratio": 1.0,
        "require_runtime_gte_catalog": True,
        "expected_catalog_scope": "scene_contract_snapshot",
        "max_errors": 0,
    }
    baseline_raw = _load_json(BASELINE_JSON)
    if baseline_raw:
        baseline.update(baseline_raw)

    catalog = _load_json(CATALOG_JSON)
    if not catalog:
        raise RuntimeError(f"missing or invalid scene catalog: {CATALOG_JSON.as_posix()}")
    source = catalog.get("source") if isinstance(catalog.get("source"), dict) else {}
    catalog_scope = str(source.get("scene_catalog_scope") or "").strip()
    catalog_scene_count = int(catalog.get("scene_count") or 0)

    base_url = get_base_url()
    intent_url = f"{base_url}/api/v1/intent"
    db_name = os.getenv("E2E_DB") or os.getenv("DB_NAME") or ""
    probe_login, token, probe_source = _login_token_with_fallback(intent_url, db_name)
    status, init_resp = http_post_json(
        intent_url,
        {"intent": "system.init", "params": {"contract_mode": "hud"}},
        headers={"Authorization": f"Bearer {token}"},
    )
    require_ok(status, init_resp, "system.init hud")
    runtime_scene_count = _extract_scene_count(init_resp)

    ratio = 0.0
    if runtime_scene_count > 0:
        ratio = round(catalog_scene_count / runtime_scene_count, 6)

    errors: list[str] = []
    if catalog_scope != str(baseline.get("expected_catalog_scope") or ""):
        errors.append(
            "catalog scope mismatch: "
            f"actual={catalog_scope!r} expected={baseline.get('expected_catalog_scope')!r}"
        )
    if catalog_scene_count < int(baseline.get("min_catalog_scene_count", 1)):
        errors.append(
            f"catalog scene count below baseline: {catalog_scene_count} < "
            f"{int(baseline.get('min_catalog_scene_count', 1))}"
        )
    if runtime_scene_count < int(baseline.get("min_runtime_scene_count", 1)):
        errors.append(
            f"runtime scene count below baseline: {runtime_scene_count} < "
            f"{int(baseline.get('min_runtime_scene_count', 1))}"
        )
    if ratio < float(baseline.get("min_catalog_runtime_ratio", 0.0)):
        errors.append(
            f"catalog/runtime ratio below baseline: {ratio} < "
            f"{float(baseline.get('min_catalog_runtime_ratio', 0.0))}"
        )
    if ratio > float(baseline.get("max_catalog_runtime_ratio", 1.0)):
        errors.append(
            f"catalog/runtime ratio above baseline: {ratio} > "
            f"{float(baseline.get('max_catalog_runtime_ratio', 1.0))}"
        )
    if bool(baseline.get("require_runtime_gte_catalog", True)) and runtime_scene_count < catalog_scene_count:
        errors.append(
            f"runtime scene count must be >= catalog scene count: {runtime_scene_count} < {catalog_scene_count}"
        )

    report = {
        "ok": len(errors) <= int(baseline.get("max_errors", 0)),
        "baseline": baseline,
        "summary": {
            "catalog_scope": catalog_scope,
            "catalog_scene_count": catalog_scene_count,
            "runtime_scene_count": runtime_scene_count,
            "catalog_runtime_ratio": ratio,
            "probe_login": probe_login,
            "probe_source": probe_source,
            "error_count": len(errors),
        },
        "errors": errors,
    }
    ARTIFACT_JSON.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Scene Catalog Runtime Alignment Guard",
        "",
        f"- status: {'PASS' if report['ok'] else 'FAIL'}",
        f"- catalog_scope: {catalog_scope}",
        f"- catalog_scene_count: {catalog_scene_count}",
        f"- runtime_scene_count: {runtime_scene_count}",
        f"- catalog_runtime_ratio: {ratio}",
        f"- probe_login: {probe_login}",
        f"- probe_source: {probe_source}",
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
        raise RuntimeError("scene catalog/runtime alignment not satisfied")
    print(
        "[scene_catalog_runtime_alignment_guard] PASS "
        f"catalog={catalog_scene_count} runtime={runtime_scene_count} ratio={ratio}"
    )


if __name__ == "__main__":
    main()
