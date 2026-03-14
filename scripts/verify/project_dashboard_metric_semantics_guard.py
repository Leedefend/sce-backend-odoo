#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
METRICS_BUILDER = ROOT / "addons" / "smart_construction_core" / "services" / "project_dashboard_builders" / "project_metrics_builder.py"
HEADER_BUILDER = ROOT / "addons" / "smart_construction_core" / "services" / "project_dashboard_builders" / "project_header_builder.py"
CONTRACT_BUILDER = ROOT / "addons" / "smart_construction_core" / "services" / "project_dashboard_builders" / "project_contract_builder.py"
FINANCE_BUILDER = ROOT / "addons" / "smart_construction_core" / "services" / "project_dashboard_builders" / "project_finance_builder.py"
PROGRESS_BUILDER = ROOT / "addons" / "smart_construction_core" / "services" / "project_dashboard_builders" / "project_progress_builder.py"
RISK_BUILDER = ROOT / "addons" / "smart_construction_core" / "services" / "project_dashboard_builders" / "project_risk_builder.py"
VIEW_FILE = ROOT / "frontend" / "apps" / "web" / "src" / "views" / "ProjectManagementDashboardView.vue"
DOC_ZH = ROOT / "docs" / "contract" / "project_dashboard_metric_semantics_v1.md"
DOC_EN = ROOT / "docs" / "contract" / "project_dashboard_metric_semantics_v1.en.md"


def _must(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit(msg)


def _contains(path: Path, fragments: list[str]) -> None:
    text = path.read_text(encoding="utf-8")
    for frag in fragments:
        _must(frag in text, f"{path.name}: missing fragment `{frag}`")


def _not_contains(path: Path, fragments: list[str]) -> None:
    text = path.read_text(encoding="utf-8")
    for frag in fragments:
        _must(frag not in text, f"{path.name}: forbidden fragment `{frag}` detected")


def main() -> None:
    _must(DOC_ZH.exists(), "metric semantics zh doc missing")
    _must(DOC_EN.exists(), "metric semantics en doc missing")

    _contains(
        HEADER_BUILDER,
        [
            "\"open_task_overdue\"",
            "\"open_task_blocked\"",
            "\"open_risk_list\"",
            "\"open_payment_requests\"",
            "quick_actions.sort",
        ],
    )

    _contains(
        METRICS_BUILDER,
        [
            "base_amount = contract_amount_total or revenue_target",
            "output_value = reported_output or progress_output",
            "payment_rate = self._safe_rate(received_amount, contract_amount_total)",
        ],
    )
    _not_contains(
        METRICS_BUILDER,
        [
            "output_value = reported_output or received_amount",
            "output_value = received_amount",
        ],
    )

    _contains(
        CONTRACT_BUILDER,
        [
            "out_domain = domain + [(\"type\", \"=\", \"out\")]",
            "in_domain = domain + [(\"type\", \"=\", \"in\")]",
            "\"subcontract_total\"",
        ],
    )

    _contains(
        FINANCE_BUILDER,
        [
            "receivable = self._safe_read_group_sum_any(\"construction.contract\", contract_out_domain",
            "payable = self._safe_read_group_sum_any(\"construction.contract\", contract_in_domain",
            "\"receive_pending\"",
            "\"pay_pending\"",
            "\"net_cash\"",
        ],
    )

    _contains(
        PROGRESS_BUILDER,
        [
            "\"task_open\"",
            "\"task_critical\"",
            "\"task_blocked\"",
            "\"milestone_upcoming_days\"",
            "\"critical_path_health\"",
        ],
    )

    _contains(
        RISK_BUILDER,
        [
            "\"TASK_OVERDUE\"",
            "\"TASK_BLOCKED\"",
            "\"MILESTONE_DELAY\"",
            "\"progress_task_overdue\"",
            "\"progress_task_blocked\"",
            "\"progress_milestone_delay\"",
            "\"open_task_list\"",
        ],
    )

    _contains(
        VIEW_FILE,
        [
            "'cost_completion_rate'",
            "'subcontract_total'",
            "'receive_pending'",
            "'pay_pending'",
            "'net_cash'",
            "'task_open'",
            "'task_critical'",
            "'task_blocked'",
            "'milestone_upcoming_days'",
            "'critical_path_health'",
            "progress_task_overdue",
            "progress_task_blocked",
            "progress_milestone_delay",
            "open_task_overdue",
            "open_task_blocked",
        ],
    )

    print("[verify.project.dashboard.metric_semantics] PASS")


if __name__ == "__main__":
    main()
