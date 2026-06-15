#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""HTTP smoke for finance handling entry surfaces.

This verifies the user-visible API surface without starting Playwright:
login, system navigation/action resolution, ui.contract.v2 page loading,
api.data list access, and downstream trace evidence for handled samples.
"""

from __future__ import annotations

import json
import os
import time
from collections import OrderedDict
from pathlib import Path
from typing import Any

from python_http_smoke_utils import extract_login_token, http_post_json, live_login_failure_hint


DB_NAME = os.getenv("DB_NAME") or os.getenv("E2E_DB") or "sc_demo"
BASE_URL = (
    os.getenv("FRONTEND_URL")
    or os.getenv("E2E_BASE_URL")
    or os.getenv("BASE_URL")
    or "http://127.0.0.1:18081"
).rstrip("/")
LOGIN = os.getenv("E2E_LOGIN") or "wutao"
PASSWORD = os.getenv("E2E_PASSWORD") or "123456"
ARTIFACT_ROOT = Path(os.getenv("ARTIFACTS_DIR") or "artifacts/verify")
MODULE = "smart_construction_core"


ENTRIES = [
    {
        "key": "payment_request",
        "label": "支付申请",
        "menu_xmlid": f"{MODULE}.menu_sc_user_payment_apply_acceptance",
        "action_xmlid": f"{MODULE}.action_payment_request_user_payment_apply",
        "model": "payment.request",
        "fields": ["id", "name", "type", "state", "project_id", "partner_id", "contract_id", "settlement_id", "amount", "attachment_ids"],
        "list_domain": [["type", "=", "pay"]],
        "handled_domain": [["type", "=", "pay"], ["state", "=", "done"]],
        "trace": {"model": "payment.ledger", "domain_field": "payment_request_id"},
        "trace_required": True,
    },
    {
        "key": "payment_execution",
        "label": "往来单位付款",
        "menu_xmlid": f"{MODULE}.menu_sc_partner_payment",
        "action_xmlid": f"{MODULE}.action_sc_payment_execution_partner_payment",
        "model": "sc.payment.execution",
        "fields": ["id", "name", "source_kind", "payment_family", "state", "project_id", "partner_id", "contract_id", "payment_request_id", "paid_amount", "attachment_ids"],
        "list_domain": [["payment_family", "=", "往来单位付款"]],
        "handled_domain": [["payment_family", "=", "往来单位付款"], ["state", "in", ["paid", "legacy_confirmed"]]],
        "trace": {"model": "sc.treasury.ledger", "source_model": "sc.payment.execution"},
        "trace_required": False,
    },
    {
        "key": "receipt_income",
        "label": "工程进度款收入登记",
        "menu_xmlid": f"{MODULE}.menu_sc_engineering_progress_income",
        "action_xmlid": f"{MODULE}.action_sc_receipt_income_engineering_progress",
        "model": "sc.receipt.income",
        "fields": ["id", "name", "source_kind", "state", "project_id", "partner_id", "contract_id", "payment_request_id", "amount", "attachment_ids"],
        "list_domain": [["business_category_id.code", "=", "finance.receipt.income.progress"]],
        "handled_domain": [["business_category_id.code", "=", "finance.receipt.income.progress"], ["state", "in", ["received", "legacy_confirmed"]]],
        "trace": {"model": "sc.treasury.ledger", "source_model": "sc.receipt.income"},
        "trace_required": False,
    },
    {
        "key": "self_funding_income",
        "label": "自筹垫付办理",
        "menu_xmlid": f"{MODULE}.menu_sc_self_funding_advance_income",
        "action_xmlid": f"{MODULE}.action_sc_self_funding_registration_income",
        "model": "sc.self.funding.registration",
        "fields": [
            "id",
            "name",
            "document_no",
            "document_date",
            "funding_type",
            "state",
            "project_id",
            "partner_id",
            "amount",
            "business_category_id",
            "company_contractor_responsibility_state",
            "company_contractor_self_funding_balance",
        ],
        "list_domain": [["funding_type", "=", "income"]],
        "handled_domain": [["funding_type", "=", "income"], ["state", "=", "done"]],
        "trace": {"model": "sc.treasury.ledger", "source_model": "sc.self.funding.registration"},
        "trace_required": False,
    },
    {
        "key": "self_funding_refund",
        "label": "自筹退回办理",
        "menu_xmlid": f"{MODULE}.menu_sc_self_funding_advance_refund",
        "action_xmlid": f"{MODULE}.action_sc_self_funding_registration_refund",
        "model": "sc.self.funding.registration",
        "fields": [
            "id",
            "name",
            "document_no",
            "document_date",
            "funding_type",
            "state",
            "project_id",
            "partner_id",
            "amount",
            "business_category_id",
            "company_contractor_responsibility_state",
            "company_contractor_self_funding_balance",
        ],
        "list_domain": [["funding_type", "=", "refund"]],
        "handled_domain": [["funding_type", "=", "refund"], ["state", "=", "done"]],
        "trace": {"model": "sc.treasury.ledger", "source_model": "sc.self.funding.registration"},
        "trace_required": False,
    },
    {
        "key": "expense_claim",
        "label": "项目费用报销单",
        "menu_xmlid": f"{MODULE}.menu_sc_project_expense_claim",
        "action_xmlid": f"{MODULE}.action_sc_expense_claim_project",
        "model": "sc.expense.claim",
        "fields": ["id", "name", "claim_type", "expense_type", "state", "project_id", "partner_id", "payment_request_id", "amount", "approved_amount", "attachment_ids"],
        "list_domain": [["claim_type", "=", "expense"]],
        "handled_domain": [["claim_type", "=", "expense"], ["state", "in", ["done", "legacy_confirmed"]]],
        "trace": {"model": "sc.treasury.ledger", "source_model": "sc.expense.claim"},
        "trace_required": False,
    },
]

EXPENSE_FIELDS = [
    "id",
    "name",
    "business_category_id",
    "claim_type",
    "guarantee_type",
    "expense_type",
    "state",
    "project_id",
    "partner_id",
    "payment_request_id",
    "amount",
    "approved_amount",
    "attachment_ids",
]


def expense_category_entry(
    key: str,
    label: str,
    menu_xmlid: str,
    action_xmlid: str,
    category_code: str,
    *,
    trace: dict[str, Any] | None = None,
    trace_required: bool = False,
    sample_required: bool = True,
) -> dict[str, Any]:
    domain = [["business_category_id.code", "=", category_code]]
    return {
        "key": key,
        "label": label,
        "menu_xmlid": menu_xmlid,
        "action_xmlid": action_xmlid,
        "model": "sc.expense.claim",
        "fields": EXPENSE_FIELDS,
        "list_domain": domain,
        "handled_domain": domain + [["state", "in", ["done", "legacy_confirmed"]]],
        "trace": trace,
        "trace_required": trace_required,
        "sample_required": sample_required,
    }


ENTRIES.extend(
    [
        expense_category_entry(
            "expense_reimbursement",
            "报销申请",
            f"{MODULE}.menu_sc_reimbursement_request",
            f"{MODULE}.action_sc_expense_claim_reimbursement_request",
            "finance.expense.reimbursement",
            trace={"model": "sc.treasury.ledger", "source_model": "sc.expense.claim"},
        ),
        expense_category_entry(
            "deposit_bid_pay",
            "投标保证金缴纳",
            f"{MODULE}.menu_sc_bid_deposit_pay",
            f"{MODULE}.action_sc_bid_deposit_pay",
            "finance.deposit.bid.pay",
            trace={"model": "sc.treasury.ledger", "source_model": "sc.expense.claim"},
        ),
        expense_category_entry(
            "deposit_bid_return",
            "投标保证金退回",
            f"{MODULE}.menu_sc_bid_deposit_return",
            f"{MODULE}.action_sc_bid_deposit_return",
            "finance.deposit.bid.return",
            trace={"model": "sc.treasury.ledger", "source_model": "sc.expense.claim"},
        ),
        expense_category_entry(
            "deposit_contract_pay",
            "合同保证金登记",
            f"{MODULE}.menu_sc_contract_deposit_register",
            f"{MODULE}.action_sc_contract_deposit_pay",
            "finance.deposit.contract.pay",
            trace={"model": "payment.ledger", "domain_field": "payment_request_id"},
            trace_required=False,
            sample_required=False,
        ),
        expense_category_entry(
            "deposit_contract_return",
            "合同保证金退回",
            f"{MODULE}.menu_sc_contract_deposit_return",
            f"{MODULE}.action_sc_contract_deposit_return",
            "finance.deposit.contract.return",
            trace={"model": "sc.treasury.ledger", "source_model": "sc.expense.claim"},
            sample_required=False,
        ),
        expense_category_entry(
            "deduction_bill",
            "扣款单",
            f"{MODULE}.menu_sc_deduction_bill",
            f"{MODULE}.action_sc_expense_claim_deduction_bill",
            "finance.deduction.bill",
        ),
        expense_category_entry(
            "deduction_paid",
            "扣款实缴登记",
            f"{MODULE}.menu_sc_deduction_paid",
            f"{MODULE}.action_sc_expense_claim_deduction_paid",
            "finance.deduction.paid",
            trace={"model": "payment.ledger", "domain_field": "payment_request_id"},
        ),
        expense_category_entry(
            "deduction_refund",
            "扣款实缴退回",
            f"{MODULE}.menu_sc_deduction_paid_refund",
            f"{MODULE}.action_sc_expense_claim_deduction_paid_refund",
            "finance.deduction.refund",
            trace={"model": "sc.treasury.ledger", "source_model": "sc.expense.claim"},
        ),
        expense_category_entry(
            "repayment_registration",
            "还款登记",
            f"{MODULE}.menu_sc_repayment_registration",
            f"{MODULE}.action_sc_expense_claim_repayment_registration",
            "finance.repayment.registration",
            trace={"model": "sc.treasury.ledger", "source_model": "sc.expense.claim"},
        ),
        expense_category_entry(
            "repayment_contractor_project",
            "承包人还项目款",
            f"{MODULE}.menu_sc_contractor_project_repay",
            f"{MODULE}.action_sc_expense_claim_contractor_project_repay",
            "finance.repayment.contractor_project",
            trace={"model": "sc.treasury.ledger", "source_model": "sc.expense.claim"},
        ),
        expense_category_entry(
            "repayment_project_company",
            "项目还公司款登记",
            f"{MODULE}.menu_sc_project_repay_company",
            f"{MODULE}.action_sc_expense_claim_project_repay_company",
            "finance.repayment.project_company",
            trace={"model": "sc.treasury.ledger", "source_model": "sc.expense.claim"},
        ),
    ]
)


def intent(name: str, params: dict[str, Any], token: str = "") -> tuple[int, dict[str, Any]]:
    headers = {
        "Content-Type": "application/json",
        "X-Odoo-DB": DB_NAME,
        "X-Trace-Id": "finance-http-surface-%s" % int(time.time() * 1000),
    }
    if token:
        headers["Authorization"] = "Bearer %s" % token
    if name in {"login", "auth.login"}:
        headers["X-Anonymous-Intent"] = "1"
    return http_post_json(
        "%s/api/v1/intent?db=%s" % (BASE_URL, DB_NAME),
        {"intent": name, "params": params},
        headers=headers,
    )


def compact_error(status: int, payload: dict[str, Any]) -> dict[str, Any]:
    err = payload.get("error") if isinstance(payload.get("error"), dict) else {}
    return {"status": status, "code": err.get("code"), "message": err.get("message") or payload.get("message")}


def assert_ok(errors: list[dict[str, Any]], key: str, status: int, payload: dict[str, Any]) -> bool:
    if status == 200 and payload.get("ok") is True:
        return True
    errors.append({"key": key, **compact_error(status, payload)})
    return False


def iter_nav_rows(nodes: Any) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not isinstance(nodes, list):
        return rows
    for node in nodes:
        if not isinstance(node, dict):
            continue
        meta = node.get("meta") if isinstance(node.get("meta"), dict) else {}
        rows.append(
            {
                "label": node.get("label") or node.get("name") or node.get("title") or "",
                "menu_xmlid": node.get("xmlid") or node.get("menu_xmlid") or meta.get("xmlid") or meta.get("menu_xmlid") or "",
                "action_id": int(meta.get("action_id") or node.get("action_id") or 0),
                "model": meta.get("model") or node.get("model") or "",
            }
        )
        rows.extend(iter_nav_rows(node.get("children")))
    return rows


def iter_group_rows(groups: Any) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not isinstance(groups, list):
        return rows
    for group in groups:
        if not isinstance(group, dict):
            continue
        for menu in group.get("menus") or []:
            if not isinstance(menu, dict):
                continue
            rows.append(
                {
                    "label": menu.get("label") or menu.get("name") or "",
                    "menu_xmlid": menu.get("menu_xmlid") or menu.get("menu_key") or menu.get("page_key") or "",
                    "action_id": int(menu.get("action_id") or 0),
                    "model": menu.get("res_model") or "",
                }
            )
    return rows


def nav_rows(system_init_data: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key_path in (("release_navigation_v1", "nav"), ("delivery_engine_v1", "nav"), ("nav",)):
        current: Any = system_init_data
        for key in key_path:
            current = current.get(key) if isinstance(current, dict) else None
        rows.extend(iter_nav_rows(current))
    rows.extend(iter_group_rows(system_init_data.get("menu_groups")))
    return rows


def resolve_action(token: str, entry: dict[str, Any], rows: list[dict[str, Any]], errors: list[dict[str, Any]]) -> dict[str, Any]:
    for row in rows:
        if row.get("menu_xmlid") == entry["menu_xmlid"] and int(row.get("action_id") or 0) > 0:
            return {"id": int(row["action_id"]), "source": "system_init_menu_xmlid"}
    for row in rows:
        if row.get("label") == entry["label"] and row.get("model") == entry["model"] and int(row.get("action_id") or 0) > 0:
            return {"id": int(row["action_id"]), "source": "system_init_label_model"}

    status, payload = api_list(
        token,
        "ir.actions.act_window",
        ["id", "name", "res_model"],
        [["name", "=", entry["label"]], ["res_model", "=", entry["model"]]],
        limit=2,
    )
    fallback_errors: list[dict[str, Any]] = []
    if not assert_ok(fallback_errors, "%s.action_lookup" % entry["key"], status, payload):
        errors.extend(fallback_errors)
        return {"id": 0, "source": "unresolved"}
    records = [row for row in (payload.get("data") or {}).get("records") or [] if isinstance(row, dict)]
    if len(records) == 1:
        return {"id": as_id(records[0].get("id")), "source": "action_name_model_fallback"}
    if len(records) > 1:
        errors.append(
            {
                "key": "%s.action_lookup_ambiguous" % entry["key"],
                "label": entry["label"],
                "model": entry["model"],
                "matches": [as_id(row.get("id")) for row in records],
            }
        )
    return {"id": 0, "source": "unresolved"}


def api_list(token: str, model: str, fields: list[str], domain: list[Any], *, limit: int = 20, need_total: bool = False) -> tuple[int, dict[str, Any]]:
    return intent(
        "api.data",
        {
            "op": "list",
            "model": model,
            "fields": fields,
            "domain": domain,
            "limit": limit,
            "order": "id desc",
            "need_total": need_total,
        },
        token,
    )


def as_id(value: Any) -> int:
    if isinstance(value, (list, tuple)) and value:
        value = value[0]
    if isinstance(value, dict):
        value = value.get("id")
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def trace_domain(entry: dict[str, Any], record: dict[str, Any]) -> list[Any]:
    trace = entry.get("trace")
    if not trace:
        return []
    if trace.get("source_model"):
        return [["source_model", "=", trace["source_model"]], ["source_res_id", "=", as_id(record.get("id"))], ["state", "!=", "void"]]
    record_field = trace.get("record_field")
    domain_value = as_id(record.get(record_field)) if record_field else as_id(record.get("id"))
    return [[trace["domain_field"], "=", domain_value]]


def trace_backed_handled_records(token: str, entry: dict[str, Any], errors: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    trace = entry.get("trace")
    if not trace:
        return [], {"status": "not_applicable"}
    if trace.get("model") != "sc.treasury.ledger" or not trace.get("source_model"):
        return [], {"status": "not_applicable"}
    trace_status, trace_payload = api_list(
        token,
        "sc.treasury.ledger",
        ["id", "source_model", "source_res_id", "state"],
        [["source_model", "=", trace["source_model"]], ["source_res_id", "!=", False], ["state", "!=", "void"]],
        limit=80,
    )
    if not assert_ok(errors, "%s.trace_backed_ledger_sample" % entry["key"], trace_status, trace_payload):
        return [], {"status": "ledger_query_failed"}
    ledgers = [row for row in (trace_payload.get("data") or {}).get("records") or [] if isinstance(row, dict)]
    source_ids = [as_id(row.get("source_res_id")) for row in ledgers]
    source_ids = [source_id for source_id in source_ids if source_id]
    if not source_ids:
        return [], {"status": "no_source_linked_ledger", "ledger_records": len(ledgers)}
    handled_status, handled_payload = api_list(
        token,
        entry["model"],
        entry["fields"],
        entry["handled_domain"] + [["id", "in", source_ids]],
        limit=20,
    )
    if not assert_ok(errors, "%s.trace_backed_handled_sample" % entry["key"], handled_status, handled_payload):
        return [], {"status": "source_query_failed", "ledger_records": len(ledgers), "source_ids": len(source_ids)}
    records = [row for row in (handled_payload.get("data") or {}).get("records") or [] if isinstance(row, dict)]
    return records, {"status": "ok", "ledger_records": len(ledgers), "source_ids": len(source_ids), "records": len(records)}


def main() -> int:
    errors: list[dict[str, Any]] = []
    evidence: OrderedDict[str, Any] = OrderedDict(
        [
            ("base_url", BASE_URL),
            ("db", DB_NAME),
            ("login", LOGIN),
            ("entries", []),
        ]
    )

    login_status, login_payload = intent("login", {"login": LOGIN, "password": PASSWORD, "contract_mode": "default", "db": DB_NAME})
    token = extract_login_token(login_payload)
    if not token:
        errors.append(
            {
                "key": "login",
                "hint": live_login_failure_hint(
                    status=login_status,
                    payload=login_payload,
                    base_url=BASE_URL,
                    db_name=DB_NAME,
                    login=LOGIN,
                ),
                **compact_error(login_status, login_payload),
            }
        )
    evidence["login_ok"] = bool(token)

    rows: list[dict[str, Any]] = []
    if token:
        init_status, init_payload = intent(
            "system.init",
            {"scene": "web", "with_preload": False, "scene_ready_mode": "registry", "with": ["workspace_home"]},
            token,
        )
        if assert_ok(errors, "system_init", init_status, init_payload):
            rows = nav_rows(init_payload.get("data") or {})
            evidence["nav_row_count"] = len(rows)

    if token:
        for entry in ENTRIES:
            item: OrderedDict[str, Any] = OrderedDict(
                [
                    ("key", entry["key"]),
                    ("label", entry["label"]),
                    ("menu_xmlid", entry["menu_xmlid"]),
                    ("action_xmlid", entry["action_xmlid"]),
                    ("model", entry["model"]),
                ]
            )
            action_resolution = resolve_action(token, entry, rows, errors)
            action_id = int(action_resolution.get("id") or 0)
            item["action_id"] = action_id
            item["action_resolution"] = action_resolution.get("source")
            if action_id <= 0:
                errors.append({"key": "%s.action_missing" % entry["key"], "action_xmlid": entry["action_xmlid"]})
                evidence["entries"].append(item)
                continue

            contract_status, contract_payload = intent(
                "ui.contract.v2",
                {
                    "op": "action_open",
                    "action_id": action_id,
                    "client_type": "web_pc",
                    "delivery_profile": "full",
                },
                token,
            )
            if assert_ok(errors, "%s.ui_contract" % entry["key"], contract_status, contract_payload):
                page_info = (contract_payload.get("data") or {}).get("pageInfo") or {}
                item["page"] = {
                    "page_name": page_info.get("pageName"),
                    "model": page_info.get("model") or page_info.get("resModel"),
                    "view_type": page_info.get("viewType"),
                }
                if item["page"]["model"] and item["page"]["model"] != entry["model"]:
                    errors.append({"key": "%s.page_model_mismatch" % entry["key"], "expected": entry["model"], "actual": item["page"]["model"]})

            list_status, list_payload = api_list(token, entry["model"], entry["fields"], entry["list_domain"], need_total=True)
            records: list[dict[str, Any]] = []
            if assert_ok(errors, "%s.api_data_list" % entry["key"], list_status, list_payload):
                data = list_payload.get("data") or {}
                records = [row for row in data.get("records") or [] if isinstance(row, dict)]
                item["list"] = {"total": data.get("total"), "records": len(records), "first_record_keys": sorted(records[0].keys()) if records else []}
                if not records and entry.get("sample_required", True):
                    errors.append({"key": "%s.list_empty" % entry["key"], "domain": entry["list_domain"]})

            handled_status, handled_payload = api_list(token, entry["model"], entry["fields"], entry["handled_domain"], limit=20)
            handled_records: list[dict[str, Any]] = []
            if assert_ok(errors, "%s.handled_sample" % entry["key"], handled_status, handled_payload):
                handled_records = [row for row in (handled_payload.get("data") or {}).get("records") or [] if isinstance(row, dict)]
                item["handled_sample"] = {"records": len(handled_records), "domain": entry["handled_domain"]}
                if not handled_records and entry.get("sample_required", True):
                    errors.append({"key": "%s.handled_sample_missing" % entry["key"], "domain": entry["handled_domain"]})
            trace_backed_records, trace_backed_evidence = trace_backed_handled_records(token, entry, errors)
            if trace_backed_evidence.get("status") != "not_applicable":
                item["trace_backed_sample"] = trace_backed_evidence
            if trace_backed_records:
                handled_records = trace_backed_records
                item["handled_sample"]["strategy"] = "trace_backed"

            if handled_records:
                trace = entry.get("trace")
                trace_fields = ["id", "amount", "payment_request_id", "project_id", "partner_id"]
                if trace and trace["model"] == "sc.treasury.ledger":
                    trace_fields = [
                        "id",
                        "amount",
                        "state",
                        "source_kind",
                        "source_model",
                        "source_res_id",
                        "payment_request_id",
                        "project_id",
                        "partner_id",
                    ]
                sample = handled_records[0]
                trace_records: list[dict[str, Any]] = []
                trace_error_record = sample
                if trace:
                    for candidate in handled_records:
                        domain = trace_domain(entry, candidate)
                        if not domain:
                            continue
                        trace_status, trace_payload = api_list(
                            token,
                            trace["model"],
                            trace_fields,
                            domain,
                            limit=5,
                        )
                        if not assert_ok(errors, "%s.downstream_trace" % entry["key"], trace_status, trace_payload):
                            break
                        candidate_trace_records = [
                            row for row in (trace_payload.get("data") or {}).get("records") or [] if isinstance(row, dict)
                        ]
                        trace_error_record = candidate
                        if candidate_trace_records:
                            sample = candidate
                            trace_records = candidate_trace_records
                            break
                    item["downstream_trace"] = {"model": trace["model"], "records": len(trace_records), "sample_id": as_id(sample.get("id"))}
                    if not trace_records and entry.get("trace_required", False):
                        errors.append(
                            {
                                "key": "%s.downstream_trace_missing" % entry["key"],
                                "trace_model": trace["model"],
                                "sample_id": trace_error_record.get("id"),
                                "sample_count": len(handled_records),
                            }
                        )
                else:
                    item["downstream_trace"] = {"model": None, "records": None, "status": "not_applicable"}

                audit_status, audit_payload = api_list(
                    token,
                    "sc.audit.log",
                    ["id", "event_code", "action", "model", "res_id"],
                    [["model", "=", entry["model"]], ["res_id", "=", as_id(sample.get("id"))]],
                    limit=5,
                )
                audit_errors: list[dict[str, Any]] = []
                if assert_ok(audit_errors, "%s.audit_trace" % entry["key"], audit_status, audit_payload):
                    audit_records = [row for row in (audit_payload.get("data") or {}).get("records") or [] if isinstance(row, dict)]
                    item["audit_trace"] = {"records": len(audit_records)}
                elif audit_status == 403:
                    item["audit_trace"] = {"records": None, "status": "not_readable_by_business_user"}
                else:
                    errors.extend(audit_errors)

            evidence["entries"].append(item)

    result = OrderedDict()
    result["status"] = "PASS" if not errors else "FAIL"
    result["evidence"] = evidence
    result["errors"] = errors

    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    output = ARTIFACT_ROOT / "finance_handling_http_surface_smoke.json"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    if not errors:
        print("FINANCE_HANDLING_HTTP_SURFACE_SMOKE: status=PASS db=%s entries=%s" % (DB_NAME, len(ENTRIES)))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
