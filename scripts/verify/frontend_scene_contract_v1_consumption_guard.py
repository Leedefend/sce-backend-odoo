#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
HOME_VIEW = ROOT / "frontend/apps/web/src/views/HomeView.vue"
PM_DASHBOARD_VIEW = ROOT / "frontend/apps/web/src/views/ProjectManagementDashboardView.vue"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.is_file() else ""


def _fail(errors: list[str]) -> int:
    print("[frontend_scene_contract_v1_consumption_guard] FAIL")
    for err in errors:
        print(f"- {err}")
    return 1


def main() -> int:
    errors: list[str] = []
    home_text = _read(HOME_VIEW)
    dashboard_text = _read(PM_DASHBOARD_VIEW)

    if not home_text:
        errors.append(f"missing file: {HOME_VIEW.relative_to(ROOT).as_posix()}")
    if not dashboard_text:
        errors.append(f"missing file: {PM_DASHBOARD_VIEW.relative_to(ROOT).as_posix()}")
    if errors:
        return _fail(errors)

    home_required = (
        "const workspaceSceneContractV1 = computed(() =>",
        "workspaceHome.value.scene_contract_v1",
        "asText(workspaceSceneContractV1.value.contract_version) === 'v1'",
    )
    dashboard_required = (
        "scene_contract_v1?: Record<string, unknown>;",
        "function asSceneContractV1(payload: DashboardResponse | null)",
        "const rawContract = payload?.scene_contract_v1;",
        "function resolveDashboardZones(payload: DashboardResponse | null)",
    )

    for token in home_required:
        if token not in home_text:
            errors.append(f"HomeView missing token: {token}")
    for token in dashboard_required:
        if token not in dashboard_text:
            errors.append(f"ProjectManagementDashboardView missing token: {token}")

    if errors:
        return _fail(errors)

    print("[frontend_scene_contract_v1_consumption_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())

