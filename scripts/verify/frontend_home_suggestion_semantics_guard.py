#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
HOME_VIEW = ROOT / "frontend/apps/web/src/views/HomeView.vue"
SESSION_STORE = ROOT / "frontend/apps/web/src/stores/session.ts"
SYSTEM_INIT = ROOT / "addons/smart_core/handlers/system_init.py"
WORKSPACE_BUILDER = ROOT / "addons/smart_core/core/workspace_home_contract_builder.py"
REPORT_JSON = ROOT / "artifacts/backend/frontend_home_suggestion_semantics_report.json"
REPORT_MD = ROOT / "docs/ops/audit/frontend_home_suggestion_semantics_report.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.is_file() else ""


def main() -> int:
    errors: list[str] = []
    home_text = _read(HOME_VIEW)
    session_text = _read(SESSION_STORE)
    handler_text = _read(SYSTEM_INIT)
    builder_text = _read(WORKSPACE_BUILDER)

    if not home_text:
        errors.append(f"missing file: {HOME_VIEW.relative_to(ROOT).as_posix()}")
    if not session_text:
        errors.append(f"missing file: {SESSION_STORE.relative_to(ROOT).as_posix()}")
    if not handler_text:
        errors.append(f"missing file: {SYSTEM_INIT.relative_to(ROOT).as_posix()}")
    if not builder_text:
        errors.append(f"missing file: {WORKSPACE_BUILDER.relative_to(ROOT).as_posix()}")

    required_home_tokens = [
        "const workspaceHome = computed(() => (session.workspaceHome || {}) as Record<string, unknown>);",
        "workspaceHome.value.layout",
        "homeLayoutText(",
        "isHomeSectionEnabled(",
        "Array.isArray(workspaceHome.value.metrics)",
        "Array.isArray(workspaceHome.value.today_actions)",
        "workspaceHome.value.risk",
        "workspaceHome.value.ops",
        "Array.isArray(workspaceHome.value.advice)",
    ]
    forbidden_home_tokens = [
        "fetchMyWorkSummary",
        "listRecords(",
        "mode = ref<'live' | 'demo'>",
        "demoStories",
        "demoSummarySeed",
        "fetchCoreMetrics(",
    ]
    required_session_tokens = [
        "workspaceHome: WorkspaceHomeContract | null;",
        "this.workspaceHome = ((result as AppInitResponse & { workspace_home?: WorkspaceHomeContract }).workspace_home ?? null);",
    ]
    required_backend_tokens = [
        "from odoo.addons.smart_core.core.workspace_home_contract_builder import build_workspace_home_contract",
        "data[\"workspace_home\"] = build_workspace_home_contract(data)",
    ]
    required_builder_tokens = [
        "\"layout\":",
        "\"sections\":",
        "\"texts\":",
        "\"actions\":",
        "\"metrics\":",
        "\"today_actions\":",
        "\"risk\":",
        "\"ops\":",
        "\"advice\":",
    ]

    for token in required_home_tokens:
        if token not in home_text:
            errors.append(f"HomeView.vue missing token: {token}")
    for token in forbidden_home_tokens:
        if token in home_text:
            errors.append(f"HomeView.vue forbidden token present: {token}")
    for token in required_session_tokens:
        if token not in session_text:
            errors.append(f"session.ts missing token: {token}")
    for token in required_backend_tokens:
        if token not in handler_text:
            errors.append(f"system_init.py missing token: {token}")
    for token in required_builder_tokens:
        if token not in builder_text:
            errors.append(f"workspace_home_contract_builder.py missing token: {token}")

    report = {
        "ok": len(errors) == 0,
        "summary": {
            "checked_files": [
                HOME_VIEW.relative_to(ROOT).as_posix(),
                SESSION_STORE.relative_to(ROOT).as_posix(),
                SYSTEM_INIT.relative_to(ROOT).as_posix(),
                WORKSPACE_BUILDER.relative_to(ROOT).as_posix(),
            ],
            "error_count": len(errors),
            "contract_boundary": "workspace_home_only",
        },
        "errors": errors,
    }
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Frontend Home Contract Boundary Report",
        "",
        f"- ok: `{report['ok']}`",
        f"- checked_files: `{len(report['summary']['checked_files'])}`",
        f"- contract_boundary: `{report['summary']['contract_boundary']}`",
        f"- error_count: `{report['summary']['error_count']}`",
    ]
    if errors:
        lines.extend(["", "## Errors"])
        lines.extend([f"- {err}" for err in errors])
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(REPORT_MD))
    print(str(REPORT_JSON))
    if errors:
        print("[frontend_home_contract_boundary_guard] FAIL")
        for err in errors:
            print(err)
        return 1

    print("[frontend_home_contract_boundary_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
