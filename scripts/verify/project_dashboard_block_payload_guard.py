#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BUILDERS = ROOT / "addons" / "smart_construction_core" / "services" / "project_dashboard_builders"


def _must(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit(msg)


def _check_file(path: Path, required_fragments: list[str]) -> None:
    text = path.read_text(encoding="utf-8")
    for frag in required_fragments:
        _must(frag in text, f"{path.name}: missing payload fragment `{frag}`")


def main() -> None:
    specs = {
        "project_header_builder.py": [
            'block_type = "record_summary"',
            '"summary": {',
            '"quick_actions": [',
            '"project_code":',
            '"stage_name":',
        ],
        "project_metrics_builder.py": [
            'block_type = "metric_row"',
            '"items": [',
            '"task_total"',
            '"contract_total"',
            '"cost_rows"',
            '"payment_total"',
        ],
        "project_progress_builder.py": [
            'block_type = "progress_summary"',
            '"task_total":',
            '"task_done":',
            '"completion_percent":',
        ],
        "project_contract_builder.py": [
            'block_type = "record_table"',
            '"columns": ["contract_count", "contract_amount_total"]',
            '"rows": [',
            '"contract_count":',
            '"contract_amount_total":',
        ],
        "project_cost_builder.py": [
            'block_type = "record_summary"',
            '"summary": {',
            '"budget_count":',
            '"cost_ledger_count":',
        ],
        "project_finance_builder.py": [
            'block_type = "record_table"',
            '"columns": ["payment_request_total"]',
            '"rows": [{"payment_request_total": total}]',
            '"quick_actions": [',
            '"open_payment_requests"',
            '"open_settlement_orders"',
        ],
        "project_risk_builder.py": [
            'block_type = "alert_panel"',
            '"alerts": alerts',
            '"quick_actions": [',
            '"NO_RISK_SIGNAL"',
            '"ACTIVITY_OVERDUE"',
        ],
    }
    for filename, frags in specs.items():
        _check_file(BUILDERS / filename, frags)
    print("[verify.project.dashboard.block_payload] PASS")


if __name__ == "__main__":
    main()
