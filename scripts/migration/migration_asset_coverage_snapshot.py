#!/usr/bin/env python3
"""Freeze a coverage snapshot for the repository migration asset bus."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ASSET_ROOT = Path("migration_assets")
CATALOG_PATH = ASSET_ROOT / "manifest/migration_asset_catalog_v1.json"
OUTPUT_JSON = ASSET_ROOT / "manifest/migration_asset_coverage_snapshot_v1.json"
OUTPUT_MD = Path("docs/migration_alignment/frozen/migration_asset_coverage_snapshot_v1.md")
EXPECTED_PACKAGE_COUNT = 17


class CoverageSnapshotError(Exception):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise CoverageSnapshotError(message)


def load_json(path: Path) -> dict[str, Any]:
    require(path.exists(), f"missing json file: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def package_summary(asset_root: Path, package: dict[str, Any]) -> dict[str, Any]:
    manifest_path = asset_root / package["asset_manifest_path"]
    manifest = load_json(manifest_path)
    counts = manifest.get("counts", {})
    return {
        "asset_package_id": package["asset_package_id"],
        "target_model": package["target_model"],
        "layer": package["layer"],
        "load_phase": package["load_phase"],
        "dependencies": package.get("dependencies", []),
        "raw_rows": counts.get("raw_rows"),
        "loadable_records": counts.get("loadable_records"),
        "blocked_records": counts.get("blocked_records", counts.get("discarded_records", 0)),
        "risk_class": package.get("risk_class"),
        "verification_command": package.get("verification_command"),
    }


def next_lanes(packages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id = {row["asset_package_id"]: row for row in packages}
    contract = by_id.get("contract_sc_v1", {})
    receipt = by_id.get("receipt_sc_v1", {})
    outflow = by_id.get("outflow_request_sc_v1", {})
    actual_outflow = by_id.get("actual_outflow_sc_v1", {})
    supplier_contract = by_id.get("supplier_contract_sc_v1", {})
    supplier_contract_line = by_id.get("supplier_contract_line_sc_v1", {})
    outflow_request_line = by_id.get("outflow_request_line_sc_v1", {})
    receipt_invoice_line = by_id.get("receipt_invoice_line_sc_v1", {})
    receipt_invoice_attachment = by_id.get("receipt_invoice_attachment_sc_v1", {})
    legacy_attachment_backfill = by_id.get("legacy_attachment_backfill_sc_v1", {})
    contract_line = by_id.get("contract_line_sc_v1", {})
    return [
        {
            "lane": "contract_blocker_recovery",
            "priority": 1,
            "reason": "合同头阻断仍控制后续收款、付款、结算事实的可锚定范围。",
            "current_blocked_records": contract.get("blocked_records"),
            "safe_next_action": "screen remaining deleted/direction/project blockers without weakening project-anchor rule",
        },
        {
            "lane": "receipt_blocker_recovery",
            "priority": 2,
            "reason": "Owner 已确认剩余收款阻断为无效业务数据，收款恢复队列关闭。",
            "current_blocked_records": receipt.get("blocked_records"),
            "safe_next_action": "closed_as_invalid_business_data_no_further_recovery",
        },
        {
            "lane": "contract_amount_gap",
            "priority": 3,
            "reason": "新模型合同头不要求金额；缺金额合同保留头信息，不伪造 summary line。",
            "current_blocked_records": contract_line.get("blocked_records"),
            "safe_next_action": "closed_keep_contract_headers_without_fabricated_summary_lines",
        },
        {
            "lane": "outflow_request_assetization",
            "priority": 4,
            "reason": "支出申请核心事实已资产化；结算、台账、会计和流程状态仍排除。",
            "current_blocked_records": outflow.get("blocked_records"),
            "safe_next_action": "closed_core_outflow_request_assets_continue_to_next_business_fact_lane",
        },
        {
            "lane": "actual_outflow_assetization",
            "priority": 5,
            "reason": "实际支出事实以草稿承载资产化；不宣称已付款状态，不生成台账、结算或会计事实。",
            "current_blocked_records": actual_outflow.get("blocked_records"),
            "safe_next_action": "closed_draft_actual_outflow_assets_continue_to_supplier_contract_lane",
        },
        {
            "lane": "supplier_contract_assetization",
            "priority": 6,
            "reason": "供应商合同头事实已按 type=in 资产化；金额和合同行进入后续独立 lane。",
            "current_blocked_records": supplier_contract.get("blocked_records"),
            "safe_next_action": "continue_to_supplier_contract_amount_or_line_lane",
        },
        {
            "lane": "supplier_contract_line_assetization",
            "priority": 7,
            "reason": "供应商合同金额已按摘要合同行资产化；不宣称旧库数量/单价明细语义。",
            "current_blocked_records": supplier_contract_line.get("blocked_records"),
            "safe_next_action": "continue_to_receipt_invoice_or_outflow_line_lane",
        },
        {
            "lane": "outflow_request_line_assetization",
            "priority": 8,
            "reason": "付款申请明细已按 payment.request.line 资产化；父申请锚点必须存在，台账/结算/会计语义仍排除。",
            "current_blocked_records": outflow_request_line.get("blocked_records"),
            "safe_next_action": "closed_line_fact_assets_no_db_replay_in_this_stage",
        },
        {
            "lane": "receipt_invoice_line_assetization",
            "priority": 9,
            "reason": "收款发票明细已按 sc.receipt.invoice.line 资产化；附件二进制进入后续独立 lane。",
            "current_blocked_records": receipt_invoice_line.get("blocked_records"),
            "safe_next_action": "continue_to_receipt_invoice_line_usability_or_attachment_index_lane",
        },
        {
            "lane": "receipt_invoice_attachment_assetization",
            "priority": 10,
            "reason": "收款发票附件已按 URL 型 ir.attachment 资产化；二进制文件本体仍由外部文件仓治理。",
            "current_blocked_records": receipt_invoice_attachment.get("blocked_records"),
            "safe_next_action": "continue_to_next_legacy_business_fact_lane_or_binary_file_custody_plan",
        },
        {
            "lane": "legacy_attachment_backfill_assetization",
            "priority": 11,
            "reason": "前置业务事实附件已按 URL 型 ir.attachment 回填资产化；二进制文件本体仍由外部文件仓治理。",
            "current_blocked_records": legacy_attachment_backfill.get("blocked_records"),
            "safe_next_action": "continue_to_binary_file_custody_plan_or_next_business_fact_lane",
        },
    ]


def render_markdown(payload: dict[str, Any]) -> str:
    rows = "\n".join(
        "| {asset_package_id} | {target_model} | {layer} | {raw_rows} | {loadable_records} | {blocked_records} | {risk_class} |".format(
            **row
        )
        for row in payload["packages"]
    )
    next_rows = "\n".join(
        f"| {row['priority']} | {row['lane']} | {row['current_blocked_records']} | {row['safe_next_action']} |"
        for row in payload["next_lanes"]
    )
    return f"""# Migration Asset Coverage Snapshot v1

Status: `{payload["status"]}`

Generated at: `{payload["generated_at"]}`

This frozen snapshot records the repository-tracked migration asset bus coverage.
It is no-DB, no-Odoo-shell, and does not materialize any runtime business side
effects.

## Catalog

- catalog: `{payload["catalog_path"]}`
- package count: `{payload["package_count"]}`
- DB writes: `0`
- Odoo shell: `false`

## Package Coverage

| Package | Target model | Layer | Raw rows | Loadable | Blocked/discarded | Risk |
|---|---|---:|---:|---:|---:|---|
{rows}

## Totals

- raw rows covered: `{payload["totals"]["raw_rows"]}`
- loadable records: `{payload["totals"]["loadable_records"]}`
- blocked/discarded records: `{payload["totals"]["blocked_records"]}`

## Next Lanes

| Priority | Lane | Current blocked | Safe next action |
|---:|---|---:|---|
{next_rows}

## Decision

`{payload["decision"]}`
"""


def build_snapshot(asset_root: Path, catalog_path: Path) -> dict[str, Any]:
    catalog = load_json(catalog_path)
    packages = [package_summary(asset_root, package) for package in catalog.get("packages", [])]
    require(len(packages) == EXPECTED_PACKAGE_COUNT, f"unexpected package count: {len(packages)}")
    totals = {
        "raw_rows": sum(int(row.get("raw_rows") or 0) for row in packages),
        "loadable_records": sum(int(row.get("loadable_records") or 0) for row in packages),
        "blocked_records": sum(int(row.get("blocked_records") or 0) for row in packages),
    }
    return {
        "status": "PASS",
        "generated_at": "2026-04-15T14:40:00+00:00",
        "catalog_path": str(catalog_path),
        "package_count": len(packages),
        "packages": packages,
        "totals": totals,
        "next_lanes": next_lanes(packages),
        "db_writes": 0,
        "odoo_shell": False,
        "decision": "coverage_snapshot_frozen_no_db_replay_continue_business_fact_assetization",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate migration asset coverage snapshot.")
    parser.add_argument("--asset-root", default=str(ASSET_ROOT))
    parser.add_argument("--catalog", default=str(CATALOG_PATH))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    try:
        payload = build_snapshot(Path(args.asset_root), Path(args.catalog))
        write_json(OUTPUT_JSON, payload)
        OUTPUT_MD.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT_MD.write_text(render_markdown(payload), encoding="utf-8")
    except (CoverageSnapshotError, json.JSONDecodeError) as exc:
        result = {"status": "FAIL", "error": str(exc), "db_writes": 0, "odoo_shell": False}
        print("MIGRATION_ASSET_COVERAGE_SNAPSHOT=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 1 if args.check else 0

    print(
        "MIGRATION_ASSET_COVERAGE_SNAPSHOT="
        + json.dumps(
            {
                "status": payload["status"],
                "package_count": payload["package_count"],
                "loadable_records": payload["totals"]["loadable_records"],
                "blocked_records": payload["totals"]["blocked_records"],
                "db_writes": 0,
                "odoo_shell": False,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
