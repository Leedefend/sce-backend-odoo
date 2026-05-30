#!/usr/bin/env python3
"""Validate the SCBS55 user acceptance migration asset freeze manifest."""

from __future__ import annotations

import json
import os
import hashlib
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "docs/migration_alignment/scbs55_user_acceptance_asset_freeze_v1.json"
EVIDENCE_LOCK = ROOT / "docs/migration_alignment/scbs55_user_acceptance_evidence_lock_v1.json"
DEFAULT_OLD_ROWS_DIR = Path(os.getenv("SCBS55_OLD_ROWS_DIR", "/tmp/scbs55_old_pages_20260530"))
DEFAULT_BROWSER_SUMMARY = Path(
    os.getenv("SCBS55_BROWSER_SUMMARY", "/tmp/scbs55_six_pages_aligned_20260530/summary.json")
)
REQUIRE_EVIDENCE = os.getenv("SCBS55_REQUIRE_ACCEPTANCE_EVIDENCE", "0") == "1"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def as_int(value: object) -> int:
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0


def rows_from_old_dump(path: Path) -> list[dict[str, Any]]:
    payload = load_json(path)
    rows = payload.get("rows") if isinstance(payload, dict) else None
    if not isinstance(rows, list):
        raise ValueError(f"{path} does not contain rows[]")
    return [row for row in rows if isinstance(row, dict)]


def browser_totals(path: Path) -> dict[int, int]:
    payload = load_json(path)
    out: dict[int, int] = {}
    for row in payload.get("rows", []) if isinstance(payload, dict) else []:
        if not isinstance(row, dict):
            continue
        menu = as_int(row.get("menu"))
        total = as_int(row.get("total"))
        if menu:
            out[menu] = total
    return out


def check_manifest(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if payload.get("asset_manifest_version") != "1.0":
        errors.append("asset_manifest_version must be 1.0")
    if payload.get("asset_package_id") != "scbs55_user_acceptance_surfaces_v1":
        errors.append("asset_package_id must be scbs55_user_acceptance_surfaces_v1")
    surfaces = payload.get("surfaces")
    if not isinstance(surfaces, list) or not surfaces:
        return ["surfaces must be a non-empty list"]

    seen: dict[str, set[object]] = {
        "key": set(),
        "name": set(),
        "old_config": set(),
        "new_menu": set(),
        "new_action": set(),
    }
    for index, surface in enumerate(surfaces):
        if not isinstance(surface, dict):
            errors.append(f"surface[{index}] must be an object")
            continue
        key = str(surface.get("key") or "")
        name = str(surface.get("name") or "")
        old = surface.get("old") if isinstance(surface.get("old"), dict) else {}
        new = surface.get("new") if isinstance(surface.get("new"), dict) else {}
        evidence = surface.get("evidence") if isinstance(surface.get("evidence"), dict) else {}
        for field, value in (
            ("key", key),
            ("name", name),
            ("old.config_id", old.get("config_id")),
            ("old.main_table", old.get("main_table")),
            ("old.identity_field", old.get("identity_field")),
            ("old.row_dump_file", old.get("row_dump_file")),
            ("new.menu_id", new.get("menu_id")),
            ("new.action_id", new.get("action_id")),
            ("new.model", new.get("model")),
            ("new.identity_field", new.get("identity_field")),
            ("new.expected_headers", new.get("expected_headers")),
            ("evidence.set_check", evidence.get("set_check")),
        ):
            if value in (None, ""):
                errors.append(f"{key or index}: missing {field}")
        headers = new.get("expected_headers")
        if not isinstance(headers, list) or not headers:
            errors.append(f"{key}: new.expected_headers must be a non-empty list")
        else:
            normalized_headers = [str(item or "").strip() for item in headers]
            missing_headers = [idx for idx, item in enumerate(normalized_headers) if not item]
            duplicate_headers = sorted({item for item in normalized_headers if normalized_headers.count(item) > 1})
            if missing_headers:
                errors.append(f"{key}: new.expected_headers has blank labels at indexes {missing_headers}")
            if duplicate_headers:
                errors.append(f"{key}: new.expected_headers has duplicate labels {duplicate_headers}")
        old_count = as_int(old.get("expected_count"))
        new_count = as_int(new.get("expected_count"))
        last_total = as_int(evidence.get("last_browser_total"))
        if old_count <= 0:
            errors.append(f"{key}: old.expected_count must be positive")
        if old_count != new_count:
            errors.append(f"{key}: old/new expected counts differ: {old_count} != {new_count}")
        if old_count != last_total:
            errors.append(f"{key}: browser evidence count differs: {old_count} != {last_total}")
        unique_values = {
            "key": key,
            "name": name,
            "old_config": old.get("config_id"),
            "new_menu": new.get("menu_id"),
            "new_action": new.get("action_id"),
        }
        for bucket, value in unique_values.items():
            if value in seen[bucket]:
                errors.append(f"{key}: duplicate {bucket}={value}")
            seen[bucket].add(value)
    return errors


def check_optional_evidence(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    surfaces = payload.get("surfaces") if isinstance(payload.get("surfaces"), list) else []
    browser = browser_totals(DEFAULT_BROWSER_SUMMARY) if DEFAULT_BROWSER_SUMMARY.exists() else {}
    if REQUIRE_EVIDENCE and not DEFAULT_BROWSER_SUMMARY.exists():
        errors.append(f"missing browser summary: {DEFAULT_BROWSER_SUMMARY}")
    for surface in surfaces:
        if not isinstance(surface, dict):
            continue
        key = str(surface.get("key") or "")
        old = surface.get("old") if isinstance(surface.get("old"), dict) else {}
        new = surface.get("new") if isinstance(surface.get("new"), dict) else {}
        expected = as_int(old.get("expected_count"))
        row_file = DEFAULT_OLD_ROWS_DIR / str(old.get("row_dump_file") or "")
        if row_file.exists():
            rows = rows_from_old_dump(row_file)
            if len(rows) != expected:
                errors.append(f"{key}: old row dump count {len(rows)} != {expected}")
            identity = str(old.get("identity_field") or "")
            values = [str(row.get(identity) or "").strip() for row in rows]
            missing = len([value for value in values if not value])
            unique_count = len(set(values))
            if missing:
                errors.append(f"{key}: old row dump has {missing} missing identity values for {identity}")
            if unique_count != len(values):
                errors.append(f"{key}: old row dump identity {identity} is not unique")
        elif REQUIRE_EVIDENCE:
            errors.append(f"{key}: missing old row dump {row_file}")
        menu_id = as_int(new.get("menu_id"))
        if menu_id in browser and browser[menu_id] != expected:
            errors.append(f"{key}: browser total {browser[menu_id]} != {expected}")
        elif REQUIRE_EVIDENCE and menu_id not in browser:
            errors.append(f"{key}: browser summary missing menu {menu_id}")
    return errors


def check_evidence_lock(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not EVIDENCE_LOCK.exists():
        errors.append(f"missing evidence lock: {EVIDENCE_LOCK.relative_to(ROOT)}")
        return errors
    lock = load_json(EVIDENCE_LOCK)
    if not isinstance(lock, dict):
        return ["evidence lock root must be object"]
    if lock.get("lock_version") != "scbs55_user_acceptance_evidence_lock_v1":
        errors.append("evidence lock version must be scbs55_user_acceptance_evidence_lock_v1")
    if lock.get("asset_package_id") != payload.get("asset_package_id"):
        errors.append("evidence lock asset_package_id does not match manifest")
    surfaces = payload.get("surfaces") if isinstance(payload.get("surfaces"), list) else []
    manifest_by_key = {str(row.get("key")): row for row in surfaces if isinstance(row, dict)}
    lock_surfaces = lock.get("surfaces") if isinstance(lock.get("surfaces"), list) else []
    if len(lock_surfaces) != len(manifest_by_key):
        errors.append(f"evidence lock surface count {len(lock_surfaces)} != manifest {len(manifest_by_key)}")
    for locked in lock_surfaces:
        if not isinstance(locked, dict):
            errors.append("evidence lock surface entry must be object")
            continue
        key = str(locked.get("key") or "")
        manifest_surface = manifest_by_key.get(key)
        if not manifest_surface:
            errors.append(f"evidence lock has unknown key {key}")
            continue
        old = manifest_surface.get("old") if isinstance(manifest_surface.get("old"), dict) else {}
        new = manifest_surface.get("new") if isinstance(manifest_surface.get("new"), dict) else {}
        expected = as_int(old.get("expected_count"))
        for field, expected_value in (
            ("old_config_id", old.get("config_id")),
            ("old_main_table", old.get("main_table")),
            ("old_row_dump_file", old.get("row_dump_file")),
            ("old_identity_field", old.get("identity_field")),
            ("new_menu_id", new.get("menu_id")),
            ("new_action_id", new.get("action_id")),
            ("new_model", new.get("model")),
        ):
            if locked.get(field) != expected_value:
                errors.append(f"{key}: evidence lock {field}={locked.get(field)!r} != {expected_value!r}")
        for field in ("old_expected_count", "new_expected_count", "old_row_count", "old_identity_count", "old_identity_unique_count", "browser_total"):
            if as_int(locked.get(field)) != expected:
                errors.append(f"{key}: evidence lock {field}={locked.get(field)} != {expected}")
        if as_int(locked.get("old_identity_missing_count")) != 0:
            errors.append(f"{key}: evidence lock has missing old identities")
        row_file = DEFAULT_OLD_ROWS_DIR / str(old.get("row_dump_file") or "")
        if row_file.exists():
            actual_sha = sha256_file(row_file)
            if actual_sha != locked.get("old_row_dump_sha256"):
                errors.append(f"{key}: old row dump sha256 drift: {actual_sha} != {locked.get('old_row_dump_sha256')}")
        elif REQUIRE_EVIDENCE:
            errors.append(f"{key}: cannot verify evidence lock because {row_file} is missing")
    browser_lock = lock.get("browser_summary") if isinstance(lock.get("browser_summary"), dict) else {}
    if DEFAULT_BROWSER_SUMMARY.exists():
        actual_sha = sha256_file(DEFAULT_BROWSER_SUMMARY)
        if actual_sha != browser_lock.get("sha256"):
            errors.append(f"browser summary sha256 drift: {actual_sha} != {browser_lock.get('sha256')}")
    elif REQUIRE_EVIDENCE:
        errors.append(f"cannot verify browser evidence lock because {DEFAULT_BROWSER_SUMMARY} is missing")
    return errors


def main() -> int:
    payload = load_json(MANIFEST)
    if not isinstance(payload, dict):
        print("[scbs55-user-acceptance-asset-manifest] FAIL: manifest root must be object")
        return 2
    errors = check_manifest(payload)
    errors.extend(check_evidence_lock(payload))
    errors.extend(check_optional_evidence(payload))
    report = {
        "status": "FAIL" if errors else "PASS",
        "manifest": str(MANIFEST.relative_to(ROOT)),
        "surface_count": len(payload.get("surfaces", [])) if isinstance(payload.get("surfaces"), list) else 0,
        "require_evidence": REQUIRE_EVIDENCE,
        "old_rows_dir": str(DEFAULT_OLD_ROWS_DIR),
        "browser_summary": str(DEFAULT_BROWSER_SUMMARY),
        "errors": errors,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 2 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
