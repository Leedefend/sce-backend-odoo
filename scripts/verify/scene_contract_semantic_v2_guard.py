#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
from pathlib import Path

from intent_smoke_utils import require_ok
from python_http_smoke_utils import get_base_url, http_post_json


ROOT = Path(__file__).resolve().parents[2]
BASELINE_JSON = ROOT / "scripts" / "verify" / "baselines" / "scene_contract_semantic_v2_guard.json"
PROD_LIKE_BASELINE_JSON = ROOT / "scripts" / "verify" / "baselines" / "role_capability_floor_prod_like.json"


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


def _system_init_hud(intent_url: str, token: str) -> list[dict]:
    status, resp = http_post_json(
        intent_url,
        {"intent": "system.init", "params": {"contract_mode": "hud"}},
        headers={"Authorization": f"Bearer {token}"},
    )
    require_ok(status, resp, "system.init hud")
    data = resp.get("data") if isinstance(resp.get("data"), dict) else {}
    if isinstance(data.get("data"), dict):
        data = data.get("data") or data
    return data.get("scenes") if isinstance(data.get("scenes"), list) else []


def main() -> int:
    baseline = {
        "min_scene_count": 1,
        "max_errors": 0,
        "min_v2_enforced_scenes": 0,
        "enforce_scene_keys": [],
    }
    baseline.update(_load_json(BASELINE_JSON))

    base_url = get_base_url()
    intent_url = f"{base_url}/api/v1/intent"
    db_name = str(os.getenv("E2E_DB") or os.getenv("DB_NAME") or "").strip()
    admin_login = str(os.getenv("E2E_LOGIN") or "admin").strip()
    admin_password = str(os.getenv("E2E_PASSWORD") or os.getenv("ADMIN_PASSWD") or "admin").strip()
    prod_like_password = str(os.getenv("E2E_PROD_LIKE_PASSWORD") or "prod_like").strip()
    demo_password = str(os.getenv("E2E_ROLE_MATRIX_DEFAULT_PASSWORD") or "demo").strip()
    raw_logins = str(os.getenv("E2E_ROLE_MATRIX_LOGINS") or "").strip()

    probe_source = "prod_like_baseline"
    if raw_logins:
        login_candidates = [x.strip() for x in raw_logins.split(",") if x.strip()]
        probe_source = "env:E2E_ROLE_MATRIX_LOGINS"
    else:
        login_candidates = _load_prod_like_logins()
        for fallback in ("admin", "demo_pm", "demo_finance", "demo_role_executive"):
            if fallback not in login_candidates:
                login_candidates.append(fallback)
    if admin_login and admin_login not in login_candidates:
        login_candidates.append(admin_login)
    if os.getenv("E2E_LOGIN"):
        probe_source = "env:E2E_LOGIN"

    role_samples: dict[str, dict] = {}
    login_failures: list[str] = []
    for login in login_candidates:
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
        try:
            scenes = _system_init_hud(intent_url, token)
            role_samples[login] = {"scene_count": len(scenes), "scenes": scenes}
        except Exception:
            login_failures.append(login)

    if not role_samples:
        raise RuntimeError("all role-matrix logins failed")

    probe_login = sorted(
        role_samples.keys(),
        key=lambda key: (int(role_samples[key]["scene_count"]), key),
        reverse=True,
    )[0]
    scenes = role_samples[probe_login]["scenes"]

    errors: list[str] = []
    warnings: list[str] = []
    v2_keys_scene_meta = ("purpose", "core_action", "priority_actions", "role_relevance_score")
    v2_keys_list_profile = ("primary_field", "status_field", "urgency_score", "highlight_rule")
    enforce_scene_keys = {
        str(item).strip()
        for item in (baseline.get("enforce_scene_keys") if isinstance(baseline.get("enforce_scene_keys"), list) else [])
        if str(item).strip()
    }
    enforced_scene_count = 0
    if len(scenes) < int(baseline.get("min_scene_count") or 1):
        errors.append(f"scene_count below baseline: {len(scenes)} < {int(baseline.get('min_scene_count') or 1)}")

    for idx, scene in enumerate(scenes):
        if not isinstance(scene, dict):
            errors.append(f"scene[{idx}] invalid object")
            continue
        scene_key = str(scene.get("code") or scene.get("key") or "").strip() or f"scene[{idx}]"
        scene_meta = scene.get("scene_meta") if isinstance(scene.get("scene_meta"), dict) else {}
        list_profile = scene.get("list_profile") if isinstance(scene.get("list_profile"), dict) else {}
        has_v2_scene_meta = any(key in scene_meta for key in v2_keys_scene_meta)
        has_v2_list_profile = any(key in list_profile for key in v2_keys_list_profile)
        enforce = scene_key in enforce_scene_keys or has_v2_scene_meta or has_v2_list_profile
        if enforce:
            enforced_scene_count += 1
        miss_bucket = errors if enforce else warnings
        for key in v2_keys_scene_meta:
            if key not in scene_meta:
                miss_bucket.append(f"{scene_key}.scene_meta missing key: {key}")
        if "priority_actions" in scene_meta and not isinstance(scene_meta.get("priority_actions"), list):
            errors.append(f"{scene_key}.scene_meta.priority_actions must be list")
        if "role_relevance_score" in scene_meta:
            score = scene_meta.get("role_relevance_score")
            if not isinstance(score, int):
                errors.append(f"{scene_key}.scene_meta.role_relevance_score must be int")
            elif score < 0 or score > 100:
                errors.append(f"{scene_key}.scene_meta.role_relevance_score out of range: {score}")
        for key in v2_keys_list_profile:
            if key not in list_profile:
                miss_bucket.append(f"{scene_key}.list_profile missing key: {key}")
        if "urgency_score" in list_profile and not isinstance(list_profile.get("urgency_score"), int):
            errors.append(f"{scene_key}.list_profile.urgency_score must be int")
        if "highlight_rule" in list_profile and not isinstance(list_profile.get("highlight_rule"), dict):
            errors.append(f"{scene_key}.list_profile.highlight_rule must be object")
        columns = list_profile.get("columns") if isinstance(list_profile.get("columns"), list) else []
        if columns and not list_profile.get("primary_field"):
            warnings.append(f"{scene_key} list_profile.columns present but primary_field empty")
    min_v2_enforced_scenes = int(baseline.get("min_v2_enforced_scenes") or 0)
    if enforced_scene_count < min_v2_enforced_scenes:
        errors.append(
            f"v2_enforced_scene_count below baseline: {enforced_scene_count} < {min_v2_enforced_scenes}"
        )

    report = {
        "ok": len(errors) <= int(baseline.get("max_errors") or 0),
        "baseline": baseline,
        "summary": {
            "probe_login": probe_login,
            "probe_source": probe_source,
            "scene_count": len(scenes),
            "warning_count": len(warnings),
            "error_count": len(errors),
            "role_sample_count": len(role_samples),
            "v2_enforced_scene_count": enforced_scene_count,
            "v2_coverage_ratio": round((enforced_scene_count / len(scenes)) if scenes else 0.0, 6),
        },
        "role_samples": {key: {"scene_count": int(val["scene_count"])} for key, val in sorted(role_samples.items())},
        "login_failures": sorted(login_failures),
        "warnings": sorted(warnings),
        "errors": sorted(errors),
    }

    artifacts_root = _resolve_artifacts_dir()
    artifact_json = artifacts_root / "backend" / "scene_contract_semantic_v2_guard.json"
    artifact_md = artifacts_root / "backend" / "scene_contract_semantic_v2_guard.md"
    artifact_json.parent.mkdir(parents=True, exist_ok=True)
    artifact_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Scene Contract Semantic V2 Guard",
        "",
        f"- status: {'PASS' if report['ok'] else 'FAIL'}",
        f"- probe_login: {report['summary']['probe_login']}",
        f"- probe_source: {report['summary']['probe_source']}",
        f"- role_sample_count: {report['summary']['role_sample_count']}",
        f"- scene_count: {report['summary']['scene_count']}",
        f"- warning_count: {report['summary']['warning_count']}",
        f"- error_count: {report['summary']['error_count']}",
    ]
    if report["errors"]:
        lines.extend(["", "## Errors", ""])
        for item in report["errors"][:200]:
            lines.append(f"- {item}")
    artifact_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(artifact_json))
    print(str(artifact_md))
    if not report["ok"]:
        print("[scene_contract_semantic_v2_guard] FAIL")
        return 1
    print("[scene_contract_semantic_v2_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
