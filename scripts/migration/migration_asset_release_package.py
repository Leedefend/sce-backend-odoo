#!/usr/bin/env python3
"""Build the migration asset release package.

The package contains production-loadable migration assets, frozen replay
payloads, and governance evidence files. It intentionally excludes materialized
XML parts because the delivery decision is to ship the complete XML file for
legacy workflow audit.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import tarfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path.cwd()
DEFAULT_ASSET_ROOT = REPO_ROOT / "migration_assets"
MIGRATION_ARTIFACT_ROOT = REPO_ROOT / "artifacts/migration"
ONECLICK = REPO_ROOT / "scripts/migration/history_continuity_oneclick.sh"
OUTPUT_JSON = REPO_ROOT / "artifacts/migration/migration_asset_release_package_v1.json"
OUTPUT_MD = REPO_ROOT / "docs/migration_alignment/migration_asset_release_package_v1.md"
DEFAULT_OUT_DIR = Path("/tmp/sce_migration_asset_release")
EXCLUDED_TOKEN = ".xml.parts/"
EVIDENCE_FILES = [
    "migration_assets/manifest/migration_asset_coverage_snapshot_v1.json",
    "migration_assets/manifest/receipt_blocker_policy_snapshot_v1.json",
]
DEPLOYMENT_FILES = [
    "Makefile",
    "scripts/common/env.sh",
    "scripts/common/guard_prod.sh",
    "scripts/deploy/fresh_production_history_init.sh",
    "scripts/ops/odoo_shell_exec.sh",
    "scripts/migration/history_continuity_oneclick.sh",
    "scripts/migration/migration_asset_bus.py",
    "scripts/migration/migration_asset_catalog_verify.py",
    "scripts/migration/migration_asset_release_package.py",
]
ARTIFACT_INPUT_RE = re.compile(
    r'^\s*(?P<var>[A-Z][A-Z0-9_]*)\s*=\s*REPO_ROOT\s*/\s*"(?P<path>artifacts/migration/[^"]+)"',
    re.MULTILINE,
)
ONECLICK_SCRIPT_RE = re.compile(r'run_odoo_script\s+"\$ROOT_DIR/scripts/migration/(?P<script>[^"]+\.py)"')
EXTRA_REPLAY_SCRIPT_NAMES = [
    "fresh_db_replay_payload_precheck.py",
]
EXTRA_REQUIRED_REPLAY_ARTIFACTS = {
    # Variable/function-based one-click dependencies that are required for
    # packaged replay but are not discoverable by the legacy direct regex.
    "artifacts/migration/fresh_db_project_anchor_replay_rollback_targets_v1.csv",
    "artifacts/migration/fresh_db_replay_manifest_v1.json",
    "artifacts/migration/project_member_neutral_34_write_result_v1.json",
}
MANDATORY_BUSINESS_SCOPE_ARTIFACTS = {
    # Tender history is part of the user-visible delivery scope.  These replay
    # payloads are not XML catalog packages, so the release package must carry
    # them explicitly for old-DB-free replay.
    "tender_history": [
        "artifacts/migration/fresh_db_legacy_tender_registration_replay_adapter_result_v1.json",
        "artifacts/migration/fresh_db_legacy_tender_registration_replay_payload_v1.csv",
    ],
}
BASELINE_EXCLUDED_REQUIRED_ARTIFACTS = {
    # Default-off privacy lanes. These are intentionally not shipped in the
    # baseline package because they may contain sensitive personal data.
    "artifacts/migration/fresh_db_legacy_attendance_checkin_replay_adapter_result_v1.json",
    "artifacts/migration/fresh_db_legacy_attendance_checkin_replay_payload_v1.csv",
    "artifacts/migration/fresh_db_legacy_personnel_movement_replay_adapter_result_v1.json",
    "artifacts/migration/fresh_db_legacy_personnel_movement_replay_payload_v1.csv",
    "artifacts/migration/fresh_db_legacy_salary_line_replay_adapter_result_v1.json",
    "artifacts/migration/fresh_db_legacy_salary_line_replay_payload_v1.csv",
    # Default-off recovery lanes backed by old downstream snapshots.
    "artifacts/migration/history_payment_request_outflow_approved_recovery_payload_v1.csv",
    "artifacts/migration/history_payment_request_outflow_done_recovery_payload_v1.csv",
    "artifacts/migration/history_project_lifecycle_continuity_payload_v1.csv",
    # Deprecated recovery lanes skipped when authoritative XML assets exist.
    "artifacts/migration/contract_12_row_write_authorization_packet_v1.json",
    "artifacts/migration/contract_12_row_write_authorization_payload_v1.csv",
    "artifacts/migration/contract_partner_source_57_design_rows_v1.csv",
    "artifacts/migration/fresh_db_contract_57_retry_rollback_targets_v1.csv",
    "artifacts/migration/fresh_db_contract_partner_12_anchor_replay_resolution_v1.csv",
    "artifacts/migration/history_contract_direction_defer_recovery_payload_v1.csv",
    "artifacts/migration/history_contract_partner_recovery_payload_v1.csv",
    "artifacts/migration/history_contract_unreached_ready_replay_payload_v1.csv",
    "artifacts/migration/history_partner_master_direction_defer_replay_payload_v1.csv",
    "artifacts/migration/history_partner_master_targeted_replay_payload_v1.csv",
    "artifacts/migration/history_receipt_parent_recovery_adapter_result_v1.json",
    "artifacts/migration/history_receipt_parent_recovery_payload_v1.csv",
    "artifacts/migration/history_receipt_partner_targeted_replay_payload_v1.csv",
}


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def rel(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def should_exclude(path: str) -> bool:
    return EXCLUDED_TOKEN in path


def should_exclude_artifact(path: Path) -> bool:
    return path == OUTPUT_JSON


def required_replay_artifacts() -> list[str]:
    required: set[str] = set()
    oneclick_text = ONECLICK.read_text(encoding="utf-8") if ONECLICK.exists() else ""
    script_names = sorted(set(ONECLICK_SCRIPT_RE.findall(oneclick_text)) | set(EXTRA_REPLAY_SCRIPT_NAMES))
    for script_name in script_names:
        script = REPO_ROOT / "scripts/migration" / script_name
        if not script.is_file():
            continue
        text = script.read_text(encoding="utf-8")
        for match in ARTIFACT_INPUT_RE.finditer(text):
            var = match.group("var")
            if var.startswith("OUTPUT"):
                continue
            path = match.group("path")
            if path in BASELINE_EXCLUDED_REQUIRED_ARTIFACTS:
                continue
            required.add(path)
    for artifacts in MANDATORY_BUSINESS_SCOPE_ARTIFACTS.values():
        required.update(artifacts)
    required.update(EXTRA_REQUIRED_REPLAY_ARTIFACTS)
    return sorted(required)


def deployment_script_files() -> list[str]:
    files = set(DEPLOYMENT_FILES)
    for pattern in ("*.py", "*.sh"):
        for path in sorted((REPO_ROOT / "scripts/migration").glob(pattern)):
            files.add(rel(path))
    return sorted(files)


def collect_files(asset_root: Path) -> tuple[list[dict[str, Any]], list[str]]:
    catalog_path = asset_root / "manifest/migration_asset_catalog_v1.json"
    catalog = load_json(catalog_path)
    files: dict[str, dict[str, Any]] = {}
    warnings: list[str] = []

    def add(path: Path, kind: str) -> None:
        rel_path = rel(path)
        if should_exclude(rel_path):
            warnings.append(f"excluded_parts={rel_path}")
            return
        if not path.is_file():
            raise FileNotFoundError(rel_path)
        files[rel_path] = {
            "path": rel_path,
            "kind": kind,
            "size_bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }

    add(catalog_path, "catalog")
    for package in catalog.get("packages", []):
        manifest_path = asset_root / package["asset_manifest_path"]
        add(manifest_path, "asset_manifest")
        manifest = load_json(manifest_path)
        for asset in manifest.get("assets", []):
            add(asset_root / asset["path"], "asset")

    for evidence in EVIDENCE_FILES:
        path = REPO_ROOT / evidence
        if path.is_file():
            add(path, "delivery_evidence")
        else:
            warnings.append(f"missing_optional_evidence={evidence}")

    missing_required_artifacts = [
        path
        for path in required_replay_artifacts()
        if not (REPO_ROOT / path).is_file()
    ]
    if missing_required_artifacts:
        raise FileNotFoundError(
            "missing required frozen replay artifacts for packaged replay: "
            + ", ".join(missing_required_artifacts[:20])
            + (f" ... (+{len(missing_required_artifacts) - 20} more)" if len(missing_required_artifacts) > 20 else "")
        )

    for path in sorted(MIGRATION_ARTIFACT_ROOT.rglob("*")):
        if not path.is_file() or should_exclude_artifact(path):
            continue
        add(path, "migration_artifact")

    for path_text in deployment_script_files():
        path = REPO_ROOT / path_text
        if path.is_file():
            add(path, "deployment_runtime")
        else:
            warnings.append(f"missing_optional_deployment_file={path_text}")

    return [files[key] for key in sorted(files)], warnings


def add_file(tar: tarfile.TarFile, file_path: Path, arcname: str) -> None:
    info = tar.gettarinfo(str(file_path), arcname=arcname)
    info.uid = 0
    info.gid = 0
    info.uname = ""
    info.gname = ""
    info.mtime = 0
    with file_path.open("rb") as handle:
        tar.addfile(info, handle)


def add_bytes(tar: tarfile.TarFile, arcname: str, data: bytes) -> None:
    info = tarfile.TarInfo(arcname)
    info.size = len(data)
    info.uid = 0
    info.gid = 0
    info.uname = ""
    info.gname = ""
    info.mtime = 0
    info.mode = 0o644
    tar.addfile(info, io.BytesIO(data))


def build_package(asset_root: Path, out_dir: Path, package_id: str) -> dict[str, Any]:
    files, warnings = collect_files(asset_root)
    excluded_paths = [
        rel(path)
        for path in sorted(asset_root.rglob("*"))
        if path.is_file() and should_exclude(rel(path))
    ]
    package_name = f"{package_id}.tar.gz"
    package_path = out_dir / package_name
    sha_path = out_dir / f"{package_name}.sha256"
    out_dir.mkdir(parents=True, exist_ok=True)

    release_manifest = {
        "manifest_id": "migration_asset_release_package_v1",
        "package_id": package_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "catalog": rel(asset_root / "manifest/migration_asset_catalog_v1.json"),
        "payload_mode": "packaged_artifacts",
        "deployment_entrypoint": "scripts/migration/history_continuity_oneclick.sh",
        "deployment_verification_commands": [
            "python3 scripts/migration/migration_asset_bus.py --asset-root migration_assets --catalog migration_assets/manifest/migration_asset_catalog_v1.json --verify-only --check",
            "python3 scripts/migration/migration_asset_delivery_audit.py --asset-root migration_assets",
            "HISTORY_CONTINUITY_MODE=rehearse HISTORY_CONTINUITY_USE_PACKAGED_PAYLOADS=1 DB_NAME=<target_db> MIGRATION_REPLAY_DB_ALLOWLIST=<target_db> bash scripts/migration/history_continuity_oneclick.sh",
            "HISTORY_CONTINUITY_MODE=replay HISTORY_CONTINUITY_USE_PACKAGED_PAYLOADS=1 DB_NAME=<target_db> MIGRATION_REPLAY_DB_ALLOWLIST=<target_db> bash scripts/migration/history_continuity_oneclick.sh",
        ],
        "mandatory_business_scope_artifacts": MANDATORY_BUSINESS_SCOPE_ARTIFACTS,
        "file_count": len(files),
        "excluded_paths": excluded_paths,
        "files": files,
    }
    manifest_bytes = json.dumps(release_manifest, ensure_ascii=False, indent=2).encode("utf-8") + b"\n"

    with tarfile.open(package_path, "w:gz") as tar:
        for item in files:
            add_file(tar, REPO_ROOT / item["path"], item["path"])
        add_bytes(tar, "migration_asset_release_manifest_v1.json", manifest_bytes)

    with tarfile.open(package_path, "r:gz") as tar:
        packaged_names = sorted(member.name for member in tar.getmembers() if member.isfile())
    expected_names = sorted([item["path"] for item in files] + ["migration_asset_release_manifest_v1.json"])
    if packaged_names != expected_names:
        missing = sorted(set(expected_names) - set(packaged_names))
        extra = sorted(set(packaged_names) - set(expected_names))
        raise RuntimeError(f"release package file list drift: missing={missing[:20]} extra={extra[:20]}")

    package_sha = sha256_file(package_path)
    sha_path.write_text(f"{package_sha}  {package_name}\n", encoding="utf-8")

    payload = {
        "status": "PASS",
        "mode": "migration_asset_release_package",
        "db_writes": 0,
        "package_id": package_id,
        "package_path": str(package_path),
        "sha256_path": str(sha_path),
        "sha256": package_sha,
        "package_size_bytes": package_path.stat().st_size,
        "package_size_mb": round(package_path.stat().st_size / 1024 / 1024, 2),
        "included_file_count": len(files),
        "excluded_file_count": len(excluded_paths),
        "excluded_paths": excluded_paths,
        "warnings": warnings,
        "payload_mode": "packaged_artifacts",
        "release_manifest_sha256": sha256_bytes(manifest_bytes),
    }
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Migration Asset Release Package v1",
        "",
        f"Status: `{payload['status']}`",
        "",
        f"- package_id: `{package_id}`",
        f"- package_path: `{package_path}`",
        f"- sha256_path: `{sha_path}`",
        f"- sha256: `{package_sha}`",
        f"- package_size_mb: `{payload['package_size_mb']}`",
        f"- included_file_count: `{len(files)}`",
        f"- excluded_file_count: `{len(excluded_paths)}`",
        "- payload_mode: `packaged_artifacts`",
        "- deployment_entrypoint: `scripts/migration/history_continuity_oneclick.sh`",
        "",
        "## Excluded Paths",
        "",
    ]
    if excluded_paths:
        lines.extend(f"- `{item}`" for item in excluded_paths)
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Verification",
            "",
            "- Excluded `.xml.parts` files are not packaged.",
            "- `artifacts/migration` replay payloads are packaged for old-DB-free production replay.",
            "- Replay entrypoint, migration Python scripts, and migration shell scripts are packaged with the assets.",
            "- Verify the package with `MIGRATION_ASSET_RELEASE_PACKAGE=<package_path> make migration.assets.release_package.verify`.",
            "- Verify after extraction with `python3 scripts/migration/migration_asset_bus.py --asset-root migration_assets --catalog migration_assets/manifest/migration_asset_catalog_v1.json --verify-only --check`.",
            "- Verify packaged replay scope with `python3 scripts/migration/migration_asset_delivery_audit.py --asset-root migration_assets`.",
            "- Rehearse against a fresh target DB with `HISTORY_CONTINUITY_MODE=rehearse HISTORY_CONTINUITY_USE_PACKAGED_PAYLOADS=1 DB_NAME=<target_db> MIGRATION_REPLAY_DB_ALLOWLIST=<target_db> bash scripts/migration/history_continuity_oneclick.sh`.",
        ]
    )
    OUTPUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Build migration asset release tarball.")
    parser.add_argument("--asset-root", default=str(DEFAULT_ASSET_ROOT), help="Migration asset root")
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR), help="Output directory for tarball")
    parser.add_argument("--package-id", default=f"migration_assets_release_{utc_stamp()}", help="Package id")
    args = parser.parse_args()

    payload = build_package(Path(args.asset_root).resolve(), Path(args.out_dir), args.package_id)
    print(
        "MIGRATION_ASSET_RELEASE_PACKAGE="
        + json.dumps(
            {
                "status": payload["status"],
                "package_path": payload["package_path"],
                "sha256_path": payload["sha256_path"],
                "package_size_mb": payload["package_size_mb"],
                "included_file_count": payload["included_file_count"],
                "excluded_file_count": payload["excluded_file_count"],
                "payload_mode": payload["payload_mode"],
                "db_writes": 0,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
