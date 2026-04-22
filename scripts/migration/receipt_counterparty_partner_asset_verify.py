#!/usr/bin/env python3
"""Verify receipt counterparty supplemental partner assets."""

from __future__ import annotations

import argparse
import hashlib
import json
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from typing import Any


PACKAGE_ID = "receipt_counterparty_partner_sc_v1"


class VerificationError(Exception):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise VerificationError(message)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    require(path.exists(), f"missing json manifest: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def parse_xml(path: Path) -> list[dict[str, str]]:
    root = ET.parse(path).getroot()
    records: list[dict[str, str]] = []
    for record in root.findall(".//record"):
        fields = {field.attrib.get("name", ""): (field.text or "").strip() for field in record.findall("field")}
        records.append({"id": record.attrib.get("id", "").strip(), "model": record.attrib.get("model", "").strip(), **fields})
    return records


def verify_hashes(asset_root: Path, manifest: dict[str, Any]) -> None:
    for asset in manifest.get("assets", []):
        rel_path = asset.get("path")
        expected = asset.get("sha256")
        require(isinstance(rel_path, str) and rel_path, "asset path missing")
        require(isinstance(expected, str) and expected, f"asset hash missing: {rel_path}")
        require(sha256_file(asset_root / rel_path) == expected, f"sha256 mismatch: {rel_path}")


def verify(asset_root: Path, lane: str) -> dict[str, Any]:
    asset_manifest = load_json(asset_root / "manifest" / f"{lane}_asset_manifest_v1.json")
    external_manifest = load_json(asset_root / "manifest" / f"{lane}_external_id_manifest_v1.json")
    validation_manifest = load_json(asset_root / "manifest" / f"{lane}_validation_manifest_v1.json")
    records = parse_xml(asset_root / "10_master" / lane / f"{lane}_master_v1.xml")

    require(asset_manifest.get("asset_package_id") == PACKAGE_ID, "unexpected asset package id")
    require(asset_manifest.get("baseline_package") is True, "asset package must be baseline")
    require(asset_manifest.get("db_writes") == 0, "db_writes must be 0")
    require(asset_manifest.get("odoo_shell") is False, "odoo_shell must be false")
    require(asset_manifest.get("dependencies") == ["partner_sc_v1"], "unexpected dependencies")
    require(asset_manifest.get("target", {}).get("model") == "res.partner", "unexpected target model")
    require(asset_manifest.get("lane", {}).get("layer") == "10_master", "unexpected layer")
    verify_hashes(asset_root, asset_manifest)

    require(len(records) == asset_manifest["counts"]["loadable_records"], "xml record count mismatch")
    ids = [row["id"] for row in records]
    duplicates = [value for value, count in Counter(ids).items() if count > 1]
    require(not duplicates, f"duplicate xml ids: {duplicates[:10]}")
    for row in records:
        require(row["id"].startswith("legacy_receipt_counterparty_sc_"), f"invalid external id: {row['id']}")
        require(row["model"] == "res.partner", f"invalid model: {row['model']}")
        require(row.get("name"), f"missing name: {row['id']}")
        require(row.get("legacy_partner_id"), f"missing legacy_partner_id: {row['id']}")
        require(row.get("legacy_partner_source") == "receipt_counterparty", f"invalid source: {row['id']}")
        require(row.get("company_type") in {"person", "company"}, f"invalid company_type: {row['id']}")
        require(row.get("is_company") in {"0", "1"}, f"invalid is_company: {row['id']}")
        require((row["company_type"] == "company") == (row["is_company"] == "1"), f"company_type/is_company mismatch: {row['id']}")

    manifest_ids = {row.get("external_id") for row in external_manifest.get("records", [])}
    require(set(ids) == manifest_ids, "external manifest ids do not match XML")
    gates = set(validation_manifest.get("validation_gates", {}).get("generate_time", []))
    required = {"personal_partner_supported", "legacy_counterparty_id_required", "legacy_counterparty_name_safe", "no_db_writes"}
    require(not (required - gates), f"missing validation gates: {sorted(required - gates)}")
    return {
        "status": "PASS",
        "asset_root": str(asset_root),
        "lane": lane,
        "records": len(records),
        "asset_package_id": PACKAGE_ID,
        "db_writes": 0,
        "odoo_shell": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify receipt counterparty partner assets.")
    parser.add_argument("--asset-root", default="migration_assets")
    parser.add_argument("--lane", default="receipt_counterparty_partner")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        result = verify(Path(args.asset_root), args.lane)
    except (VerificationError, ET.ParseError, json.JSONDecodeError) as exc:
        payload = {"status": "FAIL", "error": str(exc), "db_writes": 0, "odoo_shell": False}
        print("RECEIPT_COUNTERPARTY_PARTNER_ASSET_VERIFY=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 1 if args.check else 0
    print("RECEIPT_COUNTERPARTY_PARTNER_ASSET_VERIFY=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
