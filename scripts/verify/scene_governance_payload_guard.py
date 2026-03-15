#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
BUILDER_PATH = ROOT / "addons" / "smart_core" / "core" / "scene_governance_payload_builder.py"
SYSTEM_INIT_PATH = ROOT / "addons" / "smart_core" / "handlers" / "system_init.py"


def _load_builder():
    spec = importlib.util.spec_from_file_location("scene_governance_payload_builder_guard", BUILDER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"spec unavailable: {BUILDER_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    fn = getattr(module, "build_scene_governance_payload_v1", None)
    if not callable(fn):
        raise RuntimeError("build_scene_governance_payload_v1 not found")
    return fn


def _assert(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def _validate_wiring(errors: list[str]) -> None:
    text = SYSTEM_INIT_PATH.read_text(encoding="utf-8")
    _assert(
        "build_scene_governance_payload_v1" in text,
        "system_init missing build_scene_governance_payload_v1 import/use",
        errors,
    )
    _assert(
        'data["scene_governance_v1"]' in text,
        "system_init missing scene_governance_v1 response assignment",
        errors,
    )


def _validate_builder_contract(errors: list[str]) -> None:
    build_fn = _load_builder()
    payload = build_fn(
        data={
            "scene_channel": "stable",
            "scene_contract_ref": "stable/LATEST.json",
        },
        scene_diagnostics={
            "loaded_from": "contract",
            "governance": {"contract_mode": "user"},
            "auto_degrade": {
                "triggered": True,
                "reason_codes": ["SCENE_RESOLVE_CRITICAL", "SCENE_RESOLVE_CRITICAL"],
            },
            "normalize_warnings": [{"code": "W1"}],
            "resolve_errors": [{"code": "E1"}, {"code": "E1"}, {"code": "E2"}],
            "drift": [{"code": "D1"}],
            "role_surface_provider": {"selected_provider": "p1"},
        },
        delivery_meta={"enabled": True, "surface": "default"},
        nav_contract_meta={
            "nav_policy_validation_ok": False,
            "nav_policy_source": "platform_default",
            "nav_policy_provider": "platform.default.scene_nav_v1",
            "nav_policy_version": "v1",
            "nav_policy_validation_issues": ["missing group label"],
        },
    )

    required_root = {
        "contract_version",
        "scene_channel",
        "scene_contract_ref",
        "runtime_source",
        "governance",
        "auto_degrade",
        "delivery_policy",
        "nav_policy",
        "role_surface_provider",
        "diagnostics",
        "gates",
        "reasons",
    }
    _assert(isinstance(payload, dict), "payload must be dict", errors)
    _assert(required_root.issubset(set(payload.keys())), "payload missing required root keys", errors)

    gates = payload.get("gates") if isinstance(payload.get("gates"), dict) else {}
    for key in (
        "orchestrator_applied",
        "governance_applied",
        "delivery_policy_applied",
        "nav_policy_validation_ok",
        "auto_degrade_triggered",
    ):
        _assert(isinstance(gates.get(key), bool), f"gates.{key} must be bool", errors)

    diagnostics = payload.get("diagnostics") if isinstance(payload.get("diagnostics"), dict) else {}
    _assert(diagnostics.get("normalize_warning_count") == 1, "diagnostics.normalize_warning_count mismatch", errors)
    _assert(diagnostics.get("resolve_error_count") == 3, "diagnostics.resolve_error_count mismatch", errors)
    _assert(diagnostics.get("drift_count") == 1, "diagnostics.drift_count mismatch", errors)
    _assert(diagnostics.get("resolve_error_codes") == ["E1", "E2"], "diagnostics.resolve_error_codes mismatch", errors)

    reasons = payload.get("reasons") if isinstance(payload.get("reasons"), dict) else {}
    _assert(
        reasons.get("auto_degrade_reason_codes") == ["SCENE_RESOLVE_CRITICAL", "SCENE_RESOLVE_CRITICAL"],
        "reasons.auto_degrade_reason_codes mismatch",
        errors,
    )
    _assert(reasons.get("resolve_error_codes") == ["E1", "E2"], "reasons.resolve_error_codes mismatch", errors)


def main() -> int:
    errors: list[str] = []
    if not BUILDER_PATH.is_file():
        errors.append(f"missing builder file: {BUILDER_PATH}")
    if not SYSTEM_INIT_PATH.is_file():
        errors.append(f"missing system_init file: {SYSTEM_INIT_PATH}")
    if errors:
        print("[verify.scene.governance_payload.guard] FAIL")
        for item in errors:
            print(f" - {item}")
        return 1

    try:
        _validate_wiring(errors)
        _validate_builder_contract(errors)
    except Exception as exc:
        errors.append(str(exc))

    if errors:
        print("[verify.scene.governance_payload.guard] FAIL")
        for item in errors:
            print(f" - {item}")
        return 1

    print("[verify.scene.governance_payload.guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
