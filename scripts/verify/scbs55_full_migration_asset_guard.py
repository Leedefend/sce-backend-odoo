#!/usr/bin/env python3
"""Validate the SCBS55 full migration asset freeze scope."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
FREEZE = ROOT / "docs/migration_alignment/scbs55_full_migration_asset_freeze_v1.json"
INVENTORY = ROOT / "docs/migration_alignment/scbs55_full_migration_asset_inventory_v1.json"
REPLAY_GAP = ROOT / "docs/migration_alignment/scbs55_replay_payload_gap_report_v1.json"
PROMOTION_QUEUE = ROOT / "docs/migration_alignment/scbs55_payload_promotion_queue_v1.json"
PACKAGE_LOCK = ROOT / "docs/migration_alignment/migration_asset_package_lock_v1.json"
COMPARE = ROOT / "artifacts/migration/scbs55_wutao_old_new_final_aligned_compare.json"
SIX_SLICE = ROOT / "docs/migration_alignment/scbs55_user_acceptance_asset_freeze_v1.json"
SIX_LOCK = ROOT / "docs/migration_alignment/scbs55_user_acceptance_evidence_lock_v1.json"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def as_int(value: object) -> int:
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0


def check_freeze(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if payload.get("freeze_version") != "scbs55_full_migration_asset_freeze_v1":
        errors.append("freeze_version must be scbs55_full_migration_asset_freeze_v1")
    scope = payload.get("scope_policy") if isinstance(payload.get("scope_policy"), dict) else {}
    if scope.get("whole_migration_scope") is not True:
        errors.append("scope_policy.whole_migration_scope must be true")
    if scope.get("six_page_acceptance_slice_role") != "first locked high-risk acceptance slice only":
        errors.append("six-page slice must be declared as a slice, not the whole topic boundary")
    surfaces = payload.get("full_visibility_surfaces")
    if not isinstance(surfaces, list) or len(surfaces) != 42:
        errors.append(f"full_visibility_surfaces must contain 42 rows, got {len(surfaces) if isinstance(surfaces, list) else 0}")
        return errors
    seen_seq: set[int] = set()
    for row in surfaces:
        if not isinstance(row, dict):
            errors.append("full_visibility_surfaces entries must be objects")
            continue
        seq = as_int(row.get("seq"))
        old_count = as_int(row.get("old_count"))
        new_count = as_int(row.get("new_count"))
        if not seq:
            errors.append(f"surface missing seq: {row}")
        if seq in seen_seq:
            errors.append(f"duplicate surface seq: {seq}")
        seen_seq.add(seq)
        if row.get("status") != "PASS":
            errors.append(f"seq {seq}: status must be PASS")
        if old_count != new_count:
            errors.append(f"seq {seq}: old/new count mismatch {old_count} != {new_count}")
    expected_skip = {7, 14}
    missing = sorted(set(range(1, 45)) - expected_skip - seen_seq)
    unexpected = sorted(seq for seq in seen_seq if seq not in set(range(1, 45)) - expected_skip)
    if missing:
        errors.append(f"missing full visibility seqs: {missing}")
    if unexpected:
        errors.append(f"unexpected full visibility seqs: {unexpected}")
    return errors


def check_package_lock(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not PACKAGE_LOCK.exists():
        return [f"missing package lock: {PACKAGE_LOCK.relative_to(ROOT)}"]
    lock = load_json(PACKAGE_LOCK)
    if lock.get("lock_version") != "migration_asset_package_lock_v1":
        errors.append("package lock version must be migration_asset_package_lock_v1")
    baseline = payload.get("baseline_package") if isinstance(payload.get("baseline_package"), dict) else {}
    for field in ("package_id", "sha256", "package_size_bytes", "payload_mode", "materializes"):
        if lock.get(field) != baseline.get(field):
            errors.append(f"baseline package {field} drift: freeze={baseline.get(field)!r} lock={lock.get(field)!r}")
    return errors


def check_compare(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not COMPARE.exists():
        return [f"missing full visibility compare evidence: {COMPARE.relative_to(ROOT)}"]
    compare = load_json(COMPARE)
    evidence = payload.get("current_full_visibility_evidence") if isinstance(payload.get("current_full_visibility_evidence"), dict) else {}
    if compare.get("status") != evidence.get("status"):
        errors.append(f"compare status drift: {compare.get('status')} != {evidence.get('status')}")
    if as_int(compare.get("checked_count")) != as_int(evidence.get("checked_count")):
        errors.append("compare checked_count drift")
    if as_int(compare.get("blocking_count")) != as_int(evidence.get("blocking_count")):
        errors.append("compare blocking_count drift")
    compare_rows = compare.get("rows") if isinstance(compare.get("rows"), list) else []
    freeze_rows = payload.get("full_visibility_surfaces") if isinstance(payload.get("full_visibility_surfaces"), list) else []
    compare_by_seq = {as_int(row.get("seq")): row for row in compare_rows if isinstance(row, dict)}
    for row in freeze_rows:
        if not isinstance(row, dict):
            continue
        seq = as_int(row.get("seq"))
        actual = compare_by_seq.get(seq)
        if not actual:
            errors.append(f"compare evidence missing seq {seq}")
            continue
        for field in ("name", "old_count", "new_count", "status"):
            if actual.get(field) != row.get(field):
                errors.append(f"seq {seq}: compare {field}={actual.get(field)!r} != freeze {row.get(field)!r}")
        if as_int(actual.get("diff")) != 0:
            errors.append(f"seq {seq}: compare diff must be 0")
    return errors


def check_slices(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not SIX_SLICE.exists():
        errors.append(f"missing six-page slice manifest: {SIX_SLICE.relative_to(ROOT)}")
    if not SIX_LOCK.exists():
        errors.append(f"missing six-page evidence lock: {SIX_LOCK.relative_to(ROOT)}")
    slices = payload.get("acceptance_slices") if isinstance(payload.get("acceptance_slices"), list) else []
    if len(slices) != 1:
        errors.append("acceptance_slices must declare the current six-page slice")
    return errors


def check_inventory(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not INVENTORY.exists():
        return [f"missing full migration asset inventory: {INVENTORY.relative_to(ROOT)}"]
    inventory = load_json(INVENTORY)
    if not isinstance(inventory, dict):
        return ["full migration asset inventory root must be object"]
    if inventory.get("inventory_version") != "scbs55_full_migration_asset_inventory_v1":
        errors.append("inventory_version must be scbs55_full_migration_asset_inventory_v1")
    if inventory.get("status") != "PASS":
        errors.append(f"inventory status must be PASS, got {inventory.get('status')!r}")
    if inventory.get("scope_freeze") != str(FREEZE.relative_to(ROOT)):
        errors.append("inventory scope_freeze does not point to the full freeze file")

    compare = inventory.get("full_visibility_compare") if isinstance(inventory.get("full_visibility_compare"), dict) else {}
    evidence = payload.get("current_full_visibility_evidence") if isinstance(payload.get("current_full_visibility_evidence"), dict) else {}
    if as_int(compare.get("checked_count")) != as_int(evidence.get("checked_count")):
        errors.append("inventory full visibility checked_count drift")
    if as_int(compare.get("blocking_count")) != as_int(evidence.get("blocking_count")):
        errors.append("inventory full visibility blocking_count drift")
    if compare.get("status") != evidence.get("status"):
        errors.append("inventory full visibility status drift")

    history = inventory.get("history_continuity") if isinstance(inventory.get("history_continuity"), dict) else {}
    if as_int(history.get("step_count")) < 100:
        errors.append(f"inventory history_continuity step_count unexpectedly low: {history.get('step_count')}")
    runtime = inventory.get("runtime_artifacts") if isinstance(inventory.get("runtime_artifacts"), dict) else {}
    if as_int(runtime.get("file_count")) <= 0:
        errors.append("inventory runtime artifact file_count must be positive")
    scripts = inventory.get("script_status") if isinstance(inventory.get("script_status"), dict) else {}
    ungoverned = scripts.get("ungoverned_runtime_scripts") if isinstance(scripts.get("ungoverned_runtime_scripts"), list) else []
    if len(ungoverned) < 2:
        errors.append("inventory must explicitly classify current ungoverned runtime scripts")
    return errors


def check_replay_gap_report() -> list[str]:
    errors: list[str] = []
    if not REPLAY_GAP.exists():
        return [f"missing replay payload gap report: {REPLAY_GAP.relative_to(ROOT)}"]
    report = load_json(REPLAY_GAP)
    if not isinstance(report, dict):
        return ["replay payload gap report root must be object"]
    if report.get("report_version") != "scbs55_replay_payload_gap_report_v1":
        errors.append("replay gap report version must be scbs55_replay_payload_gap_report_v1")
    if report.get("status") not in {"PASS", "PASS_WITH_GAPS"}:
        errors.append(f"replay gap report status must be PASS or PASS_WITH_GAPS, got {report.get('status')!r}")
    if as_int(report.get("step_count")) < 100:
        errors.append(f"replay gap report step_count unexpectedly low: {report.get('step_count')}")
    if as_int(report.get("adapter_step_count")) <= 0:
        errors.append("replay gap report must include adapter steps")
    if "missing_required_inputs" not in report:
        errors.append("replay gap report must expose missing_required_inputs")
    if "runtime_outputs_not_currently_packaged" not in report:
        errors.append("replay gap report must expose runtime_outputs_not_currently_packaged")
    return errors


def check_promotion_queue() -> list[str]:
    errors: list[str] = []
    if not PROMOTION_QUEUE.exists():
        return [f"missing payload promotion queue: {PROMOTION_QUEUE.relative_to(ROOT)}"]
    queue = load_json(PROMOTION_QUEUE)
    if not isinstance(queue, dict):
        return ["payload promotion queue root must be object"]
    if queue.get("queue_version") != "scbs55_payload_promotion_queue_v1":
        errors.append("payload promotion queue version must be scbs55_payload_promotion_queue_v1")
    if queue.get("status") != "PASS":
        errors.append(f"payload promotion queue status must be PASS, got {queue.get('status')!r}")
    rows = queue.get("queue") if isinstance(queue.get("queue"), list) else []
    if len(rows) < 8:
        errors.append(f"payload promotion queue lane_count unexpectedly low: {len(rows)}")
    priorities = [as_int(row.get("priority")) for row in rows if isinstance(row, dict)]
    if priorities != sorted(priorities):
        errors.append("payload promotion queue priorities must be sorted")
    if as_int(queue.get("total_missing_required_inputs")) <= 0:
        errors.append("payload promotion queue must expose current missing required input backlog")
    return errors


def main() -> int:
    payload = load_json(FREEZE)
    if not isinstance(payload, dict):
        print("[scbs55-full-migration-asset-guard] FAIL: freeze root must be object")
        return 2
    errors = []
    errors.extend(check_freeze(payload))
    errors.extend(check_package_lock(payload))
    errors.extend(check_compare(payload))
    errors.extend(check_slices(payload))
    errors.extend(check_inventory(payload))
    errors.extend(check_replay_gap_report())
    errors.extend(check_promotion_queue())
    report = {
        "status": "FAIL" if errors else "PASS",
        "freeze": str(FREEZE.relative_to(ROOT)),
        "inventory": str(INVENTORY.relative_to(ROOT)),
        "replay_gap": str(REPLAY_GAP.relative_to(ROOT)),
        "promotion_queue": str(PROMOTION_QUEUE.relative_to(ROOT)),
        "package_lock": str(PACKAGE_LOCK.relative_to(ROOT)),
        "compare": str(COMPARE.relative_to(ROOT)),
        "surface_count": len(payload.get("full_visibility_surfaces", [])) if isinstance(payload.get("full_visibility_surfaces"), list) else 0,
        "errors": errors,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 2 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
