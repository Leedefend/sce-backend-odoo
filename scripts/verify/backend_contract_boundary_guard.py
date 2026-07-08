#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BOUNDARY_MODULE_PATH = ROOT / "addons" / "smart_core" / "utils" / "backend_contract_boundaries.py"


def _load_boundary_constants() -> dict:
    spec = importlib.util.spec_from_file_location("backend_contract_boundaries", BOUNDARY_MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return {
        "LOWCODE_SOURCE_STATUS_TENANT_RUNTIME": module.LOWCODE_SOURCE_STATUS_TENANT_RUNTIME,
        "LOWCODE_SYSTEM_CONFIG_MENU_XMLIDS": module.LOWCODE_SYSTEM_CONFIG_MENU_XMLIDS,
        "VIEW_ORCHESTRATION_SOURCE_FIELD_POLICY": module.VIEW_ORCHESTRATION_SOURCE_FIELD_POLICY,
        "MENU_ORCHESTRATION_SOURCE_TENANT_LOWCODING": module.MENU_ORCHESTRATION_SOURCE_TENANT_LOWCODING,
        "MENU_CONFIG_POLICY_MODEL": module.MENU_CONFIG_POLICY_MODEL,
        "APPROVAL_POLICY_SOURCE_TENANT_LOWCODING": module.APPROVAL_POLICY_SOURCE_TENANT_LOWCODING,
    }


BOUNDARY_CONSTANTS = _load_boundary_constants()
ALLOWED_DIRECT_CONTRACT_WRITERS = {
    "addons/smart_core/model/ui_business_config_contract.py": {
        "layer": "L1",
        "boundary": "contract_infrastructure",
        "reason": "owns ui.business.config.contract persistence and versioning",
        "expected_source": "n/a",
    },
    "addons/smart_core/handlers/form_field_configuration.py": {
        "layer": "L4",
        "boundary": "form_lowcode_runtime_config",
        "reason": "mirrors form field low-code edits into view orchestration contracts",
        "expected_source": BOUNDARY_CONSTANTS["VIEW_ORCHESTRATION_SOURCE_FIELD_POLICY"],
    },
    "addons/smart_core/handlers/menu_configuration.py": {
        "layer": "L4",
        "boundary": "menu_lowcode_runtime_config",
        "reason": "mirrors menu low-code edits into menu orchestration contracts",
        "expected_source": BOUNDARY_CONSTANTS["MENU_ORCHESTRATION_SOURCE_TENANT_LOWCODING"],
    },
    "addons/smart_construction_custom/models/user_preferences.py": {
        "layer": "L3",
        "boundary": "user_preference_projection",
        "reason": "initializes customer-specific menu and form preferences",
        "expected_source": "smart_construction_custom.*preference",
    },
    "addons/smart_construction_core/models/support/formal_list_contract_sync.py": {
        "layer": "L2",
        "boundary": "industry_formal_list_contract_projection",
        "reason": "upgrades released industry list contracts from transition fields to formal product fields",
        "expected_source": "smart_construction_core.formal_settlement_list_contract_sync",
    },
    "addons/smart_construction_core/migrations/17.0.0.61/post-migration.py": {
        "layer": "L2",
        "boundary": "industry_stale_contract_scope_cleanup_migration",
        "reason": "archives stale action-scoped business config contracts whose action model no longer matches the contract model",
        "expected_source": "smart_construction_core.stale_contract_scope_cleanup",
    },
}
ALLOWED_APPROVAL_POLICY_RUNTIME_WRITERS = {
    "addons/smart_construction_core/handlers/approval_policy_configuration.py": {
        "layer": "L2/L4",
        "boundary": "approval_policy_runtime_configuration",
        "reason": "business configuration UI writes industry approval policy runtime records",
        "expected_source": BOUNDARY_CONSTANTS["APPROVAL_POLICY_SOURCE_TENANT_LOWCODING"],
        "target_models": ["sc.approval.policy", "sc.approval.step"],
    },
}
ALLOWED_LOWCODING_POLICY_RUNTIME_WRITERS = {
    "addons/smart_core/handlers/form_field_configuration.py": {
        "layer": "L4",
        "boundary": "form_field_policy_runtime_configuration",
        "reason": "business configuration UI writes form field runtime policies",
        "expected_source": BOUNDARY_CONSTANTS["VIEW_ORCHESTRATION_SOURCE_FIELD_POLICY"],
        "target_models": ["ui.form.field.policy"],
    },
    "addons/smart_core/model/ui_form_custom_field_wizard.py": {
        "layer": "L4",
        "boundary": "form_custom_field_policy_creation",
        "reason": "custom field wizard creates the companion form field runtime policy",
        "expected_source": BOUNDARY_CONSTANTS["VIEW_ORCHESTRATION_SOURCE_FIELD_POLICY"],
        "target_models": ["ui.form.field.policy"],
    },
    "addons/smart_core/handlers/menu_configuration.py": {
        "layer": "L4",
        "boundary": "menu_config_policy_runtime_configuration",
        "reason": "business configuration UI writes menu runtime policies",
        "expected_source": BOUNDARY_CONSTANTS["MENU_ORCHESTRATION_SOURCE_TENANT_LOWCODING"],
        "target_models": ["ui.menu.config.policy"],
    },
    "addons/smart_construction_core/models/support/product_policy_sync.py": {
        "layer": "L2",
        "boundary": "industry_product_menu_policy_projection",
        "reason": "industry product policy sync writes baseline menu visibility overlays",
        "expected_source": "smart_construction_core.product_policy_sync",
        "target_models": ["ui.menu.config.policy"],
    },
    "addons/smart_construction_core/migrations/17.0.0.61/post-migration.py": {
        "layer": "L2",
        "boundary": "industry_product_menu_policy_baseline_migration",
        "reason": "normalizes legacy config menu labels in released menu runtime policies during industry module upgrade",
        "expected_source": "smart_construction_core.config_center_label_migration",
        "target_models": ["ui.menu.config.policy"],
    },
}

def _is_contract_writer(text: str) -> bool:
    if "ui.business.config.contract" not in text:
        return False
    write_markers = (
        "Contract.create(",
        "contract.write(",
        "rec.write(",
        "rec.action_publish(",
        "contract.action_publish(",
    )
    return any(marker in text for marker in write_markers)


def _is_approval_policy_runtime_writer(text: str) -> bool:
    if "sc.approval.policy" not in text and "sc.approval.step" not in text:
        return False
    write_markers = (
        "Policy.create(",
        "policy.write(",
        "Step.create(",
        "step.write(",
        "_step_writer(",
    )
    return any(marker in text for marker in write_markers)


def _is_lowcoding_policy_runtime_writer(text: str) -> bool:
    uses_menu_policy_constant_writer = "Policy = env[MENU_CONFIG_POLICY_MODEL]" in text
    if (
        "ui.form.field.policy" not in text
        and "ui.menu.config.policy" not in text
        and not uses_menu_policy_constant_writer
    ):
        return False
    write_markers = (
        'self.env["ui.form.field.policy"].create(',
        'self.env["ui.menu.config.policy"].create(',
        "Policy.create(",
        "policy.write(",
    )
    return any(marker in text for marker in write_markers)


BOUNDARY_RULES = [
    {
        "category": "business_config_contract",
        "report_key": "allowed_direct_contract_writers",
        "rows_key": "contract_writers",
        "count_key": "contract_writer_count",
        "predicate": _is_contract_writer,
        "allowed": ALLOWED_DIRECT_CONTRACT_WRITERS,
        "error_message": "direct ui.business.config.contract writer must go through an approved backend boundary",
    },
    {
        "category": "approval_policy_runtime",
        "report_key": "allowed_approval_policy_runtime_writers",
        "rows_key": "approval_policy_writers",
        "count_key": "approval_policy_writer_count",
        "predicate": _is_approval_policy_runtime_writer,
        "allowed": ALLOWED_APPROVAL_POLICY_RUNTIME_WRITERS,
        "error_message": "direct approval policy runtime writer must go through the approved approval policy configuration boundary",
    },
    {
        "category": "lowcoding_policy_runtime",
        "report_key": "allowed_lowcoding_policy_runtime_writers",
        "rows_key": "lowcoding_policy_writers",
        "count_key": "lowcoding_policy_writer_count",
        "predicate": _is_lowcoding_policy_runtime_writer,
        "allowed": ALLOWED_LOWCODING_POLICY_RUNTIME_WRITERS,
        "error_message": "direct low-code runtime policy writer must go through an approved business configuration boundary",
    },
]

REQUIRED_BOUNDARY_MARKERS = {
    "addons/smart_core/handlers/form_field_configuration.py": [
        "formal_authority\": \"ui.business.config.contract.view_orchestration",
        "compatibility_write\": \"ui.form.field.policy",
        "已阻止兼容策略表单独生效",
        "def _write_lowcode_form_contract_or_error(",
        "LOWCODE_SOURCE_STATUS_TENANT_RUNTIME",
    ],
    "addons/smart_core/handlers/menu_configuration.py": [
        "contract_source\": MENU_ORCHESTRATION_SOURCE_TENANT_LOWCODING",
        "lowcode_boundary\": \"menu_config",
        "MENU_CONFIG_SCOPE_VIOLATION",
        "LOWCODE_SOURCE_STATUS_TENANT_RUNTIME",
    ],
    "addons/smart_core/model/ui_menu_config_policy.py": [
        "LOWCODE_SYSTEM_CONFIG_MENU_XMLIDS",
    ],
}


def _scan_allowed_boundary(
    *,
    category: str,
    predicate,
    allowed: dict[str, dict],
    error_message: str,
) -> tuple[list[dict], list[dict]]:
    rows = []
    errors = []
    for path in sorted((ROOT / "addons").rglob("*.py")):
        rel = path.relative_to(ROOT).as_posix()
        if "/tests/" in rel:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = path.read_text(encoding="utf-8", errors="ignore")
        if not predicate(text):
            continue
        metadata = allowed.get(rel) or {}
        allowed_writer = bool(metadata)
        row = {"category": category, "path": rel, "allowed": allowed_writer, **metadata}
        rows.append(row)
        if not allowed_writer:
            errors.append({"category": category, "path": rel, "message": error_message})
    return rows, errors


def build_report() -> dict:
    rows_by_key = {}
    errors = []
    writer_rows = []
    report = {"guard": "backend_contract_boundary_guard", "schema_version": "1.0"}
    for rule in BOUNDARY_RULES:
        allowed = rule["allowed"]
        rows, rule_errors = _scan_allowed_boundary(
            category=rule["category"],
            predicate=rule["predicate"],
            allowed=allowed,
            error_message=rule["error_message"],
        )
        rows_by_key[rule["rows_key"]] = rows
        writer_rows.extend(rows)
        errors.extend(rule_errors)
        report[rule["report_key"]] = [
            {"path": path, **metadata}
            for path, metadata in sorted(allowed.items())
        ]
        report[rule["count_key"]] = len(rows)

    unique_writer_paths = sorted({row["path"] for row in writer_rows})
    report.update({
        "writer_count": len(writer_rows),
        "writer_boundary_count": len(writer_rows),
        "writer_file_count": len(unique_writer_paths),
        "writer_paths": unique_writer_paths,
        "error_count": len(errors),
        "writers": writer_rows,
        "errors": errors,
    })
    report.update(rows_by_key)
    marker_errors = []
    for rel, markers in REQUIRED_BOUNDARY_MARKERS.items():
        path = ROOT / rel
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = path.read_text(encoding="utf-8", errors="ignore")
        for marker in markers:
            if marker not in text:
                marker_errors.append({
                    "category": "required_boundary_marker",
                    "path": rel,
                    "message": "missing required boundary marker: %s" % marker,
                })
    errors.extend(marker_errors)
    report["required_boundary_marker_errors"] = marker_errors
    report["error_count"] = len(errors)
    report["errors"] = errors
    return report


def main() -> int:
    report = build_report()
    output = json.dumps(report, ensure_ascii=False, indent=2)
    report_path = os.environ.get("BACKEND_CONTRACT_BOUNDARY_GUARD_REPORT", "").strip()
    if report_path:
        target = Path(report_path)
        if not target.is_absolute():
            target = ROOT / target
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(output + "\n", encoding="utf-8")
    print(output)
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
