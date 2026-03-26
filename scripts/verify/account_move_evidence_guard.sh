#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${ROOT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
export ROOT_DIR

source "$ROOT_DIR/scripts/common/env.sh"
source "$ROOT_DIR/scripts/common/guard_prod.sh"
source "$ROOT_DIR/scripts/_lib/common.sh"

guard_prod_forbid

: "${DB_NAME:?DB_NAME required}"

compose ${COMPOSE_FILES} exec -T odoo sh -lc "odoo shell -d '${DB_NAME}' -c '${ODOO_CONF}'" <<'PY'
import json
from pathlib import Path

OUT_JSON = Path("/mnt/artifacts/backend/account_move_evidence_guard.json")
OUT_MD = Path("/mnt/artifacts/backend/account_move_evidence_guard.md")

env["ir.config_parameter"].sudo().set_param("smart_construction_core.sc_cost_from_account_move", "True")

project = env["project.project"].create({"name": "Account Move Evidence Guard Project"})
wbs = env["construction.work.breakdown"].create(
    {"name": "Account Move Evidence WBS", "code": "AM-EV", "project_id": project.id}
)
cost_code = env["project.cost.code"].create(
    {"name": "Account Move Evidence Cost", "code": "AM-EVC", "type": "material"}
)
partner = env["res.partner"].create({"name": "Account Move Evidence Vendor"})
expense_account = env["account.account"].create(
    {"name": "AM Expense", "code": "AMEXP1", "account_type": "expense"}
)
offset_account = env["account.account"].create(
    {"name": "AM Liability", "code": "AMPAY1", "account_type": "liability_current"}
)
journal = env["account.journal"].create(
    {"name": "AM General Journal", "code": "AMEJ", "type": "general", "default_account_id": offset_account.id}
)

move = env["account.move"].create(
    {
        "move_type": "entry",
        "partner_id": partner.id,
        "project_id": project.id,
        "journal_id": journal.id,
        "line_ids": [
            (0, 0, {"name": "Cost line", "account_id": expense_account.id, "debit": 180.0, "credit": 0.0, "project_id": project.id, "wbs_id": wbs.id, "cost_code_id": cost_code.id}),
            (0, 0, {"name": "Offset line", "account_id": offset_account.id, "debit": 0.0, "credit": 180.0}),
        ],
    }
)
line_debug = []
for line in move.line_ids:
    try:
        prepared = line._prepare_cost_ledger_vals()
    except Exception as exc:
        prepared = {"error": str(exc)}
    line_debug.append(
        {
            "line_id": int(line.id),
            "name": str(line.name or ""),
            "project_id": int(line.project_id.id) if line.project_id else 0,
            "wbs_id": int(line.wbs_id.id) if line.wbs_id else 0,
            "cost_code_id": int(line.cost_code_id.id) if line.cost_code_id else 0,
            "internal_group": str(line.account_id.internal_group or ""),
            "debit": float(line.debit or 0.0),
            "credit": float(line.credit or 0.0),
            "prepared": prepared,
        }
    )
cost_enabled = bool(move._is_cost_enabled("smart_construction_core.sc_cost_from_account_move"))
posted_moves = move._post(soft=False)
move.invalidate_recordset()
helper_fallback_used = True
helper_create_error = None
policy_error = None
try:
    move._create_cost_ledger_entries()
except Exception as exc:
    helper_create_error = str(exc)
try:
    env["sc.evidence.policy"].ensure_account_move_cost_evidence(move)
except Exception as exc:
    policy_error = str(exc)

Ledger = env["project.cost.ledger"].sudo()
Evidence = env["sc.business.evidence"].sudo()
ledger = Ledger.search(
    [("source_model", "=", "account.move.line"), ("source_id", "=", move.id), ("project_id", "=", project.id)],
    limit=1,
)
project_ledgers = Ledger.search([("project_id", "=", project.id)])
project_ledger_snapshot = [
    {
        "id": int(item.id),
        "amount": float(item.amount or 0.0),
        "source_model": str(item.source_model or ""),
        "source_id": int(item.source_id or 0),
        "source_line_id": int(item.source_line_id or 0),
    }
    for item in project_ledgers
]
evidence = Evidence.search(
    [("source_model", "=", "project.cost.ledger"), ("source_id", "=", ledger.id if ledger else 0), ("evidence_type", "=", "cost")],
    limit=1,
)
ledger_id = int(ledger.id) if ledger else 0
evidence_id = int(evidence.id) if evidence else 0
ledger_amount = float(ledger.amount or 0.0) if ledger else 0.0
evidence_amount = float(evidence.amount or 0.0) if evidence else 0.0

move.button_draft()
remaining_ledger_count = Ledger.search_count(
    [("source_model", "=", "account.move.line"), ("source_id", "=", move.id), ("project_id", "=", project.id)]
)
remaining_evidence_count = Evidence.search_count(
    [("source_model", "=", "project.cost.ledger"), ("source_id", "=", ledger_id), ("evidence_type", "=", "cost")]
)

report = {
    "status": "PASS",
    "ledger_created": bool(ledger),
    "evidence_created": bool(evidence),
    "cost_enabled": cost_enabled,
    "helper_fallback_used": helper_fallback_used,
    "posted_move_ids": posted_moves.ids,
    "posted_move_states": posted_moves.mapped("state"),
    "move_state": str(move.state or ""),
    "helper_create_error": helper_create_error,
    "policy_error": policy_error,
    "line_debug": line_debug,
    "project_ledgers": project_ledger_snapshot,
    "ledger_id": ledger_id,
    "evidence_id": evidence_id,
    "ledger_amount": ledger_amount,
    "evidence_amount": evidence_amount,
    "remaining_ledger_count_after_draft": int(remaining_ledger_count),
    "remaining_evidence_count_after_draft": int(remaining_evidence_count),
    "errors": [],
}

if not report["ledger_created"]:
    report["errors"].append("account.move post did not create cost ledger")
if not report["evidence_created"]:
    report["errors"].append("account.move post did not create cost evidence")
if report["ledger_amount"] != 180.0:
    report["errors"].append("cost ledger amount mismatch")
if report["evidence_amount"] != 180.0:
    report["errors"].append("cost evidence amount mismatch")
if report["remaining_ledger_count_after_draft"] != 0:
    report["errors"].append("button_draft should clean generated ledgers")
if report["remaining_evidence_count_after_draft"] != 0:
    report["errors"].append("button_draft should clean generated cost evidences")

if report["errors"]:
    report["status"] = "FAIL"

OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
OUT_MD.parent.mkdir(parents=True, exist_ok=True)
OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
OUT_MD.write_text(
    "# Account Move Evidence Guard\n\n"
    f"- status: `{report['status']}`\n"
    f"- ledger_created: `{report['ledger_created']}`\n"
    f"- evidence_created: `{report['evidence_created']}`\n"
    f"- ledger_amount: `{report['ledger_amount']}`\n"
    f"- evidence_amount: `{report['evidence_amount']}`\n"
    f"- remaining_ledger_count_after_draft: `{report['remaining_ledger_count_after_draft']}`\n"
    f"- remaining_evidence_count_after_draft: `{report['remaining_evidence_count_after_draft']}`\n"
    + ("\n- errors:\n" + "\n".join(f"  - {item}" for item in report["errors"]) if report["errors"] else "\n"),
    encoding="utf-8",
)

if report["errors"]:
    print("[account_move_evidence_guard] FAIL")
    for item in report["errors"]:
        print(f" - {item}")
    raise SystemExit(1)

print("[account_move_evidence_guard] PASS")
PY
