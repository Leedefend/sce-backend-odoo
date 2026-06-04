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
SCBSLY_DIRECT_EVIDENCE = ROOT / "artifacts/migration/scbsly_direct_project_acceptance_menu_probe_v1.json"
SCBSLY_DIRECT_NEW_ALIGNMENT = ROOT / "artifacts/migration/scbsly_direct_project_new_system_alignment_probe_v1.json"
SCBSLY_DIRECT_BROWSER_MENU = ROOT / "artifacts/browser/scbsly-direct-project-menu/20260530T090744/report.json"
SCBSLY_DIRECT_GAP_MATRIX = ROOT / "artifacts/migration/scbsly_direct_project_alignment_gap_matrix_v1.json"
SCBSLY_DIRECT_OLD_ROW_DUMP = ROOT / "artifacts/migration/scbsly_direct_project_old_row_dump_summary_v1.json"
SCBSLY_DIRECT_OLD_IDENTITY_LOCK = ROOT / "artifacts/migration/scbsly_direct_project_old_identity_lock_v1.json"
SCBSLY_DIRECT_REPLAY_CARRIER_PLAN = ROOT / "artifacts/migration/scbsly_direct_project_replay_carrier_plan_v1.json"
SCBSLY_DIRECT_ACCEPTANCE_REPLAY = ROOT / "artifacts/migration/scbsly_direct_project_direct_acceptance_replay_result_v1.json"
REQUIRE_EVIDENCE = os.getenv("SCBS55_REQUIRE_ACCEPTANCE_EVIDENCE", "0") == "1"
EXPECTED_DIRECT_PROJECT_MENU_GROUP = [
    ("合同类单据", ["施工合同", "分包合同", "租赁合同", "供货合同", "供货合同（数据）", "劳务合同", "机械合同（合同）"]),
    ("材料管理类单据", ["材料计划", "报价单", "入库", "材料结算单", "库存统计表（新）"]),
    ("劳务管理类单据", ["方单", "零星用工", "劳务结算"]),
    ("分包管理类单据", ["分包方单", "分包结算单"]),
    ("机械与租赁管理类单据", ["机械台班记录", "机械结算单", "租入", "还租", "租赁结算单"]),
    (
        "费用与资金管理类单据",
        [
            "项目费用报销单",
            "管理人员工资表",
            "油卡登记",
            "充值登记",
            "加油登记",
            "支付申请",
            "工程进度收款",
            "往来单位付款",
            "工程结算单",
            "进项上报",
            "总包进项上报",
            "成本统计表（数据）",
        ],
    ),
    ("项目管理类单据", ["施工日志（新）"]),
]
EXPECTED_DIRECT_PROJECT_BROWSER_LABEL_COUNT = sum(
    len(items) for _, items in EXPECTED_DIRECT_PROJECT_MENU_GROUP
)


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


def check_acceptance_groups(payload: dict[str, Any], surfaces: list[Any]) -> list[str]:
    errors: list[str] = []
    groups = payload.get("user_acceptance_groups")
    if not isinstance(groups, list) or not groups:
        return ["user_acceptance_groups must be a non-empty list"]
    by_id = {str(group.get("group_id") or ""): group for group in groups if isinstance(group, dict)}
    required_groups = {"scbs55_high_risk_six_surfaces", "scbsly_direct_project_business_menus"}
    missing_groups = sorted(required_groups - set(by_id))
    if missing_groups:
        errors.append(f"user_acceptance_groups missing required groups {missing_groups}")

    six_group = by_id.get("scbs55_high_risk_six_surfaces")
    if isinstance(six_group, dict):
        surface_keys = [str(surface.get("key") or "") for surface in surfaces if isinstance(surface, dict)]
        group_keys = [str(key or "") for key in six_group.get("surface_keys", [])]
        if group_keys != surface_keys:
            errors.append("scbs55_high_risk_six_surfaces.surface_keys must match manifest surfaces order")
        if as_int(six_group.get("item_count")) != len(surface_keys):
            errors.append("scbs55_high_risk_six_surfaces.item_count drift")

    direct_group = by_id.get("scbsly_direct_project_business_menus")
    if isinstance(direct_group, dict):
        source_system = direct_group.get("source_system") if isinstance(direct_group.get("source_system"), dict) else {}
        if source_system.get("base_url") != "https://www.builderp.cn/SCBSLY_V2":
            errors.append("direct project group source_system.base_url drift")
        categories = direct_group.get("categories") if isinstance(direct_group.get("categories"), list) else []
        expected_count = sum(len(items) for _, items in EXPECTED_DIRECT_PROJECT_MENU_GROUP)
        if as_int(direct_group.get("item_count")) != expected_count:
            errors.append(f"direct project group item_count must be {expected_count}")
        if len(categories) != len(EXPECTED_DIRECT_PROJECT_MENU_GROUP):
            errors.append(f"direct project group category count must be {len(EXPECTED_DIRECT_PROJECT_MENU_GROUP)}")
        actual_items: list[str] = []
        for index, (expected_name, expected_items) in enumerate(EXPECTED_DIRECT_PROJECT_MENU_GROUP):
            category = categories[index] if index < len(categories) and isinstance(categories[index], dict) else {}
            actual_name = str(category.get("name") or "")
            actual_category_items = [str(item or "") for item in category.get("items", [])] if isinstance(category.get("items"), list) else []
            actual_items.extend(actual_category_items)
            if actual_name != expected_name:
                errors.append(f"direct project group category[{index}] name drift: {actual_name!r} != {expected_name!r}")
            if actual_category_items != expected_items:
                errors.append(f"direct project group category[{expected_name}] items drift")
        if len(actual_items) != expected_count:
            errors.append(f"direct project group actual item count {len(actual_items)} != {expected_count}")
        duplicate_items = sorted({item for item in actual_items if actual_items.count(item) > 1})
        blank_items = [index for index, item in enumerate(actual_items) if not item]
        if duplicate_items:
            errors.append(f"direct project group has duplicate menu labels {duplicate_items}")
        if blank_items:
            errors.append(f"direct project group has blank menu labels at indexes {blank_items}")
        target_surface = (
            direct_group.get("target_acceptance_surface")
            if isinstance(direct_group.get("target_acceptance_surface"), dict)
            else {}
        )
        if target_surface.get("expected_project_policy") != "公司直营":
            errors.append("direct project group expected_project_policy must be 公司直营")
        evidence = direct_group.get("latest_online_evidence") if isinstance(direct_group.get("latest_online_evidence"), dict) else {}
        if evidence.get("status") != "PASS":
            errors.append("direct project group latest_online_evidence.status must be PASS")
        for field, expected in (
            ("path", "artifacts/migration/scbsly_direct_project_acceptance_menu_probe_v1.json"),
            ("checked_count", expected_count),
            ("pass_count", expected_count),
            ("failure_count", 0),
            ("form_list_count_probe_count", 32),
            ("report_route_count", 2),
        ):
            actual = evidence.get(field)
            if isinstance(expected, int):
                if as_int(actual) != expected:
                    errors.append(f"direct project group latest_online_evidence.{field}={actual!r} != {expected!r}")
            elif actual != expected:
                errors.append(f"direct project group latest_online_evidence.{field}={actual!r} != {expected!r}")
        aliases = evidence.get("alias_matches") if isinstance(evidence.get("alias_matches"), dict) else {}
        if aliases.get("成本统计表（数据）") != "成本统计表（综合）":
            errors.append("direct project group must record cost-statistics menu alias")
        new_alignment = (
            direct_group.get("latest_new_system_alignment")
            if isinstance(direct_group.get("latest_new_system_alignment"), dict)
            else {}
        )
        expected_new_alignment = {
            "status": "PASS",
            "path": "artifacts/migration/scbsly_direct_project_new_system_alignment_probe_v1.json",
            "report": "artifacts/migration/scbsly_direct_project_new_system_alignment_probe_v1.md",
            "gap_matrix": "artifacts/migration/scbsly_direct_project_alignment_gap_matrix_v1.json",
            "gap_matrix_report": "artifacts/migration/scbsly_direct_project_alignment_gap_matrix_v1.md",
            "checked_count": expected_count,
            "pass_count": expected_count,
            "failure_count": 0,
            "missing_menu_count": 0,
            "count_mismatch_count": 0,
            "field_failure_count": 0,
        }
        for field, expected in expected_new_alignment.items():
            actual = new_alignment.get(field)
            if isinstance(expected, int):
                if as_int(actual) != expected:
                    errors.append(f"direct project latest_new_system_alignment.{field}={actual!r} != {expected!r}")
            elif actual != expected:
                errors.append(f"direct project latest_new_system_alignment.{field}={actual!r} != {expected!r}")
        gap_buckets = (
            new_alignment.get("gap_buckets")
            if isinstance(new_alignment.get("gap_buckets"), dict)
            else {}
        )
        for field, expected in (
            ("data_scope_count_mismatch", 0),
            ("missing_user_visible_menu_route", 0),
            ("missing_server_carrier", 0),
            ("pass", expected_count),
        ):
            if as_int(gap_buckets.get(field)) != expected:
                errors.append(f"direct project latest_new_system_alignment.gap_buckets.{field} drift")
        conclusion = str(new_alignment.get("blocking_conclusion") or "")
        if "menus, fields, and counts are aligned" not in conclusion or "engineering-progress receipt" not in conclusion or "rental-return" not in conclusion or "not contract-layer trimming" not in conclusion:
            errors.append("direct project latest_new_system_alignment must record blocking conclusion")
        browser_acceptance = (
            direct_group.get("latest_browser_menu_acceptance")
            if isinstance(direct_group.get("latest_browser_menu_acceptance"), dict)
            else {}
        )
        for field, expected in (
            ("status", "PASS"),
            ("path", "artifacts/browser/scbsly-direct-project-menu/20260530T090744/report.json"),
            ("report", "artifacts/browser/scbsly-direct-project-menu/20260530T090744/report.md"),
            ("screenshot_after_expand", "artifacts/browser/scbsly-direct-project-menu/20260530T090744/02-after-expand-all.png"),
            ("environment", "daily_dev"),
            ("frontend_url", "http://1.95.85.92:18081"),
            ("db_name", "sc_demo"),
            ("login", "wutao"),
            ("expected_visible_label_count", EXPECTED_DIRECT_PROJECT_BROWSER_LABEL_COUNT),
            ("actual_visible_label_count", EXPECTED_DIRECT_PROJECT_BROWSER_LABEL_COUNT),
            ("missing_label_count", 0),
            ("platform_release_snapshot", "v20260530_scbsly_direct_acceptance_menu_daily_dev"),
        ):
            actual = browser_acceptance.get(field)
            if isinstance(expected, int):
                if as_int(actual) != expected:
                    errors.append(f"direct project latest_browser_menu_acceptance.{field}={actual!r} != {expected!r}")
            elif actual != expected:
                errors.append(f"direct project latest_browser_menu_acceptance.{field}={actual!r} != {expected!r}")
        release_policy = str(browser_acceptance.get("release_snapshot_policy") or "")
        if "API navigation evidence alone is not sufficient" not in release_policy:
            errors.append("direct project browser acceptance must record API-vs-browser release snapshot policy")
        if SCBSLY_DIRECT_BROWSER_MENU.exists():
            browser_report = load_json(SCBSLY_DIRECT_BROWSER_MENU)
            if not isinstance(browser_report, dict):
                errors.append("SCBSLY direct browser menu acceptance root must be object")
            else:
                summary = browser_report.get("summary") if isinstance(browser_report.get("summary"), dict) else {}
                if browser_report.get("ok") is not True:
                    errors.append("SCBSLY direct browser menu acceptance report must be ok=true")
                for manifest_field, summary_field in (
                    ("expected_visible_label_count", "expected_count"),
                    ("actual_visible_label_count", "visible_count"),
                    ("missing_label_count", "missing_count"),
                ):
                    if as_int(browser_acceptance.get(manifest_field)) != as_int(summary.get(summary_field)):
                        errors.append(
                            "direct project browser acceptance drift: "
                            f"{summary_field}={summary.get(summary_field)!r} != "
                            f"{browser_acceptance.get(manifest_field)!r}"
                        )
        direct_replay = (
            direct_group.get("latest_direct_acceptance_replay")
            if isinstance(direct_group.get("latest_direct_acceptance_replay"), dict)
            else {}
        )
        for field, expected in (
            ("status", "PASS"),
            ("path", "artifacts/migration/scbsly_direct_project_direct_acceptance_replay_result_v1.json"),
            ("source_system", "online_old_scbsly"),
            ("model", "sc.legacy.direct.acceptance.fact"),
            ("label_count", 26),
            ("failure_count", 0),
        ):
            actual = direct_replay.get(field)
            if isinstance(expected, int):
                if as_int(actual) != expected:
                    errors.append(f"direct project latest_direct_acceptance_replay.{field}={actual!r} != {expected!r}")
            elif actual != expected:
                errors.append(f"direct project latest_direct_acceptance_replay.{field}={actual!r} != {expected!r}")
        if SCBSLY_DIRECT_ACCEPTANCE_REPLAY.exists():
            replay_result = load_json(SCBSLY_DIRECT_ACCEPTANCE_REPLAY)
            if not isinstance(replay_result, dict):
                errors.append("SCBSLY direct acceptance replay result root must be object")
            else:
                for field in ("source_system", "label_count", "failure_count"):
                    if replay_result.get(field) != direct_replay.get(field):
                        errors.append(
                            f"direct project acceptance replay drift: "
                            f"{field}={replay_result.get(field)!r} != {direct_replay.get(field)!r}"
                        )
        if SCBSLY_DIRECT_EVIDENCE.exists():
            actual_evidence = load_json(SCBSLY_DIRECT_EVIDENCE)
            if not isinstance(actual_evidence, dict):
                errors.append("SCBSLY direct evidence root must be object")
            else:
                field_pairs = (
                    ("status", "status"),
                    ("checked_count", "checked_count"),
                    ("pass_count", "pass_count"),
                    ("failure_count", "failure_count"),
                    ("form_list_count_probe_count", "form_list_count_probe_count"),
                )
                for manifest_field, evidence_field in field_pairs:
                    if actual_evidence.get(evidence_field) != evidence.get(manifest_field):
                        errors.append(
                            "direct project evidence drift: "
                            f"{evidence_field}={actual_evidence.get(evidence_field)!r} != {evidence.get(manifest_field)!r}"
                        )
                report_routes = len(
                    [
                        row
                        for row in actual_evidence.get("rows", [])
                        if isinstance(row, dict) and row.get("route_kind") == "lowcode_report"
                    ]
                )
                if report_routes != as_int(evidence.get("report_route_count")):
                    errors.append("direct project evidence report route count drift")
        if SCBSLY_DIRECT_NEW_ALIGNMENT.exists():
            actual_alignment = load_json(SCBSLY_DIRECT_NEW_ALIGNMENT)
            if not isinstance(actual_alignment, dict):
                errors.append("SCBSLY direct new alignment root must be object")
            else:
                for manifest_field, evidence_field in (
                    ("status", "status"),
                    ("checked_count", "checked_count"),
                    ("pass_count", "pass_count"),
                    ("failure_count", "failure_count"),
                    ("missing_menu_count", "missing_menu_count"),
                    ("count_mismatch_count", "count_mismatch_count"),
                    ("field_failure_count", "field_failure_count"),
                ):
                    if actual_alignment.get(evidence_field) != new_alignment.get(manifest_field):
                        errors.append(
                            "direct project new alignment drift: "
                            f"{evidence_field}={actual_alignment.get(evidence_field)!r} != "
                            f"{new_alignment.get(manifest_field)!r}"
                        )
        if SCBSLY_DIRECT_GAP_MATRIX.exists():
            gap_matrix = load_json(SCBSLY_DIRECT_GAP_MATRIX)
            if not isinstance(gap_matrix, dict):
                errors.append("SCBSLY direct gap matrix root must be object")
            else:
                if gap_matrix.get("source_alignment") != new_alignment.get("path"):
                    errors.append("direct project gap matrix source_alignment drift")
                for matrix_field, manifest_bucket in (
                    ("data_scope_count_mismatch_count", "data_scope_count_mismatch"),
                    ("missing_user_visible_menu_route_count", "missing_user_visible_menu_route"),
                    ("missing_server_carrier_count", "missing_server_carrier"),
                    ("pass_count", "pass"),
                ):
                    if as_int(gap_matrix.get(matrix_field)) != as_int(gap_buckets.get(manifest_bucket)):
                        errors.append(f"direct project gap matrix {matrix_field} drift")
        old_row_dump = (
            direct_group.get("latest_partial_old_row_dump")
            if isinstance(direct_group.get("latest_partial_old_row_dump"), dict)
            else {}
        )
        for field, expected in (
            ("status", "PASS"),
            ("path", "artifacts/migration/scbsly_direct_project_old_row_dump_summary_v1.json"),
            ("report", "artifacts/migration/scbsly_direct_project_old_row_dump_summary_v1.md"),
            ("dumped_count", 32),
            ("total_expected_rows", 76411),
            ("total_actual_rows", 76411),
        ):
            actual = old_row_dump.get(field)
            if isinstance(expected, int):
                if as_int(actual) != expected:
                    errors.append(f"direct project latest_partial_old_row_dump.{field}={actual!r} != {expected!r}")
            elif actual != expected:
                errors.append(f"direct project latest_partial_old_row_dump.{field}={actual!r} != {expected!r}")
        expected_dump_labels = [
            "施工合同",
            "分包合同",
            "租赁合同",
            "供货合同",
            "劳务合同",
            "机械合同（合同）",
            "材料计划",
            "报价单",
            "入库",
            "材料结算单",
            "方单",
            "零星用工",
            "劳务结算",
            "分包方单",
            "分包结算单",
            "机械台班记录",
            "机械结算单",
            "租入",
            "还租",
            "租赁结算单",
            "项目费用报销单",
            "管理人员工资表",
            "油卡登记",
            "充值登记",
            "加油登记",
            "支付申请",
            "工程进度收款",
            "往来单位付款",
            "工程结算单",
            "进项上报",
            "总包进项上报",
            "施工日志（新）",
        ]
        actual_dump_labels = [str(label or "") for label in old_row_dump.get("labels", [])] if isinstance(old_row_dump.get("labels"), list) else []
        if actual_dump_labels != expected_dump_labels:
            errors.append("direct project latest_partial_old_row_dump.labels drift")
        if SCBSLY_DIRECT_OLD_ROW_DUMP.exists():
            actual_dump = load_json(SCBSLY_DIRECT_OLD_ROW_DUMP)
            if not isinstance(actual_dump, dict):
                errors.append("SCBSLY direct old row dump summary root must be object")
            else:
                for field in ("status", "dumped_count", "total_expected_rows", "total_actual_rows"):
                    if actual_dump.get(field) != old_row_dump.get(field):
                        errors.append(
                            f"direct project old row dump summary drift: "
                            f"{field}={actual_dump.get(field)!r} != {old_row_dump.get(field)!r}"
                        )
        identity_lock = (
            direct_group.get("latest_old_identity_lock")
            if isinstance(direct_group.get("latest_old_identity_lock"), dict)
            else {}
        )
        for field, expected in (
            ("status", "PASS"),
            ("path", "artifacts/migration/scbsly_direct_project_old_identity_lock_v1.json"),
            ("report", "artifacts/migration/scbsly_direct_project_old_identity_lock_v1.md"),
            ("list_count", 32),
            ("total_rows", 76411),
            ("preferred_identity_count", 24),
            ("row_index_fallback_count", 7),
            ("row_hash_fallback_count", 0),
            ("empty_list_count", 1),
            ("failure_count", 0),
        ):
            actual = identity_lock.get(field)
            if isinstance(expected, int):
                if as_int(actual) != expected:
                    errors.append(f"direct project latest_old_identity_lock.{field}={actual!r} != {expected!r}")
            elif actual != expected:
                errors.append(f"direct project latest_old_identity_lock.{field}={actual!r} != {expected!r}")
        policy = str(identity_lock.get("policy") or "")
        if "not count-only matching" not in policy:
            errors.append("direct project latest_old_identity_lock must forbid count-only matching")
        if SCBSLY_DIRECT_OLD_IDENTITY_LOCK.exists():
            actual_identity = load_json(SCBSLY_DIRECT_OLD_IDENTITY_LOCK)
            if not isinstance(actual_identity, dict):
                errors.append("SCBSLY direct old identity lock root must be object")
            else:
                for field in (
                    "status",
                    "list_count",
                    "total_rows",
                    "preferred_identity_count",
                    "row_index_fallback_count",
                    "row_hash_fallback_count",
                    "empty_list_count",
                    "failure_count",
                ):
                    if actual_identity.get(field) != identity_lock.get(field):
                        errors.append(
                            f"direct project old identity lock drift: "
                            f"{field}={actual_identity.get(field)!r} != {identity_lock.get(field)!r}"
                        )
        replay_plan = (
            direct_group.get("latest_replay_carrier_plan")
            if isinstance(direct_group.get("latest_replay_carrier_plan"), dict)
            else {}
        )
        for field, expected in (
            ("status", "READY_FOR_REPLAY_IMPLEMENTATION_WITH_BLOCKERS"),
            ("path", "artifacts/migration/scbsly_direct_project_replay_carrier_plan_v1.json"),
            ("report", "artifacts/migration/scbsly_direct_project_replay_carrier_plan_v1.md"),
            ("checked_count", 34),
            ("old_list_identity_count", 32),
        ):
            actual = replay_plan.get(field)
            if isinstance(expected, int):
                if as_int(actual) != expected:
                    errors.append(f"direct project latest_replay_carrier_plan.{field}={actual!r} != {expected!r}")
            elif actual != expected:
                errors.append(f"direct project latest_replay_carrier_plan.{field}={actual!r} != {expected!r}")
        replay_buckets = (
            replay_plan.get("bucket_summary")
            if isinstance(replay_plan.get("bucket_summary"), dict)
            else {}
        )
        expected_replay_buckets = {
            "existing_carrier_requires_identity_replay_or_scoped_surface": (21, 48250),
            "menu_alias_added_requires_replay": (7, 27621),
            "menu_alias_added_empty_old_list": (1, 0),
            "legacy_fuel_carrier_added_requires_replay": (3, 540),
            "report_route_no_row_replay": (2, 0),
        }
        for bucket, (expected_count, expected_rows) in expected_replay_buckets.items():
            stats = replay_buckets.get(bucket) if isinstance(replay_buckets.get(bucket), dict) else {}
            if as_int(stats.get("count")) != expected_count or as_int(stats.get("old_rows")) != expected_rows:
                errors.append(f"direct project latest_replay_carrier_plan bucket {bucket} drift")
        replay_policy = str(replay_plan.get("policy") or "")
        if "oil/fuel legacy carriers" not in replay_policy or "engineering-progress receipt facts" not in replay_policy or "rental-return facts" not in replay_policy:
            errors.append("direct project latest_replay_carrier_plan must record replay status for remediated carriers")
        if SCBSLY_DIRECT_REPLAY_CARRIER_PLAN.exists():
            actual_plan = load_json(SCBSLY_DIRECT_REPLAY_CARRIER_PLAN)
            if not isinstance(actual_plan, dict):
                errors.append("SCBSLY direct replay carrier plan root must be object")
            else:
                for field in ("status", "checked_count", "old_list_identity_count"):
                    if actual_plan.get(field) != replay_plan.get(field):
                        errors.append(
                            f"direct project replay carrier plan drift: "
                            f"{field}={actual_plan.get(field)!r} != {replay_plan.get(field)!r}"
                        )
                actual_buckets = actual_plan.get("bucket_summary") if isinstance(actual_plan.get("bucket_summary"), dict) else {}
                for bucket, (expected_count, expected_rows) in expected_replay_buckets.items():
                    stats = actual_buckets.get(bucket) if isinstance(actual_buckets.get(bucket), dict) else {}
                    if as_int(stats.get("count")) != expected_count or as_int(stats.get("old_rows")) != expected_rows:
                        errors.append(f"direct project replay carrier plan artifact bucket {bucket} drift")
    return errors


def check_manifest(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if payload.get("asset_manifest_version") != "1.0":
        errors.append("asset_manifest_version must be 1.0")
    if payload.get("asset_package_id") != "scbs55_user_acceptance_surfaces_v1":
        errors.append("asset_package_id must be scbs55_user_acceptance_surfaces_v1")
    surfaces = payload.get("surfaces")
    if not isinstance(surfaces, list) or not surfaces:
        return ["surfaces must be a non-empty list"]
    errors.extend(check_acceptance_groups(payload, surfaces))

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
        lineage = surface.get("full_scope_lineage") if isinstance(surface.get("full_scope_lineage"), dict) else {}
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
            ("full_scope_lineage.relation", lineage.get("relation")),
        ):
            if value in (None, ""):
                errors.append(f"{key or index}: missing {field}")
        relation = lineage.get("relation")
        if relation == "direct_full_visibility_surface":
            if as_int(lineage.get("seq")) <= 0:
                errors.append(f"{key}: full_scope_lineage.seq must be positive for direct full visibility surfaces")
            if not lineage.get("surface_name"):
                errors.append(f"{key}: full_scope_lineage.surface_name is required for direct full visibility surfaces")
        elif relation == "independent_high_risk_acceptance_slice":
            if not lineage.get("reason"):
                errors.append(f"{key}: full_scope_lineage.reason is required for independent slices")
        elif relation:
            errors.append(f"{key}: unsupported full_scope_lineage.relation {relation!r}")
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
        "user_acceptance_group_count": len(payload.get("user_acceptance_groups", [])) if isinstance(payload.get("user_acceptance_groups"), list) else 0,
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
