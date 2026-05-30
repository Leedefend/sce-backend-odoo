#!/usr/bin/env python3
"""Validate the SCBS55 full migration asset freeze scope."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
FREEZE = ROOT / "docs/migration_alignment/scbs55_full_migration_asset_freeze_v1.json"
INVENTORY = ROOT / "docs/migration_alignment/scbs55_full_migration_asset_inventory_v1.json"
REPLAY_GAP = ROOT / "docs/migration_alignment/scbs55_replay_payload_gap_report_v1.json"
PROMOTION_QUEUE = ROOT / "docs/migration_alignment/scbs55_payload_promotion_queue_v1.json"
DELIVERY_REQUIREMENT_LOCK = ROOT / "docs/migration_alignment/scbs55_delivery_replay_requirement_lock_v1.json"
PACKAGE_LOCK = ROOT / "docs/migration_alignment/migration_asset_package_lock_v1.json"
COMPARE = ROOT / "artifacts/migration/scbs55_wutao_old_new_final_aligned_compare.json"
SIX_SLICE = ROOT / "docs/migration_alignment/scbs55_user_acceptance_asset_freeze_v1.json"
SIX_LOCK = ROOT / "docs/migration_alignment/scbs55_user_acceptance_evidence_lock_v1.json"
DELIVERY_AUDIT_MD = ROOT / "docs/migration_alignment/migration_asset_delivery_audit_v1.md"
DELIVERY_MANIFEST_MD = ROOT / "docs/migration_alignment/migration_asset_delivery_manifest_v1.md"
DIRECT_PROJECT_MENU_ITEM_COUNT = 34


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
    if lock.get("payload_mode") != "packaged_artifacts":
        errors.append("package lock payload_mode must be packaged_artifacts")
    if lock.get("materializes") != "migration_assets/ and artifacts/migration/":
        errors.append("package lock must materialize both migration_assets/ and artifacts/migration/")
    if as_int(lock.get("package_size_bytes")) <= 0:
        errors.append("package lock package_size_bytes must be positive")
    if as_int(lock.get("included_file_count")) <= 0:
        errors.append("package lock included_file_count must be positive")
    required_before = lock.get("required_before") if isinstance(lock.get("required_before"), list) else []
    for target in (
        "migration.assets.verify_all",
        "migration.assets.delivery_audit",
        "history.continuity.rehearse",
        "history.production.fresh_init",
    ):
        if target not in required_before:
            errors.append(f"package lock required_before missing {target}")
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
    if not SIX_SLICE.exists():
        return errors
    slice_payload = load_json(SIX_SLICE)
    slice_surfaces = slice_payload.get("surfaces") if isinstance(slice_payload, dict) and isinstance(slice_payload.get("surfaces"), list) else []
    if len(slice_surfaces) != 6:
        errors.append(f"six-page slice must contain 6 surfaces, got {len(slice_surfaces)}")
    full_by_seq = {
        as_int(row.get("seq")): row
        for row in payload.get("full_visibility_surfaces", [])
        if isinstance(row, dict)
    }
    for surface in slice_surfaces:
        if not isinstance(surface, dict):
            errors.append("six-page slice surface entries must be objects")
            continue
        key = str(surface.get("key") or "")
        old = surface.get("old") if isinstance(surface.get("old"), dict) else {}
        new = surface.get("new") if isinstance(surface.get("new"), dict) else {}
        evidence = surface.get("evidence") if isinstance(surface.get("evidence"), dict) else {}
        lineage = surface.get("full_scope_lineage") if isinstance(surface.get("full_scope_lineage"), dict) else {}
        relation = lineage.get("relation")
        if relation == "direct_full_visibility_surface":
            seq = as_int(lineage.get("seq"))
            full = full_by_seq.get(seq)
            if not full:
                errors.append(f"{key}: direct full scope lineage seq {seq} is not present in full visibility surfaces")
                continue
            for field, expected_value in (
                ("name", surface.get("name")),
                ("old_count", old.get("expected_count")),
                ("new_count", new.get("expected_count")),
            ):
                if full.get(field) != expected_value:
                    errors.append(f"{key}: full scope lineage {field}={full.get(field)!r} != {expected_value!r}")
            if lineage.get("surface_name") != full.get("name"):
                errors.append(f"{key}: full scope lineage surface_name drift")
        elif relation == "independent_high_risk_acceptance_slice":
            if not lineage.get("reason"):
                errors.append(f"{key}: independent high-risk slice must declare a reason")
        else:
            errors.append(f"{key}: unsupported or missing full_scope_lineage.relation")
        if as_int(old.get("expected_count")) != as_int(new.get("expected_count")):
            errors.append(f"{key}: six-page slice old/new expected count drift")
        if as_int(evidence.get("last_browser_total")) != as_int(old.get("expected_count")):
            errors.append(f"{key}: six-page slice browser total drift")
    return errors


def check_user_acceptance_groups(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    groups = payload.get("user_acceptance_groups") if isinstance(payload.get("user_acceptance_groups"), list) else []
    by_id = {str(group.get("group_id") or ""): group for group in groups if isinstance(group, dict)}
    for group_id in ("scbs55_high_risk_six_surfaces", "scbsly_direct_project_business_menus"):
        if group_id not in by_id:
            errors.append(f"user_acceptance_groups missing {group_id}")
    six_group = by_id.get("scbs55_high_risk_six_surfaces")
    if isinstance(six_group, dict):
        if six_group.get("manifest") != str(SIX_SLICE.relative_to(ROOT)):
            errors.append("six-surface acceptance group manifest drift")
        if as_int(six_group.get("item_count")) != 6:
            errors.append("six-surface acceptance group item_count must be 6")
    direct_group = by_id.get("scbsly_direct_project_business_menus")
    if isinstance(direct_group, dict):
        if direct_group.get("manifest") != str(SIX_SLICE.relative_to(ROOT)):
            errors.append("direct project acceptance group manifest drift")
        if direct_group.get("source_system") != "https://www.builderp.cn/SCBSLY_V2":
            errors.append("direct project acceptance group source_system drift")
        if as_int(direct_group.get("category_count")) != 7:
            errors.append("direct project acceptance group category_count must be 7")
        if as_int(direct_group.get("item_count")) != DIRECT_PROJECT_MENU_ITEM_COUNT:
            errors.append(f"direct project acceptance group item_count must be {DIRECT_PROJECT_MENU_ITEM_COUNT}")
        if direct_group.get("latest_online_evidence") != "artifacts/migration/scbsly_direct_project_acceptance_menu_probe_v1.json":
            errors.append("direct project acceptance group latest_online_evidence drift")
        if (
            direct_group.get("latest_new_system_alignment")
            != "artifacts/migration/scbsly_direct_project_new_system_alignment_probe_v1.json"
        ):
            errors.append("direct project acceptance group latest_new_system_alignment drift")
        if (
            direct_group.get("latest_browser_menu_acceptance")
            != "artifacts/browser/scbsly-direct-project-menu/20260530T090744/report.json"
        ):
            errors.append("direct project acceptance group latest_browser_menu_acceptance drift")
        if direct_group.get("latest_gap_matrix") != "artifacts/migration/scbsly_direct_project_alignment_gap_matrix_v1.json":
            errors.append("direct project acceptance group latest_gap_matrix drift")
        if direct_group.get("platform_release_snapshot") != "v20260530_scbsly_direct_acceptance_menu_daily_dev":
            errors.append("direct project acceptance group platform_release_snapshot drift")
        if (
            direct_group.get("status")
            != "old_online_pass_new_daily_dev_browser_visible_aligned_with_identity_bound_acceptance_replay"
        ):
            errors.append("direct project acceptance group status drift")
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
    history_steps = history.get("steps") if isinstance(history.get("steps"), list) else []
    if len(history_steps) != as_int(history.get("step_count")):
        errors.append("inventory history_continuity steps count drift")
    history_by_kind = history.get("by_kind") if isinstance(history.get("by_kind"), dict) else {}
    if sum(as_int(value) for value in history_by_kind.values()) != as_int(history.get("step_count")):
        errors.append("inventory history_continuity by_kind total drift")
    runtime = inventory.get("runtime_artifacts") if isinstance(inventory.get("runtime_artifacts"), dict) else {}
    if as_int(runtime.get("file_count")) <= 0:
        errors.append("inventory runtime artifact file_count must be positive")
    runtime_by_category = runtime.get("by_category") if isinstance(runtime.get("by_category"), dict) else {}
    runtime_by_suffix = runtime.get("by_suffix") if isinstance(runtime.get("by_suffix"), dict) else {}
    if sum(as_int(value) for value in runtime_by_category.values()) != as_int(runtime.get("file_count")):
        errors.append("inventory runtime artifact by_category total drift")
    if sum(as_int(value) for value in runtime_by_suffix.values()) != as_int(runtime.get("file_count")):
        errors.append("inventory runtime artifact by_suffix total drift")
    surfaces = compare.get("surfaces") if isinstance(compare.get("surfaces"), list) else []
    if len(surfaces) != as_int(compare.get("checked_count")):
        errors.append("inventory full visibility surfaces count drift")
    if sum(as_int(row.get("old_count")) for row in surfaces if isinstance(row, dict)) != as_int(compare.get("total_old_rows")):
        errors.append("inventory full visibility total_old_rows drift")
    if sum(as_int(row.get("new_count")) for row in surfaces if isinstance(row, dict)) != as_int(compare.get("total_new_rows")):
        errors.append("inventory full visibility total_new_rows drift")
    freeze_surfaces = payload.get("full_visibility_surfaces") if isinstance(payload.get("full_visibility_surfaces"), list) else []
    inventory_by_seq = {as_int(row.get("seq")): row for row in surfaces if isinstance(row, dict)}
    for row in freeze_surfaces:
        if not isinstance(row, dict):
            continue
        seq = as_int(row.get("seq"))
        actual = inventory_by_seq.get(seq)
        if not actual:
            errors.append(f"inventory full visibility missing seq {seq}")
            continue
        for field in ("name", "old_count", "new_count", "status"):
            if actual.get(field) != row.get(field):
                errors.append(f"seq {seq}: inventory {field}={actual.get(field)!r} != freeze {row.get(field)!r}")
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
    steps = report.get("steps") if isinstance(report.get("steps"), list) else []
    step_indexes = [as_int(row.get("step_index")) for row in steps if isinstance(row, dict)]
    if len(step_indexes) != as_int(report.get("step_count")):
        errors.append("replay gap report steps count drift")
    if sorted(step_indexes) != list(range(1, len(step_indexes) + 1)):
        errors.append("replay gap report step_index must be contiguous and unique")
    unresolved_scripts = [
        row.get("step")
        for row in steps
        if isinstance(row, dict) and not row.get("script_exists")
    ]
    if unresolved_scripts:
        errors.append(f"replay gap report has unresolved step scripts: {unresolved_scripts[:10]}")
    if "missing_required_inputs" not in report:
        errors.append("replay gap report must expose missing_required_inputs")
    if "runtime_outputs_not_currently_packaged" not in report:
        errors.append("replay gap report must expose runtime_outputs_not_currently_packaged")
    missing = report.get("missing_required_inputs")
    runtime = report.get("runtime_outputs_not_currently_packaged")
    if isinstance(missing, list) and len(missing) != as_int(report.get("required_missing_input_count")):
        errors.append("replay gap report missing_required_inputs count drift")
    if isinstance(runtime, list) and len(runtime) != as_int(report.get("runtime_output_count")):
        errors.append("replay gap report runtime_outputs_not_currently_packaged count drift")
    if isinstance(missing, list):
        unique_missing_paths = {item.get("path") for item in missing if isinstance(item, dict)}
        if len(unique_missing_paths) != as_int(report.get("required_missing_input_unique_path_count")):
            errors.append("replay gap report required missing input unique path count drift")
    if isinstance(runtime, list):
        unique_runtime_paths = {item.get("path") for item in runtime if isinstance(item, dict)}
        if len(unique_runtime_paths) != as_int(report.get("runtime_output_unique_path_count")):
            errors.append("replay gap report runtime output unique path count drift")
    return errors


def check_inventory_replay_sequence() -> list[str]:
    errors: list[str] = []
    if not INVENTORY.exists() or not REPLAY_GAP.exists():
        return errors
    inventory = load_json(INVENTORY)
    report = load_json(REPLAY_GAP)
    if not isinstance(inventory, dict) or not isinstance(report, dict):
        return errors
    history = inventory.get("history_continuity") if isinstance(inventory.get("history_continuity"), dict) else {}
    inventory_steps = history.get("steps") if isinstance(history.get("steps"), list) else []
    report_steps = report.get("steps") if isinstance(report.get("steps"), list) else []
    if len(inventory_steps) != len(report_steps):
        errors.append("inventory and replay gap step counts differ")
        return errors
    for index, (inventory_step, report_step) in enumerate(zip(inventory_steps, report_steps), start=1):
        if not isinstance(inventory_step, dict) or not isinstance(report_step, dict):
            errors.append(f"step {index}: inventory and replay gap entries must be objects")
            continue
        for field in ("step_index", "step", "kind"):
            if inventory_step.get(field) != report_step.get(field):
                errors.append(
                    f"step {index}: inventory {field}={inventory_step.get(field)!r} "
                    f"!= replay gap {report_step.get(field)!r}"
                )
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
    if any(isinstance(row, dict) and row.get("lane") == "unclassified" for row in rows):
        errors.append("payload promotion queue must not contain unclassified lane")
    for row in rows:
        if not isinstance(row, dict):
            errors.append("payload promotion queue rows must be objects")
            continue
        missing = row.get("missing_required_inputs")
        runtime = row.get("runtime_output_backlog")
        if not isinstance(missing, list):
            errors.append(f"payload promotion queue lane {row.get('lane')!r} must expose missing_required_inputs")
        elif len(missing) != as_int(row.get("missing_required_input_count")):
            errors.append(f"payload promotion queue lane {row.get('lane')!r} missing_required_inputs count drift")
        if not isinstance(runtime, list):
            errors.append(f"payload promotion queue lane {row.get('lane')!r} must expose runtime_output_backlog")
        elif len(runtime) != as_int(row.get("runtime_output_backlog_count")):
            errors.append(f"payload promotion queue lane {row.get('lane')!r} runtime_output_backlog count drift")
        for item in list(missing if isinstance(missing, list) else []) + list(runtime if isinstance(runtime, list) else []):
            if not isinstance(item, dict):
                errors.append(f"payload promotion queue lane {row.get('lane')!r} backlog entries must be objects")
                continue
            for field in ("step_index", "step", "script", "path"):
                if item.get(field) in (None, ""):
                    errors.append(f"payload promotion queue lane {row.get('lane')!r} backlog entry missing {field}")
    priorities = [as_int(row.get("priority")) for row in rows if isinstance(row, dict)]
    if priorities != sorted(priorities):
        errors.append("payload promotion queue priorities must be sorted")
    if as_int(queue.get("total_missing_required_inputs")) <= 0:
        errors.append("payload promotion queue must expose current missing required input backlog")
    all_queue_missing = [
        item
        for row in rows
        if isinstance(row, dict)
        for item in row.get("missing_required_inputs", [])
        if isinstance(item, dict)
    ]
    all_queue_runtime = [
        item
        for row in rows
        if isinstance(row, dict)
        for item in row.get("runtime_output_backlog", [])
        if isinstance(item, dict)
    ]
    queue_missing_unique_paths = {item.get("path") for item in all_queue_missing}
    queue_runtime_unique_paths = {item.get("path") for item in all_queue_runtime}
    if len(queue_missing_unique_paths) != as_int(queue.get("total_missing_required_input_unique_paths")):
        errors.append("payload promotion queue missing input unique path count drift")
    if len(queue_runtime_unique_paths) != as_int(queue.get("total_runtime_output_unique_paths")):
        errors.append("payload promotion queue runtime output unique path count drift")
    lane_by_missing_path: dict[object, set[str]] = {}
    lane_by_runtime_path: dict[object, set[str]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        lane = str(row.get("lane") or "")
        for item in row.get("missing_required_inputs", []):
            if isinstance(item, dict):
                lane_by_missing_path.setdefault(item.get("path"), set()).add(lane)
        for item in row.get("runtime_output_backlog", []):
            if isinstance(item, dict):
                lane_by_runtime_path.setdefault(item.get("path"), set()).add(lane)
    expected_cross_missing = {
        path
        for path, lanes in lane_by_missing_path.items()
        if len(lanes) > 1
    }
    expected_cross_runtime = {
        path
        for path, lanes in lane_by_runtime_path.items()
        if len(lanes) > 1
    }
    actual_cross_missing = {
        item.get("path")
        for item in queue.get("cross_lane_missing_required_input_paths", [])
        if isinstance(item, dict)
    }
    actual_cross_runtime = {
        item.get("path")
        for item in queue.get("cross_lane_runtime_output_paths", [])
        if isinstance(item, dict)
    }
    if actual_cross_missing != expected_cross_missing:
        errors.append("payload promotion queue cross-lane missing input path list drift")
    if actual_cross_runtime != expected_cross_runtime:
        errors.append("payload promotion queue cross-lane runtime output path list drift")
    if REPLAY_GAP.exists():
        report = load_json(REPLAY_GAP)
        if isinstance(report, dict):
            if as_int(queue.get("total_missing_required_inputs")) != as_int(report.get("required_missing_input_count")):
                errors.append("payload promotion queue missing input total must match replay gap report")
            if as_int(queue.get("total_runtime_output_backlog")) != as_int(report.get("runtime_output_count")):
                errors.append("payload promotion queue runtime output total must match replay gap report")
            if as_int(queue.get("total_missing_required_input_unique_paths")) != as_int(report.get("required_missing_input_unique_path_count")):
                errors.append("payload promotion queue missing input unique path total must match replay gap report")
            if as_int(queue.get("total_runtime_output_unique_paths")) != as_int(report.get("runtime_output_unique_path_count")):
                errors.append("payload promotion queue runtime output unique path total must match replay gap report")
            gap_missing = {
                (as_int(item.get("step_index")), item.get("step"), item.get("script"), item.get("path"))
                for item in report.get("missing_required_inputs", [])
                if isinstance(item, dict)
            }
            gap_runtime = {
                (as_int(item.get("step_index")), item.get("step"), item.get("script"), item.get("path"))
                for item in report.get("runtime_outputs_not_currently_packaged", [])
                if isinstance(item, dict)
            }
            queue_missing = {
                (as_int(item.get("step_index")), item.get("step"), item.get("script"), item.get("path"))
                for row in rows
                if isinstance(row, dict)
                for item in row.get("missing_required_inputs", [])
                if isinstance(item, dict)
            }
            queue_runtime = {
                (as_int(item.get("step_index")), item.get("step"), item.get("script"), item.get("path"))
                for row in rows
                if isinstance(row, dict)
                for item in row.get("runtime_output_backlog", [])
                if isinstance(item, dict)
            }
            if queue_missing != gap_missing:
                errors.append("payload promotion queue missing input entries must match replay gap report")
            if queue_runtime != gap_runtime:
                errors.append("payload promotion queue runtime output entries must match replay gap report")
    return errors


def md_fact(text: str, pattern: str) -> str:
    match = re.search(pattern, text)
    return match.group(1) if match else ""


def check_delivery_manifest_facts() -> list[str]:
    errors: list[str] = []
    if not DELIVERY_AUDIT_MD.exists():
        return [f"missing delivery audit report: {DELIVERY_AUDIT_MD.relative_to(ROOT)}"]
    if not DELIVERY_MANIFEST_MD.exists():
        return [f"missing delivery manifest: {DELIVERY_MANIFEST_MD.relative_to(ROOT)}"]
    audit = DELIVERY_AUDIT_MD.read_text(encoding="utf-8")
    manifest = DELIVERY_MANIFEST_MD.read_text(encoding="utf-8")
    pairs = [
        (
            "catalog packages",
            r"- catalog packages: `([^`]+)`",
            r"- catalog 包数：`([^`]+)`",
        ),
        (
            "asset files",
            r"- asset files: `([^`]+)`",
            r"- 资产文件数：`([^`]+)`",
        ),
        (
            "referenced files",
            r"- referenced files: `([^`]+)`",
            r"- catalog 引用文件数：`([^`]+)`",
        ),
        (
            "unreferenced files",
            r"- unreferenced files: `([^`]+)`",
            r"- 未纳入 catalog 引用文件数：`([^`]+)`",
        ),
        (
            "total asset size MB",
            r"- total asset size MB: `([^`]+)`",
            r"- 资产目录总大小：`([^`]+) MB`",
        ),
        (
            "replay steps",
            r"- replay steps: `([^`]+)`",
            r"- 一键重放 step 数：`([^`]+)`",
        ),
        (
            "blockers",
            r"- blockers: `([^`]+)`",
            r"- 阻断项：`([^`]+)`",
        ),
        (
            "packaging actions",
            r"- packaging actions: `([^`]+)`",
            r"- 包装整理项：`([^`]+)`",
        ),
    ]
    for label, audit_pattern, manifest_pattern in pairs:
        audit_value = md_fact(audit, audit_pattern)
        manifest_value = md_fact(manifest, manifest_pattern)
        if not audit_value:
            errors.append(f"delivery audit missing fact: {label}")
        if not manifest_value:
            errors.append(f"delivery manifest missing fact: {label}")
        if audit_value and manifest_value and audit_value != manifest_value:
            errors.append(f"delivery manifest {label} drift: audit={audit_value!r} manifest={manifest_value!r}")
    return errors


def check_delivery_replay_required_artifacts() -> list[str]:
    errors: list[str] = []
    if not REPLAY_GAP.exists():
        return errors
    if not DELIVERY_REQUIREMENT_LOCK.exists():
        return [f"missing delivery replay requirement lock: {DELIVERY_REQUIREMENT_LOCK.relative_to(ROOT)}"]
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from scripts.migration import migration_asset_delivery_audit
    from scripts.migration import migration_asset_release_package

    report = load_json(REPLAY_GAP)
    if not isinstance(report, dict):
        return errors
    steps = report.get("steps") if isinstance(report.get("steps"), list) else []
    gap_required = {
        item.get("path")
        for step in steps
        if isinstance(step, dict) and step.get("scope") == "required"
        for item in step.get("input_artifacts", [])
        if isinstance(item, dict)
    }
    excluded = set(migration_asset_delivery_audit.BASELINE_EXCLUDED_REQUIRED_ARTIFACTS)
    expected = gap_required - excluded
    audit_required = set(migration_asset_delivery_audit.required_replay_artifacts())
    release_required = set(migration_asset_release_package.required_replay_artifacts())
    if audit_required != release_required:
        errors.append("delivery audit and release package required replay artifact sets differ")
    if audit_required != expected:
        errors.append(
            "delivery required replay artifact set must match replay gap required inputs "
            "minus baseline exclusions"
        )
    lock = load_json(DELIVERY_REQUIREMENT_LOCK)
    if not isinstance(lock, dict):
        return errors + ["delivery replay requirement lock root must be object"]
    if lock.get("lock_version") != "scbs55_delivery_replay_requirement_lock_v1":
        errors.append("delivery replay requirement lock version drift")
    if lock.get("status") != "PASS":
        errors.append(f"delivery replay requirement lock status must be PASS, got {lock.get('status')!r}")
    if as_int(lock.get("gap_required_input_unique_path_count")) != len(gap_required):
        errors.append("delivery replay requirement lock gap required count drift")
    if as_int(lock.get("baseline_excluded_required_path_count")) != len(gap_required & excluded):
        errors.append("delivery replay requirement lock baseline exclusion count drift")
    if as_int(lock.get("delivery_required_replay_artifact_count")) != len(audit_required):
        errors.append("delivery replay requirement lock delivery required count drift")
    if as_int(lock.get("release_required_replay_artifact_count")) != len(release_required):
        errors.append("delivery replay requirement lock release required count drift")
    if set(lock.get("delivery_required_replay_artifacts", [])) != audit_required:
        errors.append("delivery replay requirement lock delivery required artifact set drift")
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
    errors.extend(check_user_acceptance_groups(payload))
    errors.extend(check_inventory(payload))
    errors.extend(check_replay_gap_report())
    errors.extend(check_inventory_replay_sequence())
    errors.extend(check_promotion_queue())
    errors.extend(check_delivery_manifest_facts())
    errors.extend(check_delivery_replay_required_artifacts())
    report = {
        "status": "FAIL" if errors else "PASS",
        "freeze": str(FREEZE.relative_to(ROOT)),
        "inventory": str(INVENTORY.relative_to(ROOT)),
        "replay_gap": str(REPLAY_GAP.relative_to(ROOT)),
        "promotion_queue": str(PROMOTION_QUEUE.relative_to(ROOT)),
        "delivery_requirement_lock": str(DELIVERY_REQUIREMENT_LOCK.relative_to(ROOT)),
        "package_lock": str(PACKAGE_LOCK.relative_to(ROOT)),
        "compare": str(COMPARE.relative_to(ROOT)),
        "user_acceptance_group_count": len(payload.get("user_acceptance_groups", [])) if isinstance(payload.get("user_acceptance_groups"), list) else 0,
        "surface_count": len(payload.get("full_visibility_surfaces", [])) if isinstance(payload.get("full_visibility_surfaces"), list) else 0,
        "errors": errors,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 2 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
