#!/usr/bin/env python3
"""Produce detailed judgment for remaining legacy assetization candidates."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REMAINING_JSON = Path(".runtime_artifacts/migration_assets/remaining_business_fact_screen/legacy_remaining_business_fact_screen_v1.json")
PAYMENT_JSON = Path(".runtime_artifacts/migration_assets/payment_request_residual_screen/legacy_payment_request_residual_screen_v1.json")
FUND_LOAN_JSON = Path(".runtime_artifacts/migration_assets/fund_loan_residual_screen/legacy_fund_loan_residual_screen_v1.json")
FINANCING_ASSET_JSON = Path(".runtime_artifacts/migration_assets/legacy_financing_loan_sc_v1/legacy_financing_loan_asset_generation_v1.json")
FUND_DAILY_ASSET_JSON = Path(".runtime_artifacts/migration_assets/legacy_fund_daily_snapshot_sc_v1/legacy_fund_daily_snapshot_asset_generation_v1.json")
OUTPUT_MD = Path("docs/migration_alignment/frozen/legacy_remaining_detailed_judgment_v1.md")
OUTPUT_JSON = Path(".runtime_artifacts/migration_assets/remaining_detailed_judgment/legacy_remaining_detailed_judgment_v1.json")


class RemainingDetailedJudgmentError(Exception):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RemainingDetailedJudgmentError(message)


def load_json(path: Path) -> dict[str, Any]:
    require(path.exists(), f"missing evidence file: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_matrix(
    remaining: dict[str, Any],
    payment: dict[str, Any],
    fund_loan: dict[str, Any],
    financing_asset: dict[str, Any],
    fund_daily_asset: dict[str, Any],
) -> list[dict[str, Any]]:
    family_counts = remaining["remaining_family_counts"]
    family_tables = remaining.get("remaining_family_table_counts", {})
    return [
        {
            "family": "payment_request_residual",
            "rows": family_counts.get("payment_request_residual", 0),
            "top_tables": family_tables.get("payment_request_residual", {}),
            "layer": "core_business_fact_candidate",
            "evidence": (
                f"C_ZFSQGL direct residual screen: raw={payment.get('raw_rows')}, "
                f"already_assetized={payment.get('already_assetized_rows')}, "
                f"residual_loadable={payment.get('residual_loadable_rows')}, "
                f"blocked={payment.get('blocked_rows')}"
            ),
            "decision": "no_further_assetization",
            "reason": "All rows meeting project, partner, positive amount, and non-deleted rules are already in outflow_request_sc_v1.",
            "next_action": "none",
        },
        {
            "family": "supplier_or_purchase_residual",
            "rows": family_counts.get("supplier_or_purchase_residual", 0),
            "top_tables": family_tables.get("supplier_or_purchase_residual", {}),
            "layer": "mixed_master_and_business_fact",
            "evidence": "T_GYSHT_INFO supplier contracts already have a 5301-row supplier_contract asset lane; T_Base_CooperatCompany is partner/master-data oriented.",
            "decision": "screen_only_for_T_CGHT_INFO_then_decide",
            "reason": "Most remaining rows are master-data approvals or blocked supplier-contract rows. The only plausible uncovered business-fact slice is T_CGHT_INFO purchase-contract residue.",
            "next_action": "open read-only screen for T_CGHT_INFO and residual T_GYSHT_INFO blockers; do not model yet.",
        },
        {
            "family": "fund_daily_or_loan_residual",
            "rows": family_counts.get("fund_daily_or_loan_residual", 0),
            "top_tables": family_tables.get("fund_daily_or_loan_residual", {}),
            "layer": "partially_assetized_management_snapshot_residual",
            "evidence": (
                f"Fund/loan screen: raw={fund_loan.get('raw_rows')}, "
                f"project_financing={fund_loan.get('classification_counts', {}).get('project_anchored_financing_candidate')}, "
                f"management_snapshots={fund_loan.get('classification_counts', {}).get('management_snapshot_candidate')}, "
                f"blocked={fund_loan.get('classification_counts', {}).get('blocked')}; "
                f"financing_package={financing_asset.get('asset_package_id')} generated={financing_asset.get('counts', {}).get('loadable_records')}; "
                f"fund_daily_package={fund_daily_asset.get('asset_package_id')} generated={fund_daily_asset.get('counts', {}).get('loadable_records')}"
            ),
            "decision": "assetized_except_blocked_tail",
            "reason": "Project loan/borrowing facts are in legacy_financing_loan_sc_v1 and user-required fund daily snapshots are in legacy_fund_daily_snapshot_sc_v1. Remaining fund-family rows are blocked tail records.",
            "next_action": "none; do not open another fund/loan lane unless blocked-tail recovery is explicitly required.",
        },
        {
            "family": "tender_registration_residual",
            "rows": family_counts.get("tender_registration_residual", 0),
            "top_tables": family_tables.get("tender_registration_residual", {}),
            "layer": "pre_project_auxiliary_fact",
            "evidence": "Tender registration rows are pre-contract/pre-project business-development information.",
            "decision": "defer_unless_tender_scope_confirmed",
            "reason": "Not required for current project execution reconstruction. Could become useful only if tender/business-development history is in scope.",
            "next_action": "defer; screen later only if owner wants tender history.",
        },
        {
            "family": "document_admin_residual",
            "rows": family_counts.get("document_admin_residual", 0),
            "top_tables": family_tables.get("document_admin_residual", {}),
            "layer": "business_auxiliary_information",
            "evidence": "Seal use, document review, and archive/photo management. Attachment URL backfill already covers deterministic linked file records.",
            "decision": "no_core_fact_assetization_now",
            "reason": "Administrative documents are auxiliary evidence, not core project/accounting/contract facts. Model design should wait for a document-center requirement.",
            "next_action": "defer; optionally build document index only after document-center target model is confirmed.",
        },
        {
            "family": "attendance_hr_residual",
            "rows": family_counts.get("attendance_hr_residual", 0),
            "top_tables": family_tables.get("attendance_hr_residual", {}),
            "layer": "out_of_scope_hr_fact",
            "evidence": "Leave, outing, and performance approval rows.",
            "decision": "exclude_from_construction_migration",
            "reason": "HR facts do not support the current old-business-fact to construction project model reconstruction objective.",
            "next_action": "discard for current migration; revisit only in a dedicated HR migration objective.",
        },
        {
            "family": "unknown_or_unmapped_family",
            "rows": family_counts.get("unknown_or_unmapped_family", 0),
            "top_tables": family_tables.get("unknown_or_unmapped_family", {}),
            "layer": "mostly_blocked_or_low_confidence",
            "evidence": "Largest slice is C_JXXP_ZYFPJJD, already screened as mostly missing counterparty evidence; other slices include zero-amount refunds, residual expense/deposit rows, and miscellaneous approvals.",
            "decision": "do_not_bulk_assetize",
            "reason": "Bulk migration would weaken source-fact requirements. Only table-specific screens may promote small slices.",
            "next_action": "no bulk lane; use targeted screens only if a table becomes business-critical.",
        },
    ]


def judgment() -> dict[str, Any]:
    remaining = load_json(REMAINING_JSON)
    payment = load_json(PAYMENT_JSON)
    fund_loan = load_json(FUND_LOAN_JSON)
    financing_asset = load_json(FINANCING_ASSET_JSON)
    fund_daily_asset = load_json(FUND_DAILY_ASSET_JSON)
    require(remaining.get("status") == "PASS", "remaining screen evidence is not PASS")
    require(payment.get("status") == "PASS", "payment residual evidence is not PASS")
    require(fund_loan.get("status") == "PASS", "fund/loan screen evidence is not PASS")
    require(financing_asset.get("status") == "PASS", "financing asset evidence is not PASS")
    require(fund_daily_asset.get("status") == "PASS", "fund daily asset evidence is not PASS")
    matrix = build_matrix(remaining, payment, fund_loan, financing_asset, fund_daily_asset)
    next_lane = {
        "lane": "supplier_or_purchase_residual_screen",
        "reason": "payment residual has no loadable rows and project financing facts are now assetized; supplier/purchase is the next remaining classified business family that may still contain an uncovered purchase-contract slice.",
        "scope": [
            "T_CGHT_INFO",
            "T_GYSHT_INFO residual blockers",
        ],
        "mode": "read_only_screen_first",
    }
    return {
        "status": "PASS",
        "raw_workflow_rows": remaining["raw_rows"],
        "covered_rows": remaining["covered_rows"],
        "remaining_rows": remaining["remaining_rows"],
        "matrix": matrix,
        "next_executable_lane": next_lane,
        "db_writes": 0,
        "odoo_shell": False,
    }


def write_report(path: Path, result: dict[str, Any]) -> None:
    lines = [
        "# Legacy Remaining Detailed Judgment v1",
        "",
        "Status: `PASS`",
        "",
        "This report gives a detailed business-level judgment for remaining old-system data after the current 23-package asset bus.",
        "",
        "## Coverage Baseline",
        "",
        f"- raw workflow rows: `{result['raw_workflow_rows']}`",
        f"- covered rows: `{result['covered_rows']}`",
        f"- remaining rows: `{result['remaining_rows']}`",
        "- DB writes: `0`",
        "- Odoo shell: `false`",
        "",
        "## Detailed Decision Matrix",
        "",
        "| Family | Rows | Layer | Decision | Next action |",
        "|---|---:|---|---|---|",
    ]
    for row in result["matrix"]:
        lines.append(
            f"| {row['family']} | {row['rows']} | {row['layer']} | {row['decision']} | {row['next_action']} |"
        )
    lines.extend(["", "## Evidence By Family", ""])
    for row in result["matrix"]:
        lines.extend(
            [
                f"### {row['family']}",
                "",
                f"- rows: `{row['rows']}`",
                f"- layer: `{row['layer']}`",
                f"- top tables: `{json.dumps(row['top_tables'], ensure_ascii=False)}`",
                f"- evidence: {row['evidence']}",
                f"- reason: {row['reason']}",
                f"- decision: `{row['decision']}`",
                f"- next action: {row['next_action']}",
                "",
            ]
        )
    next_lane = result["next_executable_lane"]
    lines.extend(
        [
            "## Next Executable Lane",
            "",
            f"- lane: `{next_lane['lane']}`",
            f"- mode: `{next_lane['mode']}`",
            f"- scope: `{', '.join(next_lane['scope'])}`",
            f"- reason: {next_lane['reason']}",
            "",
            "## Operating Judgment",
            "",
            "Do not open another bulk migration lane from the remaining workflow rows.",
            "Only table-specific read-only screens should promote further data into model or XML work.",
            "The current best next step is a supplier/purchase residual source-table screen, not another payment request or fund/loan lane.",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Produce detailed remaining legacy assetization judgment.")
    parser.add_argument("--output-md", default=str(OUTPUT_MD))
    parser.add_argument("--output-json", default=str(OUTPUT_JSON))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        result = judgment()
        write_json(Path(args.output_json), result)
        write_report(Path(args.output_md), result)
    except (RemainingDetailedJudgmentError, json.JSONDecodeError) as exc:
        payload = {"status": "FAIL", "error": str(exc), "db_writes": 0, "odoo_shell": False}
        print("LEGACY_REMAINING_DETAILED_JUDGMENT=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 1 if args.check else 0
    print("LEGACY_REMAINING_DETAILED_JUDGMENT=" + json.dumps({
        "status": "PASS",
        "remaining_rows": result["remaining_rows"],
        "next_executable_lane": result["next_executable_lane"],
        "db_writes": 0,
        "odoo_shell": False,
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
