#!/usr/bin/env python3
"""Build the SCBS no-legacy replay asset package.

The package is intentionally a compact business-fact package. It does not
include the restored legacy database and does not replay the old full material
master/library; material replay is limited to the material catalog facts needed
by SCBS stock-in documents.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path


PACKAGE_NAME = "scbs_replay_asset_v1"
SOURCE_ROOT = Path("artifacts/migration")
PACKAGE_ROOT = SOURCE_ROOT / PACKAGE_NAME
PACKAGE_ARTIFACT_ROOT = PACKAGE_ROOT / "artifacts/migration"

ASSET_FILES = [
    {
        "name": "scbs_fact_staging_v1.csv",
        "role": "source business facts staging",
        "required": True,
    },
    {
        "name": "scbs_source_creator_supplement_v1.csv",
        "role": "old-system creator/time evidence for SCBS source facts",
        "required": True,
    },
    {
        "name": "scbs_business_entity_candidates_v1.csv",
        "role": "business entity mapping candidates",
        "required": True,
    },
    {
        "name": "scbs_project_candidates_v1.csv",
        "role": "project mapping candidates",
        "required": True,
    },
    {
        "name": "scbs_partner_candidates_v1.csv",
        "role": "duplicate/conflict partner mapping candidates",
        "required": True,
    },
    {
        "name": "scbs_base_system_project_links_v1.csv",
        "role": "BASE_SYSTEM unspecified project links exported from new-system facts",
        "required": True,
    },
    {
        "name": "scbs_stock_in_legacy_lines_v1.csv",
        "role": "stock-in line facts exported once from legacy source",
        "required": True,
    },
    {
        "name": "scbs_stock_in_material_mapping_workbook_v1.csv",
        "role": "material catalog mapping workbook, not full material library replay",
        "required": True,
    },
    {
        "name": "scbs_fund_daily_source_v1.csv",
        "role": "enterprise fund daily source facts exported once from legacy source",
        "required": True,
    },
    {
        "name": "scbs_replay_expected_baseline_v1.json",
        "role": "accepted previous rebuild baseline for empty-database replay reconciliation",
        "required": True,
    },
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


def main() -> None:
    missing = [item["name"] for item in ASSET_FILES if not (SOURCE_ROOT / item["name"]).exists()]
    if missing:
        raise RuntimeError({"missing_required_assets": missing})

    PACKAGE_ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    manifest_files = []
    for item in ASSET_FILES:
        source = SOURCE_ROOT / item["name"]
        target = PACKAGE_ARTIFACT_ROOT / item["name"]
        shutil.copy2(source, target)
        manifest_files.append(
            {
                "name": item["name"],
                "role": item["role"],
                "path": str(Path("artifacts/migration") / item["name"]),
                "bytes": target.stat().st_size,
                "rows": row_count(target),
                "sha256": sha256(target),
            }
        )

    manifest = {
        "package": PACKAGE_NAME,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "asset_root": str(PACKAGE_ROOT),
        "business_policy": {
            "legacy_database_required": False,
            "material_replay_scope": "SCBS stock-in material mapping and material catalog facts only",
            "full_legacy_material_library_replay": False,
            "base_system_unspecified_project_links": True,
        },
        "files": manifest_files,
        "expected_replay_targets": {
            "staging_rows": 15223,
            "base_system_project_link_rows": 2269,
            "base_system_project_count": 21,
            "fund_daily_rows": 3798,
        },
    }
    manifest_path = PACKAGE_ROOT / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("SCBS_REPLAY_ASSET_PACKAGE=" + json.dumps(manifest, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
