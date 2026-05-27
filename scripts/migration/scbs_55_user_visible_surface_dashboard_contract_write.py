#!/usr/bin/env python3
"""Close SCBS 55 dashboard visual-contract gaps with deterministic checks."""

from __future__ import annotations

import json
import os
from pathlib import Path
from xml.etree import ElementTree

from odoo.tools.safe_eval import safe_eval


SOURCE_DOCUMENT = "/home/odoo/workspace/partner_import_source/5.6优化（老系统菜单，字段列表展示）1.docx"
OUTPUT_JSON_NAME = "scbs_55_user_visible_surface_dashboard_contract_write_result_v1.json"

DASHBOARD_RULES = {
    "成本大屏": {
        "target_model": "sc.dashboard.cockpit.fact",
        "action_name": "成本大屏",
        "domain_token": ("fact_type", "=", "cost_cockpit"),
        "required_tree_fields": {
            "business_date",
            "fact_type",
            "name",
            "project_id",
            "partner_id",
            "cockpit_scope",
            "metric_period",
            "metric_value",
            "amount",
            "source_model",
            "state",
        },
        "required_pivot_fields": set(),
        "aligned_status": "dashboard_cost_metric_contract_aligned",
    },
    "经营大屏": {
        "target_model": "sc.operating.metrics.project",
        "action_name": "经营大屏",
        "domain_token": None,
        "required_tree_fields": {
            "project_id",
            "receipt_amount",
            "output_invoice_amount",
            "output_tax_amount",
            "input_invoice_amount",
            "input_tax_amount",
            "prepaid_tax_amount",
            "deduction_amount",
            "deduction_tax_amount",
            "deduction_paid_amount",
            "deduction_refund_amount",
            "net_cash_amount",
            "tax_balance_amount",
            "settlement_amount_total",
            "settlement_amount_paid",
            "settlement_amount_payable",
            "overpay_risk_count",
            "coverage_note",
        },
        "required_pivot_fields": {
            "project_id",
            "receipt_amount",
            "output_invoice_amount",
            "input_invoice_amount",
            "prepaid_tax_amount",
            "deduction_paid_amount",
            "net_cash_amount",
            "settlement_amount_total",
            "settlement_amount_payable",
            "overpay_risk_count",
        },
        "aligned_status": "dashboard_operation_metric_contract_aligned",
    },
}


def artifact_root() -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.append(Path("/mnt/artifacts/migration"))
    candidates.append(Path(f"/tmp/scbs_55_visible_surface/{env.cr.dbname}"))  # noqa: F821
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return candidate
        except Exception:
            continue
    return Path(f"/tmp/scbs_55_visible_surface/{env.cr.dbname}")  # noqa: F821


def ensure_allowed_db() -> None:
    allowlist = {
        item.strip()
        for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", env.cr.dbname).split(",")  # noqa: F821
        if item.strip()
    }
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_replay": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def fields_from_arch(arch: str) -> set[str]:
    if not arch:
        return set()
    try:
        root = ElementTree.fromstring(arch.encode("utf-8"))
    except Exception:
        return set()
    return {str(node.attrib.get("name") or "").strip() for node in root.iter("field") if node.attrib.get("name")}


def default_view_fields(model: str, view_type: str) -> set[str]:
    if not model or model not in env:  # noqa: F821
        return set()
    try:
        views = env[model].sudo().get_views([(False, view_type)], {})  # noqa: F821
    except Exception:
        return set()
    view = ((views.get("views") or {}).get(view_type) or {}) if isinstance(views, dict) else {}
    return fields_from_arch(str(view.get("arch") or ""))


def action_domain(action) -> list[object]:
    try:
        value = safe_eval(str(action.domain or "[]"), {"context": {}})
    except Exception:
        return []
    return value if isinstance(value, list) else []


def has_domain_token(action, token: tuple[str, str, str] | None) -> bool:
    if not token:
        return True
    return token in [tuple(item) for item in action_domain(action) if isinstance(item, (list, tuple))]


def record_count(model: str, action) -> int:
    domain = action_domain(action)
    if not model or model not in env:  # noqa: F821
        return 0
    return env[model].sudo().search_count(domain)  # noqa: F821


ensure_allowed_db()
artifact_dir = artifact_root()
Plan = env["sc.legacy.user.priority.menu.plan"].sudo().with_context(active_test=False)  # noqa: F821

closed: list[dict[str, object]] = []
failures: list[dict[str, object]] = []

for name, rule in DASHBOARD_RULES.items():
    record = Plan.search(
        [
            ("source_document", "=", SOURCE_DOCUMENT),
            ("legacy_menu_name", "=", name),
        ],
        limit=1,
    )
    if not record:
        failures.append({"name": name, "reason": "missing_plan_record"})
        continue

    action = record.target_action_id
    tree_fields = fields_from_arch(record.target_view_id.arch_db or "") if record.target_view_id else set()
    if not tree_fields:
        tree_fields = default_view_fields(record.target_model, "tree")
    pivot_fields = default_view_fields(record.target_model, "pivot")
    count = record_count(record.target_model, action) if action else 0

    missing_tree = sorted(rule["required_tree_fields"] - tree_fields)
    missing_pivot = sorted(rule["required_pivot_fields"] - pivot_fields)
    checks = {
        "target_model_ok": record.target_model == rule["target_model"],
        "action_name_ok": bool(action and action.name == rule["action_name"]),
        "domain_ok": bool(action and has_domain_token(action, rule["domain_token"])),
        "record_count_ok": count > 0,
        "tree_fields_ok": not missing_tree,
        "pivot_fields_ok": not missing_pivot,
    }
    if not all(checks.values()):
        record.write(
            {
                "surface_contract_status": "view_gap_audit_required",
                "runtime_gap_summary": json.dumps(
                    {
                        "status": "dashboard_metric_contract_gap_remaining",
                        "checks": checks,
                        "missing_tree_fields": missing_tree,
                        "missing_pivot_fields": missing_pivot,
                        "current_record_count": count,
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                ),
            }
        )
        failures.append({"name": name, "checks": checks, "missing_tree_fields": missing_tree, "missing_pivot_fields": missing_pivot})
        continue

    record.write(
        {
            "surface_contract_status": "view_aligned",
            "runtime_gap_summary": json.dumps(
                {
                    "status": rule["aligned_status"],
                    "current_record_count": count,
                    "target_model": record.target_model,
                    "target_action_name": action.name,
                    "target_view_name": record.target_view_id.name if record.target_view_id else "",
                    "view_mode": action.view_mode,
                    "required_tree_fields": sorted(rule["required_tree_fields"]),
                    "required_pivot_fields": sorted(rule["required_pivot_fields"]),
                },
                ensure_ascii=False,
                sort_keys=True,
            ),
        }
    )
    closed.append({"name": name, "current_record_count": count, "target_model": record.target_model})

env.cr.commit()  # noqa: F821

payload = {
    "status": "PASS" if len(closed) == len(DASHBOARD_RULES) and not failures else "FAIL",
    "mode": "scbs_55_user_visible_surface_dashboard_contract_write",
    "database": env.cr.dbname,  # noqa: F821
    "source_document": SOURCE_DOCUMENT,
    "closed_dashboards": closed,
    "failures": failures,
    "db_writes": len(closed) + len(failures),
    "decision": "scbs_55_dashboard_metric_contracts_aligned"
    if len(closed) == len(DASHBOARD_RULES) and not failures
    else "STOP_REVIEW_REQUIRED",
}
write_json(artifact_dir / OUTPUT_JSON_NAME, payload)
print("SCBS_55_USER_VISIBLE_SURFACE_DASHBOARD_CONTRACT_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
if payload["status"] != "PASS":
    raise SystemExit(2)
