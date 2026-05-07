#!/usr/bin/env python3
"""Build a self-contained partner business-aligned replay package."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tarfile
from datetime import UTC, datetime
from pathlib import Path


PACKAGE_NAME = "partner_business_aligned_replay_package_v1"
DEFAULT_SOURCE_ROOT = Path("artifacts/migration/partner_business_aligned_rebuild_v1")
DEFAULT_AUDIT_ROOT = Path("artifacts/migration/partner_import_source_audit_v1")
DEFAULT_OVERLAY_ROOT = Path("artifacts/migration/partner_business_alignment_overlay_v1")
DEFAULT_PACKAGE_ROOT = Path("artifacts/migration") / PACKAGE_NAME

REQUIRED_FILES = [
    {
        "source": DEFAULT_SOURCE_ROOT / "fact_based_partner_rebuild_business_aligned_result_v1.json",
        "target": "artifacts/migration/partner_business_aligned_rebuild_v1/fact_based_partner_rebuild_business_aligned_result_v1.json",
        "role": "business aligned payload summary",
    },
    {
        "source": DEFAULT_SOURCE_ROOT / "fact_based_partner_rebuild_payload_business_aligned_v1.csv",
        "target": "artifacts/migration/partner_business_aligned_rebuild_v1/fact_based_partner_rebuild_payload_business_aligned_v1.csv",
        "role": "unified replay payload for res.partner",
    },
    {
        "source": DEFAULT_SOURCE_ROOT / "fact_based_partner_rebuild_current_only_review_v1.csv",
        "target": "artifacts/migration/partner_business_aligned_rebuild_v1/fact_based_partner_rebuild_current_only_review_v1.csv",
        "role": "current payload rows absent from business source",
    },
    {
        "source": DEFAULT_SOURCE_ROOT / "fact_based_partner_rebuild_business_aligned_gate_result_v1.json",
        "target": "artifacts/migration/partner_business_aligned_rebuild_v1/fact_based_partner_rebuild_business_aligned_gate_result_v1.json",
        "role": "write gate summary",
    },
    {
        "source": DEFAULT_SOURCE_ROOT / "fact_based_partner_rebuild_business_aligned_gate_v1.csv",
        "target": "artifacts/migration/partner_business_aligned_rebuild_v1/fact_based_partner_rebuild_business_aligned_gate_v1.csv",
        "role": "write-gated unified payload",
    },
    {
        "source": DEFAULT_SOURCE_ROOT / "fact_based_partner_rebuild_business_aligned_write_candidates_v1.csv",
        "target": "artifacts/migration/partner_business_aligned_rebuild_v1/fact_based_partner_rebuild_business_aligned_write_candidates_v1.csv",
        "role": "safe create/update candidates",
    },
    {
        "source": DEFAULT_SOURCE_ROOT / "fact_based_partner_rebuild_business_aligned_update_only_v1.csv",
        "target": "artifacts/migration/partner_business_aligned_rebuild_v1/fact_based_partner_rebuild_business_aligned_update_only_v1.csv",
        "role": "existing-partner update-only candidates",
    },
    {
        "source": DEFAULT_SOURCE_ROOT / "fact_based_partner_rebuild_business_aligned_blocked_review_v1.csv",
        "target": "artifacts/migration/partner_business_aligned_rebuild_v1/fact_based_partner_rebuild_business_aligned_blocked_review_v1.csv",
        "role": "manual review queue",
    },
    {
        "source": DEFAULT_SOURCE_ROOT / "partner_import_review_queue_v1.csv",
        "target": "artifacts/migration/partner_business_aligned_rebuild_v1/partner_import_review_queue_v1.csv",
        "role": "application review queue for blocked partner candidates",
    },
    {
        "source": DEFAULT_SOURCE_ROOT / "partner_import_review_queue_result_v1.json",
        "target": "artifacts/migration/partner_business_aligned_rebuild_v1/partner_import_review_queue_result_v1.json",
        "role": "partner import review queue summary",
    },
    {
        "source": DEFAULT_AUDIT_ROOT / "summary_v1.json",
        "target": "artifacts/migration/partner_import_source_audit_v1/summary_v1.json",
        "role": "source audit summary",
    },
    {
        "source": DEFAULT_AUDIT_ROOT / "source_entities_v1.csv",
        "target": "artifacts/migration/partner_import_source_audit_v1/source_entities_v1.csv",
        "role": "normalized business source entities",
    },
    {
        "source": DEFAULT_OVERLAY_ROOT / "partner_business_alignment_summary_v1.json",
        "target": "artifacts/migration/partner_business_alignment_overlay_v1/partner_business_alignment_summary_v1.json",
        "role": "alignment overlay summary",
    },
]

OPTIONAL_FILES = [
    {
        "source": DEFAULT_SOURCE_ROOT / "partner_update_only_match_probe_v1.csv",
        "target": "artifacts/migration/partner_business_aligned_rebuild_v1/partner_update_only_match_probe_v1.csv",
        "role": "target database match probe for update-only candidates",
    },
    {
        "source": DEFAULT_SOURCE_ROOT / "partner_update_only_match_probe_result_v1.json",
        "target": "artifacts/migration/partner_business_aligned_rebuild_v1/partner_update_only_match_probe_result_v1.json",
        "role": "update-only match probe summary",
    },
    {
        "source": DEFAULT_SOURCE_ROOT / "partner_update_only_matched_updates_v1.csv",
        "target": "artifacts/migration/partner_business_aligned_rebuild_v1/partner_update_only_matched_updates_v1.csv",
        "role": "update-only rows with unique target match",
    },
    {
        "source": DEFAULT_SOURCE_ROOT / "partner_update_only_probe_review_queue_v1.csv",
        "target": "artifacts/migration/partner_business_aligned_rebuild_v1/partner_update_only_probe_review_queue_v1.csv",
        "role": "update-only rows requiring review after probe",
    },
    {
        "source": DEFAULT_SOURCE_ROOT / "partner_import_review_resolved_promotions_v1.csv",
        "target": "artifacts/migration/partner_business_aligned_rebuild_v1/partner_import_review_resolved_promotions_v1.csv",
        "role": "resolved review rows exported back to partner write contract",
    },
    {
        "source": DEFAULT_SOURCE_ROOT / "partner_import_review_ignored_v1.csv",
        "target": "artifacts/migration/partner_business_aligned_rebuild_v1/partner_import_review_ignored_v1.csv",
        "role": "ignored partner import review rows",
    },
]

SCRIPT_FILES = [
    "scripts/migration/partner_import_source_audit.py",
    "scripts/migration/partner_business_alignment_overlay.py",
    "scripts/migration/partner_business_aligned_rebuild_adapter.py",
    "scripts/migration/partner_business_aligned_rebuild_gate.py",
    "scripts/migration/partner_business_aligned_rebuild_write.py",
    "scripts/migration/partner_asset_generator.py",
    "scripts/migration/partner_asset_verify.py",
    "scripts/migration/partner_asset_business_fit_guard.py",
    "scripts/migration/partner_bank_business_asset_generator.py",
    "scripts/migration/fresh_db_partner_bank_replay_write.py",
    "scripts/migration/partner_import_review_asset_generator.py",
    "scripts/migration/fresh_db_partner_import_review_replay_write.py",
    "scripts/migration/fresh_db_partner_import_review_resolution_export.py",
    "scripts/migration/fresh_db_partner_update_only_match_probe.py",
    "scripts/migration/partner_update_only_probe_split.py",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def row_count(path: Path) -> int | None:
    if path.suffix.lower() != ".csv":
        return None
    with path.open("rb") as handle:
        return max(sum(1 for _ in handle) - 1, 0)


def copy_file(source: Path, package_root: Path, target_rel: str, role: str) -> dict[str, object]:
    if not source.exists():
        raise RuntimeError({"missing_required_package_file": str(source)})
    target = package_root / target_rel
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    return {
        "path": target_rel,
        "role": role,
        "bytes": target.stat().st_size,
        "rows": row_count(target),
        "sha256": sha256(target),
    }


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_tarball(package_root: Path) -> Path:
    tar_path = package_root.with_suffix(".tar.gz")
    if tar_path.exists():
        tar_path.unlink()
    with tarfile.open(tar_path, "w:gz") as archive:
        archive.add(package_root, arcname=package_root.name)
    return tar_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package-root", default=str(DEFAULT_PACKAGE_ROOT))
    args = parser.parse_args()

    package_root = Path(args.package_root)
    if package_root.exists():
        shutil.rmtree(package_root)
    package_root.mkdir(parents=True, exist_ok=True)

    files = []
    for item in REQUIRED_FILES:
        files.append(copy_file(item["source"], package_root, item["target"], item["role"]))
    skipped_optional_files = []
    for item in OPTIONAL_FILES:
        if item["source"].exists():
            files.append(copy_file(item["source"], package_root, item["target"], item["role"]))
        else:
            skipped_optional_files.append({"path": str(item["source"]), "role": item["role"]})
    for script in SCRIPT_FILES:
        files.append(copy_file(Path(script), package_root, script, "replay script"))

    manifest = {
        "package": PACKAGE_NAME,
        "created_at_utc": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "purpose": "Business-aligned partner replay package for the current model surface.",
        "db_writes_in_package_build": 0,
        "source_business_root": "/home/odoo/workspace/partner_import_source",
        "target_model": "res.partner",
        "model_surface": {
            "partner_fields": [
                "name",
                "company_type",
                "customer_rank",
                "supplier_rank",
                "sc_supplier_type",
                "sc_region",
                "street",
                "sc_registered_capital",
                "sc_business_scope",
                "sc_default_tax_rate",
                "sc_default_tax_rate_text",
                "sc_account_name",
                "sc_bank_name",
                "sc_bank_account",
                "vat",
                "legacy_partner_id",
                "legacy_partner_source",
                "legacy_partner_name",
                "legacy_credit_code",
                "legacy_tax_no",
                "legacy_source_evidence",
            ],
            "partner_bank_fields": [
                "partner_id",
                "acc_number",
                "sc_legacy_external_id",
                "sc_legacy_partner_source",
                "sc_legacy_partner_id",
                "sc_legacy_partner_name",
                "sc_account_holder_name",
                "sc_bank_name",
                "sc_source_evidence",
                "sc_import_batch",
            ],
            "review_model": "sc.partner.import.review",
            "bank_account_policy": "Write bank accounts to res.partner.bank after partner rows are loaded; keep res.partner account fields as compatibility surface only.",
        },
        "build_commands": [
            "python3 scripts/migration/partner_import_source_audit.py",
            "python3 scripts/migration/partner_business_alignment_overlay.py",
            "python3 scripts/migration/partner_business_aligned_rebuild_adapter.py",
            "python3 scripts/migration/partner_business_aligned_rebuild_gate.py",
            "python3 scripts/migration/partner_import_review_asset_generator.py --check",
            "python3 scripts/migration/partner_business_aligned_replay_package_build.py",
        ],
        "post_probe_commands": [
            "PARTNER_UPDATE_ONLY_GATE_CSV=artifacts/migration/partner_business_aligned_rebuild_v1/fact_based_partner_rebuild_business_aligned_gate_v1.csv python3 scripts/migration/fresh_db_partner_update_only_match_probe.py",
            "python3 scripts/migration/partner_update_only_probe_split.py --check",
            "PARTNER_IMPORT_REVIEW_BATCH=partner_business_fit_v1 python3 scripts/migration/fresh_db_partner_import_review_resolution_export.py",
        ],
        "dry_run_command": (
            "ENV=test ENV_FILE=.env.prod.sim DB_NAME=sc_prod_sim MIGRATION_WRITE_MODE=dry-run "
            "bash scripts/ops/odoo_shell_exec.sh < scripts/migration/partner_business_aligned_rebuild_write.py"
        ),
        "write_command": (
            "ENV=test ENV_FILE=.env.prod.sim DB_NAME=sc_prod_sim MIGRATION_WRITE_MODE=write "
            "bash scripts/ops/odoo_shell_exec.sh < scripts/migration/partner_business_aligned_rebuild_write.py"
        ),
        "files": files,
        "skipped_optional_files": skipped_optional_files,
    }
    manifest_path = package_root / "manifest.json"
    write_json(manifest_path, manifest)
    tar_path = build_tarball(package_root)
    result = {
        "status": "PASS",
        "package_root": str(package_root),
        "manifest": str(manifest_path),
        "tarball": str(tar_path),
        "tarball_bytes": tar_path.stat().st_size,
        "tarball_sha256": sha256(tar_path),
        "file_count": len(files) + 1,
        "db_writes": 0,
    }
    write_json(package_root / "package_build_result_v1.json", result)
    print("PARTNER_BUSINESS_ALIGNED_REPLAY_PACKAGE=" + json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
