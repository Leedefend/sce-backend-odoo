#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Guard the frontend-to-backend form view scope chain."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_API = ROOT / "frontend/apps/web/src/api/contract.ts"
CONTRACT_FORM = ROOT / "frontend/apps/web/src/pages/ContractFormPage.vue"
RECORD_PAGE_LIFECYCLE = ROOT / "frontend/apps/web/src/pages/contractForm/useRecordPageLifecycle.ts"
UI_CONTRACT_V2 = ROOT / "addons/smart_core/handlers/ui_contract_v2.py"
PAGE_ASSEMBLER = ROOT / "addons/smart_core/app_config_engine/services/assemblers/page_assembler.py"
APP_VIEW_CONFIG = ROOT / "addons/smart_core/app_config_engine/models/app_view_config.py"
DOC = ROOT / "docs/audit/native/form_view_scope_runtime_chain_20260515.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _assert(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def main() -> int:
    errors: list[str] = []
    contract_api = _read(CONTRACT_API)
    contract_form = _read(CONTRACT_FORM)
    record_page_lifecycle = _read(RECORD_PAGE_LIFECYCLE)
    ui_contract_v2 = _read(UI_CONTRACT_V2)
    page_assembler = _read(PAGE_ASSEMBLER)
    app_view_config = _read(APP_VIEW_CONFIG)
    doc = _read(DOC)

    _assert("viewId?: number | null;" in contract_api, "contract API options must accept explicit viewId", errors)
    _assert("params.view_id = viewId;" in contract_api, "contract API must send view_id to ui.contract.v2", errors)
    _assert(
        "const requestedViewId = toPositiveInt(route.query.view_id) || toPositiveInt(route.query.viewId) || 0;" in record_page_lifecycle,
        "record page lifecycle must read route view_id/viewId",
        errors,
    )
    _assert(
        "viewId: requestedViewId || undefined" in record_page_lifecycle,
        "record page lifecycle must pass requested viewId into contract loaders",
        errors,
    )
    _assert(
        'params.get("view_id")' in ui_contract_v2 and 'params.get("viewId")' in ui_contract_v2,
        "ui.contract.v2 must preserve explicit view_id/viewId",
        errors,
    )
    _assert(
        'view_ids = source_contract.get("view_ids_by_type")' in ui_contract_v2,
        "ui.contract.v2 must recover action-selected view ids by view type",
        errors,
    )
    _assert(
        'view_context["contract_action_id"] = action.get("id")' in page_assembler,
        "PageAssembler must pass action scope into app.view.config",
        errors,
    )
    _assert(
        'scoped_view_context["contract_view_id"] = requested_view_id' in page_assembler,
        "PageAssembler must pass explicit view scope into app.view.config",
        errors,
    )
    _assert(
        'context.get(\'contract_action_id\')' in app_view_config
        and 'context.get(\'contract_view_id\') or context.get(\'requested_view_id\')' in app_view_config,
        "app.view.config projection identity must read action/view context",
        errors,
    )
    _assert(
        'Model.with_context(load_all_views=True).get_view(view_id=view_id, view_type=view_type)' in app_view_config,
        "app.view.config must load explicit source view through Odoo get_view",
        errors,
    )
    _assert(
        "低代码字段策略写入 `model/action_id/view_id/company_id`" in doc,
        "runtime chain document must state low-code write scope",
        errors,
    )

    if errors:
        print("[form_view_scope_runtime_chain_guard] FAIL")
        for error in errors:
            print(f" - {error}")
        return 1
    print("[form_view_scope_runtime_chain_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
