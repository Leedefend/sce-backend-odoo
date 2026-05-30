#!/usr/bin/env python3
"""Build the SCBS55 full migration asset inventory.

This is a read-only inventory for the migration freeze topic. It intentionally
does not hash large runtime payloads; package integrity stays with the release
lock and delivery audit.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_ROOT = ROOT / "artifacts/migration"
ASSET_ROOT = ROOT / "migration_assets"
ONECLICK = ROOT / "scripts/migration/history_continuity_oneclick.sh"
FREEZE = ROOT / "docs/migration_alignment/scbs55_full_migration_asset_freeze_v1.json"
PACKAGE_LOCK = ROOT / "docs/migration_alignment/migration_asset_package_lock_v1.json"
COMPARE = ROOT / "artifacts/migration/scbs55_wutao_old_new_final_aligned_compare.json"
OUTPUT_JSON = ROOT / "docs/migration_alignment/scbs55_full_migration_asset_inventory_v1.json"
OUTPUT_MD = ROOT / "docs/migration_alignment/scbs55_full_migration_asset_inventory_v1.md"

RUN_STEP_RE = re.compile(r"run_step\s+([A-Za-z0-9_]+)\s+(.*)")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def size_mb(size: int) -> float:
    return round(size / 1024 / 1024, 2)


def file_rows(root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not root.exists():
        return rows
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        stat = path.stat()
        rows.append(
            {
                "path": rel(path),
                "suffix": path.suffix.lower() or "<none>",
                "size_bytes": stat.st_size,
                "size_mb": size_mb(stat.st_size),
                "category": artifact_category(path),
            }
        )
    return rows


def artifact_category(path: Path) -> str:
    text = rel(path)
    name = path.name
    if "scbs_55_old_live_full_rows" in text or "scbs55_old_pages" in text:
        return "old_live_row_dump"
    if "old_live_list_ids" in text:
        return "old_live_identity_dump"
    if name.endswith("_payload_v1.csv") or "payload" in name:
        return "replay_payload"
    if name.endswith("_adapter_result_v1.json"):
        return "adapter_result"
    if name.endswith("_write_result_v1.json"):
        return "write_result"
    if "probe" in name:
        return "probe_evidence"
    if "compare" in name or "count" in name:
        return "comparison_evidence"
    if path.suffix.lower() in {".png", ".jpg", ".jpeg"}:
        return "browser_screenshot"
    if path.suffix.lower() == ".tsv":
        return "visible_surface_export"
    return "other_artifact"


def summarize_files(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_category = Counter(row["category"] for row in rows)
    by_suffix = Counter(row["suffix"] for row in rows)
    total_size = sum(int(row["size_bytes"]) for row in rows)
    return {
        "file_count": len(rows),
        "total_size_mb": size_mb(total_size),
        "by_category": dict(sorted(by_category.items())),
        "by_suffix": dict(sorted(by_suffix.items())),
        "largest_files": sorted(rows, key=lambda item: int(item["size_bytes"]), reverse=True)[:20],
    }


def oneclick_steps() -> dict[str, Any]:
    text = ONECLICK.read_text(encoding="utf-8") if ONECLICK.exists() else ""
    rows: list[dict[str, Any]] = []
    for line in text.splitlines():
        match = RUN_STEP_RE.search(line)
        if not match:
            continue
        step_index = len(rows) + 1
        step = match.group(1)
        command = match.group(2).strip()
        if step.endswith("_adapter"):
            kind = "adapter"
        elif step.endswith("_replay") or step.endswith("_completed") or step.endswith("_pending"):
            kind = "write_replay"
        elif "projection" in step:
            kind = "formal_projection"
        elif "probe" in step:
            kind = "probe"
        elif "normalize" in step:
            kind = "normalization"
        else:
            kind = "other"
        rows.append({"step_index": step_index, "step": step, "kind": kind, "command": command[:220]})
    return {
        "script": rel(ONECLICK),
        "step_count": len(rows),
        "by_kind": dict(sorted(Counter(row["kind"] for row in rows).items())),
        "first_steps": rows[:12],
        "last_steps": rows[-12:],
        "steps": rows,
    }


def compare_summary() -> dict[str, Any]:
    if not COMPARE.exists():
        return {"exists": False}
    payload = load_json(COMPARE)
    rows = payload.get("rows") if isinstance(payload.get("rows"), list) else []
    return {
        "exists": True,
        "path": rel(COMPARE),
        "status": payload.get("status"),
        "checked_count": payload.get("checked_count"),
        "blocking_count": payload.get("blocking_count"),
        "total_old_rows": sum(int(row.get("old_count") or 0) for row in rows if isinstance(row, dict)),
        "total_new_rows": sum(int(row.get("new_count") or 0) for row in rows if isinstance(row, dict)),
        "surfaces": [
            {
                "seq": row.get("seq"),
                "name": row.get("name"),
                "old_count": row.get("old_count"),
                "new_count": row.get("new_count"),
                "status": row.get("status"),
            }
            for row in rows
            if isinstance(row, dict)
        ],
    }


def script_status() -> dict[str, Any]:
    ungoverned = [
        "frontend/apps/web/scripts/user_list_field_data_coverage.cjs",
        "scripts/migration/scbs55_live_delta_backfill_write.py",
    ]
    return {
        "ungoverned_runtime_scripts": [
            {
                "path": item,
                "exists": (ROOT / item).exists(),
                "decision": "reference_only_not_delivery_asset",
                "reason": "not constrained by full migration package lock and evidence manifest",
            }
            for item in ungoverned
        ]
    }


def package_summary() -> dict[str, Any]:
    lock = load_json(PACKAGE_LOCK) if PACKAGE_LOCK.exists() else {}
    asset_files = file_rows(ASSET_ROOT)
    return {
        "lock_file": rel(PACKAGE_LOCK),
        "package_id": lock.get("package_id"),
        "sha256": lock.get("sha256"),
        "package_size_mb": lock.get("package_size_mb"),
        "materializes": lock.get("materializes"),
        "repo_asset_files": summarize_files(asset_files),
    }


def build_inventory() -> dict[str, Any]:
    artifact_files = file_rows(ARTIFACT_ROOT)
    return {
        "inventory_version": "scbs55_full_migration_asset_inventory_v1",
        "status": "PASS",
        "scope_freeze": rel(FREEZE),
        "package": package_summary(),
        "runtime_artifacts": summarize_files(artifact_files),
        "full_visibility_compare": compare_summary(),
        "history_continuity": oneclick_steps(),
        "script_status": script_status(),
        "promotion_policy": {
            "deliverable": [
                "package lock",
                "catalog-referenced migration_assets",
                "packaged artifacts/migration replay payloads",
                "guard outputs required by docs/migration_alignment/migration_asset_delivery_manifest_v1.md",
            ],
            "not_deliverable_without_promotion": [
                "ad hoc online patches",
                "unbounded live delta backfill scripts",
                "local /tmp row dumps",
                "development database residual records",
            ],
        },
    }


def render_markdown(payload: dict[str, Any]) -> str:
    artifacts = payload["runtime_artifacts"]
    oneclick = payload["history_continuity"]
    compare = payload["full_visibility_compare"]
    categories = "\n".join(f"- `{key}`: `{value}`" for key, value in artifacts["by_category"].items())
    largest = "\n".join(f"- `{row['path']}`: `{row['size_mb']} MB`" for row in artifacts["largest_files"][:10])
    step_kinds = "\n".join(f"- `{key}`: `{value}`" for key, value in oneclick["by_kind"].items())
    return f"""# SCBS55 Full Migration Asset Inventory v1

Status: `{payload["status"]}`

## Scope

- freeze: `{payload["scope_freeze"]}`
- package: `{payload["package"]["package_id"]}`
- materializes: `{payload["package"]["materializes"]}`
- 42-surface evidence: `{compare.get("path", "")}`

## Runtime Artifacts

- files: `{artifacts["file_count"]}`
- total size MB: `{artifacts["total_size_mb"]}`

### By Category

{categories}

### Largest Files

{largest}

## User Visible Surface Evidence

- exists: `{compare.get("exists")}`
- status: `{compare.get("status")}`
- checked count: `{compare.get("checked_count")}`
- blocking count: `{compare.get("blocking_count")}`
- total old rows: `{compare.get("total_old_rows")}`
- total new rows: `{compare.get("total_new_rows")}`

## History Continuity Replay

- script: `{oneclick["script"]}`
- steps: `{oneclick["step_count"]}`

### Step Kinds

{step_kinds}

## Ungoverned Runtime Scripts

""" + "\n".join(
        f"- `{row['path']}`: `{row['decision']}`"
        for row in payload["script_status"]["ungoverned_runtime_scripts"]
    ) + "\n"


def main() -> int:
    payload = build_inventory()
    OUTPUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    OUTPUT_MD.write_text(render_markdown(payload), encoding="utf-8")
    print(
        "SCBS55_FULL_MIGRATION_ASSET_INVENTORY="
        + json.dumps(
            {
                "status": payload["status"],
                "artifact_files": payload["runtime_artifacts"]["file_count"],
                "artifact_size_mb": payload["runtime_artifacts"]["total_size_mb"],
                "history_steps": payload["history_continuity"]["step_count"],
                "visible_surfaces": payload["full_visibility_compare"].get("checked_count"),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
