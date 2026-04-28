#!/usr/bin/env python3
"""Audit migration assets for production delivery packaging.

This audit is intentionally read-only. It checks the frozen asset catalog,
asset manifests, packaging risks, and replay entrypoints, then writes a concise
delivery report for release handoff.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


REPO_ROOT = Path.cwd()
ASSET_ROOT = REPO_ROOT / "migration_assets"
CATALOG = ASSET_ROOT / "manifest/migration_asset_catalog_v1.json"
ONECLICK = REPO_ROOT / "scripts/migration/history_continuity_oneclick.sh"
PRODUCTION_ENTRY = REPO_ROOT / "scripts/deploy/fresh_production_history_init.sh"
MAKEFILE = REPO_ROOT / "Makefile"
OUTPUT_JSON = REPO_ROOT / "artifacts/migration/migration_asset_delivery_audit_v1.json"
OUTPUT_MD = REPO_ROOT / "docs/migration_alignment/migration_asset_delivery_audit_v1.md"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def size_mb(size: int) -> float:
    return round(size / 1024 / 1024, 2)


def catalog_audit() -> dict[str, Any]:
    catalog = load_json(CATALOG)
    packages = catalog.get("packages", [])
    package_order = catalog.get("package_order", [])
    package_ids = [package.get("asset_package_id") for package in packages]
    referenced: set[str] = {rel(CATALOG)}
    package_rows: list[dict[str, Any]] = []
    missing: list[str] = []
    hash_mismatches: list[dict[str, str]] = []
    asset_hash_mismatches: list[dict[str, str]] = []

    for package in packages:
        manifest_rel = package["asset_manifest_path"]
        manifest_path = ASSET_ROOT / manifest_rel
        referenced.add(rel(manifest_path))
        if not manifest_path.exists():
            missing.append(rel(manifest_path))
            continue
        manifest_hash = sha256_file(manifest_path)
        if manifest_hash != package.get("asset_manifest_sha256"):
            hash_mismatches.append(
                {
                    "asset_package_id": package["asset_package_id"],
                    "path": rel(manifest_path),
                    "expected": package.get("asset_manifest_sha256", ""),
                    "actual": manifest_hash,
                }
            )
        manifest = load_json(manifest_path)
        assets = manifest.get("assets", [])
        package_record_count = 0
        for asset in assets:
            asset_path = ASSET_ROOT / asset["path"]
            referenced.add(rel(asset_path))
            if not asset_path.exists():
                missing.append(rel(asset_path))
                continue
            expected_sha = asset.get("sha256")
            if expected_sha:
                actual_sha = sha256_file(asset_path)
                if actual_sha != expected_sha:
                    asset_hash_mismatches.append(
                        {
                            "asset_package_id": package["asset_package_id"],
                            "path": rel(asset_path),
                            "expected": expected_sha,
                            "actual": actual_sha,
                        }
                    )
            package_record_count += int(asset.get("record_count") or 0)
        package_rows.append(
            {
                "asset_package_id": package["asset_package_id"],
                "layer": package.get("layer"),
                "target_model": package.get("target_model"),
                "asset_count": len(assets),
                "declared_asset_record_count": package_record_count,
                "risk_class": package.get("risk_class"),
            }
        )

    order_mismatch = package_order != package_ids
    duplicate_package_ids = sorted({item for item in package_ids if package_ids.count(item) > 1})
    all_asset_files = sorted(path for path in ASSET_ROOT.rglob("*") if path.is_file())
    unreferenced = [rel(path) for path in all_asset_files if rel(path) not in referenced]

    return {
        "catalog_version": catalog.get("catalog_version"),
        "package_count": len(packages),
        "package_order_count": len(package_order),
        "package_order_matches_packages": not order_mismatch,
        "duplicate_package_ids": duplicate_package_ids,
        "packages": package_rows,
        "referenced_file_count": len(referenced),
        "asset_file_count": len(all_asset_files),
        "unreferenced_files": unreferenced,
        "missing_files": sorted(set(missing)),
        "manifest_hash_mismatches": hash_mismatches,
        "asset_hash_mismatches": asset_hash_mismatches,
    }


def packaging_audit() -> dict[str, Any]:
    files = sorted(path for path in ASSET_ROOT.rglob("*") if path.is_file())
    total_bytes = sum(path.stat().st_size for path in files)
    large_files = [
        {"path": rel(path), "size_mb": size_mb(path.stat().st_size)}
        for path in sorted(files, key=lambda item: item.stat().st_size, reverse=True)
        if path.stat().st_size >= 10 * 1024 * 1024
    ]
    duplicate_materialized_parts: list[dict[str, Any]] = []
    for xml_path in sorted(ASSET_ROOT.rglob("*.xml")):
        parts_dir = Path(str(xml_path) + ".parts")
        if not parts_dir.is_dir():
            continue
        part_files = sorted(parts_dir.glob("*.part"))
        if not part_files:
            continue
        duplicate_materialized_parts.append(
            {
                "xml_path": rel(xml_path),
                "xml_size_mb": size_mb(xml_path.stat().st_size),
                "parts_dir": rel(parts_dir),
                "part_count": len(part_files),
                "parts_size_mb": size_mb(sum(path.stat().st_size for path in part_files)),
                "recommendation": "keep either materialized XML or parts in the release package, not both",
            }
        )
    return {
        "file_count": len(files),
        "total_size_mb": size_mb(total_bytes),
        "large_files": large_files[:20],
        "duplicate_materialized_parts": duplicate_materialized_parts,
    }


def replay_audit() -> dict[str, Any]:
    oneclick_text = ONECLICK.read_text(encoding="utf-8") if ONECLICK.exists() else ""
    production_text = PRODUCTION_ENTRY.read_text(encoding="utf-8") if PRODUCTION_ENTRY.exists() else ""
    makefile_text = MAKEFILE.read_text(encoding="utf-8") if MAKEFILE.exists() else ""
    step_names = re.findall(r"run_step\s+([A-Za-z0-9_]+)\s", oneclick_text)
    duplicate_steps = sorted({step for step in step_names if step_names.count(step) > 1})
    return {
        "oneclick_exists": ONECLICK.exists(),
        "production_entry_exists": PRODUCTION_ENTRY.exists(),
        "make_targets_present": {
            "migration.assets.verify_all": "migration.assets.verify_all:" in makefile_text,
            "history.continuity.rehearse": "history.continuity.rehearse:" in makefile_text,
            "history.continuity.replay": "history.continuity.replay:" in makefile_text,
            "history.production.fresh_init": "history.production.fresh_init:" in makefile_text,
        },
        "production_allows_replay_guard": "HISTORY_CONTINUITY_ALLOW_PROD=1" in production_text,
        "production_calls_oneclick": "history_continuity_oneclick.sh" in production_text,
        "start_at_supported": "HISTORY_CONTINUITY_START_AT" in oneclick_text,
        "stop_after_supported": "HISTORY_CONTINUITY_STOP_AFTER" in oneclick_text,
        "step_count": len(step_names),
        "duplicate_steps": duplicate_steps,
        "privacy_opt_in_flags": [
            flag
            for flag in [
                "HISTORY_CONTINUITY_INCLUDE_ATTENDANCE_CHECKIN",
                "HISTORY_CONTINUITY_INCLUDE_PERSONNEL_MOVEMENT",
                "HISTORY_CONTINUITY_INCLUDE_SALARY_LINE",
            ]
            if flag in oneclick_text
        ],
        "first_steps": step_names[:12],
        "last_steps": step_names[-12:],
    }


def decide(payload: dict[str, Any]) -> tuple[str, list[str], list[str]]:
    blockers: list[str] = []
    actions: list[str] = []
    catalog = payload["catalog"]
    packaging = payload["packaging"]
    replay = payload["replay"]

    if catalog["missing_files"]:
        blockers.append("catalog references missing files")
    if catalog["manifest_hash_mismatches"] or catalog["asset_hash_mismatches"]:
        blockers.append("catalog or asset sha256 mismatch")
    if not catalog["package_order_matches_packages"]:
        blockers.append("package_order does not match packages order")
    if catalog["duplicate_package_ids"]:
        blockers.append("duplicate package ids")
    if not replay["oneclick_exists"] or not replay["production_entry_exists"]:
        blockers.append("required replay entrypoint is missing")
    if not replay["production_allows_replay_guard"] or not replay["production_calls_oneclick"]:
        blockers.append("production entry does not call guarded one-click replay")
    if not all(replay["make_targets_present"].values()):
        blockers.append("required Makefile replay targets are missing")

    if packaging["duplicate_materialized_parts"]:
        actions.append("remove duplicated materialized XML or parts from the final release package after choosing one canonical form")
    if catalog["unreferenced_files"]:
        actions.append("classify unreferenced migration asset files as delivery evidence or remove from release package")
    if replay["step_count"] < 20:
        actions.append("replay step count is unexpectedly low; review one-click parser and script")

    status = "FAIL" if blockers else ("PASS_WITH_PACKAGING_ACTIONS" if actions else "PASS")
    return status, blockers, actions


def write_outputs(payload: dict[str, Any]) -> None:
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    catalog = payload["catalog"]
    packaging = payload["packaging"]
    replay = payload["replay"]
    lines = [
        "# Migration Asset Delivery Audit v1",
        "",
        f"Status: `{payload['status']}`",
        "",
        "## Scope",
        "",
        "Read-only audit for production delivery packaging. This report does not",
        "connect to Odoo, execute replay writes, or mutate migration assets.",
        "",
        "## Summary",
        "",
        f"- catalog packages: `{catalog['package_count']}`",
        f"- asset files: `{catalog['asset_file_count']}`",
        f"- referenced files: `{catalog['referenced_file_count']}`",
        f"- unreferenced files: `{len(catalog['unreferenced_files'])}`",
        f"- total asset size MB: `{packaging['total_size_mb']}`",
        f"- replay steps: `{replay['step_count']}`",
        f"- duplicate materialized parts: `{len(packaging['duplicate_materialized_parts'])}`",
        "",
        "## Decision",
        "",
        f"- blockers: `{len(payload['blockers'])}`",
        f"- packaging actions: `{len(payload['packaging_actions'])}`",
    ]
    if payload["blockers"]:
        lines.extend(["", "### Blockers", ""])
        lines.extend(f"- {item}" for item in payload["blockers"])
    if payload["packaging_actions"]:
        lines.extend(["", "### Packaging Actions", ""])
        lines.extend(f"- {item}" for item in payload["packaging_actions"])
    lines.extend(
        [
            "",
            "## Entrypoints",
            "",
            f"- `history.continuity.rehearse`: `{replay['make_targets_present']['history.continuity.rehearse']}`",
            f"- `history.continuity.replay`: `{replay['make_targets_present']['history.continuity.replay']}`",
            f"- `history.production.fresh_init`: `{replay['make_targets_present']['history.production.fresh_init']}`",
            f"- production calls one-click replay: `{replay['production_calls_oneclick']}`",
            f"- `HISTORY_CONTINUITY_START_AT`: `{replay['start_at_supported']}`",
            "",
            "## Duplicate Materialized Parts",
            "",
        ]
    )
    if packaging["duplicate_materialized_parts"]:
        for item in packaging["duplicate_materialized_parts"]:
            lines.append(
                f"- `{item['xml_path']}` ({item['xml_size_mb']} MB) and `{item['parts_dir']}` "
                f"({item['part_count']} parts, {item['parts_size_mb']} MB)"
            )
    else:
        lines.append("- none")
    lines.extend(["", "## Unreferenced Asset Files", ""])
    if catalog["unreferenced_files"]:
        lines.extend(f"- `{item}`" for item in catalog["unreferenced_files"])
    else:
        lines.append("- none")
    lines.extend(["", "## Large Files", ""])
    for item in packaging["large_files"]:
        lines.append(f"- `{item['path']}`: `{item['size_mb']} MB`")
    lines.extend(["", "## Output", "", f"- JSON: `{rel(OUTPUT_JSON)}`"])
    OUTPUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    payload: dict[str, Any] = {
        "audit_id": "migration_asset_delivery_audit_v1",
        "mode": "read_only",
        "db_writes": 0,
        "catalog": catalog_audit(),
        "packaging": packaging_audit(),
        "replay": replay_audit(),
    }
    status, blockers, actions = decide(payload)
    payload["status"] = status
    payload["blockers"] = blockers
    payload["packaging_actions"] = actions
    write_outputs(payload)
    print(
        "MIGRATION_ASSET_DELIVERY_AUDIT="
        + json.dumps(
            {
                "status": status,
                "packages": payload["catalog"]["package_count"],
                "asset_files": payload["catalog"]["asset_file_count"],
                "unreferenced_files": len(payload["catalog"]["unreferenced_files"]),
                "duplicate_materialized_parts": len(payload["packaging"]["duplicate_materialized_parts"]),
                "replay_steps": payload["replay"]["step_count"],
                "blockers": len(blockers),
                "db_writes": 0,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 1 if blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
