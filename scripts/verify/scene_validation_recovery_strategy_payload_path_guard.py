#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SYSTEM_INIT_PATH = ROOT / "addons" / "smart_core" / "handlers" / "system_init.py"
SESSION_PATH = ROOT / "frontend" / "apps" / "web" / "src" / "stores" / "session.ts"


def _assert(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def _index_of(text: str, token: str) -> int:
    try:
        return text.index(token)
    except ValueError:
        return -1


def main() -> int:
    errors: list[str] = []
    for path in (SYSTEM_INIT_PATH, SESSION_PATH):
        if not path.is_file():
            errors.append(f"missing file: {path}")
    if errors:
        print("[scene_validation_recovery_strategy_payload_path_guard] FAIL")
        for item in errors:
            print(f" - {item}")
        return 1

    system_init_text = SYSTEM_INIT_PATH.read_text(encoding="utf-8")
    session_text = SESSION_PATH.read_text(encoding="utf-8")

    params_token = 'params.get("scene_validation_recovery_strategy")'
    ext_token = 'ext_facts.get("scene_validation_recovery_strategy")'
    icp_token = 'smart_core.scene_validation_recovery_strategy_json'

    params_idx = _index_of(system_init_text, params_token)
    ext_idx = _index_of(system_init_text, ext_token)
    icp_idx = _index_of(system_init_text, icp_token)

    _assert(params_idx >= 0, "system.init missing params strategy source", errors)
    _assert(ext_idx >= 0, "system.init missing ext_facts strategy source", errors)
    _assert(icp_idx >= 0, "system.init missing icp strategy source", errors)
    if params_idx >= 0 and ext_idx >= 0 and icp_idx >= 0:
        _assert(params_idx < ext_idx < icp_idx, "system.init strategy source priority order invalid", errors)

    _assert(
        'data["scene_validation_recovery_strategy"]' in system_init_text,
        "system.init missing normalized strategy output key",
        errors,
    )

    session_top_token = "validationStrategyRaw"
    session_ext_token = "extValidationStrategyRaw"
    session_apply_token = "applySceneValidationRecoveryStrategyRuntime(\n        validationStrategy"

    top_idx = _index_of(session_text, session_top_token)
    ext2_idx = _index_of(session_text, session_ext_token)
    apply_idx = _index_of(session_text, session_apply_token)

    _assert(top_idx >= 0, "session missing top-level strategy source", errors)
    _assert(ext2_idx >= 0, "session missing ext_facts fallback strategy source", errors)
    _assert(apply_idx >= 0, "session missing runtime apply hook", errors)
    if top_idx >= 0 and ext2_idx >= 0:
        _assert(top_idx < ext2_idx, "session strategy source priority order invalid", errors)
    if ext2_idx >= 0 and apply_idx >= 0:
        _assert(ext2_idx < apply_idx, "session apply hook must execute after source resolution", errors)

    if errors:
        print("[scene_validation_recovery_strategy_payload_path_guard] FAIL")
        for item in errors:
            print(f" - {item}")
        return 1

    print("[scene_validation_recovery_strategy_payload_path_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
