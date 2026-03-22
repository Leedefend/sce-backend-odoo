#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
SESSION_STORE = ROOT / "frontend/apps/web/src/stores/session.ts"
HOME_VIEW = ROOT / "frontend/apps/web/src/views/HomeView.vue"
ACTION_VIEW = ROOT / "frontend/apps/web/src/views/ActionView.vue"
RECORD_VIEW = ROOT / "frontend/apps/web/src/views/RecordView.vue"
SCENE_VIEW = ROOT / "frontend/apps/web/src/views/SceneView.vue"
WORKBENCH_VIEW = ROOT / "frontend/apps/web/src/views/WorkbenchView.vue"
USAGE_ANALYTICS_VIEW = ROOT / "frontend/apps/web/src/views/UsageAnalyticsView.vue"
LOGIN_VIEW = ROOT / "frontend/apps/web/src/views/LoginView.vue"
MENU_VIEW = ROOT / "frontend/apps/web/src/views/MenuView.vue"
PLACEHOLDER_VIEW = ROOT / "frontend/apps/web/src/views/PlaceholderView.vue"
SCENE_HEALTH_VIEW = ROOT / "frontend/apps/web/src/views/SceneHealthView.vue"
SCENE_PACKAGES_VIEW = ROOT / "frontend/apps/web/src/views/ScenePackagesView.vue"
APP_SHELL = ROOT / "frontend/apps/web/src/layouts/AppShell.vue"
NAV_REGISTRY = ROOT / "frontend/apps/web/src/app/navigationRegistry.ts"
REPORT_JSON = ROOT / "artifacts/backend/frontend_product_contract_consumption_report.json"
REPORT_MD = ROOT / "docs/ops/audit/frontend_product_contract_consumption_report.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.is_file() else ""


def _has_all(text: str, tokens: list[str]) -> tuple[bool, list[str]]:
    missing = [token for token in tokens if token not in text]
    return not missing, missing


def main() -> int:
    session_text = _read(SESSION_STORE)
    home_text = _read(HOME_VIEW)
    action_text = _read(ACTION_VIEW)
    record_text = _read(RECORD_VIEW)
    scene_text = _read(SCENE_VIEW)
    workbench_text = _read(WORKBENCH_VIEW)
    usage_analytics_text = _read(USAGE_ANALYTICS_VIEW)
    login_text = _read(LOGIN_VIEW)
    menu_text = _read(MENU_VIEW)
    placeholder_text = _read(PLACEHOLDER_VIEW)
    scene_health_text = _read(SCENE_HEALTH_VIEW)
    scene_packages_text = _read(SCENE_PACKAGES_VIEW)
    shell_text = _read(APP_SHELL)
    nav_registry_text = _read(NAV_REGISTRY)
    errors: list[str] = []

    if not session_text:
        errors.append(f"missing file: {SESSION_STORE.relative_to(ROOT).as_posix()}")
    if not home_text:
        errors.append(f"missing file: {HOME_VIEW.relative_to(ROOT).as_posix()}")
    if not action_text:
        errors.append(f"missing file: {ACTION_VIEW.relative_to(ROOT).as_posix()}")
    if not record_text:
        errors.append(f"missing file: {RECORD_VIEW.relative_to(ROOT).as_posix()}")
    if not scene_text:
        errors.append(f"missing file: {SCENE_VIEW.relative_to(ROOT).as_posix()}")
    if not workbench_text:
        errors.append(f"missing file: {WORKBENCH_VIEW.relative_to(ROOT).as_posix()}")
    if not usage_analytics_text:
        errors.append(f"missing file: {USAGE_ANALYTICS_VIEW.relative_to(ROOT).as_posix()}")
    if not login_text:
        errors.append(f"missing file: {LOGIN_VIEW.relative_to(ROOT).as_posix()}")
    if not menu_text:
        errors.append(f"missing file: {MENU_VIEW.relative_to(ROOT).as_posix()}")
    if not placeholder_text:
        errors.append(f"missing file: {PLACEHOLDER_VIEW.relative_to(ROOT).as_posix()}")
    if not scene_health_text:
        errors.append(f"missing file: {SCENE_HEALTH_VIEW.relative_to(ROOT).as_posix()}")
    if not scene_packages_text:
        errors.append(f"missing file: {SCENE_PACKAGES_VIEW.relative_to(ROOT).as_posix()}")
    if not shell_text:
        errors.append(f"missing file: {APP_SHELL.relative_to(ROOT).as_posix()}")
    if not nav_registry_text:
        errors.append(f"missing file: {NAV_REGISTRY.relative_to(ROOT).as_posix()}")

    required_session_tokens = [
        "capability_groups",
        "capabilityCatalog",
        "this.capabilityCatalog = rawCapabilities.reduce",
        "this.capabilityGroups = rawCapabilityGroups",
        "pageContracts:",
        "async ensurePageContract(pageKey: string, force = false) {",
        "intent: 'page.contract',",
        "page_contract?: PageContract;",
        "[runtimePageKey]: runtimeContract,",
        "const extFacts =",
        "const productFacts =",
        "this.productFacts =",
        "license:",
        "bundle:",
    ]
    required_home_tokens = [
        "const productFacts = computed(() => session.productFacts);",
        "const capabilityGroups = computed(() => session.capabilityGroups);",
        "const workspaceLayout = computed(() => (",
        "homeLayoutText(",
        "isHomeSectionEnabled(",
        "isHomeSectionTag(",
        "isHomeSectionOpenDefault(",
        "const capabilityCatalog = session.capabilityCatalog || {};",
        "normalizeEntryWithCapabilityMeta(",
        "capabilityStateLabel(",
        "const capabilityGroupScoreMap = computed(() => {",
        "group.state_counts?.READY",
        "const workspaceHome = computed(() => (session.workspaceHome || {}) as Record<string, unknown>);",
        "capabilityStateFilter",
        "capabilityStateCounts",
        "capability_state_filter",
        "const bucketKey = entry.groupKey || entry.sceneKey;",
        "openBundleDashboard(",
        "licenseLevelLabel",
        "bundleNameLabel",
        "capabilityGroupCards",
        "<section v-if=\"isHomeSectionEnabled('group_overview') && isHomeSectionTag('group_overview', 'section') && capabilityGroupCards.length\" class=\"group-overview\"",
    ]
    required_shell_tokens = [
        "buildRuntimeNavigationRegistry(",
        "entry_source",
        "nav_entry_total",
        "nav_scene_entries",
        "nav_cap_entries",
    ]
    required_action_tokens = [
        "const pageContract = usePageContract('action');",
        "const pageSectionEnabled = pageContract.sectionEnabled;",
        "const pageSectionStyle = pageContract.sectionStyle;",
        "const pageSectionTagIs = pageContract.sectionTagIs;",
        "pageSectionEnabled('quick_filters', true)",
        "pageSectionEnabled('quick_actions', true)",
    ]
    required_record_tokens = [
        "const pageContract = usePageContract('record');",
        "const pageSectionEnabled = pageContract.sectionEnabled;",
        "const pageSectionStyle = pageContract.sectionStyle;",
        "const pageSectionTagIs = pageContract.sectionTagIs;",
        "pageSectionEnabled('project_summary', true)",
        "pageSectionEnabled('chatter', true)",
    ]
    required_scene_tokens = [
        "const pageContract = usePageContract('scene');",
        "const pageSectionEnabled = pageContract.sectionEnabled;",
        "const pageSectionStyle = pageContract.sectionStyle;",
        "const pageSectionTagIs = pageContract.sectionTagIs;",
        "pageSectionEnabled('status_loading', true)",
        "pageSectionEnabled('status_error', true)",
        "pageSectionEnabled('status_forbidden', true)",
    ]
    required_workbench_tokens = [
        "const pageContract = usePageContract('workbench');",
        "const pageSectionEnabled = pageContract.sectionEnabled;",
        "const pageSectionStyle = pageContract.sectionStyle;",
        "const pageSectionTagIs = pageContract.sectionTagIs;",
        "pageSectionEnabled('header', true)",
        "pageSectionEnabled('status_panel', true)",
        "pageSectionEnabled('tiles', true)",
        "pageSectionEnabled('hud_details', true)",
    ]
    required_usage_analytics_tokens = [
        "const pageContract = usePageContract('usage_analytics');",
        "const pageSectionEnabled = pageContract.sectionEnabled;",
        "const pageSectionStyle = pageContract.sectionStyle;",
        "const pageSectionTagIs = pageContract.sectionTagIs;",
        "pageSectionEnabled('header', true)",
        "pageSectionEnabled('tables_top', true)",
        "pageSectionEnabled('tables_role_user', true)",
    ]
    required_login_tokens = [
        "const pageContract = usePageContract('login');",
        "const pageSectionEnabled = pageContract.sectionEnabled;",
        "const pageSectionStyle = pageContract.sectionStyle;",
        "const pageSectionTagIs = pageContract.sectionTagIs;",
        "pageSectionEnabled('card', true)",
        "pageSectionEnabled('form', true)",
    ]
    required_menu_tokens = [
        "const pageContract = usePageContract('menu');",
        "const pageSectionEnabled = pageContract.sectionEnabled;",
        "const pageSectionStyle = pageContract.sectionStyle;",
        "const pageSectionTagIs = pageContract.sectionTagIs;",
        "pageSectionEnabled('status_loading', true)",
        "pageSectionEnabled('status_error', true)",
    ]
    required_placeholder_tokens = [
        "const pageContract = usePageContract('placeholder');",
        "const pageSectionEnabled = pageContract.sectionEnabled;",
        "const pageSectionStyle = pageContract.sectionStyle;",
        "const pageSectionTagIs = pageContract.sectionTagIs;",
        "pageSectionEnabled('card', true)",
    ]
    required_scene_health_tokens = [
        "const pageContract = usePageContract('scene_health');",
        "const pageSectionEnabled = pageContract.sectionEnabled;",
        "const pageSectionStyle = pageContract.sectionStyle;",
        "const pageSectionOpenDefault = pageContract.sectionOpenDefault;",
        "const pageSectionTagIs = pageContract.sectionTagIs;",
        "pageSectionEnabled('header', true)",
        "pageSectionEnabled('governance', true)",
        "pageSectionOpenDefault('details_resolve_errors', true)",
    ]
    required_scene_packages_tokens = [
        "const pageContract = usePageContract('scene_packages');",
        "const pageSectionEnabled = pageContract.sectionEnabled;",
        "const pageSectionStyle = pageContract.sectionStyle;",
        "const pageSectionTagIs = pageContract.sectionTagIs;",
        "pageSectionEnabled('installed_packages', true)",
        "pageSectionEnabled('import_package', true)",
        "pageSectionEnabled('export_package', true)",
    ]
    required_navigation_registry_tokens = [
        "export type NavigationEntrySource = 'scene' | 'capability';",
        "export interface RuntimeNavigationEntry",
        "export interface RuntimeNavigationRegistry",
        "export function buildRuntimeNavigationRegistry(",
        "registryKey: `nav.scene::${sceneKey}`",
        "registryKey: `nav.capability::${key}`",
    ]

    ok_session, missing_session = _has_all(session_text, required_session_tokens)
    ok_home, missing_home = _has_all(home_text, required_home_tokens)
    ok_shell, missing_shell = _has_all(shell_text, required_shell_tokens)
    ok_action, missing_action = _has_all(action_text, required_action_tokens)
    ok_record, missing_record = _has_all(record_text, required_record_tokens)
    ok_scene, missing_scene = _has_all(scene_text, required_scene_tokens)
    ok_workbench, missing_workbench = _has_all(workbench_text, required_workbench_tokens)
    ok_usage_analytics, missing_usage_analytics = _has_all(usage_analytics_text, required_usage_analytics_tokens)
    ok_login, missing_login = _has_all(login_text, required_login_tokens)
    ok_menu, missing_menu = _has_all(menu_text, required_menu_tokens)
    ok_placeholder, missing_placeholder = _has_all(placeholder_text, required_placeholder_tokens)
    ok_scene_health, missing_scene_health = _has_all(scene_health_text, required_scene_health_tokens)
    ok_scene_packages, missing_scene_packages = _has_all(scene_packages_text, required_scene_packages_tokens)
    ok_nav_registry, missing_nav_registry = _has_all(nav_registry_text, required_navigation_registry_tokens)
    if not ok_session:
        errors.extend([f"session.ts missing token: {token}" for token in missing_session])
    if not ok_home:
        errors.extend([f"HomeView.vue missing token: {token}" for token in missing_home])
    if not ok_shell:
        errors.extend([f"AppShell.vue missing token: {token}" for token in missing_shell])
    if not ok_action:
        errors.extend([f"ActionView.vue missing token: {token}" for token in missing_action])
    if not ok_record:
        errors.extend([f"RecordView.vue missing token: {token}" for token in missing_record])
    if not ok_scene:
        errors.extend([f"SceneView.vue missing token: {token}" for token in missing_scene])
    if not ok_workbench:
        errors.extend([f"WorkbenchView.vue missing token: {token}" for token in missing_workbench])
    if not ok_usage_analytics:
        errors.extend([f"UsageAnalyticsView.vue missing token: {token}" for token in missing_usage_analytics])
    if not ok_login:
        errors.extend([f"LoginView.vue missing token: {token}" for token in missing_login])
    if not ok_menu:
        errors.extend([f"MenuView.vue missing token: {token}" for token in missing_menu])
    if not ok_placeholder:
        errors.extend([f"PlaceholderView.vue missing token: {token}" for token in missing_placeholder])
    if not ok_scene_health:
        errors.extend([f"SceneHealthView.vue missing token: {token}" for token in missing_scene_health])
    if not ok_scene_packages:
        errors.extend([f"ScenePackagesView.vue missing token: {token}" for token in missing_scene_packages])
    if not ok_nav_registry:
        errors.extend([f"navigationRegistry.ts missing token: {token}" for token in missing_nav_registry])

    report = {
        "ok": len(errors) == 0,
        "summary": {
            "checked_files": 14,
            "error_count": len(errors),
            "contract_signals": {
                "capability_groups": "consumed" if ok_session else "missing",
                "ext_facts.product.license": "consumed" if ok_session else "missing",
                "ext_facts.product.bundle": "consumed" if ok_session else "missing",
                "home_product_surface": "rendered" if ok_home else "missing",
                "action_section_governance": "rendered" if ok_action else "missing",
                "record_section_governance": "rendered" if ok_record else "missing",
                "scene_section_governance": "rendered" if ok_scene else "missing",
                "workbench_section_governance": "rendered" if ok_workbench else "missing",
                "usage_analytics_section_governance": "rendered" if ok_usage_analytics else "missing",
                "login_section_governance": "rendered" if ok_login else "missing",
                "menu_section_governance": "rendered" if ok_menu else "missing",
                "placeholder_section_governance": "rendered" if ok_placeholder else "missing",
                "scene_health_section_governance": "rendered" if ok_scene_health else "missing",
                "scene_packages_section_governance": "rendered" if ok_scene_packages else "missing",
                "appshell_navigation_hud": "rendered" if ok_shell else "missing",
                "runtime_navigation_registry": "available" if ok_nav_registry else "missing",
                "capability_metadata_state_reason": "consumed" if ok_session and ok_home else "missing",
            },
        },
        "errors": errors,
    }

    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Frontend Product Contract Consumption Report",
        "",
        f"- ok: `{report['ok']}`",
        f"- checked_files: `{report['summary']['checked_files']}`",
        f"- error_count: `{report['summary']['error_count']}`",
        "",
        "## Contract Signals",
    ]
    for key, val in report["summary"]["contract_signals"].items():
        lines.append(f"- {key}: `{val}`")
    if errors:
        lines.extend(["", "## Errors"])
        lines.extend([f"- {err}" for err in errors])
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(REPORT_MD))
    print(str(REPORT_JSON))
    if errors:
        print("[frontend_product_contract_consumption_guard] FAIL")
        for err in errors:
            print(err)
        return 1

    print("[frontend_product_contract_consumption_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
