#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import importlib.util
import re
import sys
import types
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LIST_VIEW_MODES = {"tree", "list"}
REQUIRED_CONTRACT_ACTIONS = {
    "action_construction_contract": "construction.contract",
    "action_construction_contract_my": "construction.contract",
    "action_construction_contract_income": "construction.contract.income",
    "action_construction_contract_expense": "construction.contract.expense",
    "action_sc_general_contract": "sc.general.contract",
    "action_sc_tier_review_my_construction_contract": "construction.contract",
    "action_sc_tier_review_my_general_contract": "sc.general.contract",
}
REQUIRED_ARCHIVE_MODELS = {
    "construction.contract": "addons/smart_construction_core/models/support/contract_center.py",
    "sc.general.contract": "addons/smart_construction_core/models/core/general_contract.py",
}
BASE_ACTIVE_MODELS = {
    "hr.department",
    "project.project",
    "res.partner",
    "res.users",
}
DELEGATED_ACTIVE_MODELS = {
    "construction.contract.income",
    "construction.contract.expense",
}
READONLY_OR_PROJECTION_PREFIXES = (
    "sc.legacy.",
    "sc.dashboard.",
    "sc.edition.",
    "sc.login.",
    "sc.norm.",
    "sc.ops.",
    "sc.product.",
    "sc.release.",
    "sc.subscription",
    "sc.usage.",
    "sc.workbench.",
)
READONLY_OR_PROJECTION_MODELS = {
    "payment.ledger",
    "project.cost.compare",
    "project.cost.ledger",
    "project.profit.compare",
    "sc.account.income.expense.summary",
    "sc.ar.ap.company.summary",
    "sc.ar.ap.project.summary",
    "sc.company.operation.summary",
    "sc.company.contractor.responsibility.fact",
    "sc.comprehensive.cost.summary",
    "sc.expense.reimbursement.summary",
    "sc.finance.business.fact",
    "sc.finance.project.capital.position",
    "sc.finance.project.counterparty.position",
    "sc.fund.daily.summary",
    "sc.interfund.movement.fact",
    "sc.invoice.category.summary",
    "sc.labor.settlement.candidate",
    "sc.material.stock.summary",
    "sc.operating.metrics.project",
    "sc.output.invoice.adjustment",
    "sc.p1.relationship.review.queue",
    "sc.p1.relationship.suggestion",
    "sc.partner.business.fact.line",
    "sc.entitlement",
    "sc.scene.company.channel",
    "sc.scene.governance.log",
    "sc.scene.snapshot",
    "sc.salary.summary",
    "sc.treasury.ledger",
    "tier.review",
    "ui.form.field.policy",
}


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def _load_contract_governance():
    smart_core_root = ROOT / "addons" / "smart_core"
    for name, path in [
        ("addons", ROOT / "addons"),
        ("addons.smart_core", smart_core_root),
        ("addons.smart_core.utils", smart_core_root / "utils"),
    ]:
        module = types.ModuleType(name)
        module.__path__ = [str(path)]
        sys.modules[name] = module
    module_name = "addons.smart_core.utils.contract_governance"
    spec = importlib.util.spec_from_file_location(
        module_name,
        smart_core_root / "utils" / "contract_governance.py",
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _assert(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def _runtime_batch_policy(contract: dict) -> dict:
    list_profile = contract.get("list_profile") if isinstance(contract.get("list_profile"), dict) else {}
    surface_policies = contract.get("surface_policies") if isinstance(contract.get("surface_policies"), dict) else {}
    profile_policy = list_profile.get("batch_policy") if isinstance(list_profile.get("batch_policy"), dict) else {}
    surface_policy = surface_policies.get("batch_policy") if isinstance(surface_policies.get("batch_policy"), dict) else {}
    return profile_policy or surface_policy


def _iter_xml_act_window_actions() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in sorted((ROOT / "addons").rglob("*.xml")):
        try:
            root = ET.parse(path).getroot()
        except Exception:
            continue
        for record in root.iter("record"):
            if record.attrib.get("model") != "ir.actions.act_window":
                continue
            row = {
                "id": record.attrib.get("id", ""),
                "path": str(path.relative_to(ROOT)),
                "name": "",
                "model": "",
                "view_mode": "",
            }
            for field in record.findall("field"):
                name = field.attrib.get("name")
                text = (field.text or "").strip()
                if name == "name":
                    row["name"] = text
                elif name == "res_model":
                    row["model"] = text
                elif name == "view_mode":
                    row["view_mode"] = text
                elif name == "views":
                    row["view_mode"] = row["view_mode"] or "tree,form"
            rows.append(row)
    return rows


def _collect_models_with_active_field() -> set[str]:
    out = set(BASE_ACTIVE_MODELS) | set(DELEGATED_ACTIVE_MODELS)
    for path in sorted((ROOT / "addons" / "smart_construction_core").rglob("*.py")):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for match in re.finditer(r'_(?:name|inherit)\s*=\s*["\']([^"\']+)["\']', text):
            model = match.group(1)
            start = match.start()
            end = text.find("\nclass ", start + 1)
            block = text[start : end if end != -1 else len(text)]
            header_start = text.rfind("\nclass ", 0, start)
            header_end = text.find(":", header_start if header_start != -1 else 0)
            header = text[header_start:header_end] if header_start != -1 and header_end != -1 else ""
            if re.search(r"\bactive\s*=\s*fields\.Boolean", block) or "_ListBatchArchiveFieldMixin" in header:
                out.add(model)
    return out


def _is_readonly_or_projection_model(model: str) -> bool:
    if model in READONLY_OR_PROJECTION_MODELS:
        return True
    if any(model.startswith(prefix) for prefix in READONLY_OR_PROJECTION_PREFIXES):
        return True
    return model.endswith(".summary") or ".summary" in model


def _is_business_list_model(model: str) -> bool:
    if _is_readonly_or_projection_model(model):
        return False
    return model.startswith((
        "construction.",
        "payment.",
        "project.",
        "purchase.",
        "sc.",
        "tender.",
    )) or model in BASE_ACTIVE_MODELS


def _action_has_list_view(row: dict[str, str]) -> bool:
    modes = {
        item.strip().lower()
        for item in (row.get("view_mode") or "tree,form").split(",")
        if item.strip()
    }
    return bool(modes & LIST_VIEW_MODES)


def _probe_contract_governance(errors: list[str]) -> None:
    governance = _load_contract_governance()

    missing_active = {
        "head": {"model": "payment.request", "view_type": "tree"},
        "views": {"tree": {"columns": ["name"]}},
        "fields": {"name": {"string": "名称", "type": "char"}},
        "permissions": {"effective": {"rights": {"write": True, "unlink": True}}},
        "surface_policies": {
            "delete_mode": "none",
            "batch_policy": {
                "enabled": True,
                "available_actions": ["archive", "activate"],
            },
        },
    }
    out = governance.apply_contract_governance(missing_active, "user")
    batch_policy = _runtime_batch_policy(out)
    _assert(batch_policy.get("enabled") is False, "archive/activate must be disabled when active field is absent", errors)
    _assert(batch_policy.get("available_actions") == [], "available_actions must be empty when no batch action is executable", errors)

    delete_only = {
        "head": {"model": "sc.expense.claim", "view_type": "tree,form"},
        "views": {"tree": {"columns": ["name"]}},
        "fields": {"name": {"string": "名称", "type": "char"}},
        "permissions": {"effective": {"rights": {"write": True, "unlink": True}}},
        "delete_policy": {"allowed": True, "delete_mode": "unlink"},
        "surface_policies": {
            "delete_mode": "unlink",
            "batch_policy": {
                "enabled": False,
                "available_actions": [],
            },
        },
    }
    out = governance.apply_contract_governance(delete_only, "user")
    batch_policy = _runtime_batch_policy(out)
    _assert(batch_policy.get("enabled") is True, "delete-only list policy should be enabled when unlink is allowed", errors)
    _assert(batch_policy.get("delete_mode") == "unlink", "delete-only list policy must preserve unlink mode", errors)
    _assert(batch_policy.get("available_actions") == ["delete"], "delete-only list policy must expose delete without active field", errors)

    executable = {
        "head": {"model": "payment.request", "view_type": "tree"},
        "views": {"tree": {"columns": ["name", "active"]}},
        "fields": {
            "name": {"string": "名称", "type": "char"},
            "active": {"string": "启用", "type": "boolean"},
        },
        "permissions": {"effective": {"rights": {"write": True, "unlink": True}}},
        "delete_policy": {"allowed": True, "delete_mode": "unlink"},
        "surface_policies": {
            "delete_mode": "unlink",
            "batch_policy": {
                "enabled": True,
                "available_actions": ["archive", "activate", "delete"],
            },
        },
    }
    out = governance.apply_contract_governance(executable, "user")
    batch_policy = _runtime_batch_policy(out)
    _assert(batch_policy.get("enabled") is True, "executable batch policy should stay enabled", errors)
    _assert(batch_policy.get("active_field") == "active", "active field should be preserved for archive/activate", errors)
    _assert(batch_policy.get("delete_mode") == "unlink", "delete mode should stay unlink when delete is executable", errors)
    _assert(
        batch_policy.get("available_actions") == ["archive", "activate", "delete"],
        "archive/activate/delete should be preserved when all are executable",
        errors,
    )

    contract_master = {
        "head": {"model": "construction.contract", "view_type": "tree"},
        "views": {"tree": {"columns": ["subject", "active"]}},
        "fields": {
            "subject": {"string": "合同标题", "type": "char"},
            "active": {"string": "有效", "type": "boolean"},
        },
        "permissions": {"effective": {"rights": {"write": True, "unlink": True}}},
        "delete_policy": {"allowed": True, "delete_mode": "unlink"},
        "surface_policies": {
            "delete_mode": "unlink",
            "batch_policy": {
                "enabled": True,
                "available_actions": ["archive", "activate", "delete"],
            },
        },
    }
    out = governance.apply_contract_governance(contract_master, "user")
    batch_policy = _runtime_batch_policy(out)
    _assert(
        batch_policy.get("available_actions") == ["archive", "activate", "delete"],
        "construction.contract list must expose archive/activate/delete when permissions allow",
        errors,
    )


def _probe_real_action_catalog(errors: list[str]) -> None:
    rows = _iter_xml_act_window_actions()
    active_models = _collect_models_with_active_field()
    by_id = {row.get("id"): row for row in rows if row.get("id")}
    list_actions = [row for row in rows if _action_has_list_view(row)]
    _assert(list_actions, "static action catalog must include at least one list/tree action", errors)
    for action_id, expected_model in REQUIRED_CONTRACT_ACTIONS.items():
        row = by_id.get(action_id)
        _assert(row is not None, f"required contract list action missing: {action_id}", errors)
        if not row:
            continue
        _assert(row.get("model") == expected_model, f"{action_id} must target {expected_model}", errors)
        _assert(_action_has_list_view(row), f"{action_id} must include tree/list view mode", errors)
    business_models = sorted({row.get("model", "") for row in list_actions if _is_business_list_model(row.get("model", ""))})
    missing_active = [model for model in business_models if model not in active_models]
    _assert(
        not missing_active,
        "business list models missing active field for batch archive: " + ", ".join(missing_active[:30]),
        errors,
    )


def _probe_real_model_archive_fields(errors: list[str]) -> None:
    for model, rel_path in REQUIRED_ARCHIVE_MODELS.items():
        source = _read(rel_path)
        _assert(
            "active = fields.Boolean" in source,
            f"{model} must define standard active field for list archive/activate",
            errors,
        )


def _probe_frontend_sources(errors: list[str]) -> None:
    list_page = _read("frontend/apps/web/src/pages/ListPage.vue")
    action_view = _read("frontend/apps/web/src/views/ActionView.vue")
    batch_flow = _read("frontend/apps/web/src/app/runtime/actionViewBatchActionFlowRuntime.ts")

    _assert(
        "const hasSelectionActions = computed(() => selectionActions.value.length > 0);" in list_page,
        "ListPage must compute hasSelectionActions",
        errors,
    )
    _assert(
        "const showSelectionColumn = computed(() => hasSelectionActions.value" in list_page,
        "ListPage selection column must be hidden when no batch action is executable",
        errors,
    )
    _assert(
        "action === 'delete' ? String(batchPolicy.value.delete_mode || 'none') === 'unlink' : Boolean(activeField.value)" in action_view,
        "ActionView must disable delete/archive buttons from batch policy guards",
        errors,
    )
    _assert(
        "const result = await unlinkActionViewRecord" in action_view,
        "ActionView batch delete must call unlinkActionViewRecord",
        errors,
    )
    _assert(
        "const result = await batchUpdateActionViewRecords" in action_view,
        "ActionView archive/activate must call batchUpdateActionViewRecords",
        errors,
    )
    _assert(
        "return resolveBatchActionGuard(" in batch_flow,
        "batch flow must use the shared guard decision",
        errors,
    )


def _probe_backend_handlers(errors: list[str]) -> None:
    batch = _read("addons/smart_core/handlers/api_data_batch.py")
    unlink = _read("addons/smart_core/handlers/api_data_unlink.py")
    _assert('"archive": {"active": False}' in batch, "api.data.batch must map archive to active=False", errors)
    _assert('"activate": {"active": True}' in batch, "api.data.batch must map activate to active=True", errors)
    _assert("env_model.check_access_rights(\"write\")" in batch, "api.data.batch must check write ACL", errors)
    _assert("rec.check_access_rule(\"write\")" in batch, "api.data.batch must check record write rule", errors)
    _assert("apply_project_scope_domain" in batch, "api.data.batch must enforce project scope", errors)
    _assert("resolve_idempotency_decision" in batch, "api.data.batch must keep idempotency", errors)
    _assert("resolve_unlink_policy" in unlink, "api.data.unlink must enforce delete_policy", errors)
    _assert("env_model.check_access_rights(\"unlink\")" in unlink, "api.data.unlink must check unlink ACL", errors)
    _assert("recs.check_access_rule(\"unlink\")" in unlink, "api.data.unlink must check record unlink rule", errors)
    _assert("dry_run = parse_bool" in unlink, "api.data.unlink must keep dry_run support", errors)


def main() -> int:
    errors: list[str] = []
    _probe_contract_governance(errors)
    _probe_real_action_catalog(errors)
    _probe_real_model_archive_fields(errors)
    _probe_frontend_sources(errors)
    _probe_backend_handlers(errors)
    if errors:
        print("[verify.list_batch_action.closure_guard] FAIL")
        for item in errors:
            print(f"- {item}")
        return 1
    print("[verify.list_batch_action.closure_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
