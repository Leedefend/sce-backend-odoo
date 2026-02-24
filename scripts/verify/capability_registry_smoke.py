#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
import re
from pathlib import Path

from intent_smoke_utils import require_ok
from python_http_smoke_utils import get_base_url, http_post_json

ROOT = Path(__file__).resolve().parents[2]
BASELINE_JSON = ROOT / "scripts" / "verify" / "baselines" / "role_capability_floor_prod_like.json"
ARTIFACT_JSON = ROOT / "artifacts" / "backend" / "capability_registry_smoke.json"
ARTIFACT_MD = ROOT / "artifacts" / "backend" / "capability_registry_smoke.md"

KEY_RE = re.compile(r"^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*$")


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _login(intent_url: str, db_name: str, login: str, password: str) -> str:
    status, resp = http_post_json(
        intent_url,
        {"intent": "login", "params": {"db": db_name, "login": login, "password": password}},
        headers={"X-Anonymous-Intent": "1"},
    )
    if status != 200 or not isinstance(resp, dict):
        return ""
    data = resp.get("data") if isinstance(resp.get("data"), dict) else {}
    return str(data.get("token") or "").strip()


def _system_init(intent_url: str, token: str, mode: str = "user") -> tuple[list[dict], list[dict]]:
    status, resp = http_post_json(
        intent_url,
        {"intent": "system.init", "params": {"contract_mode": mode}},
        headers={"Authorization": f"Bearer {token}"},
    )
    require_ok(status, resp, f"system.init:{mode}")
    data = resp.get("data") if isinstance(resp.get("data"), dict) else {}
    if isinstance(data.get("data"), dict):
        data = data.get("data") or data
    scenes = data.get("scenes") if isinstance(data.get("scenes"), list) else []
    caps = data.get("capabilities") if isinstance(data.get("capabilities"), list) else []
    return scenes, caps


def _is_openable_target(target: dict) -> bool:
    if not isinstance(target, dict):
        return False
    return bool(
        str(target.get("route") or "").strip()
        or target.get("action_id")
        or str(target.get("model") or "").strip()
    )


def main() -> int:
    baseline = _load_json(BASELINE_JSON)
    fixtures = baseline.get("fixtures") if isinstance(baseline.get("fixtures"), list) else []

    db_name = str(os.getenv("E2E_DB") or os.getenv("DB_NAME") or "").strip()
    base_url = get_base_url()
    intent_url = f"{base_url}/api/v1/intent"

    prod_like_pwd = str(os.getenv("E2E_PROD_LIKE_PASSWORD") or baseline.get("fixture_password") or "prod_like").strip()
    admin_login = str(os.getenv("E2E_LOGIN") or "admin").strip()
    admin_pwd = str(os.getenv("E2E_PASSWORD") or os.getenv("ADMIN_PASSWD") or "admin").strip()

    role_tokens: dict[str, str] = {}
    login_failures: list[str] = []
    for fixture in fixtures:
        if not isinstance(fixture, dict):
            continue
        role = str(fixture.get("role") or "").strip()
        login = str(fixture.get("login") or "").strip()
        if not role or not login:
            continue
        token = _login(intent_url, db_name, login, prod_like_pwd)
        if not token:
            login_failures.append(login)
            continue
        role_tokens[role] = token

    if admin_login not in [str(item.get("login") or "").strip() for item in fixtures]:
        admin_token = _login(intent_url, db_name, admin_login, admin_pwd)
    else:
        admin_token = ""
    if not admin_token:
        # fall back to executive fixture for full catalog probing
        admin_token = role_tokens.get("executive") or role_tokens.get("pm") or role_tokens.get("finance") or ""

    errors: list[str] = []
    warnings: list[str] = []

    if not admin_token:
        errors.append("missing admin/executive token for registry probing")
        caps = []
        scenes = []
    else:
        scenes, caps = _system_init(intent_url, admin_token, mode="hud")

    scene_keys = {
        str(scene.get("code") or scene.get("key") or "").strip(): scene
        for scene in scenes
        if isinstance(scene, dict) and str(scene.get("code") or scene.get("key") or "").strip()
    }

    key_set: set[str] = set()
    openability_failures: list[dict] = []
    for cap in caps:
        if not isinstance(cap, dict):
            errors.append("capability item must be object")
            continue
        key = str(cap.get("key") or "").strip()
        if not key:
            errors.append("capability key missing")
            continue
        if key in key_set:
            errors.append(f"duplicate key: {key}")
        key_set.add(key)

        if not KEY_RE.match(key):
            errors.append(f"key regex mismatch: {key}")

        group_key = str(cap.get("group_key") or "").strip()
        if not group_key:
            errors.append(f"group_key missing: {key}")

        payload = cap.get("default_payload") if isinstance(cap.get("default_payload"), dict) else {}
        scene_key = str(payload.get("scene_key") or "").strip()
        has_open_target = _is_openable_target(payload)
        if scene_key:
            scene = scene_keys.get(scene_key)
            if not scene:
                openability_failures.append({"capability_key": key, "scene_key": scene_key, "reason": "scene_missing"})
                continue
            scene_target = scene.get("target") if isinstance(scene.get("target"), dict) else {}
            if not _is_openable_target(scene_target):
                openability_failures.append({"capability_key": key, "scene_key": scene_key, "reason": "scene_target_not_openable"})
                continue
        elif not has_open_target:
            openability_failures.append({"capability_key": key, "scene_key": "", "reason": "payload_not_openable"})

    if len(key_set) < 30:
        errors.append(f"capability_count too low: {len(key_set)} < 30")

    if openability_failures:
        errors.append(f"openability failures: {len(openability_failures)}")

    role_cap_counts: dict[str, int] = {}
    for role, token in sorted(role_tokens.items()):
        try:
            _, role_caps = _system_init(intent_url, token, mode="user")
        except Exception as exc:
            errors.append(f"role {role} system.init failed: {exc}")
            continue
        role_cap_counts[role] = len(role_caps)

    focus_roles = ["pm", "finance", "executive"]
    focus_counts = [role_cap_counts.get(role, 0) for role in focus_roles]
    if any(count < 10 for count in focus_counts):
        errors.append(f"runtime_capability_matrix.min_role_capability_count < 10: {dict(zip(focus_roles, focus_counts))}")

    max_count = max(role_cap_counts.values()) if role_cap_counts else 0
    if max_count < 20:
        errors.append(f"runtime_capability_matrix.max_role_capability_count < 20: {max_count}")

    report = {
        "ok": not errors,
        "summary": {
            "capability_count": len(key_set),
            "scene_count": len(scene_keys),
            "openability_failure_count": len(openability_failures),
            "role_capability_counts": role_cap_counts,
            "min_role_capability_count": min(focus_counts) if focus_counts else 0,
            "max_role_capability_count": max_count,
            "login_failure_count": len(login_failures),
            "warning_count": len(warnings),
            "error_count": len(errors),
        },
        "login_failures": sorted(login_failures),
        "openability_failures": openability_failures,
        "warnings": warnings,
        "errors": errors,
    }

    ARTIFACT_JSON.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    md_lines = [
        "# Capability Registry Smoke",
        "",
        f"- status: {'PASS' if report['ok'] else 'FAIL'}",
        f"- capability_count: {report['summary']['capability_count']}",
        f"- scene_count: {report['summary']['scene_count']}",
        f"- openability_failure_count: {report['summary']['openability_failure_count']}",
        f"- min_role_capability_count(pm/finance/executive): {report['summary']['min_role_capability_count']}",
        f"- max_role_capability_count: {report['summary']['max_role_capability_count']}",
        f"- login_failure_count: {report['summary']['login_failure_count']}",
        f"- error_count: {report['summary']['error_count']}",
    ]
    if errors:
        md_lines.extend(["", "## Errors", ""])
        md_lines.extend([f"- {item}" for item in errors])
    if openability_failures:
        md_lines.extend(["", "## Openability Failures", ""])
        md_lines.extend([f"- {row['capability_key']}: {row['reason']} ({row.get('scene_key') or '-'})" for row in openability_failures[:20]])
    ARTIFACT_MD.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    if errors:
        print("[capability_registry_smoke] FAIL")
        for item in errors:
            print(item)
        return 1

    print("[capability_registry_smoke] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
