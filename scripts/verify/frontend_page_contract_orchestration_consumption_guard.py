#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
PAGE_CONTRACT_TS = ROOT / "frontend/apps/web/src/app/pageContract.ts"
PAGE_BUILDER = ROOT / "addons/smart_core/core/page_contracts_builder.py"
ACTION_TARGET_SCHEMA = ROOT / "addons/smart_core/core/action_target_schema.py"
WORKBENCH_VIEW = ROOT / "frontend/apps/web/src/views/WorkbenchView.vue"
ACTION_VIEW = ROOT / "frontend/apps/web/src/views/ActionView.vue"
RECORD_VIEW = ROOT / "frontend/apps/web/src/views/RecordView.vue"
SCENE_VIEW = ROOT / "frontend/apps/web/src/views/SceneView.vue"
LOGIN_VIEW = ROOT / "frontend/apps/web/src/views/LoginView.vue"
MENU_VIEW = ROOT / "frontend/apps/web/src/views/MenuView.vue"
PLACEHOLDER_VIEW = ROOT / "frontend/apps/web/src/views/PlaceholderView.vue"
SCENE_HEALTH_VIEW = ROOT / "frontend/apps/web/src/views/SceneHealthView.vue"
USAGE_ANALYTICS_VIEW = ROOT / "frontend/apps/web/src/views/UsageAnalyticsView.vue"
HOME_VIEW = ROOT / "frontend/apps/web/src/views/HomeView.vue"
MY_WORK_VIEW = ROOT / "frontend/apps/web/src/views/MyWorkView.vue"
SCENE_PACKAGES_VIEW = ROOT / "frontend/apps/web/src/views/ScenePackagesView.vue"
PAGE_ACTION_RUNTIME = ROOT / "frontend/apps/web/src/app/pageContractActionRuntime.ts"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.is_file() else ""


def _fail(errors: list[str]) -> int:
    print("[frontend_page_contract_orchestration_consumption_guard] FAIL")
    for err in errors:
        print(f"- {err}")
    return 1


def _expect(text: str, scope: str, tokens: list[str], errors: list[str]) -> None:
    for token in tokens:
        if token not in text:
            errors.append(f"{scope} missing token: {token}")


def main() -> int:
    page_contract_text = _read(PAGE_CONTRACT_TS)
    page_builder_text = _read(PAGE_BUILDER)
    action_target_schema_text = _read(ACTION_TARGET_SCHEMA)
    workbench_text = _read(WORKBENCH_VIEW)
    action_view_text = _read(ACTION_VIEW)
    record_view_text = _read(RECORD_VIEW)
    scene_view_text = _read(SCENE_VIEW)
    login_view_text = _read(LOGIN_VIEW)
    menu_view_text = _read(MENU_VIEW)
    placeholder_view_text = _read(PLACEHOLDER_VIEW)
    scene_health_text = _read(SCENE_HEALTH_VIEW)
    usage_analytics_text = _read(USAGE_ANALYTICS_VIEW)
    home_text = _read(HOME_VIEW)
    my_work_text = _read(MY_WORK_VIEW)
    scene_packages_text = _read(SCENE_PACKAGES_VIEW)
    action_runtime_text = _read(PAGE_ACTION_RUNTIME)
    errors: list[str] = []

    if not page_contract_text:
        errors.append(f"missing file: {PAGE_CONTRACT_TS.relative_to(ROOT).as_posix()}")
    if not page_builder_text:
        errors.append(f"missing file: {PAGE_BUILDER.relative_to(ROOT).as_posix()}")
    if not workbench_text:
        errors.append(f"missing file: {WORKBENCH_VIEW.relative_to(ROOT).as_posix()}")
    if not action_view_text:
        errors.append(f"missing file: {ACTION_VIEW.relative_to(ROOT).as_posix()}")
    if not record_view_text:
        errors.append(f"missing file: {RECORD_VIEW.relative_to(ROOT).as_posix()}")
    if not scene_view_text:
        errors.append(f"missing file: {SCENE_VIEW.relative_to(ROOT).as_posix()}")
    if not login_view_text:
        errors.append(f"missing file: {LOGIN_VIEW.relative_to(ROOT).as_posix()}")
    if not menu_view_text:
        errors.append(f"missing file: {MENU_VIEW.relative_to(ROOT).as_posix()}")
    if not placeholder_view_text:
        errors.append(f"missing file: {PLACEHOLDER_VIEW.relative_to(ROOT).as_posix()}")
    if not action_target_schema_text:
        errors.append(f"missing file: {ACTION_TARGET_SCHEMA.relative_to(ROOT).as_posix()}")
    if not scene_health_text:
        errors.append(f"missing file: {SCENE_HEALTH_VIEW.relative_to(ROOT).as_posix()}")
    if not usage_analytics_text:
        errors.append(f"missing file: {USAGE_ANALYTICS_VIEW.relative_to(ROOT).as_posix()}")
    if not home_text:
        errors.append(f"missing file: {HOME_VIEW.relative_to(ROOT).as_posix()}")
    if not my_work_text:
        errors.append(f"missing file: {MY_WORK_VIEW.relative_to(ROOT).as_posix()}")
    if not scene_packages_text:
        errors.append(f"missing file: {SCENE_PACKAGES_VIEW.relative_to(ROOT).as_posix()}")
    if not action_runtime_text:
        errors.append(f"missing file: {PAGE_ACTION_RUNTIME.relative_to(ROOT).as_posix()}")
    if errors:
        return _fail(errors)

    _expect(
        page_contract_text,
        "pageContract.ts",
        [
            "contract.value?.page_orchestration_v1?.action_schema",
            "const orchestrationDataSources = computed<Record<string, unknown>>(() => {",
            "contract.value?.page_orchestration_v1?.data_sources",
            "const hasV1Zones = zones.length > 0;",
            "const dataSourceKey = asText(row.data_source);",
            "const dataSource = dataSourcesRow[dataSourceKey];",
            "const raw = hasV1Zones",
            "const globalActions = computed<GlobalActionConfig[]>(() => {",
            "(page as Record<string, unknown>).global_actions",
            "const orchestrationActions = computed<Record<string, unknown>>(() => {",
            "const row = orchestrationActions.value[key];",
            "const label = asText((row as Record<string, unknown>).label);",
            "function actionIntent(key: string, fallback = ''): string {",
            "function actionTarget(key: string): Record<string, unknown> {",
            "function dataSourceSpec(key: string): Record<string, unknown> {",
            "function dataSourceType(key: string): string {",
            "function hasDataSource(key: string): boolean {",
            "actionIntent,",
            "actionTarget,",
            "dataSourceSpec,",
            "dataSourceType,",
            "hasDataSource,",
            "globalActions,",
        ],
        errors,
    )
    _expect(
        page_builder_text,
        "page_contracts_builder.py",
        [
            '"action_schema": {"actions": action_schema_actions},',
            '"actions": _action_templates(section_key),',
            "def _shared_action_target(action_key: str, page_key: str) -> Dict[str, Any]:",
            'helper_path = Path(__file__).with_name("action_target_schema.py")',
            "def _default_page_actions(page_key: str) -> list[Dict[str, Any]]:",
            'if key == "home":',
            '{"key": "open_usage_analytics", "label": "使用分析", "intent": "ui.contract"}',
            '{"key": "open_workbench", "label": "返回工作台", "intent": "ui.contract"}',
            'if key in {"scene_health", "usage_analytics", "scene_packages"}:',
        ],
        errors,
    )
    _expect(
        action_target_schema_text,
        "action_target_schema.py",
        [
            "def resolve_action_target(action_key: str, page_key: str) -> Dict[str, Any]:",
            'if key == "open_usage_analytics":',
            'return route_path_target("/admin/usage-analytics")',
            'if key in {"refresh_page", "refresh"}:',
            "return page_refresh_target()",
            'if key == "open_menu":',
            "return menu_first_reachable_target()",
            "return scene_target(page)",
        ],
        errors,
    )
    _expect(
        action_runtime_text,
        "pageContractActionRuntime.ts",
        [
            "export async function executePageContractAction(deps: ContractActionDeps): Promise<boolean> {",
            "if (kind === 'page.refresh') {",
            "if (kind === 'menu.first_reachable') {",
            "if (kind === 'route.path') {",
            "if (kind === 'scene.key') {",
            "if (intent === 'ui.contract' && scene) {",
            "if (deps.onFallback) {",
        ],
        errors,
    )
    _expect(
        scene_packages_text,
        "ScenePackagesView.vue",
        [
            "import { executePageContractAction } from '../app/pageContractActionRuntime';",
            "const pageActionIntent = pageContract.actionIntent;",
            "const pageActionTarget = pageContract.actionTarget;",
            "const pageGlobalActions = pageContract.globalActions;",
            "const headerActions = computed(() => pageGlobalActions.value);",
            "v-for=\"action in headerActions\"",
            "@click=\"executeHeaderAction(action.key)\"",
            "async function executeHeaderAction(actionKey: string) {",
            "const handled = await executePageContractAction({",
            "onRefresh: loadPackages,",
        ],
        errors,
    )
    _expect(
        workbench_text,
        "WorkbenchView.vue",
        [
            "const pageActionText = pageContract.actionText;",
            "const pageActionIntent = pageContract.actionIntent;",
            "const pageActionTarget = pageContract.actionTarget;",
            "const pageHasDataSource = pageContract.hasDataSource;",
            "const pageDataSourceType = pageContract.dataSourceType;",
            "const pageGlobalActions = pageContract.globalActions;",
            "import { executePageContractAction } from '../app/pageContractActionRuntime';",
            "const statusPanelDataSourceType = computed(() => pageDataSourceType('ds_section_status_panel'));",
            "const hasStatusPanelDataSource = computed(() => pageHasDataSource('ds_section_status_panel') && statusPanelDataSourceType.value === 'scene_context');",
            "const headerActions = computed(() => {",
            "v-for=\"action in headerActions\"",
            "@click=\"executeWorkbenchAction(action.key)\"",
            "async function executeWorkbenchAction(actionKey: string) {",
            "const handled = await executePageContractAction({",
            "onOpenMenuFirstReachable: async () => {",
        ],
        errors,
    )
    _expect(
        action_view_text,
        "ActionView.vue",
        [
            "import { executePageContractAction } from '../app/pageContractActionRuntime';",
            "const pageActionIntent = pageContract.actionIntent;",
            "const pageActionTarget = pageContract.actionTarget;",
            "const pageGlobalActions = pageContract.globalActions;",
            "const headerActions = computed(() => pageGlobalActions.value);",
            "v-for=\"action in vm.header.actions\"",
            "@click=\"executeHeaderAction(action.key)\"",
            "useActionViewHeaderRuntime({",
            "executeHeaderAction,",
        ],
        errors,
    )
    _expect(
        login_view_text,
        "LoginView.vue",
        [
            "import { executePageContractAction } from '../app/pageContractActionRuntime';",
            "const pageActionIntent = pageContract.actionIntent;",
            "const pageActionTarget = pageContract.actionTarget;",
            "const pageGlobalActions = pageContract.globalActions;",
            "const headerActions = computed(() => pageGlobalActions.value);",
            "v-for=\"action in headerActions\"",
            "@click=\"executeHeaderAction(action.key)\"",
            "async function executeHeaderAction(actionKey: string) {",
            "const handled = await executePageContractAction({",
        ],
        errors,
    )
    _expect(
        menu_view_text,
        "MenuView.vue",
        [
            "import { executePageContractAction } from '../app/pageContractActionRuntime';",
            "const pageActionIntent = pageContract.actionIntent;",
            "const pageActionTarget = pageContract.actionTarget;",
            "const pageGlobalActions = pageContract.globalActions;",
            "const headerActions = computed(() => pageGlobalActions.value);",
            "v-for=\"action in headerActions\"",
            "@click=\"executeHeaderAction(action.key)\"",
            "async function executeHeaderAction(actionKey: string) {",
            "const handled = await executePageContractAction({",
            "onRefresh: resolve,",
        ],
        errors,
    )
    _expect(
        placeholder_view_text,
        "PlaceholderView.vue",
        [
            "import { executePageContractAction } from '../app/pageContractActionRuntime';",
            "const pageActionIntent = pageContract.actionIntent;",
            "const pageActionTarget = pageContract.actionTarget;",
            "const pageGlobalActions = pageContract.globalActions;",
            "const headerActions = computed(() => pageGlobalActions.value);",
            "v-for=\"action in headerActions\"",
            "@click=\"executeHeaderAction(action.key)\"",
            "async function executeHeaderAction(actionKey: string) {",
            "const handled = await executePageContractAction({",
        ],
        errors,
    )
    _expect(
        record_view_text,
        "RecordView.vue",
        [
            "import { executePageContractAction } from '../app/pageContractActionRuntime';",
            "const pageActionIntent = pageContract.actionIntent;",
            "const pageActionTarget = pageContract.actionTarget;",
            "const pageGlobalActions = pageContract.globalActions;",
            "const headerActions = computed(() => pageGlobalActions.value);",
            "v-for=\"action in headerActions\"",
            "@click=\"executeHeaderAction(action.key)\"",
            "async function executeHeaderAction(actionKey: string) {",
            "const handled = await executePageContractAction({",
            "onRefresh: reload,",
        ],
        errors,
    )
    _expect(
        scene_view_text,
        "SceneView.vue",
        [
            "import { executePageContractAction } from '../app/pageContractActionRuntime';",
            "const pageActionIntent = pageContract.actionIntent;",
            "const pageActionTarget = pageContract.actionTarget;",
            "const pageGlobalActions = pageContract.globalActions;",
            "const headerActions = computed(() => pageGlobalActions.value);",
            "v-for=\"action in headerActions\"",
            "@click=\"executeHeaderAction(action.key)\"",
            "async function executeHeaderAction(actionKey: string) {",
            "const handled = await executePageContractAction({",
            "onRefresh: resolveScene,",
        ],
        errors,
    )
    _expect(
        home_text,
        "HomeView.vue",
        [
            "import { executePageContractAction } from '../app/pageContractActionRuntime';",
            "const pageActionIntent = pageContract.actionIntent;",
            "const pageActionTarget = pageContract.actionTarget;",
            "const pageGlobalActions = pageContract.globalActions;",
            "const heroQuickActions = computed(() => {",
            "v-for=\"action in heroQuickActions\"",
            "@click=\"executeHeroAction(action.key)\"",
            "async function executeHeroAction(actionKey: string) {",
            "const handled = await executePageContractAction({",
            "onFallback: async (key) => {",
        ],
        errors,
    )
    _expect(
        scene_health_text,
        "SceneHealthView.vue",
        [
            "const pageActionText = pageContract.actionText;",
            "const pageActionIntent = pageContract.actionIntent;",
            "const pageActionTarget = pageContract.actionTarget;",
            "const pageGlobalActions = pageContract.globalActions;",
            "import { executePageContractAction } from '../app/pageContractActionRuntime';",
            "const headerActions = computed(() => {",
            "v-for=\"action in headerActions\"",
            "@click=\"executeHeaderAction(action.key)\"",
            "async function executeHeaderAction(actionKey: string) {",
            "const handled = await executePageContractAction({",
            "onRefresh: loadHealth,",
        ],
        errors,
    )
    _expect(
        my_work_text,
        "MyWorkView.vue",
        [
            "import { executePageContractAction } from '../app/pageContractActionRuntime';",
            "const pageActionIntent = pageContract.actionIntent;",
            "const pageActionTarget = pageContract.actionTarget;",
            "const pageGlobalActions = pageContract.globalActions;",
            "const headerActions = computed(() => pageGlobalActions.value);",
            "v-for=\"action in headerActions\"",
            "@click=\"executeHeaderAction(action.key)\"",
            "async function executeHeaderAction(actionKey: string) {",
            "const handled = await executePageContractAction({",
            "onRefresh: load,",
        ],
        errors,
    )
    _expect(
        usage_analytics_text,
        "UsageAnalyticsView.vue",
        [
            "import { executePageContractAction } from '../app/pageContractActionRuntime';",
            "const pageActionIntent = pageContract.actionIntent;",
            "const pageActionTarget = pageContract.actionTarget;",
            "const pageGlobalActions = pageContract.globalActions;",
            "const headerActions = computed(() => pageGlobalActions.value);",
            "v-for=\"action in headerActions\"",
            "@click=\"executeHeaderAction(action.key)\"",
            "async function executeHeaderAction(actionKey: string) {",
            "const handled = await executePageContractAction({",
            "onRefresh: load,",
        ],
        errors,
    )

    if errors:
        return _fail(errors)

    print("[frontend_page_contract_orchestration_consumption_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
