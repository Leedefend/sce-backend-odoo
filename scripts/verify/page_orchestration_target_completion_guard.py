#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]

SEMANTICS = ROOT / "addons/smart_core/core/orchestration_semantics.py"
PAGE_PROVIDER = ROOT / "addons/smart_core/core/page_orchestration_data_provider.py"
HOME_PROVIDER = ROOT / "addons/smart_core/core/workspace_home_data_provider.py"
PAGE_BUILDER = ROOT / "addons/smart_core/core/page_contracts_builder.py"
HOME_BUILDER = ROOT / "addons/smart_core/core/workspace_home_contract_builder.py"
HOME_VIEW = ROOT / "frontend/apps/web/src/views/HomeView.vue"
WORKBENCH_VIEW = ROOT / "frontend/apps/web/src/views/WorkbenchView.vue"
MY_WORK_VIEW = ROOT / "frontend/apps/web/src/views/MyWorkView.vue"
REGISTRY = ROOT / "frontend/apps/web/src/app/pageBlockRegistry.ts"
MAKEFILE = ROOT / "Makefile"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.is_file() else ""


def _fail(errors: list[str]) -> int:
    print("[page_orchestration_target_completion_guard] FAIL")
    for err in errors:
        print(f"- {err}")
    return 1


def _expect(scope: str, text: str, tokens: list[str], errors: list[str]) -> None:
    for token in tokens:
        if token not in text:
            errors.append(f"{scope} missing token: {token}")


def main() -> int:
    files = {
        "semantics": _read(SEMANTICS),
        "page_provider": _read(PAGE_PROVIDER),
        "home_provider": _read(HOME_PROVIDER),
        "page_builder": _read(PAGE_BUILDER),
        "home_builder": _read(HOME_BUILDER),
        "home_view": _read(HOME_VIEW),
        "workbench_view": _read(WORKBENCH_VIEW),
        "my_work_view": _read(MY_WORK_VIEW),
        "registry": _read(REGISTRY),
        "makefile": _read(MAKEFILE),
    }
    errors: list[str] = []

    for key, text in files.items():
        if not text:
            errors.append(f"missing/empty file for {key}")
    if errors:
        return _fail(errors)

    # 动作1：页面区块语义标准
    _expect(
        "orchestration_semantics.py",
        files["semantics"],
        [
            "BLOCK_TYPES",
            '"metric_row"',
            '"todo_list"',
            '"alert_panel"',
            '"entry_grid"',
            "STATE_TONES",
            "PROGRESS_STATES",
            '"pending"',
            '"blocked"',
            '"completed"',
            '"overdue"',
        ],
        errors,
    )
    _expect(
        "pageBlockRegistry.ts",
        files["registry"],
        [
            "metric_row",
            "todo_list",
            "alert_panel",
            "entry_grid",
            "record_summary",
            "progress_summary",
            "activity_feed",
            "accordion_group",
        ],
        errors,
    )

    # 动作2：页面编排契约（page/zones/blocks）与 provider-first
    _expect(
        "page_contracts_builder.py",
        files["page_builder"],
        [
            '"contract_version": "page_orchestration_v1"',
            '"page": {',
            '"zones": zones',
            '"data_sources": data_sources',
            '"state_schema": {',
            '"action_schema": {"actions": action_schema_actions},',
            'fn = getattr(provider, "build_base_data_sources", None)',
            'fn = getattr(provider, "build_section_data_source", None)',
            'fn = getattr(provider, "build_section_data_source_key", None)',
            'fn = getattr(provider, "build_zone_from_tag", None)',
            'fn = getattr(provider, "build_semantic_from_section", None)',
            'fn = getattr(provider, "build_action_templates", None)',
        ],
        errors,
    )
    _expect(
        "workspace_home_contract_builder.py",
        files["home_builder"],
        [
            '"page_orchestration_v1": _build_page_orchestration_v1(role_code, role_source_code=role_source_code)',
            '"page_orchestration": _build_page_orchestration(role_code, role_source_code=role_source_code)',
            'fn = getattr(provider, "build_v1_zones", None)',
            'fn = getattr(provider, "build_v1_page_profile", None)',
            'fn = getattr(provider, "build_v1_data_sources", None)',
            'fn = getattr(provider, "build_v1_state_schema", None)',
            'fn = getattr(provider, "build_v1_action_specs", None)',
            'zones_fn = getattr(provider, "build_legacy_zones", None)',
            'blocks_fn = getattr(provider, "build_legacy_blocks", None)',
        ],
        errors,
    )

    # 动作3：状态语义协议
    _expect(
        "page_orchestration_data_provider.py",
        files["page_provider"],
        [
            "def build_page_type(",
            "def build_page_audience(",
            "def build_default_page_actions(",
            "def build_role_zone_order(",
            "def build_role_focus_sections(",
        ],
        errors,
    )
    _expect(
        "workspace_home_data_provider.py",
        files["home_provider"],
        [
            "def build_v1_state_schema()",
            '"pending": {"tone": "warning", "label": "待处理"}',
            '"running": {"tone": "info", "label": "进行中"}',
            '"blocked": {"tone": "danger", "label": "已阻塞"}',
            '"completed": {"tone": "success", "label": "已完成"}',
            '"overdue": {"tone": "danger", "label": "已逾期"}',
        ],
        errors,
    )

    # 动作4：角色态页面裁剪 + 前端统一渲染默认路径
    _expect(
        "HomeView.vue",
        files["home_view"],
        [
            "<PageRenderer",
            'v-if="useUnifiedHomeRenderer"',
            "route.query.legacy_home",
            "return hasV1 && isDashboard && zones.length > 0;",
        ],
        errors,
    )
    _expect(
        "WorkbenchView.vue",
        files["workbench_view"],
        [
            "<PageRenderer",
            'v-if="useUnifiedWorkbenchRenderer"',
            "route.query.legacy_workbench",
            "return hasV1 && zones.length > 0;",
        ],
        errors,
    )
    _expect(
        "MyWorkView.vue",
        files["my_work_view"],
        [
            "<PageRenderer",
            'v-if="useUnifiedMyWorkRenderer"',
            "route.query.legacy_my_work",
            "return hasV1 && zones.length > 0;",
        ],
        errors,
    )

    _expect(
        "Makefile",
        files["makefile"],
        [
            "verify.frontend.page_block_renderer_smoke",
            "verify.frontend.portal_dashboard_block_migration",
            "verify.frontend.workbench_block_migration",
            "verify.frontend.my_work_block_migration",
            "verify.frontend.page_block_registry_guard",
            "verify.frontend.page_legacy_renderer_residue_guard",
            "verify.frontend.page_renderer_default_guard",
            "verify.workspace_home.provider_split.guard",
            "verify.page_contract.provider_split.guard",
            "verify.page_contract.semantic_provider_split.guard",
            "verify.page_contract.strategy_provider_split.guard",
            "verify.page_contract.role_strategy_provider_split.guard",
            "verify.page_contract.role_orchestration_variance.guard",
        ],
        errors,
    )

    if errors:
        return _fail(errors)

    print("[page_orchestration_target_completion_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
