# -*- coding: utf-8 -*-
"""Backfill formal business fields from user-confirmed legacy visible data.

Run inside Odoo shell:
    odoo shell -d sc_demo < scripts/ops/user_confirmed_formal_data_backfill.py

The script only fills empty or migration-placeholder formal fields from locked
acceptance facts.  It deliberately does not change menus, actions, or list
views, and it does not attach binary files; attachment binding is a separate
file-index workflow.
"""

from __future__ import annotations

import json
import re

from odoo.addons.smart_construction_core.models.support.p1_daily_business_visible_alias_fields import (
    MODEL_LABEL_SOURCE_OVERRIDES,
    _format_alias_value,
)
from odoo.addons.smart_construction_core.models.support.user_confirmed_formal_visible_fields import (
    USER_CONFIRMED_FORMAL_VISIBLE_FIELDS,
)


def _table_exists(table):
    env.cr.execute("SELECT to_regclass(%s)", [f"public.{table}"])  # noqa: F821
    row = env.cr.fetchone()  # noqa: F821
    return bool(row and row[0])


def _column_exists(table, column):
    env.cr.execute(  # noqa: F821
        """
        SELECT 1
          FROM information_schema.columns
         WHERE table_schema = 'public'
           AND table_name = %s
           AND column_name = %s
        """,
        [table, column],
    )
    return bool(env.cr.fetchone())  # noqa: F821


def _run(name, sql, params=None, required=()):
    for table, columns in required:
        if not _table_exists(table) or any(not _column_exists(table, column) for column in columns):
            return {"name": name, "skipped": True, "reason": "missing_table_or_columns"}
    env.cr.execute(sql, params or [])  # noqa: F821
    return {"name": name, "updated": env.cr.rowcount}  # noqa: F821


_IDENT_RE = re.compile(r"^[a-z_][a-z0-9_]*$")
_SQL_COPY_TYPES = {"char", "text", "selection", "date", "datetime", "integer", "float", "monetary"}
_GENERIC_LABEL_SOURCE_CANDIDATES = {
    "单据状态": ("legacy_document_state", "legacy_visible_document_state", "document_status", "state"),
    "状态": ("legacy_document_state", "legacy_visible_document_state", "state"),
    "单据编号": ("legacy_visible_document_no", "legacy_document_no", "document_no", "name"),
    "项目名称": ("legacy_visible_project_name", "legacy_project_name", "project_name", "project_id"),
    "录入人": ("source_created_by", "creator_name", "legacy_visible_creator_name", "create_uid"),
    "填写人": ("source_created_by", "creator_name", "legacy_visible_writer", "create_uid"),
    "录入时间": ("source_created_at", "created_time", "legacy_visible_created_time", "create_date"),
    "登记时间": ("source_created_at", "created_time", "legacy_visible_created_time", "create_date"),
}
_MODEL_LABEL_SOURCE_CANDIDATES = {
    "sc.financing.loan": {
        "项目名称": ("legacy_visible_project_name",),
        "申请部门": ("legacy_visible_request_department",),
        "申请时间": ("legacy_visible_request_time",),
        "申请人": ("legacy_visible_applicant",),
        "是否预算内": ("legacy_visible_budget_included",),
        "实际借款金额": ("legacy_visible_actual_loan_amount",),
        "主要资金使用安排": ("legacy_visible_fund_usage_plan",),
        "收款人": ("legacy_visible_payee",),
        "收款账户": ("legacy_visible_receipt_account",),
        "开户银行": ("legacy_visible_bank_name",),
        "公司名称": ("legacy_visible_company_name",),
        "备注": ("legacy_visible_note",),
        "付款单位": ("legacy_visible_payer_unit",),
        "收款单位": ("legacy_visible_receiver_unit",),
        "往来单位名称": ("legacy_visible_counterparty_name",),
        "往来单位账户": ("legacy_visible_counterparty_account",),
        "借款账号": ("legacy_visible_loan_account",),
        "实际批复金额": ("legacy_visible_approved_amount",),
        "申请金额": ("legacy_visible_request_amount",),
        "预计归还时间": ("legacy_visible_expected_return_time",),
        "借款类型": ("legacy_visible_loan_type",),
        "借款人": ("legacy_visible_applicant",),
        "借款金额": ("legacy_visible_actual_loan_amount",),
        "用途": ("legacy_visible_fund_usage_plan",),
        "约定期限": ("legacy_visible_expected_return_time",),
        "借款利息": ("legacy_visible_loan_interest",),
        "借款利率": ("legacy_visible_annual_rate",),
        "利息": ("legacy_visible_loan_interest",),
        "还款时间": ("legacy_visible_repayment_date",),
        "贷款金额": ("legacy_visible_actual_loan_amount",),
        "到期利息": ("legacy_visible_due_interest",),
        "还款金额": ("legacy_visible_repayment_amount",),
        "未还款金额": ("legacy_visible_unpaid_amount",),
        "贷款日期": ("legacy_visible_loan_date",),
        "还款日期": ("legacy_visible_repayment_date",),
        "贷款天数": ("legacy_visible_loan_days",),
        "年利率": ("legacy_visible_annual_rate",),
        "贷款账户": ("legacy_visible_loan_account",),
        "贷款银行": ("legacy_visible_loan_bank",),
        "实际还款天数": ("legacy_visible_actual_repayment_days",),
        "实际年利率": ("legacy_visible_actual_annual_rate",),
        "贷款利息": ("legacy_visible_loan_interest",),
        "还款账户": ("legacy_visible_repayment_account",),
        "填写人": ("legacy_visible_writer",),
    },
}


def _ident(name):
    if not _IDENT_RE.match(name or ""):
        raise ValueError("unsafe SQL identifier: %r" % name)
    return '"%s"' % name


def _sql_backfill_column(Model, source_name, target_name):
    source_field = Model._fields.get(source_name)
    target_field = Model._fields.get(target_name)
    if not source_field or not target_field:
        return None
    if not _column_exists(Model._table, source_name) or not _column_exists(Model._table, target_name):
        return None
    if source_field.type not in _SQL_COPY_TYPES or target_field.type not in {"char", "text"}:
        return None
    table = _ident(Model._table)
    source = _ident(source_name)
    target = _ident(target_name)
    env.cr.execute(  # noqa: F821
        """
        UPDATE {table}
           SET {target} = NULLIF(({source})::text, '')
         WHERE COALESCE({target}, '') = ''
           AND COALESCE(({source})::text, '') <> ''
        """.format(
            table=table,
            source=source,
            target=target,
        )
    )
    return env.cr.rowcount  # noqa: F821


def _source_candidates(Model, entry):
    source_name = entry["source_field"]
    candidates = []
    if source_name.startswith("p1_visible_"):
        candidates.extend(MODEL_LABEL_SOURCE_OVERRIDES.get(Model._name, {}).get(entry["label"]) or [])
        candidates.extend(_MODEL_LABEL_SOURCE_CANDIDATES.get(Model._name, {}).get(entry["label"]) or [])
        candidates.extend(_GENERIC_LABEL_SOURCE_CANDIDATES.get(entry["label"]) or [])
    candidates.append(source_name)
    return [name for name in dict.fromkeys(candidates) if name in Model._fields and not name.startswith("p1_visible_")]


def _sql_backfill_contract_expense_parent_column(Model, source_name, target_name):
    if Model._name != "construction.contract.expense":
        return None
    if not _column_exists("construction_contract", source_name) or not _column_exists(Model._table, target_name):
        return None
    target_field = Model._fields.get(target_name)
    source_field = Model._fields.get(source_name)
    if not source_field or not target_field:
        return None
    if source_field.type not in _SQL_COPY_TYPES or target_field.type not in {"char", "text"}:
        return None
    env.cr.execute(  # noqa: F821
        """
        UPDATE construction_contract_expense child
           SET {target} = NULLIF((parent.{source})::text, '')
          FROM construction_contract parent
         WHERE child.contract_id = parent.id
           AND COALESCE(child.{target}, '') = ''
           AND COALESCE((parent.{source})::text, '') <> ''
        """.format(
            source=_ident(source_name),
            target=_ident(target_name),
        )
    )
    return env.cr.rowcount  # noqa: F821


def _orm_backfill_user_confirmed_formal_visible_fields():
    total_records = 0
    total_values = 0
    per_model = []
    for model_name, entries in USER_CONFIRMED_FORMAL_VISIBLE_FIELDS.items():
        if model_name not in env:  # noqa: F821
            per_model.append({"model": model_name, "skipped": True, "reason": "missing_model"})
            continue
        Model = env[model_name].sudo().with_context(active_test=False)  # noqa: F821
        entries = [
            entry
            for entry in entries
            if entry["source_field"] in Model._fields and entry["field_name"] in Model._fields
        ]
        if not entries:
            per_model.append({"model": model_name, "skipped": True, "reason": "missing_fields"})
            continue
        print(json.dumps({"backfill_model": model_name, "fields": len(entries), "phase": "start"}, ensure_ascii=False), flush=True)
        updated_records = 0
        updated_values = 0
        orm_entries = []
        for entry in entries:
            target_name = entry["field_name"]
            copied = 0
            copied_by_sql = False
            for source_name in _source_candidates(Model, entry):
                rowcount = _sql_backfill_column(Model, source_name, target_name)
                if rowcount is None:
                    rowcount = _sql_backfill_contract_expense_parent_column(Model, source_name, target_name)
                if rowcount is None:
                    continue
                copied += rowcount
                copied_by_sql = True
                if rowcount:
                    break
            if copied_by_sql:
                updated_values += copied
            else:
                orm_entries.append(entry)
        if orm_entries:
            last_id = 0
            batch_size = 200
            while True:
                records = Model.search([("id", ">", last_id)], limit=batch_size, order="id asc")
                if not records:
                    break
                last_id = records[-1].id
                for record in records:
                    vals = {}
                    for entry in orm_entries:
                        target_name = entry["field_name"]
                        if record[target_name]:
                            continue
                        value = _format_alias_value(record, entry["source_field"])
                        if value:
                            vals[target_name] = value
                    if vals:
                        record.with_context(tracking_disable=True, mail_create_nolog=True).write(vals)
                        updated_records += 1
                        updated_values += len(vals)
        env.cr.commit()  # noqa: F821
        total_records += updated_records
        total_values += updated_values
        per_model.append({"model": model_name, "records": updated_records, "values": updated_values})
        print(
            json.dumps(
                {"backfill_model": model_name, "records": updated_records, "values": updated_values, "phase": "done"},
                ensure_ascii=False,
            ),
            flush=True,
        )
    return {
        "name": "user_confirmed_formal_visible_fields",
        "updated_records": total_records,
        "updated_values": total_values,
        "models": per_model,
    }


updates = []

updates.append(
    _run(
        "contract_entry_user_time",
        """
        UPDATE construction_contract
           SET entry_user_text = COALESCE(NULLIF(entry_user_text, ''), NULLIF(legacy_visible_creator_name, '')),
               entry_time = COALESCE(entry_time, legacy_visible_created_time)
         WHERE COALESCE(legacy_visible_creator_name, '') <> ''
            OR legacy_visible_created_time IS NOT NULL
        """,
        required=[("construction_contract", ("entry_user_text", "entry_time", "legacy_visible_creator_name", "legacy_visible_created_time"))],
    )
)

updates.append(
    _run(
        "tax_deduction_source_created",
        """
        UPDATE sc_tax_deduction_registration
           SET source_created_by = COALESCE(NULLIF(source_created_by, ''), NULLIF(creator_name, '')),
               source_created_at = COALESCE(source_created_at, created_time)
         WHERE COALESCE(creator_name, '') <> ''
            OR created_time IS NOT NULL
        """,
        required=[("sc_tax_deduction_registration", ("source_created_by", "source_created_at", "creator_name", "created_time"))],
    )
)

updates.append(
    _run(
        "receipt_income_company_name",
        """
        UPDATE sc_receipt_income income
           SET legacy_company_name = company.name
          FROM res_company company
         WHERE income.company_id = company.id
           AND COALESCE(income.legacy_company_name, '') = ''
           AND COALESCE(company.name, '') <> ''
        """,
        required=[("sc_receipt_income", ("legacy_company_name", "company_id")), ("res_company", ("name",))],
    )
)

updates.append(
    _run(
        "expense_company_name_text",
        """
        UPDATE sc_expense_claim claim
           SET company_name_text = company.name
          FROM res_company company
         WHERE claim.company_id = company.id
           AND COALESCE(company.name, '') <> ''
           AND (
                COALESCE(claim.company_name_text, '') = ''
                OR claim.company_name_text IN ('公司直属项目', '系统默认公司')
           )
        """,
        required=[("sc_expense_claim", ("company_name_text", "company_id")), ("res_company", ("name",))],
    )
)

updates.append(
    _run(
        "expense_accepted_company_name",
        """
        UPDATE sc_expense_claim claim
           SET uc_formal_7eb96c495624 = company.name
          FROM res_company company
         WHERE claim.company_id = company.id
           AND COALESCE(company.name, '') <> ''
           AND (
                COALESCE(claim.uc_formal_7eb96c495624, '') = ''
                OR claim.uc_formal_7eb96c495624 = claim.company_name_text
           )
        """,
        required=[("sc_expense_claim", ("company_id", "company_name_text", "uc_formal_7eb96c495624")), ("res_company", ("name",))],
    )
)

updates.append(
    _run(
        "expense_adjustment_summary",
        """
        UPDATE sc_expense_claim
           SET summary = legacy_visible_adjustment_item
         WHERE COALESCE(legacy_visible_adjustment_item, '') <> ''
           AND (
                COALESCE(summary, '') = ''
                OR summary LIKE '关于%自动%'
                OR summary = expense_type
           )
        """,
        required=[("sc_expense_claim", ("summary", "expense_type", "legacy_visible_adjustment_item"))],
    )
)

updates.append(
    _run(
        "expense_visible_note",
        """
        UPDATE sc_expense_claim
           SET note = legacy_visible_note
         WHERE COALESCE(legacy_visible_note, '') <> ''
           AND (
                COALESCE(note, '') = ''
                OR note LIKE 'SCBS55 old visible surface mirror:%'
                OR note LIKE '[migration:%'
           )
        """,
        required=[("sc_expense_claim", ("note", "legacy_visible_note"))],
    )
)

updates.append(
    _run(
        "payment_request_note",
        """
        UPDATE payment_request
           SET note = legacy_visible_remark
         WHERE COALESCE(legacy_visible_remark, '') <> ''
           AND (
                COALESCE(note, '') = ''
                OR note LIKE '[migration:%'
                OR note LIKE 'SCBS55 old visible surface mirror:%'
           )
        """,
        required=[("payment_request", ("note", "legacy_visible_remark"))],
    )
)

updates.append(
    _run(
        "construction_diary_note",
        """
        UPDATE sc_construction_diary
           SET note = legacy_visible_08
         WHERE COALESCE(legacy_visible_08, '') <> ''
           AND (
                COALESCE(note, '') = ''
                OR note LIKE '直营项目用户验收合格数据迁入正式业务模型:%'
                OR note LIKE 'SCBS55 old visible surface mirror:%'
                OR note LIKE '[migration:%'
           )
        """,
        required=[("sc_construction_diary", ("note", "legacy_visible_08"))],
    )
)

updates.append(
    _run(
        "payment_request_legacy_account_text",
        """
        UPDATE payment_request
           SET legacy_payment_account_no = COALESCE(NULLIF(legacy_payment_account_no, ''), NULLIF(legacy_payee_account_no, '')),
               legacy_payment_account_name = COALESCE(NULLIF(legacy_payment_account_name, ''), NULLIF(legacy_payee_account_name, '')),
               actual_payee_unit = COALESCE(NULLIF(actual_payee_unit, ''), NULLIF(legacy_visible_actual_payee_unit, '')),
               payer_unit = COALESCE(NULLIF(payer_unit, ''), NULLIF(legacy_visible_payer_unit, ''), NULLIF(legacy_payment_account_name, '')),
               payment_account_name = COALESCE(NULLIF(payment_account_name, ''), NULLIF(legacy_payee_account_name, '')),
               payment_bank_name = COALESCE(NULLIF(payment_bank_name, ''), NULLIF(legacy_payee_bank_name, '')),
               payment_account_no = COALESCE(NULLIF(payment_account_no, ''), NULLIF(legacy_payee_account_no, ''), NULLIF(legacy_payment_account_no, '')),
               accepted_amount_uppercase = COALESCE(NULLIF(accepted_amount_uppercase, ''), NULLIF(legacy_visible_amount_uppercase, ''))
         WHERE COALESCE(legacy_payee_account_no, '') <> ''
            OR COALESCE(legacy_payee_account_name, '') <> ''
            OR COALESCE(legacy_payee_bank_name, '') <> ''
            OR COALESCE(legacy_visible_actual_payee_unit, '') <> ''
            OR COALESCE(legacy_visible_payer_unit, '') <> ''
            OR COALESCE(legacy_payment_account_name, '') <> ''
            OR COALESCE(legacy_payment_account_no, '') <> ''
            OR COALESCE(legacy_visible_amount_uppercase, '') <> ''
        """,
        required=[
            (
                "payment_request",
                (
                    "legacy_payment_account_no",
                    "legacy_payment_account_name",
                    "legacy_payee_account_no",
                    "legacy_payee_account_name",
                    "legacy_payee_bank_name",
                    "legacy_visible_actual_payee_unit",
                    "legacy_visible_payer_unit",
                    "actual_payee_unit",
                    "payer_unit",
                    "payment_account_name",
                    "payment_bank_name",
                    "payment_account_no",
                    "accepted_amount_uppercase",
                    "legacy_visible_amount_uppercase",
                ),
            )
        ],
    )
)

updates.append(
    _run(
        "material_rfq_contact",
        """
        UPDATE sc_material_rfq
           SET contact_name = COALESCE(NULLIF(contact_name, ''), NULLIF(legacy_visible_13, '')),
               contact_phone = COALESCE(NULLIF(contact_phone, ''), NULLIF(legacy_visible_14, ''))
         WHERE COALESCE(legacy_visible_13, '') <> ''
            OR COALESCE(legacy_visible_14, '') <> ''
        """,
        required=[("sc_material_rfq", ("contact_name", "contact_phone", "legacy_visible_13", "legacy_visible_14"))],
    )
)

updates.append(
    _run(
        "fuel_card_state_label",
        """
        UPDATE sc_legacy_fuel_card_fact
           SET document_state = CASE document_state
               WHEN '0' THEN '草稿'
               WHEN '1' THEN '审批中'
               WHEN '2' THEN '审核通过'
               WHEN '3' THEN '否决'
               ELSE document_state
           END
         WHERE document_state IN ('0', '1', '2', '3')
        """,
        required=[("sc_legacy_fuel_card_fact", ("document_state",))],
    )
)

updates.append(
    _run(
        "fuel_card_recharge_state_label",
        """
        UPDATE sc_legacy_fuel_card_recharge_fact
           SET document_state = CASE document_state
               WHEN '0' THEN '草稿'
               WHEN '1' THEN '审批中'
               WHEN '2' THEN '审核通过'
               WHEN '3' THEN '否决'
               ELSE document_state
           END
         WHERE document_state IN ('0', '1', '2', '3')
        """,
        required=[("sc_legacy_fuel_card_recharge_fact", ("document_state",))],
    )
)

updates.append(
    _run(
        "payment_request_legacy_approved_state",
        """
        UPDATE payment_request
           SET state = CASE
                   WHEN legacy_document_state IN ('-1', '已作废') THEN 'cancel'
                   WHEN legacy_document_state IN ('1', '审批中', '审核中') THEN 'approve'
                   WHEN legacy_document_state IN ('2', '审核通过') THEN 'approved'
                   ELSE state
               END
         WHERE (
                legacy_document_state IN ('-1', '已作废')
                OR
                legacy_document_state IN ('1', '审批中', '审核中')
                OR legacy_document_state IN ('2', '审核通过')
           )
           AND state = 'draft'
        """,
        required=[("payment_request", ("state", "legacy_document_state"))],
    )
)

updates.append(
    _run(
        "hr_payroll_legacy_visible_business_fields",
        """
        UPDATE sc_hr_payroll_document
           SET legacy_document_state = CASE legacy_document_state
                   WHEN '0' THEN '草稿'
                   WHEN '1' THEN '审批中'
                   WHEN '2' THEN '审核通过'
                   WHEN '3' THEN '否决'
                   ELSE COALESCE(NULLIF(legacy_document_state, ''), NULLIF(legacy_visible_01, ''))
               END,
               state = CASE
                   WHEN COALESCE(legacy_visible_01, legacy_document_state) IN ('2', '审核通过') AND state = 'draft'
                   THEN 'done'
                   ELSE state
               END,
               payer_unit = COALESCE(NULLIF(payer_unit, ''), NULLIF(legacy_visible_02, '')),
               payout_unit = COALESCE(NULLIF(payout_unit, ''), NULLIF(legacy_visible_02, ''), NULLIF(payer_unit, '')),
               description = CASE
                   WHEN COALESCE(legacy_visible_11, '') <> ''
                    AND COALESCE(description, '') = ''
                   THEN legacy_visible_11
                   ELSE description
               END,
               result_note = CASE
                   WHEN COALESCE(legacy_visible_11, '') <> ''
                    AND (
                        COALESCE(result_note, '') = ''
                        OR result_note LIKE '直营项目用户验收合格数据迁入正式业务模型:%'
                    )
                   THEN legacy_visible_11
                   ELSE result_note
               END
         WHERE COALESCE(legacy_visible_01, legacy_document_state, legacy_visible_02, legacy_visible_11, '') <> ''
        """,
        required=[
            (
                "sc_hr_payroll_document",
                (
                    "legacy_document_state",
                    "state",
                    "payer_unit",
                    "payout_unit",
                    "description",
                    "result_note",
                    "legacy_visible_01",
                    "legacy_visible_02",
                    "legacy_visible_11",
                ),
            )
        ],
    )
)

updates.append(_orm_backfill_user_confirmed_formal_visible_fields())

env.cr.commit()  # noqa: F821
print(json.dumps({"updates": updates}, ensure_ascii=False))
