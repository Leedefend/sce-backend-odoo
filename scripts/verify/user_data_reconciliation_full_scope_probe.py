#!/usr/bin/env python3
"""Audit full user-facing historical data for reconciliation readiness.

The narrower user_reconciliation_readiness_probe guards the core financial
ledgers. This probe scans every P1 daily-business visible model and checks
whether users can reconcile historical rows through stable business axes:
project, document/date, counterparty, type/category, amounts, and source entry.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

from lxml import etree

from odoo.addons.smart_construction_core.models.support.p1_daily_business_visible_alias_fields import (  # noqa: E501
    LABEL_SOURCE_OVERRIDES,
    MODEL_LABEL_SOURCE_OVERRIDES,
    P1_ALIAS_LABELS,
)


def artifact_root() -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.append(Path("/mnt/artifacts/verify"))
    candidates.append(Path(f"/tmp/history_continuity/{env.cr.dbname}/verify"))  # noqa: F821
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return candidate
        except Exception:
            continue
    return Path(f"/tmp/history_continuity/{env.cr.dbname}/verify")  # noqa: F821


def existing_fields(model_name: str) -> set[str]:
    return set(env[model_name]._fields)  # noqa: F821


def first_existing(
    model_name: str,
    candidates: list[str] | tuple[str, ...],
    preferred: set[str] | None = None,
) -> str | None:
    fields = existing_fields(model_name)
    preferred = preferred or set()
    for field_name in candidates:
        if field_name in fields and field_name in preferred:
            return field_name
    for field_name in candidates:
        if field_name in fields:
            return field_name
    return None


def best_axis_field(
    model_name: str,
    candidates: list[str] | tuple[str, ...],
    domain: list[object],
    total: int,
    preferred: set[str] | None = None,
) -> tuple[str | None, int]:
    fields = existing_fields(model_name)
    preferred = preferred or set()
    existing = [field_name for field_name in candidates if field_name in fields]
    if not existing:
        return None, 0
    if not total:
        preferred_existing = [field_name for field_name in existing if field_name in preferred]
        return (preferred_existing or existing)[0], 0

    scored = []
    for field_name in existing:
        filled = non_empty_count(model_name, field_name, domain)
        grouped_rank = 1 if field_name in preferred else 0
        scored.append((grouped_rank, filled, -existing.index(field_name), field_name))
    grouped = [item for item in scored if item[0]]
    pool = grouped or scored
    _, filled, _, field_name = max(pool)
    return field_name, filled


def domain_for_model(model_name: str) -> list[object]:
    fields = existing_fields(model_name)
    if "source_origin" in fields:
        return [("source_origin", "=", "legacy")]
    if "legacy_record_id" in fields:
        return [("legacy_record_id", "!=", False)]
    if "legacy_source_id" in fields:
        return [("legacy_source_id", "!=", False)]
    if "legacy_source_model" in fields:
        return [("legacy_source_model", "!=", False)]
    return []


def non_empty_count(model_name: str, field_name: str, domain: list[object]) -> int:
    field = env[model_name]._fields.get(field_name)  # noqa: F821
    if field and field.compute and not field.store:
        return 0
    if field and field.type == "boolean":
        return env[model_name].sudo().search_count(domain)  # noqa: F821
    return env[model_name].sudo().search_count(domain + [(field_name, "!=", False)])  # noqa: F821


def amount_sum(model_name: str, field_name: str, domain: list[object]) -> float:
    field = env[model_name]._fields.get(field_name)  # noqa: F821
    if field and field.compute and not field.store:
        return 0.0
    Model = env[model_name].sudo()  # noqa: F821
    total = 0.0
    for group in Model.read_group(domain, [f"{field_name}:sum"], [], lazy=False):
        total += float(group.get(field_name) or 0.0)
    return total


def view_fields(model_name: str, view_type: str) -> dict[str, set[str]]:
    group_fields: set[str] = set()
    sum_fields: set[str] = set()
    visible_fields: set[str] = set()
    views = env["ir.ui.view"].sudo().search([("model", "=", model_name), ("type", "=", view_type)])  # noqa: F821
    for view in views:
        arch = view.arch_db or ""
        for group_field in re.findall(r"group_by'?\s*:\s*'([^']+)'", arch):
            group_fields.add(group_field.split(":", 1)[0])
        try:
            root = etree.fromstring(arch.encode("utf-8")) if arch else None
        except Exception:
            root = None
        if root is None:
            continue
        for node in root.xpath(".//field[@name]"):
            name = node.get("name")
            if not name:
                continue
            visible_fields.add(name)
            if node.get("sum"):
                sum_fields.add(name)
    return {
        "group_fields": group_fields,
        "sum_fields": sum_fields,
        "visible_fields": visible_fields,
    }


AXES = {
    "project": [
        "project_id",
        "business_entity_id",
        "legacy_project_name",
        "legacy_visible_project_name",
        "project_name",
        "project_name_text",
        "legacy_xmmc",
    ],
    "document": [
        "document_no",
        "legacy_document_no",
        "legacy_visible_document_no",
        "legacy_record_id",
        "name",
        "contract_no",
        "invoice_no",
        "source_login",
        "generated_login",
    ],
    "date": [
        "document_date",
        "request_date",
        "date_request",
        "date_claim",
        "date_payment",
        "date_receipt",
        "invoice_date",
        "operation_date",
        "date_contract",
        "business_date",
        "apply_date",
        "date",
        "receipt_time",
        "settlement_date",
        "rental_date",
        "usage_date",
        "contract_date",
        "date_diary",
        "inbound_date",
        "outbound_date",
        "snapshot_date",
        "create_date",
        "created_time",
        "source_created_at",
    ],
    "party": [
        "partner_id",
        "supplier_id",
        "contractor_id",
        "subcontractor_id",
        "owner_id",
        "requester_id",
        "partner_name",
        "partner_name_text",
        "legacy_partner_name",
        "construction_unit_name",
        "receipt_partner_name",
    ],
    "type": [
        "source_kind",
        "contract_type",
        "contract_family",
        "claim_type",
        "expense_type",
        "payment_family",
        "payment_method",
        "income_category",
        "receipt_type",
        "legacy_receipt_type",
        "legacy_receipt_subtype",
        "operation_type",
        "operation_strategy",
        "entity_type",
        "fact_type",
        "invoice_type",
        "direction",
        "tax_rate",
        "cost_category_name",
        "document_scope",
        "source_family",
        "document_state",
        "user_type",
        "person_state",
        "state",
    ],
    "creator": ["source_created_by", "creator_name", "requester_id", "owner_id"],
    "created_at": ["source_created_at", "created_time", "create_date"],
}

AMOUNT_FIELDS = [
    "visible_contract_amount",
    "visible_invoice_amount",
    "visible_received_amount",
    "visible_unreceived_amount",
    "amount_total",
    "amount",
    "paid_amount",
    "planned_amount",
    "invoice_amount",
    "received_amount",
    "unreceived_amount",
    "unpaid_amount",
    "approved_amount",
    "deduction_amount",
    "tax_amount",
    "amount_no_tax",
    "invoice_amount_total",
    "daily_income",
    "daily_expense",
    "account_balance_total",
    "bank_balance_total",
    "bank_system_difference",
]


def best_label_source(model_name: str, candidates: list[str], domain: list[object], total: int) -> tuple[str | None, int]:
    fields = existing_fields(model_name)
    seen = []
    for candidate in candidates:
        if candidate in fields and candidate not in seen:
            seen.append(candidate)
    if not seen:
        return None, 0
    if not total:
        return seen[0], 0

    best_field = seen[0]
    best_filled = -1
    for field_name in seen:
        filled = non_empty_count(model_name, field_name, domain)
        if filled > best_filled:
            best_field = field_name
            best_filled = filled
    return best_field, max(best_filled, 0)


RENTAL_ORDER_LABEL_DOMAINS = {
    "租赁合同": {
        "合同编号",
        "合同标题",
        "租赁内容",
        "总金额",
        "已开票金额",
        "已付款金额",
        "未付款金额",
        "未开票金额",
        "开户行",
        "银行账号",
        "开户人姓名",
        "签订时间",
    },
    "租入": {
        "单据日期",
        "材料名称",
        "规格型号",
        "数量",
        "单价",
        "租赁押金",
    },
}

TENDER_GUARANTEE_SOURCE_LABEL_DOMAINS = {
    "online_old_scbs:ZJGL_BZJGL_Branch_SBZJDJ:list868": {
        "状态",
        "单据编号",
        "投标项目名称",
        "项目名称",
        "所属公司",
        "金额",
        "已退保证金金额",
        "转款单位",
        "汇款方式",
        "保证金类型",
        "收款账户",
        "收款账户名称",
        "备注",
        "附件",
        "录入人",
        "录入时间",
    },
    "online_old_scbs:ZJGL_BZJGL_Branch_SBZJTH:list869": {
        "状态",
        "收保证金单号",
        "单据编号",
        "项目名称",
        "投标项目名称",
        "退还金额",
        "备注",
        "退还账号",
        "退还开户行",
        "单位",
        "收款开户行",
        "收款账号",
        "录入人",
        "录入时间",
        "附件",
    },
    "online_old_scbs:ZJGL_BZJGL_Pay_FBZJ:list870": {
        "状态",
        "推送结果",
        "金蝶单据编号",
        "单据编号",
        "投标项目",
        "工程项目",
        "保证金类型",
        "所属公司",
        "保证金金额",
        "已退金额",
        "未退金额",
        "是否需要退回",
        "收款单位",
        "支付账户",
        "备注",
        "附件",
        "录入人",
        "录入时间",
    },
    "online_old_scbs:ZJGL_BZJGL_Pay_FBZJTH:list871": {
        "状态",
        "推送结果",
        "退回单编号",
        "所属公司",
        "投标项目名称",
        "保证金类型",
        "退回项目",
        "退回金额",
        "退回账户",
        "收款单位",
        "备注",
        "录入人",
        "退回日期",
        "附件",
    },
}


DOCUMENT_ADMIN_PROJECT_SOURCE_TABLES = {
    "online_old_scbs:SGZL_RZRJ:list856",
    "online_old_scbs:SGZL_RZRJ:list856:hidden",
    "fresh_db_legacy_document_borrow",
    "online_old_scbs:ZJGL_ZSJYGL:list865",
}

DOCUMENT_ADMIN_LABEL_FACT_TYPE_DOMAINS = {
    "company_document_archive": {
        "单据状态",
        "项目名称",
        "资料类型",
        "资料说明",
        "录入人",
        "备注",
        "录入时间",
    },
    "certificate_registration": {
        "证照名称",
        "编号",
        "持有人",
        "有效期",
    },
    "document_borrow": {
        "单据编号",
        "借阅项目名称",
        "证件名称",
        "申请日期",
        "借阅部门或项目部名称",
        "借阅人",
        "联系方式",
        "借阅形式",
        "借阅日期",
        "负责人",
        "归还申请日期",
        "申请归还时间",
        "是否归还",
        "确认归还时间",
        "归还日期",
        "附件",
        "修改人",
        "修改日期",
        "修改备注",
        "审定人",
        "审定时间",
        "审定意见",
    },
}

DOCUMENT_ADMIN_LABEL_SOURCE_TABLE_DOMAINS = {
    "项目名称": {
        "online_old_scbs:SGZL_RZRJ:list856",
        "online_old_scbs:SGZL_RZRJ:list856:hidden",
    },
    "联系方式": {"online_old_scbs:ZJGL_ZSJYGL:list865"},
    "负责人": {"online_old_scbs:ZJGL_ZSJYGL:list865"},
    "附件": {"online_old_scbs:ZJGL_ZSJYGL:list865"},
    "修改备注": {"online_old_scbs:ZJGL_ZSJYGL:list865"},
    "审定人": {"online_old_scbs:ZJGL_ZSJYGL:list865"},
    "审定时间": {"online_old_scbs:ZJGL_ZSJYGL:list865"},
    "审定意见": {"online_old_scbs:ZJGL_ZSJYGL:list865"},
}

EXPENSE_CLAIM_LABEL_SOURCE_TABLE_DOMAINS = {
    "部门": {
        "CWGL_FYBX",
        "CWGL_FYBX_CB",
    },
    "付款方式": {
        "SCBSLY_DIRECT_PROJECT_EXPENSE_CLAIM",
        "CWGL_FYBX_CB",
        "C_JFHKLR",
        "C_JFHKLR_TH_ZCDF_CB",
        "C_ZFSQGL_BZJKD",
    },
}

FINANCING_LOAN_LABEL_SOURCE_TABLE_DOMAINS = {
    "申请部门": {"BGGL_JHK_JKSQ", "BGGL_JHK_HKDJ"},
    "申请时间": {"BGGL_JHK_JKSQ", "BGGL_JHK_HKDJ"},
    "申请人": {"BGGL_JHK_JKSQ", "BGGL_JHK_HKDJ"},
    "是否预算内": {"BGGL_JHK_JKSQ"},
    "实际借款金额": {"BGGL_JHK_JKSQ"},
    "主要资金使用安排": {"BGGL_JHK_JKSQ"},
    "收款人": {"BGGL_JHK_JKSQ"},
    "收款账户": {"BGGL_JHK_JKSQ"},
    "开户银行": {"BGGL_JHK_JKSQ"},
    "公司名称": {"BGGL_JHK_JKSQ"},
    "付款单位": {"BGGL_JHK_JKSQ"},
    "收款单位": {"BGGL_JHK_JKSQ"},
    "往来单位名称": {"BGGL_JHK_JKSQ", "BGGL_JHK_HKDJ"},
    "往来单位账户": {"BGGL_JHK_JKSQ"},
    "借款账号": {"BGGL_JHK_JKSQ"},
    "实际批复金额": {"BGGL_JHK_JKSQ"},
    "申请金额": {"BGGL_JHK_JKSQ"},
    "预计归还时间": {"BGGL_JHK_JKSQ"},
    "借款类型": {"BGGL_JHK_JKSQ"},
    "借款人": {"ZJGL_ZCDFSZ_FXJK_JK"},
    "借款金额": {"ZJGL_ZCDFSZ_FXJK_JK", "BGGL_JHK_HKDJ"},
    "用途": {"ZJGL_ZCDFSZ_FXJK_JK"},
    "约定期限": {"ZJGL_ZCDFSZ_FXJK_JK"},
    "借款利息": {"ZJGL_ZCDFSZ_FXJK_JK"},
    "贷款金额": {"ZJGL_ZJSZ_DKGL_DKDJ"},
    "到期利息": {"ZJGL_ZJSZ_DKGL_DKDJ"},
    "未还款金额": {"ZJGL_ZJSZ_DKGL_DKDJ"},
    "贷款日期": {"ZJGL_ZJSZ_DKGL_DKDJ"},
    "还款日期": {"ZJGL_ZJSZ_DKGL_DKDJ"},
    "贷款天数": {"ZJGL_ZJSZ_DKGL_DKDJ"},
    "年利率": {"ZJGL_ZJSZ_DKGL_DKDJ"},
    "贷款账户": {"ZJGL_ZJSZ_DKGL_DKDJ", "ZJGL_ZJSZ_DKGL_HKDJ"},
    "贷款银行": {"ZJGL_ZJSZ_DKGL_DKDJ", "ZJGL_ZJSZ_DKGL_HKDJ"},
    "还款金额": {"ZJGL_ZJSZ_DKGL_HKDJ"},
    "还款账户": {"ZJGL_ZJSZ_DKGL_HKDJ"},
    "填写人": {"ZJGL_ZJSZ_DKGL_HKDJ"},
}

OFFICE_ADMIN_LABEL_FACT_TYPE_DOMAINS = {
    "请假天数": {"leave_request"},
    "请假类型": {"leave_request"},
    "请假时间": {"leave_request"},
    "销假时间": {"leave_request"},
    "请假时长": {"leave_request"},
    "用印时间": {"seal_use"},
    "用印部门": {"seal_use"},
    "用印申请人": {"seal_use"},
    "用印部门负责人签字": {"seal_use"},
    "用印种类": {"seal_use"},
    "用印文本名称及文号": {"seal_use"},
    "经办人签字": {"seal_use"},
    "领导签字": {"seal_use"},
    "份数": {"seal_use"},
    "归还时间": {"seal_use"},
    "合同金额": {"seal_use"},
    "合同编号": {"seal_use"},
    "所属公司": {"seal_use"},
    "使用印章公司": {"seal_use"},
    "是否外带": {"seal_use"},
}

OFFICE_ADMIN_LABEL_SOURCE_TABLE_DOMAINS = {
    "附件": {"online_old_scbs:BGGL_XZD_YZSYSPB:list858"},
}

FUND_ACCOUNT_OPERATION_LABEL_SOURCE_TABLE_DOMAINS = {
    "单据状态": {"C_FKGL_ZHJZJWL"},
    "项目名称": {"C_FKGL_ZHJZJWL"},
    "发生时间": {"C_FKGL_ZHJZJWL"},
    "账户号码": {"C_FKGL_ZHJZJWL"},
    "转账类别": {"C_FKGL_ZHJZJWL"},
    "事由": {"C_FKGL_ZHJZJWL"},
    "附件": {"C_FKGL_ZHJZJWL"},
    "单据编号": {"C_FKGL_ZHJZJWL"},
    "收款账户": {"C_FKGL_ZHJZJWL"},
}

PAYMENT_EXECUTION_EMPTY_LEGACY_LABELS = {
    "凭证号",
}


def axis_domain(model_name: str, axis: str, base_domain: list[object]) -> list[object]:
    if model_name == "sc.document.admin.document" and axis == "project":
        return [
            "|",
            ("legacy_source_table", "in", sorted(DOCUMENT_ADMIN_PROJECT_SOURCE_TABLES)),
            ("fact_type", "=", "document_borrow"),
        ] + base_domain
    return base_domain


def label_domain(model_name: str, label: str, base_domain: list[object]) -> list[object]:
    if model_name == "sc.office.admin.document":
        source_tables = OFFICE_ADMIN_LABEL_SOURCE_TABLE_DOMAINS.get(label)
        if source_tables:
            return base_domain + [("legacy_source_table", "in", sorted(source_tables))]
        fact_types = OFFICE_ADMIN_LABEL_FACT_TYPE_DOMAINS.get(label)
        if fact_types:
            return base_domain + [("fact_type", "in", sorted(fact_types))]
    if model_name == "sc.fund.account.operation":
        source_tables = FUND_ACCOUNT_OPERATION_LABEL_SOURCE_TABLE_DOMAINS.get(label)
        if source_tables:
            return base_domain + [("legacy_source_table", "in", sorted(source_tables))]
    if model_name == "sc.payment.execution" and label in PAYMENT_EXECUTION_EMPTY_LEGACY_LABELS:
        return base_domain + [("id", "=", 0)]
    if model_name == "sc.financing.loan":
        source_tables = FINANCING_LOAN_LABEL_SOURCE_TABLE_DOMAINS.get(label)
        if source_tables:
            return base_domain + [("legacy_source_table", "in", sorted(source_tables))]
    if model_name == "sc.expense.claim":
        source_tables = EXPENSE_CLAIM_LABEL_SOURCE_TABLE_DOMAINS.get(label)
        if source_tables:
            return base_domain + [("legacy_source_table", "in", sorted(source_tables))]
    if model_name == "sc.document.admin.document":
        source_tables = DOCUMENT_ADMIN_LABEL_SOURCE_TABLE_DOMAINS.get(label)
        if source_tables:
            return base_domain + [("legacy_source_table", "in", sorted(source_tables))]
        fact_types = [
            fact_type
            for fact_type, labels in DOCUMENT_ADMIN_LABEL_FACT_TYPE_DOMAINS.items()
            if label in labels
        ]
        if fact_types:
            return base_domain + [("fact_type", "in", fact_types)]
    if model_name == "sc.material.rental.order" and "legacy_acceptance_label" in existing_fields(model_name):
        for acceptance_label, labels in RENTAL_ORDER_LABEL_DOMAINS.items():
            if label in labels:
                return base_domain + [("legacy_acceptance_label", "=", acceptance_label)]
    if model_name == "tender.guarantee":
        source_models = [
            source_model
            for source_model, labels in TENDER_GUARANTEE_SOURCE_LABEL_DOMAINS.items()
            if label in labels
        ]
        if source_models:
            return base_domain + [("bid_id.legacy_fact_model", "in", source_models)]
    return base_domain


def label_source_coverage(model_name: str, labels: list[str], domain: list[object], total: int) -> list[dict[str, object]]:
    rows = []
    for label in labels:
        effective_domain = label_domain(model_name, label, domain)
        effective_total = env[model_name].sudo().search_count(effective_domain)  # noqa: F821
        candidates = [
            name for name, field in env[model_name]._fields.items()  # noqa: F821
            if field.string == label and not name.startswith("p1_visible_")
        ]
        candidates += list(MODEL_LABEL_SOURCE_OVERRIDES.get(model_name, {}).get(label, ()))
        candidates += list(LABEL_SOURCE_OVERRIDES.get(label, ()))
        field_name, filled = best_label_source(model_name, candidates, effective_domain, effective_total)
        rows.append(
            {
                "label": label,
                "field": field_name,
                "filled": filled,
                "total": effective_total,
                "ratio": round(filled / effective_total, 4) if effective_total else 1.0,
                "source_missing": field_name is None and effective_total > 0,
            }
        )
    return rows


results = []
blocking_gaps = []
warnings = []
empty_model_infos = []
low_volume_infos = []

for model_name, labels in sorted(P1_ALIAS_LABELS.items()):
    if model_name not in env:  # noqa: F821
        blocking_gaps.append({"model": model_name, "reason": "model_missing"})
        continue
    Model = env[model_name].sudo()  # noqa: F821
    domain = domain_for_model(model_name)
    total = Model.search_count(domain)
    fields = existing_fields(model_name)
    search = view_fields(model_name, "search")
    tree = view_fields(model_name, "tree")
    amount_candidates = [
        field_name
        for field_name in AMOUNT_FIELDS
        if field_name in fields and field_name in tree["visible_fields"]
    ]
    amount_field = first_existing(model_name, amount_candidates)
    amount_total = amount_sum(model_name, amount_field, domain) if amount_field and total else 0.0

    axes = {}
    missing_axes = []
    weak_axes = []
    for axis, candidates in AXES.items():
        effective_domain = axis_domain(model_name, axis, domain)
        effective_total = Model.search_count(effective_domain)
        field_name, filled = best_axis_field(model_name, candidates, effective_domain, effective_total, search["group_fields"])
        ratio = round(filled / effective_total, 4) if effective_total else 1.0
        axes[axis] = {
            "field": field_name,
            "filled": filled,
            "total": effective_total,
            "ratio": ratio,
            "grouped": bool(field_name and field_name in search["group_fields"]),
            "visible": bool(field_name and field_name in tree["visible_fields"]),
        }
        if effective_total >= 100 and axis in {"project", "document", "date", "type"} and not field_name:
            missing_axes.append(axis)
        if effective_total >= 100 and field_name and ratio < 0.8 and axis in {"project", "document", "date", "type"}:
            weak_axes.append(axis)

    amount_visible = bool(amount_field and amount_field in tree["visible_fields"])
    amount_summed = bool(amount_field and amount_field in tree["sum_fields"])
    group_gap_axes = [
        axis
        for axis in ("project", "date", "party", "type")
        if axes[axis]["field"] and total >= 100 and not axes[axis]["grouped"]
    ]
    label_rows = label_source_coverage(model_name, labels, domain, total)
    label_source_missing = [row["label"] for row in label_rows if row["source_missing"]]
    low_label_coverage = [
        row for row in label_rows
        if row["total"] >= 100 and not row["source_missing"] and row["ratio"] < 0.2
    ]

    if total >= 100 and amount_field and not amount_summed:
        blocking_gaps.append({"model": model_name, "reason": "amount_not_summed", "field": amount_field, "total": total})
    for axis in missing_axes:
        blocking_gaps.append({"model": model_name, "reason": "axis_missing", "axis": axis, "total": total})
    if total >= 100 and group_gap_axes:
        warnings.append({"model": model_name, "reason": "group_axes_not_exposed", "axes": group_gap_axes, "total": total})
    if weak_axes:
        warnings.append({"model": model_name, "reason": "weak_axis_coverage", "axes": weak_axes, "total": total})
    if label_source_missing and total >= 100:
        warnings.append(
            {
                "model": model_name,
                "reason": "p1_label_source_missing",
                "labels": label_source_missing[:20],
                "count": len(label_source_missing),
                "total": total,
            }
        )
    elif label_source_missing and total > 0:
        low_volume_infos.append(
            {
                "model": model_name,
                "reason": "low_volume_p1_label_source_missing",
                "labels": label_source_missing[:20],
                "count": len(label_source_missing),
                "total": total,
            }
        )
    elif label_source_missing:
        empty_model_infos.append(
            {
                "model": model_name,
                "reason": "empty_model_p1_label_source_missing",
                "labels": label_source_missing[:20],
                "count": len(label_source_missing),
                "total": total,
            }
        )
    if low_label_coverage:
        warnings.append(
            {
                "model": model_name,
                "reason": "low_p1_label_coverage",
                "labels": [
                    {"label": row["label"], "field": row["field"], "ratio": row["ratio"]}
                    for row in low_label_coverage[:20]
                ],
                "count": len(low_label_coverage),
            }
        )

    results.append(
        {
            "model": model_name,
            "total": total,
            "domain": domain,
            "amount_field": amount_field,
            "amount_sum": amount_total,
            "amount_visible": amount_visible,
            "amount_summed": amount_summed,
            "axes": axes,
            "group_gap_axes": group_gap_axes,
            "label_source_missing_count": len(label_source_missing),
            "low_label_coverage_count": len(low_label_coverage),
            "label_coverage_sample": label_rows[:12],
        }
    )

payload = {
    "status": "FAIL" if blocking_gaps else "PASS",
    "database": env.cr.dbname,  # noqa: F821
    "mode": "user_data_reconciliation_full_scope_probe",
    "model_count": len(results),
    "blocking_gap_count": len(blocking_gaps),
    "warning_count": len(warnings),
    "empty_model_info_count": len(empty_model_infos),
    "low_volume_info_count": len(low_volume_infos),
    "blocking_gaps": blocking_gaps,
    "warnings": warnings[:120],
    "empty_model_infos": empty_model_infos[:120],
    "low_volume_infos": low_volume_infos[:120],
    "results": results,
}
output = artifact_root() / "user_data_reconciliation_full_scope_probe_result_v1.json"
output.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print("USER_DATA_RECONCILIATION_FULL_SCOPE_PROBE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))

if blocking_gaps:
    raise SystemExit(1)
