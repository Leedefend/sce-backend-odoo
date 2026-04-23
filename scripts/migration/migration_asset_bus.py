#!/usr/bin/env python3
"""Run the migration asset rebuild bus in no-DB verification mode."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from migration_asset_catalog_verify import CatalogVerificationError, load_json, verify_catalog


VERIFY_ONLY_PACKAGES = {
    "project_sc_v1": {
        "lane": "project",
        "script": "scripts/migration/project_asset_verify.py",
    },
    "partner_sc_v1": {
        "lane": "partner",
        "script": "scripts/migration/partner_asset_verify.py",
    },
    "contract_counterparty_partner_sc_v1": {
        "lane": "contract_counterparty_partner",
        "script": "scripts/migration/contract_counterparty_partner_asset_verify.py",
    },
    "receipt_counterparty_partner_sc_v1": {
        "lane": "receipt_counterparty_partner",
        "script": "scripts/migration/receipt_counterparty_partner_asset_verify.py",
    },
    "user_sc_v1": {
        "lane": "user",
        "script": "scripts/migration/user_asset_verify.py",
    },
    "project_member_sc_v1": {
        "lane": "project_member",
        "script": "scripts/migration/project_member_asset_verify.py",
    },
    "contract_sc_v1": {
        "lane": "contract",
        "script": "scripts/migration/contract_header_asset_verify.py",
    },
    "contract_line_sc_v1": {
        "lane": "contract_line",
        "script": "scripts/migration/contract_line_summary_asset_verify.py",
    },
    "receipt_sc_v1": {
        "lane": "receipt",
        "script": "scripts/migration/receipt_core_asset_verify.py",
    },
    "outflow_request_sc_v1": {
        "lane": "outflow",
        "script": "scripts/migration/legacy_outflow_request_asset_verify.py",
    },
    "actual_outflow_sc_v1": {
        "lane": "actual_outflow",
        "script": "scripts/migration/legacy_actual_outflow_asset_verify.py",
    },
    "supplier_contract_sc_v1": {
        "lane": "supplier_contract",
        "script": "scripts/migration/legacy_supplier_contract_asset_verify.py",
    },
    "supplier_contract_line_sc_v1": {
        "lane": "supplier_contract_line",
        "script": "scripts/migration/legacy_supplier_contract_line_asset_verify.py",
    },
    "outflow_request_line_sc_v1": {
        "lane": "outflow_request_line",
        "script": "scripts/migration/legacy_outflow_request_line_asset_verify.py",
    },
    "receipt_invoice_line_sc_v1": {
        "lane": "receipt_invoice_line",
        "script": "scripts/migration/legacy_receipt_invoice_asset_verify.py",
    },
    "receipt_invoice_attachment_sc_v1": {
        "lane": "receipt_invoice_attachment",
        "script": "scripts/migration/legacy_receipt_invoice_attachment_asset_verify.py",
    },
    "legacy_attachment_backfill_sc_v1": {
        "lane": "legacy_attachment_backfill",
        "script": "scripts/migration/legacy_attachment_backfill_asset_verify.py",
    },
    "legacy_workflow_audit_sc_v1": {
        "lane": "legacy_workflow_audit",
        "script": "scripts/migration/legacy_workflow_audit_asset_verify.py",
    },
    "legacy_expense_deposit_sc_v1": {
        "lane": "legacy_expense_deposit",
        "script": "scripts/migration/legacy_expense_deposit_asset_verify.py",
    },
    "legacy_invoice_tax_sc_v1": {
        "lane": "legacy_invoice_tax",
        "script": "scripts/migration/legacy_invoice_tax_asset_verify.py",
    },
    "legacy_receipt_income_sc_v1": {
        "lane": "legacy_receipt_income",
        "script": "scripts/migration/legacy_receipt_income_asset_verify.py",
    },
    "legacy_financing_loan_sc_v1": {
        "lane": "legacy_financing_loan",
        "script": "scripts/migration/legacy_financing_loan_asset_verify.py",
    },
    "legacy_fund_daily_snapshot_sc_v1": {
        "lane": "legacy_fund_daily_snapshot",
        "script": "scripts/migration/legacy_fund_daily_snapshot_asset_verify.py",
    }
}


class MigrationAssetBusError(Exception):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise MigrationAssetBusError(message)


def run_package_verifier(repo_root: Path, asset_root: Path, package_id: str) -> dict[str, Any]:
    verifier = VERIFY_ONLY_PACKAGES.get(package_id)
    require(verifier is not None, f"package verifier is not allowlisted: {package_id}")

    script_path = repo_root / verifier["script"]
    require(script_path.exists(), f"package verifier script does not exist: {script_path}")
    cmd = [
        sys.executable,
        str(script_path),
        "--asset-root",
        str(asset_root),
        "--lane",
        verifier["lane"],
        "--check",
    ]
    completed = subprocess.run(cmd, cwd=repo_root, text=True, capture_output=True, check=False)
    require(completed.returncode == 0, f"{package_id} verifier failed: {completed.stdout}{completed.stderr}")
    return {
        "asset_package_id": package_id,
        "lane": verifier["lane"],
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
    }


def run_verify_only(asset_root: Path, catalog_path: Path) -> dict[str, Any]:
    repo_root = Path.cwd()
    catalog_result = verify_catalog(asset_root, catalog_path)
    catalog = load_json(catalog_path)
    package_order = catalog.get("package_order", [])
    require(isinstance(package_order, list) and package_order, "catalog package_order must be non-empty")

    package_results = [run_package_verifier(repo_root, asset_root, package_id) for package_id in package_order]
    return {
        "status": "PASS",
        "mode": "verify-only",
        "asset_root": str(asset_root),
        "catalog": str(catalog_path),
        "catalog_status": catalog_result["status"],
        "package_count": len(package_results),
        "packages": [result["asset_package_id"] for result in package_results],
        "db_writes": 0,
        "odoo_shell": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Migration asset rebuild bus runner.")
    parser.add_argument("--asset-root", default="migration_assets", help="Repository asset root")
    parser.add_argument(
        "--catalog",
        default="migration_assets/manifest/migration_asset_catalog_v1.json",
        help="Migration asset catalog path",
    )
    parser.add_argument("--verify-only", action="store_true", help="Run only catalog and package verifiers")
    parser.add_argument("--check", action="store_true", help="Fail non-zero on verification errors")
    args = parser.parse_args()

    try:
        require(args.verify_only, "only --verify-only mode is currently supported")
        result = run_verify_only(Path(args.asset_root), Path(args.catalog))
    except (CatalogVerificationError, MigrationAssetBusError, json.JSONDecodeError) as exc:
        payload = {"status": "FAIL", "error": str(exc), "db_writes": 0, "odoo_shell": False}
        print("MIGRATION_ASSET_BUS=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 1 if args.check else 0

    print("MIGRATION_ASSET_BUS=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
