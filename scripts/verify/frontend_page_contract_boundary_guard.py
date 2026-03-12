#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
VIEWS_DIR = ROOT / "frontend/apps/web/src/views"
APP_SHELL = ROOT / "frontend/apps/web/src/layouts/AppShell.vue"
MENU_TREE = ROOT / "frontend/apps/web/src/components/MenuTree.vue"
ROUTER = ROOT / "frontend/apps/web/src/router/index.ts"

REPORT_JSON = ROOT / "artifacts/backend/frontend_page_contract_boundary_report.json"
REPORT_MD = ROOT / "docs/ops/audit/frontend_page_contract_boundary_report.md"
WORKSPACE_HOME_BUILDER = ROOT / "addons/smart_core/core/workspace_home_contract_builder.py"
PAGE_CONTRACTS_BUILDER = ROOT / "addons/smart_core/core/page_contracts_builder.py"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.is_file() else ""


def _check_required(text: str, tokens: list[str], scope: str, errors: list[str]) -> None:
    for token in tokens:
        if token not in text:
            errors.append(f"{scope}: missing token: {token}")


def _check_forbidden(text: str, tokens: list[str], scope: str, errors: list[str]) -> None:
    for token in tokens:
        if token in text:
            errors.append(f"{scope}: forbidden token present: {token}")


def main() -> int:
    errors: list[str] = []
    scanned: list[str] = []

    view_files = sorted(VIEWS_DIR.glob("*.vue"))
    expected_views = {
        "ActionView.vue",
        "HomeView.vue",
        "LoginView.vue",
        "MenuView.vue",
        "MyWorkView.vue",
        "PlaceholderView.vue",
        "ProjectManagementDashboardView.vue",
        "RecordView.vue",
        "SceneHealthView.vue",
        "ScenePackagesView.vue",
        "SceneView.vue",
        "UsageAnalyticsView.vue",
        "WorkbenchView.vue",
    }
    actual_views = {path.name for path in view_files}
    missing_views = sorted(expected_views - actual_views)
    extra_views = sorted(actual_views - expected_views)
    if missing_views:
        errors.append(f"views missing from boundary matrix: {', '.join(missing_views)}")
    if extra_views:
        errors.append(f"new views not yet covered by boundary matrix: {', '.join(extra_views)}")

    router_text = _read(ROUTER)
    if not router_text:
        errors.append("router missing: frontend/apps/web/src/router/index.ts")
    else:
        _check_required(
            router_text,
            [
                "component: HomeView",
                "component: SceneView",
                "component: ActionView",
                "component: ContractFormPage",
            ],
            "router/index.ts",
            errors,
        )
        _check_forbidden(
            router_text,
            [
                "component: ModelFormPage",
                "component: ModelListPage",
            ],
            "router/index.ts",
            errors,
        )

    global_forbidden_tokens = [
        "config/scenesCore",
        "config/scenes'",
        'config/scenes"',
        "path: '/projects'",
        "path: '/projects/:id'",
        "demoSummarySeed",
        "mode = ref<'live' | 'demo'>",
        "fetchCoreMetrics(",
    ]

    page_contract_exempt_views = {
        "ProjectManagementDashboardView.vue",
    }

    for view in view_files:
        text = _read(view)
        rel = view.relative_to(ROOT).as_posix()
        scanned.append(rel)
        if not text:
            errors.append(f"{rel}: unreadable")
            continue
        if "usePageContract(" not in text and view.name not in page_contract_exempt_views:
            errors.append(f"{rel}: missing token: usePageContract(")
        _check_forbidden(text, global_forbidden_tokens, rel, errors)
        if view.name != "ActionView.vue":
            _check_forbidden(text, ["listRecords("], rel, errors)

    per_view_required = {
        "LoginView.vue": [
            "await session.loadAppInit();",
            "session.resolveLandingPath('/')",
            "pageSectionEnabled(",
            "pageSectionStyle(",
            "pageSectionTagIs(",
            "pageSectionEnabled('card', true)",
            "pageSectionEnabled('form', true)",
        ],
        "HomeView.vue": [
            "session.workspaceHome",
            "workspaceHome.value.layout",
            "homeLayoutText(",
            "isHomeSectionEnabled(",
            "isHomeSectionTag(",
            "isHomeSectionOpenDefault(",
            "homeSectionOrderMap",
            "homeSectionStyle('hero')",
            "homeSectionStyle('metrics')",
            "homeSectionStyle('scene_groups')",
            "isHomeSectionTag('hero', 'header')",
            "isHomeSectionTag('ops', 'details')",
            "isHomeSectionOpenDefault('ops')",
            "isHomeSectionOpenDefault('advice')",
            "Array.isArray(workspaceHome.value.metrics)",
            "Array.isArray(workspaceHome.value.today_actions)",
            "keywordList('todo_keywords_approval'",
            "keywordList('todo_keywords_contract'",
            "keywordList('todo_keywords_risk'",
            "keywordList('todo_keywords_change'",
            "keywordList('todo_keywords_overdue'",
            "keywordList('action_enter_keywords_approval'",
            "keywordList('action_enter_keywords_contract'",
            "keywordList('action_enter_keywords_risk'",
            "keywordList('action_enter_keywords_change'",
            "keywordList('action_enter_keywords_task'",
        ],
        "MenuView.vue": [
            "resolveMenuAction(",
            "evaluateCapabilityPolicy(",
            "pageSectionEnabled(",
            "pageSectionStyle(",
            "pageSectionTagIs(",
            "pageSectionEnabled('status_loading', true)",
            "pageSectionEnabled('status_error', true)",
        ],
        "PlaceholderView.vue": [
            "pageSectionEnabled(",
            "pageSectionStyle(",
            "pageSectionTagIs(",
            "pageSectionEnabled('card', true)",
        ],
        "SceneView.vue": [
            "getSceneByKey",
            "evaluateCapabilityPolicy(",
            "resolveVisibleActionTarget(",
            "pageSectionEnabled(",
            "pageSectionStyle(",
            "pageSectionTagIs(",
            "pageSectionEnabled('status_loading', true)",
            "pageSectionEnabled('status_error', true)",
            "pageSectionEnabled('status_forbidden', true)",
        ],
        "ActionView.vue": [
            "resolveAction(session.menuTree",
            "listRecords({",
            "pageSectionEnabled(",
            "pageSectionStyle(",
            "pageSectionTagIs(",
            "pageSectionEnabled('quick_filters', true)",
            "pageSectionEnabled('quick_actions', true)",
            "keywordList('surface_kind_keywords_risk'",
            "keywordList('surface_kind_keywords_contract'",
            "keywordList('surface_kind_keywords_cost'",
            "keywordList('surface_kind_keywords_project'",
            "keywordList('group_keywords_basic'",
            "keywordList('group_keywords_workflow'",
            "keywordList('group_keywords_drilldown'",
            "keywordList('columns_risk_bucket_identity'",
            "keywordList('columns_contract_bucket_amount'",
            "keywordList('columns_cost_bucket_execution'",
            "keywordList('columns_project_bucket_identity'",
        ],
        "RecordView.vue": [
            "contract-driven record view",
            "lastIntent.value = 'api.data.read'",
            "lastIntent.value = 'api.data.write'",
            "pageSectionEnabled(",
            "pageSectionStyle(",
            "pageSectionTagIs(",
            "pageSectionEnabled('project_summary', true)",
            "pageSectionEnabled('chatter', true)",
        ],
        "MyWorkView.vue": [
            "fetchMyWorkSummary",
            "completeMyWorkItem",
            "completeMyWorkItemsBatch",
        ],
        "WorkbenchView.vue": [
            "diagnostic-only surface",
            "pageText('message_act_unsupported_type'",
            "pageText('message_capability_missing'",
            "pageSectionEnabled(",
            "pageSectionStyle(",
            "pageSectionTagIs(",
            "pageSectionEnabled('header', true)",
            "pageSectionEnabled('status_panel', true)",
            "pageSectionEnabled('tiles', true)",
            "pageSectionEnabled('hud_details', true)",
        ],
        "SceneHealthView.vue": [
            "fetchSceneHealth",
            "governanceSetChannel",
            "pageSectionEnabled(",
            "pageSectionStyle(",
            "pageSectionOpenDefault(",
            "pageSectionTagIs(",
            "pageSectionEnabled('header', true)",
            "pageSectionEnabled('governance', true)",
            "pageSectionOpenDefault('details_resolve_errors', true)",
        ],
        "ScenePackagesView.vue": [
            "scenePackageImport",
            "scenePackageExport",
            "pageSectionEnabled(",
            "pageSectionStyle(",
            "pageSectionTagIs(",
            "pageSectionEnabled('installed_packages', true)",
            "pageSectionEnabled('import_package', true)",
            "pageSectionEnabled('export_package', true)",
        ],
        "UsageAnalyticsView.vue": [
            "fetchUsageReport",
            "exportUsageCsv",
            "pageSectionEnabled(",
            "pageSectionStyle(",
            "pageSectionTagIs(",
            "pageSectionEnabled('header', true)",
            "pageSectionEnabled('tables_top', true)",
            "pageSectionEnabled('tables_role_user', true)",
        ],
        "ProjectManagementDashboardView.vue": [
            "intentRequest<DashboardResponse>",
            "executePageContractAction",
            "PageRenderer",
        ],
    }
    per_view_forbidden = {
        "HomeView.vue": [
            "return '审核付款申请';",
            "return '查看合同异常';",
            "return '处理风险事项';",
            "return '确认变更事项';",
            "return '处理任务';",
            "return '查看详情';",
            "return '→ 0%';",
            "`T-${idx + 1}`",
            "includesAny(text, ['付款', '支付', 'approval', '审批'])",
            "includesAny(text, ['合同', 'contract'])",
            "includesAny(text, ['风险', 'risk'])",
            "includesAny(text, ['变更', 'change'])",
            "includesAny(text, ['逾期', '任务', 'todo'])",
            "includesAny(mergeText, ['payment', '付款', '支付', 'approval', '审批'])",
            "includesAny(mergeText, ['contract', '合同'])",
            "includesAny(mergeText, ['risk', '风险', '预警'])",
            "includesAny(mergeText, ['change', '变更'])",
            "includesAny(mergeText, ['task', '任务', 'todo', '待办'])",
        ],
        "ActionView.vue": [
            "if (key.includes('risk') || key.includes('风险')) return 'risk';",
            "if (key.includes('contract') || key.includes('合同')) return 'contract';",
            "if (key.includes('cost') || key.includes('成本')) return 'cost';",
            "if (key.includes('project') || key.includes('项目')) return 'project';",
            "const basic = all.filter((item) => /创建|保存|submit|create|save/i.test(item.label));",
            "const workflow = all.filter((item) => /阶段|审批|workflow|transition/i.test(item.label));",
            "const drilldown = all.filter((item) => /查看|列表|看板|open|view/i.test(item.label));",
            "pick(['title', 'name', '风险', '事项'])",
            "pick(['amount_total', 'contract_amount', '金额', '合同额'])",
            "pick(['cost', '执行率', 'rate'])",
            "pick(['title', 'name', '项目'])",
        ],
        "RecordView.vue": [
            ">Back<",
            ">Edit<",
            ">Save<",
            ">Cancel<",
            ">Reload<",
            ">Download<",
            "|| 'Ribbon'",
            "title=\"Record Context\"",
            "status.value === 'editing' ? 'Editing contract fields' : 'Record details'",
        ],
    }
    for name, tokens in per_view_required.items():
        target = VIEWS_DIR / name
        text = _read(target)
        if not text:
            errors.append(f"missing file: {target.relative_to(ROOT).as_posix()}")
            continue
        _check_required(text, tokens, target.relative_to(ROOT).as_posix(), errors)
    for name, tokens in per_view_forbidden.items():
        target = VIEWS_DIR / name
        text = _read(target)
        if not text:
            errors.append(f"missing file: {target.relative_to(ROOT).as_posix()}")
            continue
        _check_forbidden(text, tokens, target.relative_to(ROOT).as_posix(), errors)

    app_shell_text = _read(APP_SHELL)
    menu_tree_text = _read(MENU_TREE)
    if not app_shell_text:
        errors.append("missing file: frontend/apps/web/src/layouts/AppShell.vue")
    else:
        _check_forbidden(
            app_shell_text,
            [
                "fixture",
            ],
            "layouts/AppShell.vue",
            errors,
        )
    if not menu_tree_text:
        errors.append("missing file: frontend/apps/web/src/components/MenuTree.vue")
    else:
        _check_forbidden(menu_tree_text, ["fixture"], "components/MenuTree.vue", errors)

    workspace_home_builder_text = _read(WORKSPACE_HOME_BUILDER)
    if not workspace_home_builder_text:
        errors.append("missing file: addons/smart_core/core/workspace_home_contract_builder.py")
    else:
        _check_required(
            workspace_home_builder_text,
            [
                '"key": "hero", "enabled": True, "tag": "header"',
                '"key": "ops", "enabled": True, "tag": "details", "open": False',
                '"key": "advice", "enabled": True, "tag": "details", "open": False',
                '"key": "scene_groups", "enabled": True, "tag": "div"',
            ],
            "workspace_home_contract_builder.py",
            errors,
        )

    page_contracts_builder_text = _read(PAGE_CONTRACTS_BUILDER)
    if not page_contracts_builder_text:
        errors.append("missing file: addons/smart_core/core/page_contracts_builder.py")
    else:
        _check_required(
            page_contracts_builder_text,
            [
                '"action": {',
                '"sections": [',
                '"key": "quick_filters"',
                '"key": "quick_actions"',
                '"key": "status_loading"',
                '"key": "status_error"',
                '"key": "status_forbidden"',
                '"key": "status_panel"',
                '"key": "tables_top"',
                '"key": "tables_role_user"',
                '"key": "status_info"',
                '"key": "installed_packages"',
                '"key": "details_resolve_errors"',
                '"tag": "details", "open": True',
                '"record": {',
                '"key": "project_summary"',
                '"key": "chatter"',
            ],
            "page_contracts_builder.py",
            errors,
        )

    report = {
        "ok": len(errors) == 0,
        "summary": {
            "checked_views": len(scanned),
            "checked_layouts": 2,
            "error_count": len(errors),
            "boundary": "all-pages-contract-driven",
        },
        "scanned": scanned,
        "errors": errors,
    }
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# Frontend Page Contract Boundary Report",
        "",
        f"- ok: `{report['ok']}`",
        f"- checked_views: `{report['summary']['checked_views']}`",
        f"- checked_layouts: `{report['summary']['checked_layouts']}`",
        f"- boundary: `{report['summary']['boundary']}`",
        f"- error_count: `{report['summary']['error_count']}`",
        "",
        "## Scanned Views",
    ]
    for item in scanned:
        lines.append(f"- `{item}`")
    if errors:
        lines.extend(["", "## Errors"])
        lines.extend([f"- {err}" for err in errors])
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(REPORT_MD))
    print(str(REPORT_JSON))
    if errors:
        print("[frontend_page_contract_boundary_guard] FAIL")
        for err in errors:
            print(err)
        return 1
    print("[frontend_page_contract_boundary_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
