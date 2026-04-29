#!/usr/bin/env python3
"""Fetch and materialize the external migration asset package."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import tarfile
import tempfile
import urllib.request
from pathlib import Path
from typing import Any


REPO_ROOT = Path.cwd()
DEFAULT_LOCK = REPO_ROOT / "docs/migration_alignment/migration_asset_package_lock_v1.json"
README_TEXT = """# Migration Assets

The migration asset payloads are externalized and are no longer tracked in Git.

Materialize the locked package before running migration asset verification or
history replay:

```bash
make migration.assets.fetch
make migration.assets.verify_all
```

By default the lock records the locally generated package path used during this
cleanup. In another environment, set one of:

```bash
MIGRATION_ASSET_PACKAGE_PATH=/path/to/migration_assets_release_*.tar.gz
MIGRATION_ASSET_PACKAGE_URL=https://private-authenticated-object-store/...
```

Do not publish migration asset packages to public GitHub Releases. They contain
reconstructed user and business migration data.

The package hash is pinned in
`docs/migration_alignment/migration_asset_package_lock_v1.json`.
"""


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_package(lock: dict[str, Any]) -> Path:
    explicit_path = os.environ.get("MIGRATION_ASSET_PACKAGE_PATH")
    if explicit_path:
        return Path(explicit_path)

    locked_path = lock.get("package_path")
    if locked_path and Path(locked_path).is_file():
        return Path(locked_path)

    url = os.environ.get("MIGRATION_ASSET_PACKAGE_URL") or lock.get("package_url")
    if not url:
        raise SystemExit(
            "missing migration asset package: set MIGRATION_ASSET_PACKAGE_PATH "
            "or MIGRATION_ASSET_PACKAGE_URL"
        )

    cache_dir = Path(os.environ.get("MIGRATION_ASSET_CACHE_DIR", "/tmp/sce_migration_asset_release"))
    cache_dir.mkdir(parents=True, exist_ok=True)
    package_path = cache_dir / Path(url).name
    urllib.request.urlretrieve(url, package_path)
    return package_path


def safe_members(tar: tarfile.TarFile) -> list[tarfile.TarInfo]:
    members: list[tarfile.TarInfo] = []
    for member in tar.getmembers():
        target = Path(member.name)
        if target.is_absolute() or ".." in target.parts:
            raise SystemExit(f"unsafe tar member: {member.name}")
        allowed = (
            str(target).startswith("migration_assets/")
            or str(target).startswith("artifacts/migration/")
            or member.name == "migration_asset_release_manifest_v1.json"
        )
        if not allowed:
            raise SystemExit(f"unexpected tar member: {member.name}")
        members.append(member)
    return members


def copy_tree(src: Path, dst: Path) -> int:
    count = 0
    for path in sorted(src.rglob("*")):
        if not path.is_file():
            continue
        target = dst / path.relative_to(src)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        count += 1
    return count


def extract_package(package_path: Path, asset_root: Path, artifact_root: Path) -> dict[str, int]:
    with tempfile.TemporaryDirectory(prefix="sce_migration_assets_") as tmp_name:
        tmp_root = Path(tmp_name)
        with tarfile.open(package_path, "r:gz") as tar:
            members = safe_members(tar)
            tar.extractall(tmp_root, members=members)
        extracted_assets = tmp_root / "migration_assets"
        if not extracted_assets.is_dir():
            raise SystemExit("package does not contain migration_assets/")
        if asset_root.exists():
            shutil.rmtree(asset_root)
        asset_root.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(extracted_assets), str(asset_root))
        (asset_root / "README.md").write_text(README_TEXT, encoding="utf-8")

        artifact_count = 0
        extracted_artifacts = tmp_root / "artifacts/migration"
        if extracted_artifacts.is_dir():
            artifact_count = copy_tree(extracted_artifacts, artifact_root)

        return {
            "asset_file_count": sum(1 for path in asset_root.rglob("*") if path.is_file()),
            "artifact_file_count": artifact_count,
        }


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch and extract the locked migration asset package.")
    parser.add_argument("--lock", default=str(DEFAULT_LOCK), help="Asset package lock file")
    parser.add_argument("--asset-root", default="migration_assets", help="Extraction root")
    parser.add_argument("--artifact-root", default="artifacts/migration", help="Frozen replay artifact extraction root")
    args = parser.parse_args()

    lock_path = Path(args.lock)
    lock = load_json(lock_path)
    package_path = resolve_package(lock)
    expected_sha = lock.get("sha256")
    if not expected_sha:
        raise SystemExit(f"lock file missing sha256: {lock_path}")
    actual_sha = sha256_file(package_path)
    if actual_sha != expected_sha:
        raise SystemExit(f"sha256 mismatch: expected={expected_sha} actual={actual_sha}")

    counts = extract_package(package_path, Path(args.asset_root), Path(args.artifact_root))
    print(
        "MIGRATION_ASSET_FETCH="
        + json.dumps(
            {
                "status": "PASS",
                "package_id": lock.get("package_id"),
                "package_path": str(package_path),
                "asset_root": args.asset_root,
                "artifact_root": args.artifact_root,
                "file_count": counts["asset_file_count"] + counts["artifact_file_count"],
                "asset_file_count": counts["asset_file_count"],
                "artifact_file_count": counts["artifact_file_count"],
                "sha256": actual_sha,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
