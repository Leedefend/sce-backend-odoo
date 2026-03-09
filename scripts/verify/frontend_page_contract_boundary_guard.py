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

    for view in view_files:
        text = _read(view)
        rel = view.relative_to(ROOT).as_posix()
        scanned.append(rel)
        if not text:
            errors.append(f"{rel}: unreadable")
            continue
        _check_forbidden(text, global_forbidden_tokens, rel, errors)
        if view.name != "ActionView.vue":
            _check_forbidden(text, ["listRecords("], rel, errors)

    per_view_required = {
        "LoginView.vue": [
            "await session.loadAppInit();",
            "session.resolveLandingPath('/')",
        ],
        "HomeView.vue": [
            "session.workspaceHome",
            "workspaceHome.value.layout",
            "homeLayoutText(",
            "isHomeSectionEnabled(",
            "Array.isArray(workspaceHome.value.metrics)",
            "Array.isArray(workspaceHome.value.today_actions)",
        ],
        "MenuView.vue": [
            "resolveMenuAction(",
            "evaluateCapabilityPolicy(",
        ],
        "SceneView.vue": [
            "getSceneByKey",
            "evaluateCapabilityPolicy(",
            "resolveVisibleActionTarget(",
        ],
        "ActionView.vue": [
            "resolveAction(session.menuTree",
            "listRecords({",
        ],
        "RecordView.vue": [
            "contract-driven record view",
            "lastIntent.value = 'api.data.read'",
            "lastIntent.value = 'api.data.write'",
        ],
        "MyWorkView.vue": [
            "fetchMyWorkSummary",
            "completeMyWorkItem",
            "completeMyWorkItemsBatch",
        ],
        "WorkbenchView.vue": [
            "diagnostic-only surface",
            "当前动作类型暂未在门户壳层支持。",
            "当前账号尚未开通该能力。",
        ],
        "SceneHealthView.vue": [
            "fetchSceneHealth",
            "governanceSetChannel",
        ],
        "ScenePackagesView.vue": [
            "scenePackageImport",
            "scenePackageExport",
        ],
        "UsageAnalyticsView.vue": [
            "fetchUsageReport",
            "exportUsageCsv",
        ],
    }
    for name, tokens in per_view_required.items():
        target = VIEWS_DIR / name
        text = _read(target)
        if not text:
            errors.append(f"missing file: {target.relative_to(ROOT).as_posix()}")
            continue
        _check_required(text, tokens, target.relative_to(ROOT).as_posix(), errors)

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
