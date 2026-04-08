#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BASELINE_PATH = ROOT / "scripts" / "verify" / "baselines" / "scene_base_contract_asset_coverage_guard.json"
BUILDER_PATH = ROOT / "addons" / "smart_core" / "core" / "scene_ready_contract_builder.py"
SYSTEM_INIT_PATH = ROOT / "addons" / "smart_core" / "handlers" / "system_init.py"
REPOSITORY_PATH = ROOT / "addons" / "smart_core" / "core" / "ui_base_contract_asset_repository.py"
MODEL_PATH = ROOT / "addons" / "smart_core" / "models" / "ui_base_contract_asset.py"
PRODUCER_PATH = ROOT / "addons" / "smart_core" / "core" / "ui_base_contract_asset_producer.py"
QUEUE_PATH = ROOT / "addons" / "smart_core" / "core" / "ui_base_contract_asset_event_queue.py"
TRIGGER_PATH = ROOT / "addons" / "smart_core" / "models" / "ui_base_contract_asset_event_trigger.py"
CRON_XML_PATH = ROOT / "addons" / "smart_core" / "data" / "ui_base_contract_asset_cron.xml"
MANIFEST_PATH = ROOT / "addons" / "smart_core" / "__manifest__.py"


def _assert(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _safe_int(value: object, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _safe_float(value: object, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _merge_dict(base: dict, ext: dict) -> dict:
    out = dict(base)
    for key, value in ext.items():
        out[key] = value
    return out


def _resolve_state_path(baseline: dict) -> Path:
    raw = str(baseline.get("state_file") or "").strip()
    if not raw:
        return ROOT / "artifacts" / "backend" / "scene_base_contract_asset_coverage_state.json"
    return ROOT / raw


def _resolve_runtime_env(payload: dict) -> str:
    governance = payload.get("scene_governance_v1") if isinstance(payload.get("scene_governance_v1"), dict) else {}
    delivery_policy = governance.get("delivery_policy") if isinstance(governance.get("delivery_policy"), dict) else {}
    runtime_env = str(delivery_policy.get("runtime_env") or "").strip()
    if runtime_env:
        return runtime_env
    return str(os.getenv("SC_RUNTIME_ENV") or os.getenv("ENV") or "dev").strip() or "dev"


def _validate_wiring(errors: list[str]) -> None:
    text = SYSTEM_INIT_PATH.read_text(encoding="utf-8")
    _assert(
        "bind_scene_assets" in text,
        "system_init missing bind_scene_assets wiring",
        errors,
    )
    for key in (
        "ui_base_contract_asset_scene_count",
        "ui_base_contract_bound_scene_count",
        "ui_base_contract_missing_scene_count",
    ):
        _assert(key in text, f"system_init missing nav_meta.{key}", errors)


def _validate_builder_coverage(errors: list[str]) -> None:
    text = BUILDER_PATH.read_text(encoding="utf-8")
    _assert(
        "base_contract_bound_scene_count" in text,
        "scene_ready builder missing base_contract_bound_scene_count metric",
        errors,
    )
    _assert(
        "compile_issue_scene_count" in text,
        "scene_ready builder missing compile_issue_scene_count metric",
        errors,
    )
    _assert(
        "scene_compile(" in text,
        "scene_ready builder missing scene_compile invocation",
        errors,
    )


def _validate_asset_model_semantics(errors: list[str]) -> None:
    text = MODEL_PATH.read_text(encoding="utf-8")
    for field_name in (
        "contract_kind",
        "source_type",
        "scope_hash",
        "generated_at",
        "code_version",
    ):
        _assert(field_name in text, f"asset model missing field: {field_name}", errors)
    _assert(
        "_check_single_active_per_scope" in text,
        "asset model missing single-active lifecycle constraint",
        errors,
    )
    _assert(
        "unique(contract_kind, scene_key, role_code, company_id, asset_version)" in text,
        "asset model missing scope+version unique constraint",
        errors,
    )


def _validate_production_wiring(errors: list[str]) -> None:
    model_text = MODEL_PATH.read_text(encoding="utf-8")
    producer_text = PRODUCER_PATH.read_text(encoding="utf-8")
    queue_text = QUEUE_PATH.read_text(encoding="utf-8")
    trigger_text = TRIGGER_PATH.read_text(encoding="utf-8")
    cron_xml = CRON_XML_PATH.read_text(encoding="utf-8")
    manifest_text = MANIFEST_PATH.read_text(encoding="utf-8")
    _assert(
        "refresh_assets_for_scene_keys" in model_text and "cron_refresh_ui_base_contract_assets" in model_text,
        "asset model missing production entry methods",
        errors,
    )
    _assert(
        "refresh_ui_base_contract_assets" in producer_text,
        "asset producer missing refresh_ui_base_contract_assets",
        errors,
    )
    _assert(
        "enqueue_scene_keys" in queue_text and "pop_scene_keys" in queue_text,
        "asset queue missing enqueue/pop support",
        errors,
    )
    _assert(
        "event:ir.actions.act_window" in trigger_text and "event:ir.ui.view" in trigger_text and "event:res.groups" in trigger_text,
        "event trigger wiring missing action/view/group hooks",
        errors,
    )
    _assert(
        "pop_scene_keys" in model_text and "source_type = \"event_queue\"" in model_text,
        "asset cron missing queue-consume refresh path",
        errors,
    )
    _assert(
        "model.cron_refresh_ui_base_contract_assets" in cron_xml,
        "cron xml missing ui base contract asset refresh action",
        errors,
    )
    _assert(
        "data/ui_base_contract_asset_cron.xml" in manifest_text,
        "manifest missing ui_base_contract_asset_cron.xml registration",
        errors,
    )


def _fetch_runtime_data() -> dict:
    from intent_smoke_utils import require_ok
    from python_http_smoke_utils import get_base_url, http_post_json

    base_url = get_base_url()
    intent_url = f"{base_url}/api/v1/intent"
    db_name = os.getenv("E2E_DB") or os.getenv("DB_NAME") or ""
    login = os.getenv("E2E_LOGIN") or "admin"
    password = os.getenv("E2E_PASSWORD") or os.getenv("ADMIN_PASSWD") or "admin"

    status, login_resp = http_post_json(
        intent_url,
        {"intent": "login", "params": {"db": db_name, "login": login, "password": password}},
        headers={"X-Anonymous-Intent": "1"},
    )
    require_ok(status, login_resp, "login")
    token = ((login_resp.get("data") or {}).get("token") or "")
    if not token:
        raise RuntimeError("login response missing token")

    status, init_resp = http_post_json(
        intent_url,
        {"intent": "system.init", "params": {"contract_mode": "user", "with_preload": True}},
        headers={"Authorization": f"Bearer {token}"},
    )
    require_ok(status, init_resp, "system.init")
    data = init_resp.get("data") if isinstance(init_resp.get("data"), dict) else {}
    nav_meta = data.get("nav_meta") if isinstance(data.get("nav_meta"), dict) else {}
    scene_ready = data.get("scene_ready_contract_v1") if isinstance(data.get("scene_ready_contract_v1"), dict) else {}
    scene_meta = scene_ready.get("meta") if isinstance(scene_ready.get("meta"), dict) else {}

    role_code = str(nav_meta.get("role_surface_code") or "").strip() or "unknown"
    runtime_env = _resolve_runtime_env(data)
    asset_scene_count = _safe_int(nav_meta.get("ui_base_contract_asset_scene_count"), 0)
    asset_bound_scene_count = _safe_int(nav_meta.get("ui_base_contract_bound_scene_count"), 0)
    asset_missing_scene_count = _safe_int(nav_meta.get("ui_base_contract_missing_scene_count"), 0)
    scenes = scene_ready.get("scenes") if isinstance(scene_ready.get("scenes"), list) else []
    scene_count = _safe_int(scene_meta.get("scene_count"), len(scenes))
    scene_bound_count = _safe_int(scene_meta.get("base_contract_bound_scene_count"), 0)
    compile_issue_count = _safe_int(scene_meta.get("compile_issue_scene_count"), 0)

    if scene_bound_count <= 0 and scenes:
        scene_bound_count = sum(
            1
            for row in scenes
            if bool(
                ((row.get("meta") or {}).get("compile_verdict") or {}).get("base_contract_bound")
            )
        )
    if compile_issue_count <= 0 and scenes:
        compile_issue_count = sum(
            1
            for row in scenes
            if not bool(
                ((row.get("meta") or {}).get("compile_verdict") or {}).get("ok")
            )
        )

    return {
        "runtime_env": runtime_env,
        "role_code": role_code,
        "asset_scene_count": asset_scene_count,
        "asset_bound_scene_count": asset_bound_scene_count,
        "asset_missing_scene_count": asset_missing_scene_count,
        "asset_bind_ratio": (float(asset_bound_scene_count) / float(asset_scene_count)) if asset_scene_count > 0 else 1.0,
        "scene_count": scene_count,
        "scene_bound_count": scene_bound_count,
        "scene_bind_ratio": (float(scene_bound_count) / float(scene_count)) if scene_count > 0 else 1.0,
        "compile_issue_scene_count": compile_issue_count,
    }


def _resolve_threshold_policy(baseline: dict, *, runtime_env: str, role_code: str) -> dict:
    policy = _merge_dict({}, baseline.get("default") if isinstance(baseline.get("default"), dict) else {})
    env_map = baseline.get("env") if isinstance(baseline.get("env"), dict) else {}
    role_map = baseline.get("role") if isinstance(baseline.get("role"), dict) else {}
    env_role_map = baseline.get("env_role") if isinstance(baseline.get("env_role"), dict) else {}
    if isinstance(env_map.get(runtime_env), dict):
        policy = _merge_dict(policy, env_map.get(runtime_env) or {})
    if isinstance(role_map.get(role_code), dict):
        policy = _merge_dict(policy, role_map.get(role_code) or {})
    env_role_key = f"{runtime_env}:{role_code}"
    if isinstance(env_role_map.get(env_role_key), dict):
        policy = _merge_dict(policy, env_role_map.get(env_role_key) or {})
    return policy


def _evaluate_thresholds(metrics: dict, policy: dict, errors: list[str]) -> None:
    min_scene_count = _safe_int(policy.get("min_scene_count"), 0)
    min_scene_bind_ratio = _safe_float(policy.get("min_scene_bind_ratio"), 0.0)
    min_asset_bind_ratio = _safe_float(policy.get("min_asset_bind_ratio"), 0.0)
    max_compile_issue_scene_count = _safe_int(policy.get("max_compile_issue_scene_count"), 999999)

    scene_count = _safe_int(metrics.get("scene_count"), 0)
    scene_bind_ratio = _safe_float(metrics.get("scene_bind_ratio"), 0.0)
    asset_bind_ratio = _safe_float(metrics.get("asset_bind_ratio"), 0.0)
    compile_issue_scene_count = _safe_int(metrics.get("compile_issue_scene_count"), 0)

    if scene_count < min_scene_count:
        errors.append(f"scene_count below threshold: {scene_count} < {min_scene_count}")
    if scene_bind_ratio < min_scene_bind_ratio:
        errors.append(f"scene_bind_ratio below threshold: {scene_bind_ratio:.4f} < {min_scene_bind_ratio:.4f}")
    if asset_bind_ratio < min_asset_bind_ratio:
        errors.append(f"asset_bind_ratio below threshold: {asset_bind_ratio:.4f} < {min_asset_bind_ratio:.4f}")
    if compile_issue_scene_count > max_compile_issue_scene_count:
        errors.append(
            f"compile_issue_scene_count exceeded: {compile_issue_scene_count} > {max_compile_issue_scene_count}"
        )


def main() -> int:
    baseline = _load_json(BASELINE_PATH)
    if not baseline:
        print("[verify.scene.base_contract_asset_coverage.guard] FAIL")
        print(f" - missing or invalid baseline: {BASELINE_PATH.relative_to(ROOT).as_posix()}")
        return 1

    errors: list[str] = []
    warnings: list[str] = []
    for path in (
        BUILDER_PATH,
        SYSTEM_INIT_PATH,
        REPOSITORY_PATH,
        MODEL_PATH,
        PRODUCER_PATH,
        QUEUE_PATH,
        TRIGGER_PATH,
        CRON_XML_PATH,
        MANIFEST_PATH,
    ):
        if not path.is_file():
            errors.append(f"missing required file: {path}")
    if errors:
        print("[verify.scene.base_contract_asset_coverage.guard] FAIL")
        for item in errors:
            print(f" - {item}")
        return 1

    try:
        _validate_wiring(errors)
        _validate_builder_coverage(errors)
        _validate_asset_model_semantics(errors)
        _validate_production_wiring(errors)
    except Exception as exc:
        errors.append(str(exc))

    state_path = _resolve_state_path(baseline)
    state_path.parent.mkdir(parents=True, exist_ok=True)

    strict_live = str(os.getenv("SC_BASE_CONTRACT_ASSET_COVERAGE_REQUIRE_LIVE") or "").strip() in {
        "1",
        "true",
        "TRUE",
        "yes",
    }
    metrics: dict = {}
    fetch_error = ""
    source = "live"
    try:
        metrics = _fetch_runtime_data()
    except Exception as exc:
        fetch_error = str(exc)
        source = "state"
        metrics = _load_json(state_path)
        if not metrics:
            source = "none"
            if strict_live:
                errors.append(f"unable to fetch live coverage metrics: {fetch_error or 'unknown error'}")
            else:
                warnings.append(f"live coverage fetch skipped: {fetch_error or 'unknown error'}")

    if metrics:
        if source != "live" and not strict_live:
            state_scene_count = _safe_int(metrics.get("scene_count"), 0)
            state_asset_count = _safe_int(metrics.get("asset_scene_count"), 0)
            if state_scene_count <= 0 and state_asset_count <= 0:
                warnings.append("state coverage metrics empty; skip threshold checks until live sample is available")
                metrics = {}

    if metrics:
        runtime_env = str(metrics.get("runtime_env") or _resolve_runtime_env({})).strip() or "dev"
        role_code = str(metrics.get("role_code") or "unknown").strip() or "unknown"
        policy = _resolve_threshold_policy(baseline, runtime_env=runtime_env, role_code=role_code)
        if policy:
            _evaluate_thresholds(metrics, policy, errors)
        else:
            warnings.append("threshold policy is empty; skip ratio checks")
        metrics["evaluated_policy"] = policy
        metrics["evaluated_source"] = source
        metrics["captured_at"] = datetime.utcnow().isoformat(timespec="seconds") + "Z"
        if source == "live":
            state_path.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")

    if errors:
        print("[verify.scene.base_contract_asset_coverage.guard] FAIL")
        for item in errors:
            print(f" - {item}")
        if warnings:
            for item in warnings:
                print(f" - warn: {item}")
        return 1

    if warnings:
        print("[verify.scene.base_contract_asset_coverage.guard] WARN")
        for item in warnings:
            print(f" - {item}")
    print("[verify.scene.base_contract_asset_coverage.guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
