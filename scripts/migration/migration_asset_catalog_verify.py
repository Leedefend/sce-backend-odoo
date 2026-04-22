#!/usr/bin/env python3
"""Verify the repository migration asset catalog without DB access."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


REQUIRED_GATES = {
    "catalog_schema_valid",
    "package_order_complete",
    "asset_manifest_exists",
    "asset_manifest_hash_matches",
    "package_dependencies_declared_before_dependents",
    "package_verifier_declared",
    "no_demo_module_dependency",
    "no_db_write_in_catalog_stage",
    "no_high_risk_lane_leakage",
}
FORBIDDEN_PACKAGE_TOKENS = ("payment", "settlement", "account", "security", "record_rule", "__manifest__")
PACKAGE_RULES = {
    "project_sc_v1": {"target_model": "project.project", "layer": "10_master"},
    "partner_sc_v1": {"target_model": "res.partner", "layer": "10_master"},
    "contract_counterparty_partner_sc_v1": {"target_model": "res.partner", "layer": "10_master"},
    "receipt_counterparty_partner_sc_v1": {"target_model": "res.partner", "layer": "10_master"},
    "user_sc_v1": {"target_model": "res.users", "layer": "10_master"},
    "project_member_sc_v1": {"target_model": "sc.project.member.staging", "layer": "30_relation"},
    "contract_sc_v1": {"target_model": "construction.contract", "layer": "20_business"},
    "contract_line_sc_v1": {"target_model": "construction.contract.line", "layer": "20_business"},
    "receipt_sc_v1": {"target_model": "payment.request", "layer": "20_business"},
    "outflow_request_sc_v1": {"target_model": "payment.request", "layer": "20_business"},
    "actual_outflow_sc_v1": {"target_model": "payment.request", "layer": "20_business"},
    "supplier_contract_sc_v1": {"target_model": "construction.contract", "layer": "20_business"},
    "supplier_contract_line_sc_v1": {"target_model": "construction.contract.line", "layer": "20_business"},
    "outflow_request_line_sc_v1": {"target_model": "payment.request.line", "layer": "20_business"},
    "receipt_invoice_line_sc_v1": {"target_model": "sc.receipt.invoice.line", "layer": "20_business"},
    "receipt_invoice_attachment_sc_v1": {"target_model": "ir.attachment", "layer": "30_relation"},
    "legacy_attachment_backfill_sc_v1": {"target_model": "ir.attachment", "layer": "30_relation"},
    "legacy_workflow_audit_sc_v1": {"target_model": "sc.legacy.workflow.audit", "layer": "30_relation"},
    "legacy_expense_deposit_sc_v1": {"target_model": "sc.legacy.expense.deposit.fact", "layer": "30_relation"},
    "legacy_invoice_tax_sc_v1": {"target_model": "sc.legacy.invoice.tax.fact", "layer": "30_relation"},
    "legacy_receipt_income_sc_v1": {"target_model": "sc.legacy.receipt.income.fact", "layer": "30_relation"},
    "legacy_financing_loan_sc_v1": {"target_model": "sc.legacy.financing.loan.fact", "layer": "30_relation"},
    "legacy_fund_daily_snapshot_sc_v1": {"target_model": "sc.legacy.fund.daily.snapshot.fact", "layer": "30_relation"},
}
PACKAGE_ALLOWED_TOKENS = {
    "receipt_sc_v1": {"payment"},
    "outflow_request_sc_v1": {"payment"},
    "actual_outflow_sc_v1": {"payment"},
    "outflow_request_line_sc_v1": {"payment"},
}


class CatalogVerificationError(Exception):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise CatalogVerificationError(message)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise CatalogVerificationError(f"missing json file: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def verify_package(asset_root: Path, package: dict[str, Any], seen: set[str]) -> None:
    package_id = package.get("asset_package_id")
    require(isinstance(package_id, str) and package_id, "package asset_package_id must be non-empty")
    require(package.get("required") is True, f"{package_id}: package must be required")
    require(package.get("baseline_package") is True, f"{package_id}: package must be baseline_package")
    package_rule = PACKAGE_RULES.get(package_id)
    require(package_rule is not None, f"{package_id}: package target model is not allowlisted")
    require(package.get("layer") == package_rule["layer"], f"{package_id}: unexpected layer")
    require(package.get("target_model") == package_rule["target_model"], f"{package_id}: unexpected target model")
    require(package.get("verification_command"), f"{package_id}: missing verification_command")

    package_payload = json.dumps(package, ensure_ascii=False)
    allowed_tokens = PACKAGE_ALLOWED_TOKENS.get(package_id, set())
    forbidden_tokens = [token for token in FORBIDDEN_PACKAGE_TOKENS if token not in allowed_tokens]
    require(not any(token in package_payload for token in forbidden_tokens), f"{package_id}: high-risk token leaked into package declaration")

    manifest_rel = package.get("asset_manifest_path")
    expected_hash = package.get("asset_manifest_sha256")
    require(isinstance(manifest_rel, str) and manifest_rel, f"{package_id}: missing asset_manifest_path")
    require(isinstance(expected_hash, str) and expected_hash, f"{package_id}: missing asset_manifest_sha256")
    manifest_path = asset_root / manifest_rel
    require(manifest_path.exists(), f"{package_id}: missing asset manifest {manifest_rel}")
    actual_hash = sha256_file(manifest_path)
    require(actual_hash == expected_hash, f"{package_id}: asset manifest hash mismatch")

    asset_manifest = load_json(manifest_path)
    require(asset_manifest.get("asset_package_id") == package_id, f"{package_id}: manifest package id mismatch")
    require(asset_manifest.get("db_writes") == 0, f"{package_id}: asset manifest must declare db_writes=0")
    require(asset_manifest.get("odoo_shell") is False, f"{package_id}: asset manifest must declare odoo_shell=false")
    require(asset_manifest.get("baseline_package") is True, f"{package_id}: asset manifest must be baseline")

    dependencies = package.get("dependencies", [])
    require(isinstance(dependencies, list), f"{package_id}: dependencies must be a list")
    missing_dependencies = [dependency for dependency in dependencies if dependency not in seen]
    require(not missing_dependencies, f"{package_id}: dependencies not declared before package: {missing_dependencies}")


def verify_catalog(asset_root: Path, catalog_path: Path) -> dict[str, Any]:
    catalog = load_json(catalog_path)
    require(catalog.get("catalog_version") == "1.0", "unsupported catalog_version")
    policy = catalog.get("rebuild_policy", {})
    require(policy.get("db_writes_in_catalog_stage") == 0, "catalog stage must not write DB")
    require(policy.get("odoo_shell_required") is False, "catalog stage must not require odoo shell")
    require(policy.get("demo_module_required") is False, "fresh rebuild catalog must not require demo module")

    gates = set(catalog.get("validation_gates", []))
    missing_gates = sorted(REQUIRED_GATES - gates)
    require(not missing_gates, f"catalog missing validation gates: {missing_gates}")

    package_order = catalog.get("package_order", [])
    packages = catalog.get("packages", [])
    require(isinstance(package_order, list) and package_order, "package_order must be non-empty")
    require(isinstance(packages, list) and packages, "packages must be non-empty")
    package_ids = [package.get("asset_package_id") for package in packages]
    require(package_order == package_ids, "package_order must exactly match packages order")
    require(len(package_ids) == len(set(package_ids)), "duplicate package ids in catalog")

    seen: set[str] = set()
    for package in packages:
        verify_package(asset_root, package, seen)
        seen.add(package["asset_package_id"])

    return {
        "status": "PASS",
        "asset_root": str(asset_root),
        "catalog": str(catalog_path),
        "packages": package_ids,
        "db_writes": 0,
        "odoo_shell": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify migration asset catalog without DB access.")
    parser.add_argument("--asset-root", default="migration_assets", help="Repository asset root")
    parser.add_argument(
        "--catalog",
        default="migration_assets/manifest/migration_asset_catalog_v1.json",
        help="Migration asset catalog path",
    )
    parser.add_argument("--check", action="store_true", help="Fail non-zero on verification errors")
    args = parser.parse_args()

    try:
        result = verify_catalog(Path(args.asset_root), Path(args.catalog))
    except (CatalogVerificationError, json.JSONDecodeError) as exc:
        payload = {"status": "FAIL", "error": str(exc), "db_writes": 0, "odoo_shell": False}
        print("MIGRATION_ASSET_CATALOG_VERIFY=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 1 if args.check else 0

    print("MIGRATION_ASSET_CATALOG_VERIFY=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
