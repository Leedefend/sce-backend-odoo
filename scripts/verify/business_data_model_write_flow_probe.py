# -*- coding: utf-8 -*-
"""Write-flow proof for business data entry models without a state lifecycle.

The maturity matrix intentionally does not force every business model into a
submit/done workflow.  This probe proves the remaining data-entry models can
be created, saved, read back, and can execute their own business actions where
those actions exist.  The transaction is rolled back at the end.

Run with:
ENV=test ENV_FILE=.env.prod.sim DB_NAME=sc_prod_sim make odoo.shell.exec < scripts/verify/business_data_model_write_flow_probe.py
"""

import json


def _first(model, domain=None):
    return env[model].sudo().search(domain or [], limit=1)


def _project():
    return _first("project.project", [("lifecycle_state", "not in", ["paused", "closed", "closing"])]) or _first(
        "project.project"
    )


def _ensure_cost_code():
    rec = _first("project.cost.code")
    if rec:
        return rec
    return env["project.cost.code"].sudo().create({"name": "验收成本科目", "code": "PROOF", "type": "other"})


def _fixtures():
    return {
        "project": _project(),
        "partner": _first("res.partner"),
        "uom": _first("uom.uom"),
        "cost_code": _ensure_cost_code(),
    }


def _missing(fixtures):
    return [name for name, rec in fixtures.items() if not rec]


def _create_tender_bid(fixtures):
    return env["tender.bid"].sudo().create(
        {
            "project_id": fixtures["project"].id,
            "owner_id": fixtures["partner"].id,
            "tender_name": "投标办理验收",
            "bid_amount": 10000,
        }
    )


def _create_budget(fixtures):
    return env["project.budget"].sudo().create(
        {
            "name": "目标成本办理验收",
            "project_id": fixtures["project"].id,
            "amount_revenue_target": 10000,
            "amount_cost_target": 8000,
        }
    )


def _readback(rec, fields):
    return rec.read(fields)[0]


def main():
    fixtures = _fixtures()
    failures = []
    flows = []
    missing = _missing(fixtures)
    if missing:
        print(
            json.dumps(
                {"ok": False, "database": env.cr.dbname, "reason": "fixture_missing", "missing": missing},
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )
        return 1

    try:
        tender_bid = _create_tender_bid(fixtures)
        opening = env["tender.opening"].sudo().create(
            {
                "bid_id": tender_bid.id,
                "open_time": "2026-05-02 10:00:00",
                "result": "pending",
                "win_price": 9000,
                "remark": "开标记录办理验收",
            }
        )
        opening.write({"result": "won", "remark": "开标记录办理验收-已回写"})
        flows.append(
            {
                "label": "投标管理/开标记录",
                "model": "tender.opening",
                "record_id": opening.id,
                "readback": _readback(opening, ["bid_id", "project_id", "result", "win_price", "remark"]),
            }
        )

        guarantee = env["tender.guarantee"].sudo().create(
            {"bid_id": tender_bid.id, "type": "out", "amount": 3000, "remark": "投标保证金办理验收"}
        )
        guarantee.write({"amount": 3200, "remark": "投标保证金办理验收-已回写"})
        flows.append(
            {
                "label": "投标管理/投标保证金",
                "model": "tender.guarantee",
                "record_id": guarantee.id,
                "readback": _readback(guarantee, ["bid_id", "project_id", "type", "amount", "remark"]),
            }
        )

        boq = env["project.boq.line"].sudo().create(
            {
                "project_id": fixtures["project"].id,
                "code": "BOQ-PROOF-001",
                "name": "预算清单办理验收",
                "uom_id": fixtures["uom"].id,
                "quantity": 10,
                "price": 20,
                "section_type": "other",
            }
        )
        boq.write({"quantity": 12, "price": 25})
        flows.append(
            {
                "label": "项目预算/预算清单",
                "model": "project.boq.line",
                "record_id": boq.id,
                "readback": _readback(boq, ["project_id", "code", "name", "quantity", "price", "amount"]),
            }
        )

        budget = _create_budget(fixtures)
        budget.action_archive_version()
        budget.action_set_active()
        flows.append(
            {
                "label": "成本中心/目标成本",
                "model": "project.budget",
                "record_id": budget.id,
                "readback": _readback(
                    budget,
                    ["project_id", "name", "version", "amount_revenue_target", "amount_cost_target", "is_active"],
                ),
            }
        )

        budget_line = env["project.budget.boq.line"].sudo().create(
            {
                "budget_id": budget.id,
                "name": "预算分摊清单行验收",
                "uom_id": fixtures["uom"].id,
                "qty_bidded": 10,
                "price_bidded": 20,
            }
        )
        alloc = env["project.budget.cost.alloc"].sudo().create(
            {
                "budget_boq_line_id": budget_line.id,
                "cost_code_id": fixtures["cost_code"].id,
                "ratio": 0.5,
                "amount_budget": 100,
                "note": "预算清单分摊办理验收",
            }
        )
        alloc.write({"ratio": 0.6, "amount_budget": 120})
        flows.append(
            {
                "label": "成本中心/预算清单分摊",
                "model": "project.budget.cost.alloc",
                "record_id": alloc.id,
                "readback": _readback(alloc, ["budget_boq_line_id", "project_id", "cost_code_id", "ratio", "amount_budget"]),
            }
        )

        ledger = env["project.cost.ledger"].sudo().create(
            {
                "project_id": fixtures["project"].id,
                "cost_code_id": fixtures["cost_code"].id,
                "date": "2026-05-02",
                "qty": 2,
                "uom_id": fixtures["uom"].id,
                "amount": 200,
                "partner_id": fixtures["partner"].id,
                "note": "成本台账办理验收",
            }
        )
        ledger.write({"amount": 260, "note": "成本台账办理验收-已回写"})
        flows.append(
            {
                "label": "成本中心/成本台账",
                "model": "project.cost.ledger",
                "record_id": ledger.id,
                "readback": _readback(ledger, ["project_id", "cost_code_id", "period", "period_id", "amount", "note"]),
            }
        )

        for flow in flows:
            if not flow.get("record_id") or not flow.get("readback"):
                failures.append({"check": "readback", **flow})
    except Exception as exc:
        failures.append({"check": "exception", "error": "%s: %s" % (type(exc).__name__, str(exc))})
    finally:
        env.cr.rollback()

    result = {
        "ok": not failures,
        "database": env.cr.dbname,
        "rollback": True,
        "scope": "business_data_model_write_flow",
        "checked": len(flows),
        "flows": flows,
        "failures": failures,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True, default=str))
    return 0 if not failures else 1


raise SystemExit(main())
