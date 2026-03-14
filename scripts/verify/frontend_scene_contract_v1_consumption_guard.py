#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
HOME_VIEW = ROOT / "frontend/apps/web/src/views/HomeView.vue"
PM_DASHBOARD_VIEW = ROOT / "frontend/apps/web/src/views/ProjectManagementDashboardView.vue"
MY_WORK_VIEW = ROOT / "frontend/apps/web/src/views/MyWorkView.vue"
WORKBENCH_VIEW = ROOT / "frontend/apps/web/src/views/WorkbenchView.vue"
ACTION_VIEW = ROOT / "frontend/apps/web/src/views/ActionView.vue"
RECORD_VIEW = ROOT / "frontend/apps/web/src/views/RecordView.vue"
PAGE_CONTRACT = ROOT / "frontend/apps/web/src/app/pageContract.ts"
SCENE_VIEW = ROOT / "frontend/apps/web/src/views/SceneView.vue"
MENU_VIEW = ROOT / "frontend/apps/web/src/views/MenuView.vue"
SCENE_HEALTH_VIEW = ROOT / "frontend/apps/web/src/views/SceneHealthView.vue"
SCENE_PACKAGES_VIEW = ROOT / "frontend/apps/web/src/views/ScenePackagesView.vue"
USAGE_ANALYTICS_VIEW = ROOT / "frontend/apps/web/src/views/UsageAnalyticsView.vue"
PLACEHOLDER_VIEW = ROOT / "frontend/apps/web/src/views/PlaceholderView.vue"
LOGIN_VIEW = ROOT / "frontend/apps/web/src/views/LoginView.vue"


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
    my_work_text = _read(MY_WORK_VIEW)
    workbench_text = _read(WORKBENCH_VIEW)
    action_text = _read(ACTION_VIEW)
    record_text = _read(RECORD_VIEW)
    page_contract_text = _read(PAGE_CONTRACT)
    scene_text = _read(SCENE_VIEW)
    menu_text = _read(MENU_VIEW)
    scene_health_text = _read(SCENE_HEALTH_VIEW)
    scene_packages_text = _read(SCENE_PACKAGES_VIEW)
    usage_analytics_text = _read(USAGE_ANALYTICS_VIEW)
    placeholder_text = _read(PLACEHOLDER_VIEW)
    login_text = _read(LOGIN_VIEW)

    if not home_text:
        errors.append(f"missing file: {HOME_VIEW.relative_to(ROOT).as_posix()}")
    if not dashboard_text:
        errors.append(f"missing file: {PM_DASHBOARD_VIEW.relative_to(ROOT).as_posix()}")
    if not my_work_text:
        errors.append(f"missing file: {MY_WORK_VIEW.relative_to(ROOT).as_posix()}")
    if not workbench_text:
        errors.append(f"missing file: {WORKBENCH_VIEW.relative_to(ROOT).as_posix()}")
    if not action_text:
        errors.append(f"missing file: {ACTION_VIEW.relative_to(ROOT).as_posix()}")
    if not record_text:
        errors.append(f"missing file: {RECORD_VIEW.relative_to(ROOT).as_posix()}")
    if not page_contract_text:
        errors.append(f"missing file: {PAGE_CONTRACT.relative_to(ROOT).as_posix()}")
    if not scene_text:
        errors.append(f"missing file: {SCENE_VIEW.relative_to(ROOT).as_posix()}")
    if not menu_text:
        errors.append(f"missing file: {MENU_VIEW.relative_to(ROOT).as_posix()}")
    if not scene_health_text:
        errors.append(f"missing file: {SCENE_HEALTH_VIEW.relative_to(ROOT).as_posix()}")
    if not scene_packages_text:
        errors.append(f"missing file: {SCENE_PACKAGES_VIEW.relative_to(ROOT).as_posix()}")
    if not usage_analytics_text:
        errors.append(f"missing file: {USAGE_ANALYTICS_VIEW.relative_to(ROOT).as_posix()}")
    if not placeholder_text:
        errors.append(f"missing file: {PLACEHOLDER_VIEW.relative_to(ROOT).as_posix()}")
    if not login_text:
        errors.append(f"missing file: {LOGIN_VIEW.relative_to(ROOT).as_posix()}")
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
    my_work_required = (
        "normalizeSceneContractV1ToPageContract(pageContract.contract.value?.scene_contract_v1)",
        "function normalizeSceneContractV1ToPageContract(raw: unknown): PageOrchestrationContract",
    )
    workbench_required = (
        "normalizeSceneContractV1ToPageContract(pageContract.contract.value?.scene_contract_v1)",
        "function normalizeSceneContractV1ToPageContract(raw: unknown): PageOrchestrationContract",
    )
    page_contract_required = (
        "const sceneContractV1 = computed<Record<string, unknown>>(() =>",
        "contract.value?.scene_contract_v1",
        "fromSceneV1.length",
        "sceneActionSchema",
    )
    action_required = (
        "const sceneContractV1 = computed<Record<string, unknown>>(() =>",
        "surface_policies?.intent_profile",
        "surface_policies?.delete_mode",
    )
    record_forbidden = (
        "key.includes('project')",
        "key.includes('项目')",
    )
    p1_p2_required = (
        "const pageContract = usePageContract(",
    )

    for token in home_required:
        if token not in home_text:
            errors.append(f"HomeView missing token: {token}")
    for token in dashboard_required:
        if token not in dashboard_text:
            errors.append(f"ProjectManagementDashboardView missing token: {token}")
    for token in my_work_required:
        if token not in my_work_text:
            errors.append(f"MyWorkView missing token: {token}")
    for token in workbench_required:
        if token not in workbench_text:
            errors.append(f"WorkbenchView missing token: {token}")
    for token in page_contract_required:
        if token not in page_contract_text:
            errors.append(f"pageContract.ts missing token: {token}")
    for token in action_required:
        if token not in action_text:
            errors.append(f"ActionView missing token: {token}")
    for token in record_forbidden:
        if token in record_text:
            errors.append(f"RecordView contains forbidden model keyword special-case token: {token}")
    for name, text in (
        ("SceneView", scene_text),
        ("MenuView", menu_text),
        ("SceneHealthView", scene_health_text),
        ("ScenePackagesView", scene_packages_text),
        ("UsageAnalyticsView", usage_analytics_text),
        ("PlaceholderView", placeholder_text),
        ("LoginView", login_text),
    ):
        for token in p1_p2_required:
            if token not in text:
                errors.append(f"{name} missing token: {token}")

    if errors:
        return _fail(errors)

    print("[frontend_scene_contract_v1_consumption_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
