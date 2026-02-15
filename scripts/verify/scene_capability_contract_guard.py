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


def main() -> None:
    base_url = get_base_url()
    db_name = os.getenv("E2E_DB") or os.getenv("DB_NAME") or ""
    login = os.getenv("E2E_LOGIN") or "admin"
    password = os.getenv("E2E_PASSWORD") or os.getenv("ADMIN_PASSWD") or "admin"
    intent_url = f"{base_url}/api/v1/intent"

    status, login_resp = http_post_json(
        intent_url,
        {"intent": "login", "params": {"db": db_name, "login": login, "password": password}},
        headers={"X-Anonymous-Intent": "1"},
    )
    require_ok(status, login_resp, "login")
    token = (login_resp.get("data") or {}).get("token")
    if not token:
        raise RuntimeError("login response missing token")
    auth = {"Authorization": f"Bearer {token}"}

    status, init_resp = http_post_json(
        intent_url,
        {"intent": "system.init", "params": {"contract_mode": "hud"}},
        headers=auth,
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
    if len(missing_refs) > int(baseline.get("max_missing_refs", 0)):
        errors.append(f"missing refs above baseline: {len(missing_refs)} > {baseline.get('max_missing_refs')}")
    if len(errors) > int(baseline.get("max_errors", 0)):
        pass

    report = {
        "ok": len(errors) <= int(baseline.get("max_errors", 0)),
        "baseline": baseline,
        "summary": {
            "scene_count": len(scenes),
            "capability_count": len(cap_keys),
            "missing_ref_count": len(missing_refs),
            "error_count": len(errors),
        },
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
        f"- missing_ref_count: {report['summary']['missing_ref_count']}",
        f"- error_count: {report['summary']['error_count']}",
    ]
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
