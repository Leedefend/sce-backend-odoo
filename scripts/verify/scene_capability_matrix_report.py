#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
from pathlib import Path

from intent_smoke_utils import require_ok
from python_http_smoke_utils import get_base_url, http_post_json


ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_JSON = ROOT / "artifacts" / "backend" / "scene_capability_matrix_report.json"
ARTIFACT_MD = ROOT / "artifacts" / "backend" / "scene_capability_matrix_report.md"
BASELINE_JSON = ROOT / "scripts" / "verify" / "baselines" / "scene_capability_matrix_report.json"
PROD_LIKE_BASELINE_JSON = ROOT / "scripts" / "verify" / "baselines" / "role_capability_floor_prod_like.json"


def _to_str_list(value) -> list[str]:
    if not isinstance(value, list):
        return []
    out: list[str] = []
    for item in value:
        text = str(item or "").strip()
        if text:
            out.append(text)
    return out


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
    payload = _load_json(PROD_LIKE_BASELINE_JSON)
    fixtures = payload.get("fixtures") if isinstance(payload.get("fixtures"), list) else []
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
    data = resp.get("data") if isinstance(resp, dict) and isinstance(resp.get("data"), dict) else {}
    return str(data.get("token") or "").strip()


def _system_init_hud(intent_url: str, token: str) -> tuple[list[dict], list[dict]]:
    status, resp = http_post_json(
        intent_url,
        {"intent": "system.init", "params": {"contract_mode": "hud"}},
        headers={"Authorization": f"Bearer {token}"},
    )
    require_ok(status, resp, "system.init hud")
    data = resp.get("data") if isinstance(resp.get("data"), dict) else {}
    if isinstance(data.get("data"), dict):
        data = data.get("data") or data
    scenes = data.get("scenes") if isinstance(data.get("scenes"), list) else []
    capabilities = data.get("capabilities") if isinstance(data.get("capabilities"), list) else []
    return scenes, capabilities


def _collect_scene_caps(scene: dict) -> tuple[set[str], set[str]]:
    declared: set[str] = set()
    required: set[str] = set()
    declared.update(_to_str_list(scene.get("capabilities")))
    required.update(_to_str_list(scene.get("required_capabilities")))
    access = scene.get("access")
    if isinstance(access, dict):
        declared.update(_to_str_list(access.get("capabilities")))
        required.update(_to_str_list(access.get("required_capabilities")))
    tiles = scene.get("tiles") if isinstance(scene.get("tiles"), list) else []
    for tile in tiles:
        if not isinstance(tile, dict):
            continue
        declared.update(_to_str_list(tile.get("capabilities")))
        required.update(_to_str_list(tile.get("required_capabilities")))
    return declared, required


def main() -> int:
    baseline = {
        "min_scene_count": 1,
        "min_capability_count": 1,
        "max_missing_capability_refs": 0,
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
    raw_logins = str(os.getenv("E2E_ROLE_MATRIX_LOGINS") or "").strip()

    probe_source = "prod_like_baseline"
    if raw_logins:
        login_candidates = [item.strip() for item in raw_logins.split(",") if item.strip()]
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
            scenes, capabilities = _system_init_hud(intent_url, token)
            role_samples[login] = {
                "scene_count": len(scenes),
                "capability_count": len(capabilities),
                "scenes": scenes,
                "capabilities": capabilities,
            }
        except Exception:
            login_failures.append(login)

    if not role_samples:
        raise RuntimeError("all role-matrix logins failed")

    probe_login = sorted(
        role_samples.keys(),
        key=lambda key: (
            int(role_samples[key]["capability_count"]),
            int(role_samples[key]["scene_count"]),
            key,
        ),
        reverse=True,
    )[0]

    scenes = role_samples[probe_login]["scenes"]
    capabilities = role_samples[probe_login]["capabilities"]
    capability_keys = sorted(
        {
            str(item.get("key") or "").strip()
            for item in capabilities
            if isinstance(item, dict) and str(item.get("key") or "").strip()
        }
    )
    capability_key_set = set(capability_keys)

    matrix: list[dict] = []
    used_capabilities: set[str] = set()
    scene_without_binding: list[str] = []
    missing_refs: list[dict] = []
    errors: list[str] = []
    warnings: list[str] = []

    for scene in scenes:
        if not isinstance(scene, dict):
            continue
        scene_key = str(scene.get("code") or scene.get("key") or "").strip()
        if not scene_key:
            errors.append("scene missing code/key")
            continue
        declared, required = _collect_scene_caps(scene)
        all_refs = declared | required
        used_capabilities.update(all_refs)
        if not all_refs:
            scene_without_binding.append(scene_key)
        missing = sorted([key for key in all_refs if key not in capability_key_set])
        if missing:
            missing_refs.append({"scene_key": scene_key, "missing_capabilities": missing})
            errors.append(f"{scene_key}: missing capability refs: {','.join(missing)}")
        matrix.append(
            {
                "scene_key": scene_key,
                "declared_capabilities": sorted(declared),
                "required_capabilities": sorted(required),
                "all_capabilities": sorted(all_refs),
                "missing_capabilities": missing,
            }
        )

    unused_capabilities = sorted([key for key in capability_keys if key not in used_capabilities])
    if scene_without_binding:
        warnings.append(f"scene_without_binding_count={len(scene_without_binding)}")
    if unused_capabilities:
        warnings.append(f"unused_capability_count={len(unused_capabilities)}")

    if len(scenes) < int(baseline.get("min_scene_count") or 1):
        errors.append(f"scene_count below baseline: {len(scenes)} < {int(baseline.get('min_scene_count') or 1)}")
    if len(capability_keys) < int(baseline.get("min_capability_count") or 1):
        errors.append(
            f"capability_count below baseline: {len(capability_keys)} < {int(baseline.get('min_capability_count') or 1)}"
        )
    if len(missing_refs) > int(baseline.get("max_missing_capability_refs") or 0):
        errors.append(
            f"missing_capability_refs above baseline: {len(missing_refs)} > {int(baseline.get('max_missing_capability_refs') or 0)}"
        )

    report = {
        "ok": len(errors) <= int(baseline.get("max_errors") or 0),
        "baseline": baseline,
        "summary": {
            "probe_login": probe_login,
            "probe_source": probe_source,
            "scene_count": len(scenes),
            "capability_count": len(capability_keys),
            "scene_without_binding_count": len(scene_without_binding),
            "unused_capability_count": len(unused_capabilities),
            "missing_capability_ref_count": len(missing_refs),
            "warning_count": len(warnings),
            "error_count": len(errors),
            "role_sample_count": len(role_samples),
        },
        "role_samples": {
            key: {
                "scene_count": int(value["scene_count"]),
                "capability_count": int(value["capability_count"]),
            }
            for key, value in sorted(role_samples.items())
        },
        "capability_keys": capability_keys,
        "scene_keys": sorted(
            {
                str(item.get("code") or item.get("key") or "").strip()
                for item in scenes
                if isinstance(item, dict) and str(item.get("code") or item.get("key") or "").strip()
            }
        ),
        "scene_without_binding": sorted(scene_without_binding),
        "unused_capabilities": unused_capabilities,
        "missing_capability_refs": sorted(missing_refs, key=lambda item: str(item.get("scene_key") or "")),
        "matrix": sorted(matrix, key=lambda item: str(item.get("scene_key") or "")),
        "login_failures": sorted(login_failures),
        "warnings": sorted(warnings),
        "errors": sorted(errors),
    }

    artifacts_root = _resolve_artifacts_dir()
    artifact_json = artifacts_root / "backend" / ARTIFACT_JSON.name
    artifact_md = artifacts_root / "backend" / ARTIFACT_MD.name
    artifact_json.parent.mkdir(parents=True, exist_ok=True)
    artifact_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Scene Capability Matrix Report",
        "",
        f"- status: {'PASS' if report['ok'] else 'FAIL'}",
        f"- probe_login: {report['summary']['probe_login']}",
        f"- probe_source: {report['summary']['probe_source']}",
        f"- role_sample_count: {report['summary']['role_sample_count']}",
        f"- scene_count: {report['summary']['scene_count']}",
        f"- capability_count: {report['summary']['capability_count']}",
        f"- scene_without_binding_count: {report['summary']['scene_without_binding_count']}",
        f"- unused_capability_count: {report['summary']['unused_capability_count']}",
        f"- missing_capability_ref_count: {report['summary']['missing_capability_ref_count']}",
        f"- warning_count: {report['summary']['warning_count']}",
        f"- error_count: {report['summary']['error_count']}",
        "",
        "## Role Samples",
        "",
    ]
    for key, value in sorted(report["role_samples"].items()):
        lines.append(f"- {key}: scenes={value['scene_count']} capabilities={value['capability_count']}")
    if report["scene_without_binding"]:
        lines.extend(["", "## Scene Without Binding", ""])
        for key in report["scene_without_binding"][:200]:
            lines.append(f"- {key}")
    if report["unused_capabilities"]:
        lines.extend(["", "## Unused Capabilities", ""])
        for key in report["unused_capabilities"][:200]:
            lines.append(f"- {key}")
    if report["missing_capability_refs"]:
        lines.extend(["", "## Missing Capability Refs", ""])
        for item in report["missing_capability_refs"][:200]:
            lines.append(f"- {item['scene_key']}: {', '.join(item['missing_capabilities'])}")
    artifact_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(artifact_json))
    print(str(artifact_md))
    if not report["ok"]:
        print("[scene_capability_matrix_report] FAIL")
        return 1
    print("[scene_capability_matrix_report] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
