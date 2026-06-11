#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""HTTP smoke for the company-contractor responsibility balance surface.

This intentionally verifies the current local/dev target through the same
intent endpoints used by the SPA, without requiring Playwright or a browser.
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
TARGET_MENU_XMLID = "smart_construction_core.menu_sc_company_contractor_responsibility_summary"
TARGET_MODEL = "sc.company.contractor.responsibility.summary"
FACT_MODEL = "sc.company.contractor.responsibility.fact"
TARGET_LABEL = "公司-承包人资金责任余额"


def intent(name: str, params: dict[str, Any], token: str = "") -> tuple[int, dict[str, Any]]:
    trace_id = "company-contractor-http-%s" % int(time.time() * 1000)
    headers = {
        "Content-Type": "application/json",
        "X-Odoo-DB": DB_NAME,
        "X-Trace-Id": trace_id,
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
    return {
        "status": status,
        "code": err.get("code"),
        "message": err.get("message") or payload.get("message"),
    }


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
                "menu_id": int(node.get("menu_id") or meta.get("menu_id") or node.get("id") or 0),
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
                    "menu_id": int(menu.get("menu_id") or 0),
                    "model": menu.get("res_model") or "",
                }
            )
    return rows


def find_target_menu(system_init_data: dict[str, Any]) -> dict[str, Any] | None:
    candidates = []
    for key_path in (
        ("release_navigation_v1", "nav"),
        ("delivery_engine_v1", "nav"),
        ("nav",),
    ):
        current: Any = system_init_data
        for key in key_path:
            current = current.get(key) if isinstance(current, dict) else None
        candidates.extend(iter_nav_rows(current))
    candidates.extend(iter_group_rows(system_init_data.get("menu_groups")))
    for row in candidates:
        if row.get("menu_xmlid") == TARGET_MENU_XMLID:
            return row
    for row in candidates:
        if row.get("label") == TARGET_LABEL or row.get("model") == TARGET_MODEL:
            return row
    return None


def assert_ok(errors: list[dict[str, Any]], key: str, status: int, payload: dict[str, Any]) -> bool:
    if status == 200 and payload.get("ok") is True:
        return True
    errors.append({"key": key, **compact_error(status, payload)})
    return False


def action_domain(payload: dict[str, Any]) -> list[Any]:
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    result = data.get("result") if isinstance(data.get("result"), dict) else {}
    raw_action = result.get("raw_action") if isinstance(result.get("raw_action"), dict) else {}
    domain = raw_action.get("domain")
    return domain if isinstance(domain, list) else []


def main() -> int:
    errors: list[dict[str, Any]] = []
    evidence: OrderedDict[str, Any] = OrderedDict(
        [
            ("base_url", BASE_URL),
            ("db", DB_NAME),
            ("login", LOGIN),
            ("target_menu_xmlid", TARGET_MENU_XMLID),
            ("target_model", TARGET_MODEL),
        ]
    )

    login_status, login_payload = intent(
        "login",
        {"login": LOGIN, "password": PASSWORD, "contract_mode": "default", "db": DB_NAME},
    )
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

    target_menu: dict[str, Any] | None = None
    if token:
        init_status, init_payload = intent(
            "system.init",
            {
                "scene": "web",
                "with_preload": False,
                "scene_ready_mode": "registry",
                "with": ["workspace_home"],
            },
            token,
        )
        if assert_ok(errors, "system_init", init_status, init_payload):
            target_menu = find_target_menu(init_payload.get("data") or {})
            if not target_menu:
                errors.append({"key": "target_menu_missing", "menu_xmlid": TARGET_MENU_XMLID, "label": TARGET_LABEL})
            else:
                evidence["target_menu"] = target_menu

    if token and target_menu:
        action_id = int(target_menu.get("action_id") or 0)
        if not action_id:
            errors.append({"key": "target_menu_action_missing", "target_menu": target_menu})
        else:
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
            if assert_ok(errors, "ui_contract", contract_status, contract_payload):
                page_info = (contract_payload.get("data") or {}).get("pageInfo") or {}
                evidence["contract_page"] = {
                    "action_id": action_id,
                    "page_name": page_info.get("pageName"),
                    "model": page_info.get("model") or page_info.get("resModel"),
                    "view_type": page_info.get("viewType"),
                }

    fields = [
        "id",
        "responsibility_state",
        "project_id",
        "partner_name",
        "currency_id",
        "source_line_count",
        "arrival_amount",
        "paid_amount",
        "deducted_amount",
        "arrival_processed_amount",
        "arrival_unprocessed_amount",
        "arrival_over_processed_amount",
        "self_funding_income_amount",
        "self_funding_refund_amount",
        "self_funding_balance",
    ]
    if token:
        list_params = {
            "op": "list",
            "model": TARGET_MODEL,
            "fields": fields,
            "domain": [],
            "limit": 20,
            "offset": 0,
            "order": "project_id, partner_name",
            "context": {},
        }
        list_status, list_payload = intent("api.data", list_params, token)
        summary_sample: dict[str, Any] | None = None
        if assert_ok(errors, "api_data_list", list_status, list_payload):
            data = list_payload.get("data") or {}
            records = data.get("records") or []
            summary_sample = next(
                (
                    rec
                    for rec in records
                    if isinstance(rec, dict)
                    and int(rec.get("id") or 0) > 0
                    and int(rec.get("source_line_count") or 0) > 0
                ),
                None,
            )
            evidence["list"] = {
                "total": data.get("total"),
                "records": len(records),
                "first_record_keys": sorted((records or [{}])[0].keys()) if records else [],
                "drilldown_sample_id": int((summary_sample or {}).get("id") or 0),
                "drilldown_sample_source_line_count": int((summary_sample or {}).get("source_line_count") or 0),
            }
            if not summary_sample:
                errors.append({"key": "summary_drilldown_sample_missing"})

        grouped_params = {
            **list_params,
            "group_by": "responsibility_state",
            "need_total": True,
            "need_aggregates": True,
            "need_group_total": True,
        }
        grouped_status, grouped_payload = intent("api.data", grouped_params, token)
        if assert_ok(errors, "api_data_grouped_list", grouped_status, grouped_payload):
            data = grouped_payload.get("data") or {}
            evidence["grouped_list"] = {
                "total": data.get("total"),
                "records": len(data.get("records") or []),
                "group_summary": len(data.get("group_summary") or []),
                "aggregates": sorted((data.get("aggregates") or {}).keys()),
            }

        if summary_sample:
            button_status, button_payload = intent(
                "execute_button",
                {
                    "model": TARGET_MODEL,
                    "res_id": int(summary_sample.get("id") or 0),
                    "button": {"name": "action_open_responsibility_facts", "type": "object"},
                },
                token,
            )
            if assert_ok(errors, "summary_open_facts_button", button_status, button_payload):
                domain = action_domain(button_payload)
                if not domain:
                    errors.append({"key": "summary_open_facts_domain_missing"})
                fact_fields = [
                    "id",
                    "responsibility_type",
                    "source_model",
                    "source_res_id",
                    "source_document_no",
                    "source_menu_hint",
                    "project_id",
                    "partner_name",
                    "amount",
                    "arrival_amount",
                    "paid_amount",
                    "deducted_amount",
                    "self_funding_income_amount",
                    "self_funding_refund_amount",
                    "coverage_note",
                ]
                fact_status, fact_payload = intent(
                    "api.data",
                    {
                        "op": "list",
                        "model": FACT_MODEL,
                        "fields": fact_fields,
                        "domain": domain,
                        "limit": 20,
                        "offset": 0,
                        "order": "document_date desc, id desc",
                        "context": {},
                    },
                    token,
                )
                if assert_ok(errors, "summary_facts_list", fact_status, fact_payload):
                    fact_data = fact_payload.get("data") or {}
                    fact_records = fact_data.get("records") or []
                    expected_count = int(summary_sample.get("source_line_count") or 0)
                    actual_count = int(fact_data.get("total") or len(fact_records) or 0)
                    if expected_count and actual_count != expected_count:
                        errors.append(
                            {
                                "key": "summary_facts_count_mismatch",
                                "expected": expected_count,
                                "actual": actual_count,
                                "domain": domain,
                            }
                        )
                    first_fact = fact_records[0] if fact_records and isinstance(fact_records[0], dict) else {}
                    if not first_fact.get("responsibility_type") or not first_fact.get("source_model") or not first_fact.get("source_res_id"):
                        errors.append({"key": "summary_fact_source_trace_missing", "first_fact": first_fact})
                    evidence["drilldown"] = {
                        "summary_id": int(summary_sample.get("id") or 0),
                        "button_result_model": FACT_MODEL,
                        "domain": domain,
                        "expected_fact_count": expected_count,
                        "actual_fact_count": actual_count,
                        "first_fact_keys": sorted(first_fact.keys()) if first_fact else [],
                        "first_fact_source_model": first_fact.get("source_model"),
                        "first_fact_responsibility_type": first_fact.get("responsibility_type"),
                    }

    result = OrderedDict()
    result["status"] = "PASS" if not errors else "FAIL"
    result["evidence"] = evidence
    result["errors"] = errors

    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    output = ARTIFACT_ROOT / "company_contractor_responsibility_http_smoke.json"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
