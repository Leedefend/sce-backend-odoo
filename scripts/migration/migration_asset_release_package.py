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
import tarfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path.cwd()
DEFAULT_ASSET_ROOT = REPO_ROOT / "migration_assets"
MIGRATION_ARTIFACT_ROOT = REPO_ROOT / "artifacts/migration"
OUTPUT_JSON = REPO_ROOT / "artifacts/migration/migration_asset_release_package_v1.json"
OUTPUT_MD = REPO_ROOT / "docs/migration_alignment/migration_asset_release_package_v1.md"
DEFAULT_OUT_DIR = Path("/tmp/sce_migration_asset_release")
EXCLUDED_TOKEN = ".xml.parts/"
EVIDENCE_FILES = [
    "migration_assets/manifest/migration_asset_coverage_snapshot_v1.json",
    "migration_assets/manifest/receipt_blocker_policy_snapshot_v1.json",
]


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

    for path in sorted(MIGRATION_ARTIFACT_ROOT.rglob("*")):
        if not path.is_file() or should_exclude_artifact(path):
            continue
        add(path, "migration_artifact")

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
        "file_count": len(files),
        "excluded_paths": excluded_paths,
        "files": files,
    }
    manifest_bytes = json.dumps(release_manifest, ensure_ascii=False, indent=2).encode("utf-8") + b"\n"

    with tarfile.open(package_path, "w:gz") as tar:
        for item in files:
            add_file(tar, REPO_ROOT / item["path"], item["path"])
        add_bytes(tar, "migration_asset_release_manifest_v1.json", manifest_bytes)

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

    payload = build_package(Path(args.asset_root), Path(args.out_dir), args.package_id)
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
