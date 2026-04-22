#!/usr/bin/env python3
"""Verify legacy expense and deposit XML migration assets."""

from __future__ import annotations

import argparse
import hashlib
import json
import xml.etree.ElementTree as ET
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any


REQUIRED_FIELDS = {
    "legacy_source_table",
    "legacy_record_id",
    "source_family",
    "direction",
    "project_id",
    "legacy_project_id",
    "source_amount",
    "source_amount_field",
    "import_batch",
}
ALLOWED_XML_FIELDS = {
    "legacy_source_table",
    "legacy_record_id",
    "legacy_pid",
    "source_family",
    "direction",
    "document_no",
    "document_date",
    "legacy_state",
    "project_id",
    "legacy_project_id",
    "legacy_project_name",
    "partner_id",
    "legacy_partner_id",
    "legacy_partner_name",
    "source_amount",
    "source_amount_field",
    "note",
    "import_batch",
}
FORBIDDEN_XML_FIELDS = {
    "account_move_id",
    "settlement_id",
    "payment_id",
    "payment_request_id",
    "validation_status",
    "review_ids",
    "res_id",
}
ALLOWED_FAMILIES = {
    "expense_reimbursement",
    "company_financial_outflow",
    "pay_guarantee_deposit",
    "pay_guarantee_deposit_refund",
    "self_funded_income_refund",
    "received_guarantee_deposit_refund",
    "project_deduction_refund",
    "received_guarantee_deposit_register",
}
ALLOWED_DIRECTIONS = {"outflow", "inflow", "inflow_or_refund"}


class ExpenseDepositAssetVerificationError(Exception):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ExpenseDepositAssetVerificationError(message)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    require(path.exists(), f"missing json manifest: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def parse_xml(xml_path: Path) -> list[dict[str, str]]:
    root = ET.parse(xml_path).getroot()
    records: list[dict[str, str]] = []
    for record in root.findall(".//record"):
        row = {"id": record.attrib.get("id", "").strip(), "model": record.attrib.get("model", "").strip()}
        for field in record.findall("field"):
            name = field.attrib.get("name", "").strip()
            row[name] = field.attrib.get("ref", "").strip() or (field.text or "").strip()
        records.append(row)
    return records


def project_refs(asset_root: Path) -> set[str]:
    manifest = load_json(asset_root / "manifest/project_external_id_manifest_v1.json")
    refs = {
        str(row.get("external_id", "")).strip()
        for row in manifest.get("records", [])
        if row.get("status") == "loadable" and str(row.get("external_id", "")).strip()
    }
    require(refs, "project reference set is empty")
    return refs


def partner_refs(asset_root: Path) -> set[str]:
    manifest = load_json(asset_root / "manifest/partner_external_id_manifest_v1.json")
    return {
        str(row.get("external_id", "")).strip()
        for row in manifest.get("records", [])
        if row.get("status") == "loadable" and str(row.get("external_id", "")).strip()
    }


def verify_hashes(asset_root: Path, asset_manifest: dict[str, Any]) -> None:
    for asset in asset_manifest.get("assets", []):
        rel_path = asset.get("path")
        expected_hash = asset.get("sha256")
        require(isinstance(rel_path, str) and rel_path, "asset path must be non-empty")
        require(isinstance(expected_hash, str) and expected_hash, f"asset {rel_path} missing sha256")
        path = asset_root / rel_path
        require(path.exists(), f"declared asset does not exist: {rel_path}")
        require(sha256_file(path) == expected_hash, f"sha256 mismatch for {rel_path}")


def parse_positive_amount(value: str) -> Decimal:
    try:
        amount = Decimal(str(value).strip())
    except InvalidOperation as exc:
        raise ExpenseDepositAssetVerificationError(f"invalid amount: {value}") from exc
    require(amount > 0, f"source amount must be positive: {value}")
    return amount


def verify_asset_manifest(asset_root: Path, asset_manifest: dict[str, Any], lane: str) -> None:
    require(asset_manifest.get("asset_manifest_version") == "1.0", "unsupported asset manifest version")
    require(asset_manifest.get("asset_package_id") == "legacy_expense_deposit_sc_v1", "unexpected package id")
    require(asset_manifest.get("baseline_package") is True, "asset package must be baseline")
    require(asset_manifest.get("db_writes") == 0, "asset manifest must declare db_writes=0")
    require(asset_manifest.get("odoo_shell") is False, "asset manifest must declare odoo_shell=false")
    require(asset_manifest.get("lane", {}).get("lane_id") == lane, "unexpected lane")
    require(asset_manifest.get("lane", {}).get("layer") == "30_relation", "unexpected layer")
    require(asset_manifest.get("target", {}).get("model") == "sc.legacy.expense.deposit.fact", "unexpected target model")
    require(asset_manifest.get("counts", {}).get("loadable_records") == 11167, "loadable count drifted")
    boundary = load_json(asset_root / "manifest/legacy_expense_deposit_validation_manifest_v1.json").get("business_boundary", {})
    require(boundary.get("account_move") == "excluded", "account_move must be excluded")
    require(boundary.get("settlement_state") == "excluded", "settlement_state must be excluded")
    require(boundary.get("payment_ledger") == "excluded", "payment_ledger must be excluded")


def verify_xml_records(records: list[dict[str, str]], expected_count: int, project_set: set[str], partner_set: set[str]) -> None:
    require(len(records) == expected_count, f"xml record count mismatch: {len(records)} != {expected_count}")
    ids = [row["id"] for row in records]
    require(len(ids) == len(set(ids)), "duplicate XML external ids")
    for row in records:
        require(row["id"].startswith("legacy_expense_deposit_sc_"), f"invalid external id: {row['id']}")
        require(row["model"] == "sc.legacy.expense.deposit.fact", f"invalid XML model: {row['model']}")
        missing = sorted(field for field in REQUIRED_FIELDS if not row.get(field))
        require(not missing, f"missing required fields for {row['id']}: {missing}")
        unexpected = sorted(set(row) - ALLOWED_XML_FIELDS - {"id", "model"})
        require(not unexpected, f"unexpected expense/deposit fields for {row['id']}: {unexpected}")
        forbidden = sorted(FORBIDDEN_XML_FIELDS & set(row))
        require(not forbidden, f"forbidden runtime financial fields for {row['id']}: {forbidden}")
        require(row["project_id"] in project_set, f"project external id does not resolve: {row['project_id']}")
        if row.get("partner_id"):
            require(row["partner_id"] in partner_set, f"partner external id does not resolve: {row['partner_id']}")
        parse_positive_amount(row["source_amount"])
        require(row["source_family"] in ALLOWED_FAMILIES, f"bad source family: {row['source_family']}")
        require(row["direction"] in ALLOWED_DIRECTIONS, f"bad direction: {row['direction']}")


def verify_external_manifest(external_manifest: dict[str, Any], records: list[dict[str, str]]) -> None:
    manifest_records = external_manifest.get("records", [])
    require(isinstance(manifest_records, list), "external manifest records must be a list")
    xml_ids = {row["id"] for row in records}
    manifest_ids = {row.get("external_id") for row in manifest_records}
    require(xml_ids == manifest_ids, "external manifest ids do not match XML ids")
    require(external_manifest.get("summary", {}).get("loadable") == len(records), "loadable count mismatch")
    for row in manifest_records:
        require(row.get("status") == "loadable", f"non-loadable manifest row: {row}")
        require(row.get("project_external_id"), f"missing project external id: {row}")


def verify_validation_manifest(validation_manifest: dict[str, Any]) -> None:
    gates = set(validation_manifest.get("validation_gates", {}).get("generate_time", []))
    required = {
        "legacy_source_key_unique",
        "project_external_id_required_and_resolves",
        "partner_external_id_optional_when_assetized",
        "source_amount_positive",
        "no_account_move_records_generated",
        "no_settlement_records_generated",
        "no_payment_ledger_records_generated",
        "no_runtime_approval_records_generated",
        "no_database_integer_ids_required",
    }
    missing = sorted(required - gates)
    require(not missing, f"validation manifest missing gates: {missing}")
    boundary = validation_manifest.get("business_boundary", {})
    require(boundary.get("legacy_expense_deposit_fact") == "included", "legacy fact must be included")
    require(boundary.get("account_move") == "excluded", "account.move must be excluded")
    require(boundary.get("settlement_state") == "excluded", "settlement must be excluded")
    require(boundary.get("payment_ledger") == "excluded", "payment ledger must be excluded")
    require(boundary.get("approval_runtime") == "excluded", "approval runtime must be excluded")


def verify(asset_root: Path, lane: str) -> dict[str, Any]:
    asset_manifest = load_json(asset_root / "manifest/legacy_expense_deposit_asset_manifest_v1.json")
    external_manifest = load_json(asset_root / "manifest/legacy_expense_deposit_external_id_manifest_v1.json")
    validation_manifest = load_json(asset_root / "manifest/legacy_expense_deposit_validation_manifest_v1.json")
    records = parse_xml(asset_root / "30_relation" / lane / "legacy_expense_deposit_v1.xml")
    verify_asset_manifest(asset_root, asset_manifest, lane)
    verify_hashes(asset_root, asset_manifest)
    verify_xml_records(records, asset_manifest["counts"]["loadable_records"], project_refs(asset_root), partner_refs(asset_root))
    verify_external_manifest(external_manifest, records)
    verify_validation_manifest(validation_manifest)
    return {
        "status": "PASS",
        "asset_root": str(asset_root),
        "lane": lane,
        "records": len(records),
        "blocked_records": asset_manifest["counts"].get("blocked_records"),
        "asset_package_id": asset_manifest.get("asset_package_id"),
        "db_writes": 0,
        "odoo_shell": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify legacy expense/deposit XML migration assets.")
    parser.add_argument("--asset-root", default="migration_assets")
    parser.add_argument("--lane", default="legacy_expense_deposit")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        result = verify(Path(args.asset_root), args.lane)
    except (ExpenseDepositAssetVerificationError, ET.ParseError, json.JSONDecodeError) as exc:
        payload = {"status": "FAIL", "error": str(exc), "db_writes": 0, "odoo_shell": False}
        print("LEGACY_EXPENSE_DEPOSIT_ASSET_VERIFY=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 1 if args.check else 0
    print("LEGACY_EXPENSE_DEPOSIT_ASSET_VERIFY=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
