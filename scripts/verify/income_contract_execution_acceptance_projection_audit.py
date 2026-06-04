# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import re

from lxml import etree
from odoo.tools.safe_eval import safe_eval


DIRECT_PREFIX = "direct_acceptance:construction_contract:"
OLD_BUSINESS_ACTION_ID = 855

DIRECT_VISIBLE_FIELDS = [
    ("legacy_visible_01", "legacy_visible_document_state", "单据状态", "text"),
    ("legacy_visible_02", "legacy_visible_document_no", "单据编号", "text"),
    ("legacy_visible_03", "legacy_visible_counterparty", "发包人", "text"),
    ("legacy_visible_04", "legacy_visible_contractor", "承包人", "text"),
    ("legacy_visible_05", "legacy_visible_project_name", "项目名称", "text"),
    ("legacy_visible_06", "legacy_visible_title", "合同标题", "text"),
    ("legacy_visible_07", "legacy_visible_amount", "合同金额", "number"),
    ("legacy_visible_08", "legacy_visible_invoice_amount", "累计开票", "number"),
    ("legacy_visible_09", "legacy_visible_received_amount", "累计收款", "number"),
    ("legacy_visible_10", "legacy_visible_invoice_unreceived_amount", "开票未收款", "number"),
    ("legacy_visible_11", "legacy_visible_unreceived_amount", "未收款", "number"),
    ("legacy_visible_12", "legacy_visible_unreceived_rate", "未收款比例", "text"),
    ("legacy_visible_13", "legacy_visible_contract_no", "合同编号", "text"),
    ("legacy_visible_14", "legacy_visible_contract_date", "合同订立日期", "date"),
    ("legacy_visible_15", "legacy_visible_engineering_address", "工程地址", "text"),
    ("legacy_visible_16", "legacy_visible_engineering_content", "工程内容", "text"),
    ("legacy_visible_17", "legacy_visible_contract_duration_days", "合同工期天数", "text"),
    ("legacy_visible_18", "legacy_visible_creator_name", "录入人", "text"),
    ("legacy_visible_19", "legacy_visible_created_time", "录入时间", "datetime"),
    ("legacy_visible_20", "legacy_visible_attachment", "附件", "text"),
]


def _text(value) -> str:
    cleaned = str(value or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    if cleaned in {"False", "false", "None", "none"}:
        return ""
    return cleaned


def _normalize_text(value) -> str:
    return re.sub(r"\s+", " ", _text(value)).strip()


def _normalize_number(value) -> str:
    raw = _text(value).replace(",", "").replace("￥", "").replace("¥", "")
    if not raw:
        return "0"
    match = re.search(r"-?\d+(?:\.\d+)?", raw)
    if not match:
        return raw
    return ("%.2f" % float(match.group(0))).rstrip("0").rstrip(".")


def _normalize_value(value, kind: str) -> str:
    if kind == "number":
        return _normalize_number(value)
    if kind == "date":
        return _text(value)[:10]
    if kind == "datetime":
        return _text(value)[:19]
    return _normalize_text(value)


def _domain_text(action_xmlid: str) -> str:
    action = env.ref(action_xmlid, raise_if_not_found=False)  # noqa: F821
    if not action:
        raise AssertionError("missing action: %s" % action_xmlid)
    return str(action.domain or "")


def _old_business_action():
    action = env["ir.actions.act_window"].sudo().browse(OLD_BUSINESS_ACTION_ID)  # noqa: F821
    if not action.exists():
        raise AssertionError("missing old business acceptance action: %s" % OLD_BUSINESS_ACTION_ID)
    if action.res_model != "construction.contract":
        raise AssertionError("old business acceptance action model changed: %s" % action.res_model)
    return action


def _old_business_action_domain() -> list:
    action = _old_business_action()
    domain = safe_eval(action.domain or "[]")
    if ("legacy_contract_id", "not ilike", DIRECT_PREFIX + "%") not in domain:
        raise AssertionError("old business acceptance action domain includes direct acceptance data: %s" % action.domain)
    return domain


def _view_fields(view, include_optional_hide=False) -> list[tuple[str, str]]:
    root = etree.fromstring((view.arch_db or "<tree/>").encode())
    fields = []
    for node in root.xpath(".//field[@name]"):
        if not include_optional_hide and node.get("optional") == "hide":
            continue
        fields.append((node.get("name"), node.get("string") or node.get("name")))
    return fields


def _direct_visible_alignment_errors(Fact, Income) -> list[dict]:
    errors = []
    facts = Fact.search(
        [
            ("source_system", "=", "online_old_scbsly"),
            ("acceptance_label", "=", "施工合同"),
            ("active", "=", True),
        ]
    )
    mismatch_counts = {label: 0 for _, _, label, _ in DIRECT_VISIBLE_FIELDS}
    samples = []
    missing = []
    for fact in facts:
        income = Income.search([("legacy_contract_id", "=", DIRECT_PREFIX + _text(fact.legacy_record_id))], limit=1)
        if not income:
            missing.append(fact.id)
            continue
        for source_field, target_field, label, kind in DIRECT_VISIBLE_FIELDS:
            source_value = _normalize_value(getattr(fact, source_field), kind)
            target_value = _normalize_value(getattr(income, target_field), kind)
            if source_value == target_value:
                continue
            mismatch_counts[label] += 1
            if len(samples) < 20:
                samples.append(
                    {
                        "fact_id": fact.id,
                        "income_id": income.id,
                        "field": label,
                        "source": source_value,
                        "target": target_value,
                    }
                )
    if missing or any(mismatch_counts.values()):
        errors.append(
            {
                "error": "direct_acceptance_visible_field_mismatch",
                "missing_income": missing[:20],
                "mismatch_counts": mismatch_counts,
                "sample_mismatches": samples,
            }
        )
    return errors


def _joint_acceptance_projection_errors(Contract, Income) -> tuple[list[dict], dict]:
    action = _old_business_action()
    source_domain = _old_business_action_domain() + [("type", "=", "out")]
    source_contracts = Contract.search(source_domain)
    target_view = env.ref("smart_construction_core.view_construction_contract_income_tree")  # noqa: F821
    source_fields = _view_fields(action.view_id)
    target_fields = _view_fields(target_view)
    target_by_label = {label: field for field, label in target_fields}
    missing = []
    wrong_contract = []
    missing_labels = []
    value_mismatches = []
    attachment_stats = {
        "source_visible_nonempty": 0,
        "target_visible_nonempty": 0,
        "visible_mismatch_count": 0,
        "sample_mismatches": [],
    }
    for contract in source_contracts:
        income = Income.search([("contract_id", "=", contract.id)], limit=1)
        if not income:
            missing.append({"contract_id": contract.id, "legacy_contract_id": contract.legacy_contract_id})
        elif income.legacy_contract_id != contract.legacy_contract_id:
            wrong_contract.append(
                {
                    "contract_id": contract.id,
                    "income_id": income.id,
                    "source_legacy_contract_id": contract.legacy_contract_id,
                    "income_legacy_contract_id": income.legacy_contract_id,
                }
            )
    for source_field, label in source_fields:
        target_field = target_by_label.get(label)
        if not target_field:
            missing_labels.append({"label": label, "source_field": source_field})
            continue
        for contract in source_contracts:
            income = Income.search([("contract_id", "=", contract.id)], limit=1)
            if not income:
                continue
            source_value = _normalize_text(getattr(contract, source_field))
            target_value = _normalize_text(getattr(income, target_field))
            if label == "附件":
                if source_value:
                    attachment_stats["source_visible_nonempty"] += 1
                if target_value:
                    attachment_stats["target_visible_nonempty"] += 1
                if source_value != target_value:
                    attachment_stats["visible_mismatch_count"] += 1
                    if len(attachment_stats["sample_mismatches"]) < 20:
                        attachment_stats["sample_mismatches"].append(
                            {
                                "contract_id": contract.id,
                                "income_id": income.id,
                                "document_no": contract.legacy_document_no,
                                "source": source_value,
                                "target": target_value,
                            }
                        )
            if source_value != target_value:
                value_mismatches.append(
                    {
                        "label": label,
                        "source_field": source_field,
                        "target_field": target_field,
                        "contract_id": contract.id,
                        "income_id": income.id,
                        "document_no": contract.legacy_document_no,
                        "source": source_value,
                        "target": target_value,
                    }
                )
                break
    errors = []
    if missing or wrong_contract or missing_labels or value_mismatches:
        errors.append(
            {
                "error": "joint_acceptance_contract_income_wrapper_mismatch",
                "missing_income": missing[:20],
                "wrong_contract": wrong_contract[:20],
                "missing_target_labels": missing_labels,
                "first_value_mismatches": value_mismatches[:20],
            }
        )
    return errors, {
        "source_model": "construction.contract",
        "source_action_id": action.id,
        "source_action_name": action.name,
        "source_action_domain": action.domain,
        "source_count": len(source_contracts),
        "income_count": Income.search_count([("contract_id", "in", source_contracts.ids)]),
        "source_field_count": len(source_fields),
        "target_default_field_count": len(target_fields),
        "attachment": attachment_stats,
    }


def main():
    Contract = env["construction.contract"].sudo()  # noqa: F821
    Income = env["construction.contract.income"].sudo()  # noqa: F821
    Fact = env["sc.legacy.direct.acceptance.fact"].sudo().with_context(active_test=False)  # noqa: F821

    domain = _domain_text("smart_construction_core.action_construction_contract_income_execution")
    if "legacy_income_surface_visible" not in domain or "confirmed" not in domain or "running" not in domain:
        raise AssertionError("income execution action domain no longer carries accepted legacy data: %s" % domain)

    direct_fact_count = Fact.search_count(
        [
            ("source_system", "=", "online_old_scbsly"),
            ("acceptance_label", "=", "施工合同"),
            ("active", "=", True),
        ]
    )
    direct_contract_count = Contract.search_count(
        [
            ("legacy_contract_id", "ilike", DIRECT_PREFIX + "%"),
            ("type", "=", "out"),
            ("legacy_income_surface_visible", "=", True),
        ]
    )
    direct_income_count = Income.search_count(
        [
            ("legacy_contract_id", "ilike", DIRECT_PREFIX + "%"),
            ("legacy_income_surface_visible", "=", True),
        ]
    )
    old_business_income_count = Income.search_count(
        [
            ("legacy_document_no", "ilike", "WBHTGL%"),
            ("legacy_income_surface_visible", "=", True),
            ("legacy_contract_id", "not ilike", DIRECT_PREFIX + "%"),
        ]
    )
    income_execution_count = Income.search_count(
        [
            "|",
            ("legacy_income_surface_visible", "=", True),
            "&",
            ("state", "in", ["confirmed", "running"]),
            ("legacy_contract_id", "=", False),
        ]
    )

    errors = []
    if direct_fact_count and direct_contract_count != direct_fact_count:
        errors.append(
            {
                "error": "direct_contract_projection_count_mismatch",
                "facts": direct_fact_count,
                "contracts": direct_contract_count,
            }
        )
    if direct_fact_count and direct_income_count != direct_fact_count:
        errors.append(
            {
                "error": "direct_income_wrapper_count_mismatch",
                "facts": direct_fact_count,
                "income_records": direct_income_count,
            }
        )
    accepted_income_count = old_business_income_count + direct_income_count
    if income_execution_count < accepted_income_count:
        errors.append(
            {
                "error": "income_execution_below_accepted_legacy_surface",
                "income_execution_count": income_execution_count,
                "accepted_income_count": accepted_income_count,
                "old_business_income_count": old_business_income_count,
                "direct_income_count": direct_income_count,
            }
        )
    if direct_fact_count:
        errors.extend(_direct_visible_alignment_errors(Fact, Income))
    joint_errors, joint_summary = _joint_acceptance_projection_errors(Contract, Income)
    errors.extend(joint_errors)

    result = {
        "status": "PASS" if not errors else "FAIL",
        "db": env.cr.dbname,  # noqa: F821
        "action_domain": domain,
        "accepted_income_count": accepted_income_count,
        "old_business_income_count": old_business_income_count,
        "direct_acceptance_fact_count": direct_fact_count,
        "direct_projected_contract_count": direct_contract_count,
        "direct_projected_income_count": direct_income_count,
        "income_execution_count": income_execution_count,
        "joint_acceptance_source": joint_summary,
        "errors": errors,
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    if errors:
        raise AssertionError(result)


main()
