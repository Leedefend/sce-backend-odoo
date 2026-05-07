#!/usr/bin/env python3
"""Regression guard for old and business-fit partner asset lanes."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path


DEFAULT_GATE = Path(
    "artifacts/migration/partner_business_aligned_rebuild_v1/"
    "fact_based_partner_rebuild_business_aligned_gate_v1.csv"
)
DEFAULT_RUNTIME_ROOT = Path(".runtime_artifacts/migration_assets/partner_business_fit_guard")
DEFAULT_BANK_RUNTIME_ROOT = Path(".runtime_artifacts/migration_assets/partner_bank_business_fit_guard")
REQUIRED_BUSINESS_FIELDS = {
    "customer_rank",
    "supplier_rank",
    "sc_supplier_type",
    "sc_region",
    "street",
    "sc_registered_capital",
    "sc_account_name",
    "sc_bank_name",
    "sc_bank_account",
}


def run(command: list[str]) -> str:
    proc = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    if proc.returncode != 0:
        raise RuntimeError({"command_failed": command, "output": proc.stdout})
    return proc.stdout


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def xml_field_names(path: Path) -> set[str]:
    root = ET.parse(path).getroot()
    return {field.attrib.get("name", "") for field in root.findall(".//field") if field.attrib.get("name")}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gate", default=str(DEFAULT_GATE))
    parser.add_argument("--runtime-root", default=str(DEFAULT_RUNTIME_ROOT))
    parser.add_argument("--bank-runtime-root", default=str(DEFAULT_BANK_RUNTIME_ROOT))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    runtime_root = Path(args.runtime_root)
    if runtime_root.exists():
        shutil.rmtree(runtime_root)
    bank_runtime_root = Path(args.bank_runtime_root)
    if bank_runtime_root.exists():
        shutil.rmtree(bank_runtime_root)

    result: dict[str, object]
    try:
        old_verify = run(["python3", "scripts/migration/partner_asset_verify.py", "--asset-root", "migration_assets", "--lane", "partner", "--check"])
        generator_output = run(
            [
                "python3",
                "scripts/migration/partner_asset_generator.py",
                "--business-gate",
                args.gate,
                "--out",
                str(runtime_root),
                "--source",
                "partner_import_source",
                "--asset-version",
                "business_fit_guard_v1",
                "--check",
            ]
        )
        business_verify = run(["python3", "scripts/migration/partner_asset_verify.py", "--asset-root", str(runtime_root), "--lane", "partner", "--check"])
        bank_generator_output = run(
            [
                "python3",
                "scripts/migration/partner_bank_business_asset_generator.py",
                "--business-gate",
                args.gate,
                "--out",
                str(bank_runtime_root),
                "--check",
            ]
        )

        manifest = load_json(runtime_root / "manifest/partner_asset_manifest_v1.json")
        bank_manifest = load_json(bank_runtime_root / "manifest/partner_bank_asset_manifest_v1.json")
        validation = load_json(runtime_root / "manifest/partner_validation_manifest_v1.json")
        xml_fields = xml_field_names(runtime_root / "10_master/partner/partner_master_v1.xml")
        business_fit = manifest.get("business_fit") or {}
        gates = set((validation.get("validation_gates") or {}).get("generate_time") or [])
        missing_fields = sorted(REQUIRED_BUSINESS_FIELDS - xml_fields)
        missing_gates = sorted(
            {
                "partner_role_fields_allowed",
                "partner_basic_info_fields_present",
                "write_gate_queues_present",
            }
            - gates
        )
        errors = []
        if missing_fields:
            errors.append({"missing_business_fields": missing_fields})
        if missing_gates:
            errors.append({"missing_business_gates": missing_gates})
        if not business_fit.get("enabled"):
            errors.append({"business_fit_not_enabled": business_fit})
        if int((manifest.get("counts") or {}).get("loadable_records") or 0) != 6348:
            errors.append({"unexpected_loadable_records": (manifest.get("counts") or {}).get("loadable_records")})
        if int((manifest.get("counts") or {}).get("discarded_records") or 0) != 1444:
            errors.append({"unexpected_discarded_records": (manifest.get("counts") or {}).get("discarded_records")})
        bank_counts = bank_manifest.get("counts") or {}
        if int(bank_counts.get("loadable_records") or 0) != 5574:
            errors.append({"unexpected_bank_loadable_records": bank_counts.get("loadable_records")})
        if int(bank_counts.get("discarded_records") or 0) != 2218:
            errors.append({"unexpected_bank_discarded_records": bank_counts.get("discarded_records")})
        if bank_manifest.get("target", {}).get("model") != "res.partner.bank":
            errors.append({"unexpected_bank_target": bank_manifest.get("target")})
        if errors:
            raise RuntimeError({"partner_asset_business_fit_guard_failed": errors})
        result = {
            "status": "PASS",
            "old_verify": old_verify.strip(),
            "business_generator": generator_output.strip(),
            "business_verify": business_verify.strip(),
            "bank_generator": bank_generator_output.strip(),
            "runtime_root": str(runtime_root),
            "bank_runtime_root": str(bank_runtime_root),
            "loadable_records": (manifest.get("counts") or {}).get("loadable_records"),
            "discarded_records": (manifest.get("counts") or {}).get("discarded_records"),
            "bank_loadable_records": bank_counts.get("loadable_records"),
            "bank_discarded_records": bank_counts.get("discarded_records"),
            "business_fit": business_fit,
            "db_writes": 0,
        }
    except Exception as exc:
        result = {"status": "FAIL", "error": str(exc), "db_writes": 0}
        print("PARTNER_ASSET_BUSINESS_FIT_GUARD=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 1 if args.check else 0

    print("PARTNER_ASSET_BUSINESS_FIT_GUARD=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
