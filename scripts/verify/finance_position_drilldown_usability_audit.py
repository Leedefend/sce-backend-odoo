# -*- coding: utf-8 -*-
"""Audit drilldown actions from finance position projections to source facts."""

from __future__ import annotations

import json
import os
from collections import OrderedDict
from pathlib import Path


def artifact_root() -> Path:
    raw = os.getenv("MIGRATION_ARTIFACT_ROOT") or os.getenv("FINANCE_POSITION_DRILLDOWN_ARTIFACT_ROOT")
    candidates = [Path(raw)] if raw else []
    candidates.extend([Path("/mnt/artifacts/backend"), Path(f"/tmp/finance_position_drilldown/{env.cr.dbname}")])  # noqa: F821
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return candidate
        except OSError:
            continue
    return Path("/tmp")


def assert_action_count(errors, record, method_name, target_model, expected_count):
    action = getattr(record, method_name)()
    domain = action.get("domain") or []
    actual_count = env[target_model].sudo().search_count(domain)  # noqa: F821
    if action.get("type") != "ir.actions.act_window":
        errors.append({"key": f"{method_name}.type", "record": record.display_name, "actual": action.get("type")})
    if action.get("res_model") != target_model:
        errors.append({"key": f"{method_name}.res_model", "record": record.display_name, "actual": action.get("res_model")})
    if int(actual_count or 0) != int(expected_count or 0):
        errors.append(
            {
                "key": f"{record._name}.{method_name}.count",
                "record": record.display_name,
                "expected": int(expected_count or 0),
                "actual": int(actual_count or 0),
                "domain": domain,
            }
        )
    return {"record": record.display_name, "expected": int(expected_count or 0), "actual": int(actual_count or 0)}


errors = []
summary = OrderedDict()

ProjectCapital = env["sc.finance.project.capital.position"].sudo()  # noqa: F821
ProjectCounterparty = env["sc.finance.project.counterparty.position"].sudo()  # noqa: F821
CounterpartySummary = env["sc.finance.counterparty.position.summary"].sudo()  # noqa: F821

capital_finance = ProjectCapital.search([("project_id", "!=", False), ("finance_source_line_count", ">", 0)], limit=5)
capital_interfund = ProjectCapital.search([("project_id", "!=", False), ("interfund_source_line_count", ">", 0)], limit=5)
summary["project_capital_finance_samples"] = [
    assert_action_count(errors, row, "action_open_finance_facts", "sc.finance.business.fact", row.finance_source_line_count)
    for row in capital_finance
]
summary["project_capital_interfund_samples"] = [
    assert_action_count(errors, row, "action_open_interfund_facts", "sc.interfund.movement.fact", row.interfund_source_line_count)
    for row in capital_interfund
]

counterparty_finance = ProjectCounterparty.search([("project_id", "!=", False), ("finance_source_line_count", ">", 0)], limit=10)
summary["project_counterparty_finance_samples"] = [
    assert_action_count(errors, row, "action_open_finance_facts", "sc.finance.business.fact", row.finance_source_line_count)
    for row in counterparty_finance
]

counterparty_interfund_samples = ProjectCounterparty.browse()
for counterparty_type in ("company", "project", "partner", "internal", "unknown"):
    row = ProjectCounterparty.search(
        [("project_id", "!=", False), ("counterparty_type", "=", counterparty_type), ("interfund_source_line_count", ">", 0)],
        limit=1,
    )
    counterparty_interfund_samples |= row
summary["project_counterparty_interfund_samples"] = [
    assert_action_count(errors, row, "action_open_interfund_facts", "sc.interfund.movement.fact", row.interfund_source_line_count)
    for row in counterparty_interfund_samples
]

counterparty_summary_samples = CounterpartySummary.search([("project_count", ">", 0)], order="project_count desc, source_line_count desc", limit=10)
summary["counterparty_summary_project_position_samples"] = [
    assert_action_count(errors, row, "action_open_project_positions", "sc.finance.project.counterparty.position", row.project_count)
    for row in counterparty_summary_samples
]

if not summary["project_capital_finance_samples"]:
    errors.append({"key": "missing_sample.project_capital_finance"})
if not summary["project_capital_interfund_samples"]:
    errors.append({"key": "missing_sample.project_capital_interfund"})
if not summary["project_counterparty_finance_samples"]:
    errors.append({"key": "missing_sample.project_counterparty_finance"})
if not summary["project_counterparty_interfund_samples"]:
    errors.append({"key": "missing_sample.project_counterparty_interfund"})
if not summary["counterparty_summary_project_position_samples"]:
    errors.append({"key": "missing_sample.counterparty_summary_project_positions"})

result = OrderedDict(
    [
        ("status", "PASS" if not errors else "FAIL"),
        ("database", env.cr.dbname),  # noqa: F821
        ("summary", summary),
        ("errors", errors),
    ]
)

target = artifact_root() / f"finance_position_drilldown_usability_audit_{env.cr.dbname}.json"  # noqa: F821
target.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(result, ensure_ascii=False, indent=2))
if errors:
    raise SystemExit(1)
