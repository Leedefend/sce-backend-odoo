#!/usr/bin/env python3
"""Verify the customer/supplier acceptance replay package is self-contained."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path


EXPECTED_ROWS = {
    "artifacts/migration/fresh_db_partner_l4_business_fit_payload_v1.csv": 6842,
    "artifacts/migration_assets/partner_bank_business_fit_v1/10_master/partner_bank/partner_bank_master_v1.csv": 5640,
    "artifacts/migration/partner_business_aligned_rebuild_v1/partner_import_review_queue_v1.csv": 1935,
}

REQUIRED_SCRIPTS = {
    "scripts/migration/fresh_db_partner_l4_replay_write.py",
    "scripts/migration/fresh_db_partner_bank_replay_write.py",
    "scripts/migration/fresh_db_partner_import_review_replay_write.py",
    "scripts/migration/partner_display_surface_runtime_probe.py",
    "scripts/ops/odoo_shell_exec.sh",
}

FORBIDDEN_COMMAND_TOKENS = (
    "/home/odoo/workspace/partner_import_source",
    ".runtime_artifacts",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def csv_rows(path: Path) -> int:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return max(sum(1 for _ in csv.reader(handle)) - 1, 0)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package-root", default="artifacts/migration/partner_business_aligned_replay_package_v1")
    args = parser.parse_args()

    root = Path(args.package_root)
    manifest_path = root / "manifest.json"
    errors: list[dict[str, object]] = []
    if not manifest_path.exists():
        raise RuntimeError({"missing_manifest": str(manifest_path)})
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    file_entries = manifest.get("files") if isinstance(manifest.get("files"), list) else []
    entry_by_path = {str(row.get("path")): row for row in file_entries if isinstance(row, dict)}

    for rel_path, expected in EXPECTED_ROWS.items():
        path = root / rel_path
        if not path.exists():
            errors.append({"error": "missing_payload", "path": rel_path})
            continue
        actual = csv_rows(path)
        if actual != expected:
            errors.append({"error": "unexpected_payload_rows", "path": rel_path, "actual": actual, "expected": expected})
        entry = entry_by_path.get(rel_path)
        if not entry:
            errors.append({"error": "payload_missing_from_manifest", "path": rel_path})
        elif entry.get("sha256") != sha256(path):
            errors.append({"error": "manifest_sha_mismatch", "path": rel_path})

    for rel_path in REQUIRED_SCRIPTS:
        if not (root / rel_path).exists():
            errors.append({"error": "missing_required_script", "path": rel_path})

    commands = manifest.get("replay_commands") if isinstance(manifest.get("replay_commands"), list) else []
    if len(commands) < 4:
        errors.append({"error": "missing_replay_commands", "actual": len(commands), "expected_min": 4})
    command_text = "\n".join(str(command) for command in commands)
    for token in FORBIDDEN_COMMAND_TOKENS:
        if token in command_text:
            errors.append({"error": "replay_command_has_external_dependency", "token": token})
    for required in (
        "FRESH_DB_PARTNER_L4_INPUT_CSV=artifacts/migration/fresh_db_partner_l4_business_fit_payload_v1.csv",
        "FRESH_DB_PARTNER_BANK_INPUT_CSV=artifacts/migration_assets/partner_bank_business_fit_v1/10_master/partner_bank/partner_bank_master_v1.csv",
        "FRESH_DB_PARTNER_IMPORT_REVIEW_INPUT_CSV=artifacts/migration/partner_business_aligned_rebuild_v1/partner_import_review_queue_v1.csv",
    ):
        if required not in command_text:
            errors.append({"error": "replay_command_missing_required_env", "required": required})

    result = {
        "status": "PASS" if not errors else "FAIL",
        "mode": "partner_acceptance_replay_package_verify",
        "package_root": str(root),
        "checked_payloads": len(EXPECTED_ROWS),
        "checked_scripts": len(REQUIRED_SCRIPTS),
        "replay_command_count": len(commands),
        "errors": errors,
        "db_writes": 0,
    }
    print("PARTNER_ACCEPTANCE_REPLAY_PACKAGE_VERIFY=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
    if errors:
        raise RuntimeError(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
