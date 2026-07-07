#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Static guard for current project scope contract coverage."""

from __future__ import annotations

import ast
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]

REQUIRED_SCOPE_FILES = {
    "addons/smart_core/handlers/api_data.py": ["apply_project_scope_domain", "selected_project_id_from_context"],
    "addons/smart_core/handlers/api_data_write.py": ["record_in_project_scope", "selected_project_id_from_context"],
    "addons/smart_core/handlers/api_data_batch.py": ["apply_project_scope_domain", "selected_project_id_from_context"],
    "addons/smart_core/handlers/api_data_unlink.py": ["apply_project_scope_domain", "selected_project_id_from_context"],
    "addons/smart_core/handlers/api_onchange.py": ["record_in_project_scope", "selected_project_id_from_context"],
    "addons/smart_core/handlers/chatter_post.py": ["record_in_project_scope", "selected_project_id_from_context"],
    "addons/smart_core/handlers/chatter_activity_schedule.py": ["record_in_project_scope", "selected_project_id_from_context"],
    "addons/smart_core/handlers/chatter_timeline.py": ["record_in_project_scope", "selected_project_id_from_context"],
    "addons/smart_core/handlers/execute_button.py": ["record_in_project_scope", "selected_project_id_from_context"],
    "addons/smart_core/handlers/file_upload.py": ["record_in_project_scope", "selected_project_id_from_context"],
    "addons/smart_core/handlers/file_download.py": ["record_in_project_scope", "selected_project_id_from_context"],
    "addons/smart_construction_core/handlers/my_work_summary.py": ["record_in_project_scope", "selected_project_id_from_context"],
    "addons/smart_construction_core/handlers/my_work_complete.py": ["record_in_project_scope", "selected_project_id_from_context"],
    "addons/smart_construction_core/handlers/payment_request_approval.py": ["record_in_project_scope", "selected_project_id_from_context"],
    "addons/smart_construction_core/handlers/payment_request_available_actions.py": ["record_in_project_scope", "selected_project_id_from_context"],
    "addons/smart_construction_core/handlers/risk_action_execute.py": ["record_in_project_scope", "selected_project_id_from_context"],
    "addons/smart_construction_core/handlers/project_execution_enter.py": ["selected_project_id_from_context"],
    "addons/smart_construction_core/handlers/project_execution_block_fetch.py": ["selected_project_id_from_context"],
    "addons/smart_construction_core/handlers/project_execution_advance.py": ["selected_project_id_from_context"],
    "addons/smart_construction_core/handlers/cost_tracking_enter.py": ["selected_project_id_from_context"],
    "addons/smart_construction_core/handlers/cost_tracking_block_fetch.py": ["selected_project_id_from_context"],
    "addons/smart_construction_core/handlers/cost_tracking_record_create.py": ["selected_project_id_from_context"],
    "addons/smart_construction_core/handlers/payment_slice_enter.py": ["selected_project_id_from_context"],
    "addons/smart_construction_core/handlers/payment_slice_block_fetch.py": ["selected_project_id_from_context"],
    "addons/smart_construction_core/handlers/payment_slice_record_create.py": ["selected_project_id_from_context"],
    "addons/smart_construction_core/handlers/settlement_slice_enter.py": ["selected_project_id_from_context"],
    "addons/smart_construction_core/handlers/settlement_slice_block_fetch.py": ["selected_project_id_from_context"],
    "addons/smart_construction_core/services/project_execution_item_projection_service.py": ["selected_project_id_from_context"],
}

REQUIRED_RUNTIME_IMPORT_FILES = {
    "addons/smart_construction_core/handlers/project_execution_advance.py": [
        "addons/smart_construction_core/services/project_execution_consistency_guard.py",
        "addons/smart_construction_core/services/project_execution_post_transition_service.py",
        "addons/smart_construction_core/services/project_execution_project_lookup_service.py",
        "addons/smart_construction_core/services/project_execution_request_service.py",
        "addons/smart_construction_core/services/project_execution_hint_service.py",
        "addons/smart_construction_core/services/project_execution_state_machine.py",
        "addons/smart_construction_core/services/project_execution_response_builder.py",
        "addons/smart_construction_core/services/project_execution_precheck_service.py",
        "addons/smart_construction_core/services/project_execution_task_transition_service.py",
        "addons/smart_construction_core/services/project_execution_transition_service.py",
    ],
    "addons/smart_construction_core/services/project_execution_service.py": [
        "addons/smart_construction_core/services/project_execution_builders/__init__.py",
        "addons/smart_construction_core/services/project_execution_builders/project_execution_tasks_builder.py",
        "addons/smart_construction_core/services/project_execution_builders/project_execution_next_actions_builder.py",
        "addons/smart_construction_core/services/project_execution_builders/project_execution_readiness_precheck_builder.py",
    ],
    "addons/smart_construction_core/services/cost_tracking_service.py": [
        "addons/smart_construction_core/services/cost_tracking_builders/__init__.py",
        "addons/smart_construction_core/services/cost_tracking_builders/cost_tracking_summary_builder.py",
        "addons/smart_construction_core/services/cost_tracking_builders/cost_tracking_next_actions_builder.py",
    ],
    "addons/smart_construction_core/services/payment_slice_service.py": [
        "addons/smart_construction_core/services/payment_slice_native_adapter.py",
        "addons/smart_construction_core/services/payment_slice_entry_service.py",
        "addons/smart_construction_core/services/payment_slice_builders/__init__.py",
        "addons/smart_construction_core/services/payment_slice_builders/payment_slice_summary_builder.py",
        "addons/smart_construction_core/services/payment_slice_builders/payment_slice_next_actions_builder.py",
    ],
    "addons/smart_construction_core/services/settlement_slice_service.py": [
        "addons/smart_construction_core/services/settlement_slice_builders/__init__.py",
        "addons/smart_construction_core/services/settlement_slice_builders/settlement_slice_summary_builder.py",
        "addons/smart_construction_core/services/settlement_slice_builders/settlement_slice_next_actions_builder.py",
    ],
    "addons/smart_construction_core/handlers/payment_slice_enter.py": [
        "addons/smart_core/orchestration/payment_slice_contract_orchestrator.py",
    ],
    "addons/smart_construction_core/handlers/settlement_slice_enter.py": [
        "addons/smart_core/orchestration/settlement_slice_contract_orchestrator.py",
    ],
}

REQUIRED_RUNTIME_REGISTRY_TOKENS = {
    "addons/smart_construction_core/core_extension.py": [
        "project.execution.advance",
        "ProjectExecutionAdvanceHandler",
        "payment.request.available_actions",
        "PaymentRequestAvailableActionsHandler",
        "risk.action.execute",
        "RiskActionExecuteHandler",
        "cost.tracking.enter",
        "CostTrackingEnterHandler",
        "cost.tracking.block.fetch",
        "CostTrackingBlockFetchHandler",
        "cost.tracking.record.create",
        "CostTrackingRecordCreateHandler",
        "payment.enter",
        "PaymentSliceEnterHandler",
        "payment.block.fetch",
        "PaymentSliceBlockFetchHandler",
        "payment.record.create",
        "PaymentSliceRecordCreateHandler",
        "settlement.enter",
        "SettlementSliceEnterHandler",
        "settlement.block.fetch",
        "SettlementSliceBlockFetchHandler",
    ],
}

CLASSIFICATION_DOC = "docs/architecture/current_project_scope_contract_matrix_v1.md"


def _intent_types(path: Path) -> list[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    intents: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        for stmt in node.body:
            if not isinstance(stmt, ast.Assign):
                continue
            for target in stmt.targets:
                if isinstance(target, ast.Name) and target.id == "INTENT_TYPE" and isinstance(stmt.value, ast.Constant):
                    intents.append(str(stmt.value.value))
    return sorted(set(intents))


def main() -> int:
    failures: list[dict] = []
    rows: list[dict] = []
    for rel_path, required_tokens in sorted(REQUIRED_SCOPE_FILES.items()):
        path = REPO_ROOT / rel_path
        text = path.read_text(encoding="utf-8") if path.exists() else ""
        missing = [token for token in required_tokens if token not in text]
        row = {
            "path": rel_path,
            "intents": _intent_types(path) if path.exists() else [],
            "required_tokens": required_tokens,
            "missing": missing,
            "ok": not missing,
        }
        rows.append(row)
        if missing:
            failures.append(row)

    runtime_imports: list[dict] = []
    for owner_path, dependency_paths in sorted(REQUIRED_RUNTIME_IMPORT_FILES.items()):
        missing = [dep for dep in dependency_paths if not (REPO_ROOT / dep).exists()]
        row = {
            "path": owner_path,
            "required_runtime_files": dependency_paths,
            "missing": missing,
            "ok": not missing,
        }
        runtime_imports.append(row)
        if missing:
            failures.append(row)

    runtime_registry: list[dict] = []
    for rel_path, required_tokens in sorted(REQUIRED_RUNTIME_REGISTRY_TOKENS.items()):
        path = REPO_ROOT / rel_path
        text = path.read_text(encoding="utf-8") if path.exists() else ""
        missing = [token for token in required_tokens if token not in text]
        row = {
            "path": rel_path,
            "required_registry_tokens": required_tokens,
            "missing": missing,
            "ok": not missing,
        }
        runtime_registry.append(row)
        if missing:
            failures.append(row)

    doc_path = REPO_ROOT / CLASSIFICATION_DOC
    if not doc_path.exists():
        failures.append({"path": CLASSIFICATION_DOC, "missing": ["classification_doc"], "ok": False})

    result = {
        "ok": not failures,
        "classification_doc": CLASSIFICATION_DOC,
        "checked_files": rows,
        "runtime_imports": runtime_imports,
        "runtime_registry": runtime_registry,
        "failures": failures,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
