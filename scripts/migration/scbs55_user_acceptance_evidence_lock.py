#!/usr/bin/env python3
"""Generate a hash lock for SCBS55 user-acceptance migration evidence files."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "docs/migration_alignment/scbs55_user_acceptance_asset_freeze_v1.json"
DEFAULT_OLD_ROWS_DIR = Path("/tmp/scbs55_old_pages_20260530")
DEFAULT_BROWSER_SUMMARY = Path("/tmp/scbs55_six_pages_aligned_20260530/summary.json")
DEFAULT_OUTPUT = ROOT / "docs/migration_alignment/scbs55_user_acceptance_evidence_lock_v1.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def rows_from_dump(path: Path) -> list[dict[str, Any]]:
    payload = load_json(path)
    rows = payload.get("rows") if isinstance(payload, dict) else None
    if not isinstance(rows, list):
        raise RuntimeError(f"{path} does not contain rows[]")
    return [row for row in rows if isinstance(row, dict)]


def browser_totals(path: Path) -> dict[int, int]:
    payload = load_json(path)
    out: dict[int, int] = {}
    for row in payload.get("rows", []) if isinstance(payload, dict) else []:
        if not isinstance(row, dict):
            continue
        menu = int(row.get("menu") or 0)
        total = int(row.get("total") or 0)
        if menu:
            out[menu] = total
    return out


def build_lock(old_rows_dir: Path, browser_summary: Path) -> dict[str, Any]:
    manifest = load_json(MANIFEST)
    if not isinstance(manifest, dict) or not isinstance(manifest.get("surfaces"), list):
        raise RuntimeError("manifest surfaces missing")
    browser = browser_totals(browser_summary)
    surfaces: list[dict[str, Any]] = []
    for surface in manifest["surfaces"]:
        old = surface["old"]
        new = surface["new"]
        row_file = old_rows_dir / old["row_dump_file"]
        rows = rows_from_dump(row_file)
        identity = str(old["identity_field"])
        identities = [str(row.get(identity) or "").strip() for row in rows]
        surfaces.append(
            {
                "key": surface["key"],
                "name": surface["name"],
                "old_config_id": old["config_id"],
                "old_main_table": old["main_table"],
                "old_expected_count": old["expected_count"],
                "old_row_dump_file": old["row_dump_file"],
                "old_row_dump_sha256": sha256_file(row_file),
                "old_row_dump_size_bytes": row_file.stat().st_size,
                "old_row_count": len(rows),
                "old_identity_field": identity,
                "old_identity_count": len(identities),
                "old_identity_unique_count": len(set(identities)),
                "old_identity_missing_count": len([value for value in identities if not value]),
                "new_menu_id": new["menu_id"],
                "new_action_id": new["action_id"],
                "new_model": new["model"],
                "new_expected_count": new["expected_count"],
                "browser_total": browser.get(int(new["menu_id"])),
            }
        )
    return {
        "lock_version": "scbs55_user_acceptance_evidence_lock_v1",
        "asset_package_id": manifest["asset_package_id"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_manifest": str(MANIFEST.relative_to(ROOT)),
        "old_rows_dir_note": "Raw row dumps are evidence inputs; do not commit user data to git.",
        "browser_summary": {
            "path": str(browser_summary),
            "sha256": sha256_file(browser_summary),
            "size_bytes": browser_summary.stat().st_size,
        },
        "surface_count": len(surfaces),
        "surfaces": surfaces,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--old-rows-dir", default=str(DEFAULT_OLD_ROWS_DIR))
    parser.add_argument("--browser-summary", default=str(DEFAULT_BROWSER_SUMMARY))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()
    output = Path(args.output)
    lock = build_lock(Path(args.old_rows_dir), Path(args.browser_summary))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(lock, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"SCBS55_USER_ACCEPTANCE_EVIDENCE_LOCK={output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
