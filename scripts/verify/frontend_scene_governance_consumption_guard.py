#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SESSION_PATH = ROOT / "frontend" / "apps" / "web" / "src" / "stores" / "session.ts"
APP_SHELL_PATH = ROOT / "frontend" / "apps" / "web" / "src" / "layouts" / "AppShell.vue"
SCENE_HEALTH_PATH = ROOT / "frontend" / "apps" / "web" / "src" / "views" / "SceneHealthView.vue"


def _assert(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def main() -> int:
    errors: list[str] = []
    for path in (SESSION_PATH, APP_SHELL_PATH, SCENE_HEALTH_PATH):
        if not path.is_file():
            errors.append(f"missing file: {path}")
    if errors:
        print("[frontend_scene_governance_consumption_guard] FAIL")
        for item in errors:
            print(f" - {item}")
        return 1

    session_text = SESSION_PATH.read_text(encoding="utf-8")
    app_shell_text = APP_SHELL_PATH.read_text(encoding="utf-8")
    scene_health_text = SCENE_HEALTH_PATH.read_text(encoding="utf-8")

    _assert("scene_ready_consumption?: Record<string, unknown>;" in session_text, "session governance payload missing scene_ready_consumption field", errors)

    _assert("sceneGovernanceConsumptionSummary" in app_shell_text, "AppShell missing governance consumption summary compute", errors)
    _assert("governance.scene_ready_consumption" in app_shell_text, "AppShell HUD missing governance.scene_ready_consumption entry", errors)

    _assert("governanceConsumptionLabel" in scene_health_text, "SceneHealthView missing governance consumption label compute", errors)
    _assert("governance.scene_ready_consumption" in scene_health_text, "SceneHealthView missing governance.scene_ready_consumption display", errors)

    if errors:
        print("[frontend_scene_governance_consumption_guard] FAIL")
        for item in errors:
            print(f" - {item}")
        return 1

    print("[frontend_scene_governance_consumption_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

