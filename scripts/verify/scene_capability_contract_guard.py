#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
from pathlib import Path

from intent_smoke_utils import require_ok
from python_http_smoke_utils import get_base_url, http_post_json

ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_JSON = ROOT / "artifacts" / "scene_capability_contract_guard.json"
ARTIFACT_MD = ROOT / "artifacts" / "scene_capability_contract_guard.md"
BASELINE_JSON = ROOT / "scripts/verify/baselines/scene_capability_contract_guard.json"
PROD_LIKE_BASELINE_JSON = ROOT / "scripts/verify/baselines/role_capability_floor_prod_like.json"


def _to_str_list(value):
    if isinstance(value, list):
        out = []
        for item in value:
            val = str(item or "").strip()
            if val:
                out.append(val)
        return out
    return []


def _collect_required_caps(scene: dict):
    required = set()
    required.update(_to_str_list(scene.get("required_capabilities")))
    access = scene.get("access")
    if isinstance(access, dict):
        required.update(_to_str_list(access.get("required_capabilities")))
    for tile in scene.get("tiles") if isinstance(scene.get("tiles"), list) else []:
        if not isinstance(tile, dict):
            continue
        required.update(_to_str_list(tile.get("required_capabilities")))
    return required


def _login(intent_url: str, *, db_name: str, login: str, password: str):
    status, login_resp = http_post_json(
        intent_url,
        {"intent": "login", "params": {"db": db_name, "login": login, "password": password}},
        headers={"X-Anonymous-Intent": "1"},
    )
    if status != 200:
        return None
    data = login_resp.get("data") if isinstance(login_resp, dict) else {}
    token = data.get("token") if isinstance(data, dict) else None
    if not token:
        return None
    return str(token)


def _load_prod_like_logins() -> list[str]:
    if not PROD_LIKE_BASELINE_JSON.is_file():
        return []
    try:
        payload = json.loads(PROD_LIKE_BASELINE_JSON.read_text(encoding="utf-8"))
    except Exception:
        return []
    fixtures = payload.get("fixtures") if isinstance(payload, dict) and isinstance(payload.get("fixtures"), list) else []
    logins: list[str] = []
    for fixture in fixtures:
        if not isinstance(fixture, dict):
            continue
        login = str(fixture.get("login") or "").strip()
        if login and login not in logins:
            logins.append(login)
    return logins


def _system_init_hud(intent_url: str, token: str):
    status, init_resp = http_post_json(
        intent_url,
        {"intent": "system.init", "params": {"contract_mode": "hud"}},
        headers={"Authorization": f"Bearer {token}"},
    )
    require_ok(status, init_resp, "system.init hud")
    data = init_resp.get("data") if isinstance(init_resp.get("data"), dict) else {}
    if isinstance(data.get("data"), dict):  # compat with nested envelope
        data = data.get("data") or data
    scenes = data.get("scenes") if isinstance(data.get("scenes"), list) else []
    capabilities = data.get("capabilities") if isinstance(data.get("capabilities"), list) else []
    cap_keys = {
        str(item.get("key") or "").strip()
        for item in capabilities
        if isinstance(item, dict) and str(item.get("key") or "").strip()
    }
    return {
        "scenes": scenes,
        "cap_keys": cap_keys,
    }


def main() -> None:
    base_url = get_base_url()
    db_name = os.getenv("E2E_DB") or os.getenv("DB_NAME") or ""
    login = os.getenv("E2E_LOGIN") or "admin"
    password = os.getenv("E2E_PASSWORD") or os.getenv("ADMIN_PASSWD") or "admin"
    intent_url = f"{base_url}/api/v1/intent"

    raw_logins = str(os.getenv("E2E_ROLE_MATRIX_LOGINS") or "").strip()
    probe_source = "prod_like_baseline"
    if raw_logins:
        login_candidates = [item.strip() for item in raw_logins.split(",") if item.strip()]
        probe_source = "env:E2E_ROLE_MATRIX_LOGINS"
    else:
        login_candidates = _load_prod_like_logins()
        if "admin" not in login_candidates:
            login_candidates.append("admin")
        for legacy_login in ("demo_pm", "demo_finance", "demo_role_executive"):
            if legacy_login not in login_candidates:
                login_candidates.append(legacy_login)
    if login and login not in login_candidates:
        login_candidates.append(login)
    if login:
        probe_source = "env:E2E_LOGIN" if os.getenv("E2E_LOGIN") else probe_source

    demo_pwd = os.getenv("E2E_ROLE_MATRIX_DEFAULT_PASSWORD") or "demo"
    prod_like_pwd = os.getenv("E2E_PROD_LIKE_PASSWORD") or "prod_like"
    default_pwd_map = {
        "admin": password,
    }
    role_samples = {}
    login_failures = []
    for candidate in login_candidates:
        if candidate in default_pwd_map:
            candidate_pwd = default_pwd_map.get(candidate) or demo_pwd
        elif candidate.startswith("sc_fx_"):
            candidate_pwd = prod_like_pwd
        else:
            candidate_pwd = demo_pwd
        token = _login(intent_url, db_name=db_name, login=candidate, password=candidate_pwd)
        if not token:
            login_failures.append(candidate)
            continue
        try:
            payload = _system_init_hud(intent_url, token)
            role_samples[candidate] = {
                "scene_count": len(payload["scenes"]),
                "capability_count": len(payload["cap_keys"]),
                "scenes": payload["scenes"],
                "cap_keys": payload["cap_keys"],
            }
        except Exception:
            login_failures.append(candidate)

    if not role_samples:
        raise RuntimeError(
            f"all role-matrix logins failed: {','.join(login_candidates)} "
            "(override by E2E_ROLE_MATRIX_LOGINS or E2E_LOGIN/E2E_PASSWORD)"
        )

    best_login = sorted(
        role_samples.keys(),
        key=lambda key: (
            int(role_samples[key]["capability_count"]),
            int(role_samples[key]["scene_count"]),
            key,
        ),
        reverse=True,
    )[0]
    scenes = role_samples[best_login]["scenes"]
    cap_keys = role_samples[best_login]["cap_keys"]

    errors = []
    missing_refs = []
    for scene in scenes:
        if not isinstance(scene, dict):
            errors.append("scene item must be object")
            continue
        scene_key = str(scene.get("code") or scene.get("key") or "").strip()
        if not scene_key:
            errors.append("scene missing code/key")
            continue
        refs = _collect_required_caps(scene)
        missing = sorted([key for key in refs if key not in cap_keys])
        if missing:
            missing_refs.append({"scene_key": scene_key, "missing_capabilities": missing})
            errors.append(f"{scene_key}: missing required capabilities {','.join(missing)}")

    baseline = {
        "min_scenes": 1,
        "min_capabilities": 1,
        "role_min_capabilities": {},
        "max_errors": 0,
        "max_missing_refs": 0,
    }
    if BASELINE_JSON.is_file():
        try:
            data = json.loads(BASELINE_JSON.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                baseline.update(data)
        except Exception:
            errors.append(f"invalid baseline file: {BASELINE_JSON.as_posix()}")

    if len(scenes) < int(baseline.get("min_scenes", 1)):
        errors.append(f"scenes below baseline: {len(scenes)} < {baseline.get('min_scenes')}")
    if len(cap_keys) < int(baseline.get("min_capabilities", 1)):
        errors.append(f"capabilities below baseline: {len(cap_keys)} < {baseline.get('min_capabilities')}")
    role_min_caps = baseline.get("role_min_capabilities")
    if isinstance(role_min_caps, dict):
        for role_login, expected in role_min_caps.items():
            key = str(role_login or "").strip()
            if not key:
                continue
            if key not in role_samples:
                errors.append(f"required role login missing: {key}")
                continue
            actual = int(role_samples[key]["capability_count"])
            if actual < int(expected):
                errors.append(f"{key}: capabilities below baseline: {actual} < {int(expected)}")
    if len(missing_refs) > int(baseline.get("max_missing_refs", 0)):
        errors.append(f"missing refs above baseline: {len(missing_refs)} > {baseline.get('max_missing_refs')}")
    if len(errors) > int(baseline.get("max_errors", 0)):
        pass

    report = {
        "ok": len(errors) <= int(baseline.get("max_errors", 0)),
        "baseline": baseline,
        "summary": {
            "probe_login": best_login,
            "probe_source": probe_source,
            "scene_count": len(scenes),
            "capability_count": len(cap_keys),
            "missing_ref_count": len(missing_refs),
            "error_count": len(errors),
            "role_sample_count": len(role_samples),
        },
        "role_samples": {
            key: {
                "scene_count": int(val["scene_count"]),
                "capability_count": int(val["capability_count"]),
            }
            for key, val in sorted(role_samples.items())
        },
        "login_failures": sorted(login_failures),
        "missing_refs": missing_refs,
        "errors": errors,
    }

    ARTIFACT_JSON.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Scene Capability Contract Guard",
        "",
        f"- status: {'PASS' if report['ok'] else 'FAIL'}",
        f"- scene_count: {report['summary']['scene_count']}",
        f"- capability_count: {report['summary']['capability_count']}",
        f"- probe_login: {report['summary']['probe_login']}",
        f"- role_sample_count: {report['summary']['role_sample_count']}",
        f"- missing_ref_count: {report['summary']['missing_ref_count']}",
        f"- error_count: {report['summary']['error_count']}",
    ]
    if report["role_samples"]:
        lines.extend(["", "## Role Samples", ""])
        for key, val in report["role_samples"].items():
            lines.append(f"- {key}: scenes={val['scene_count']} capabilities={val['capability_count']}")
    if report["login_failures"]:
        lines.extend(["", "## Login Failures", ""])
        for key in report["login_failures"]:
            lines.append(f"- {key}")
    if missing_refs:
        lines.extend(["", "## Missing Refs", ""])
        for item in missing_refs[:50]:
            lines.append(f"- {item['scene_key']}: {','.join(item['missing_capabilities'])}")
    if errors:
        lines.extend(["", "## Errors", ""])
        for item in errors[:50]:
            lines.append(f"- {item}")
    ARTIFACT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(ARTIFACT_JSON))
    print(str(ARTIFACT_MD))
    if not report["ok"]:
        raise RuntimeError("scene-capability inconsistency: " + " | ".join(errors[:20]))
    print(f"[scene_capability_contract_guard] PASS scenes={len(scenes)} capabilities={len(cap_keys)}")


if __name__ == "__main__":
    main()
