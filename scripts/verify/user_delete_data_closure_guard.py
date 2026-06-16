#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import csv
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(rel_path: str) -> str:
    return (ROOT / rel_path).read_text(encoding="utf-8")


def _assert(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def _action_model(xmlid: str) -> str:
    model = ""
    for path in sorted((ROOT / "addons" / "smart_construction_core" / "views").rglob("*.xml")):
        try:
            root = ET.parse(path).getroot()
        except Exception:
            continue
        for record in root.iter("record"):
            if record.attrib.get("id") != xmlid or record.attrib.get("model") != "ir.actions.act_window":
                continue
            for field in record.findall("field"):
                if field.attrib.get("name") == "res_model":
                    model = (field.text or "").strip()
    return model


def _probe_backend_unlink(errors: list[str]) -> None:
    source = _read("addons/smart_core/handlers/api_data_unlink.py")
    policy_source = _read("addons/smart_core/utils/delete_policy.py")
    assembler_source = _read("addons/smart_core/app_config_engine/services/assemblers/page_assembler.py")
    _assert("resolve_unlink_policy" in source, "api.data.unlink must be gated by delete_policy", errors)
    _assert("dry_run = parse_bool" in source, "api.data.unlink must keep dry_run support", errors)
    _assert("missing_ids = [rec_id for rec_id in ids if rec_id not in found_ids]" in source, "api.data.unlink must reject partial missing id sets", errors)
    _assert("return self._err(404, \"记录不存在\", REASON_NOT_FOUND)" in source, "partial missing unlink must fail as NOT_FOUND", errors)
    _assert("def _check_record_delete_policy" in source and "state_field" in source and "allowed_states" in source, "api.data.unlink must enforce record-state delete policy", errors)
    _assert("policy_error = self._check_record_delete_policy(recs, delete_policy)" in source, "api.data.unlink must check state policy before ACL/unlink execution", errors)
    _assert("if not dry_run:" in source and "recs.unlink()" in source, "dry_run must not call unlink", errors)
    _assert("\"deleted_count\": 0 if dry_run else len(set(ids))" in source, "unlink result must expose deleted_count", errors)
    _assert('"state_field"' in policy_source and '"allowed_states"' in policy_source, "delete_policy normalization must preserve state-limited policy metadata", errors)
    _assert(
        '"unlink": env[model].check_access_rights("unlink", raise_exception=False)' in assembler_source
        and 'effective_rights.update(' in assembler_source,
        "page contract effective rights must sync unlink from Odoo runtime ACL",
        errors,
    )


def _probe_business_delete_policy_scope(errors: list[str]) -> None:
    source = _read("addons/smart_construction_core/core_extension.py")
    tree = ast.parse(source)
    policy_models: set[str] = set()
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == "API_DATA_UNLINK_POLICIES" for target in node.targets):
            continue
        policies = ast.literal_eval(node.value)
        policy_models = {str(model) for model in policies}
    required_physical_delete_models = {
        "construction.contract",
        "construction.contract.income",
        "construction.contract.expense",
        "payment.request",
        "payment.request.line",
        "project.task",
        "project.tags",
        "res.partner",
        "sc.approval.policy",
        "sc.approval.step",
        "sc.document.admin.document",
        "sc.hr.payroll.document",
        "sc.office.admin.document",
        "sc.project.stage.requirement.item",
        "sc.supplier.type",
    }
    missing = sorted(required_physical_delete_models - policy_models)
    _assert(not missing, "business maintenance models missing explicit unlink policy: " + ", ".join(missing), errors)
    required_draft_models = {
        "payment.request",
        "sc.general.contract",
        "sc.expense.claim",
        "sc.financing.loan",
        "sc.invoice.registration",
        "sc.payment.execution",
        "sc.receipt.income",
        "sc.fund.account.operation",
        "sc.self.funding.registration",
        "sc.tax.deduction.registration",
        "sc.settlement.order",
        "sc.material.purchase.request",
        "project.material.plan",
        "sc.material.acceptance",
        "sc.material.inbound",
        "sc.material.outbound",
        "sc.material.rfq",
        "sc.material.settlement",
        "sc.labor.request",
        "sc.equipment.request",
        "sc.safety.plan",
        "sc.quality.issue",
        "sc.quality.rectification",
        "sc.quality.recheck",
        "sc.safety.rectification",
        "sc.safety.recheck",
        "project.progress.entry",
        "tender.bid",
        "tender.doc.purchase",
    }
    missing_draft = sorted(model for model in required_draft_models if f'"{model}"' not in source)
    _assert(not missing_draft, "draft-state business documents missing unlink policy: " + ", ".join(missing_draft), errors)
    acl_unlink_models: set[str] = set()
    with (ROOT / "addons" / "smart_construction_core" / "security" / "ir.model.access.csv").open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row.get("perm_unlink") != "1":
                continue
            model = str(row.get("model_id:id") or "").removeprefix("model_").replace("_", ".")
            acl_unlink_models.add(model)
    missing_acl = sorted(required_draft_models - acl_unlink_models)
    _assert(not missing_acl, "draft-state delete policies must remain backed by unlink ACLs: " + ", ".join(missing_acl), errors)
    _assert(
        "API_DATA_DRAFT_UNLINK_POLICIES" in source
        and "DRAFT_DELETE_ALLOWED_STATES" in source
        and '"state_field": state_field' in source
        and 'state_field: str = "state"' in source
        and 'state_field="issue_state"' in source
        and '"allowed_states": list(allowed_states)' in source
        and '"tender.bid": _state_unlink_policy("tender.bid", "投标主单", ("prepare", "estimating"))' in source,
        "business document delete policies must be centrally state-limited, with tender pre-submit states covered",
        errors,
    )
    _assert("project.project" not in policy_models, "project.project must not be in static all-user physical delete policy", errors)
    _assert(
        '"project.project"' in source
        and '"PROJECT_MASTER_DELETE_ALLOWED"' in source
        and '"dependency_guard": "project.project._raise_project_unlink_blockers"' in source,
        "project.project delete policy must be dynamically exposed and keep dependency guard metadata",
        errors,
    )
    _assert(
        '"requires_group": "smart_construction_core.group_sc_cap_business_config_admin"' not in source,
        "project.project delete policy must not add a group gate beyond ACL and record rules",
        errors,
    )
    project_source = _read("addons/smart_construction_core/models/core/project_core.py")
    _assert("def _raise_project_unlink_blockers" in project_source and "def unlink(self):" in project_source, "project.project must keep unlink dependency blockers", errors)
    _assert("self._raise_project_unlink_blockers()" in project_source, "project.project unlink must call dependency blocker guard", errors)
    _assert("project.cost.compare" not in policy_models and "payment.ledger" not in policy_models, "read-only ledgers/projections must not be physically deletable", errors)


def _probe_frontend_delete_flow(errors: list[str]) -> None:
    api = _read("frontend/apps/web/src/api/data.ts")
    flow = _read("frontend/apps/web/src/app/runtime/actionViewBatchActionFlowRuntime.ts")
    action_view = _read("frontend/apps/web/src/views/ActionView.vue")
    list_page = _read("frontend/apps/web/src/pages/ListPage.vue")
    shape_runtime = _read("frontend/apps/web/src/app/action_runtime/useActionViewContractShapeRuntime.ts")
    v2_adapter = _read("frontend/apps/web/src/app/runtime/unifiedPageContractV2CompatProjection.ts")
    v2_handler = _read("addons/smart_core/handlers/ui_contract_v2.py")
    _assert("dryRun?: boolean;" in api and "dry_run: Boolean(params.dryRun)" in api, "unlinkRecord must expose dryRun to api.data.unlink", errors)
    _assert("dryRunIdempotencyKey" in flow and "'delete.dry_run'" in flow, "batch delete must use a distinct dry-run idempotency key", errors)
    _assert("dryRun: true" in action_view, "ActionView batch delete must preflight with dryRun", errors)
    _assert("const result = await unlinkActionViewRecord" in action_view, "ActionView batch delete must still execute real unlink after preflight", errors)
    _assert("const hasSelectionActions = computed(() => selectionActions.value.length > 0);" in list_page, "ListPage must derive selection visibility from executable actions", errors)
    _assert("const showSelectionColumn = computed(() => hasSelectionActions.value" in list_page, "ListPage must hide selection column without delete/archive actions", errors)
    _assert(
        "Array.isArray(profilePolicy.available_actions) && profilePolicy.available_actions.length > 0" in action_view
        and "actionContract.value?.surface_policies?.batch_policy || profilePolicy || {}" in action_view,
        "ActionView batch policy must fall back to surface policy when list_profile has no executable actions",
        errors,
    )
    _assert(
        "const hasRawBatchPolicy = Object.keys(rawBatchPolicy).length > 0;" in shape_runtime
        and "...(hasRawBatchPolicy ? { batch_policy: batchPolicy } : {})" in shape_runtime,
        "list_profile extraction must not synthesize an empty batch_policy that shadows surface policy",
        errors,
    )
    _assert("contract_v2[\"surface_policies\"]" in v2_handler, "ui.contract.v2 must carry governed surface batch policy", errors)
    _assert("const sourceSurfacePolicies = asDict(v2Contract.surface_policies);" in v2_adapter, "V2 adapter must consume backend surface policies", errors)
    _assert("sourceBatchPolicy.available_actions" in v2_adapter, "V2 adapter must prefer backend batch available_actions", errors)


def _probe_domain_action_binding(errors: list[str]) -> None:
    model = _action_model("action_construction_contract_expense")
    _assert(model == "construction.contract.expense", "action_construction_contract_expense must remain bound to editable expense contracts", errors)
    ledger = _action_model("action_sc_expense_contract_ledger_alias")
    _assert(ledger == "sc.expense.contract.ledger", "expense ledger alias action must stay separate from editable expense contract action", errors)


def main() -> int:
    errors: list[str] = []
    _probe_backend_unlink(errors)
    _probe_business_delete_policy_scope(errors)
    _probe_frontend_delete_flow(errors)
    _probe_domain_action_binding(errors)
    if errors:
        print("[verify.user_delete_data.closure_guard] FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[verify.user_delete_data.closure_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
