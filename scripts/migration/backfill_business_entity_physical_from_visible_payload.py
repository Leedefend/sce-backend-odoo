#!/usr/bin/env python3
"""Backfill business entity visible fields from the preserved alias payload."""

from __future__ import annotations

import json
import re


FIELD_COLUMNS = {
    "legacy_visible_document_state": "varchar",
    "legacy_visible_push_result": "varchar",
    "legacy_visible_cooperation_type": "varchar",
    "legacy_visible_bank_name": "varchar",
    "legacy_visible_account_no": "varchar",
    "legacy_visible_account_holder": "varchar",
    "legacy_visible_social_credit_code": "varchar",
    "legacy_visible_main_tax_rate": "varchar",
    "legacy_visible_receipt_amount": "varchar",
    "legacy_visible_payment_amount": "varchar",
    "document_state_text": "varchar",
    "push_result": "varchar",
    "project_name": "varchar",
    "cooperation_type": "varchar",
    "bank_name": "varchar",
    "bank_account_no": "varchar",
    "bank_account_holder": "varchar",
    "social_credit_code": "varchar",
    "main_tax_rate": "varchar",
    "receipt_amount": "numeric",
    "payment_amount": "numeric",
    "entry_user_name": "varchar",
    "entry_time": "timestamp",
}

LABEL_FIELDS = {
    "单据状态": "legacy_visible_document_state",
    "推送结果": "legacy_visible_push_result",
    "合作类型": "legacy_visible_cooperation_type",
    "开户银行": "legacy_visible_bank_name",
    "账号": "legacy_visible_account_no",
    "开户账号": "legacy_visible_account_no",
    "银行账号": "legacy_visible_account_no",
    "开户姓名": "legacy_visible_account_holder",
    "统一社会信用代码": "legacy_visible_social_credit_code",
    "主税率": "legacy_visible_main_tax_rate",
    "收款金额": "legacy_visible_receipt_amount",
    "付款金额": "legacy_visible_payment_amount",
}

FORMAL_LABEL_FIELDS = {
    "单据状态": "document_state_text",
    "推送结果": "push_result",
    "项目名称": "project_name",
    "合作类型": "cooperation_type",
    "开户银行": "bank_name",
    "账号": "bank_account_no",
    "开户账号": "bank_account_no",
    "银行账号": "bank_account_no",
    "开户姓名": "bank_account_holder",
    "统一社会信用代码": "social_credit_code",
    "主税率": "main_tax_rate",
    "录入人": "entry_user_name",
}


def clean(value: object) -> str:
    if value in (None, False):
        return ""
    text = re.sub(r"\s+", " ", str(value).replace("\u3000", " ").strip())
    return "" if text in {"False", "false", "None", "NULL"} else text


def parse_amount(value: object):
    text = clean(value)
    if not text:
        return None
    normalized = re.sub(r"[^0-9.\-]", "", text)
    if normalized in {"", "-", ".", "-."}:
        return None
    try:
        return float(normalized)
    except ValueError:
        return None


def ensure_columns() -> None:
    for field_name, column_type in FIELD_COLUMNS.items():
        env.cr.execute(f"ALTER TABLE sc_business_entity ADD COLUMN IF NOT EXISTS {field_name} {column_type}")  # noqa: F821


def main() -> None:
    ensure_columns()
    env.cr.execute("SELECT to_regclass('public.sc_p1_legacy_visible_alias_payload')")  # noqa: F821
    if not env.cr.fetchone()[0]:  # noqa: F821
        print(json.dumps({"status": "SKIP", "reason": "payload_table_missing"}, ensure_ascii=False))
        return

    env.cr.execute(  # noqa: F821
        """
        SELECT e.id, p.payload
          FROM sc_business_entity e
          JOIN sc_p1_legacy_visible_alias_payload p
            ON p.model = 'sc.business.entity'
           AND p.res_id = e.id
        """
    )
    rows = env.cr.fetchall()  # noqa: F821
    updates = {field_name: 0 for field_name in FIELD_COLUMNS}
    updated_rows = 0
    for record_id, payload in rows:
        if not isinstance(payload, dict):
            continue
        values = {field_name: "" for field_name in FIELD_COLUMNS}
        for label, field_name in LABEL_FIELDS.items():
            value = clean(payload.get(label))
            if value and not values[field_name]:
                values[field_name] = value
        for label, field_name in FORMAL_LABEL_FIELDS.items():
            value = clean(payload.get(label))
            if value and not values[field_name]:
                values[field_name] = value
        values["receipt_amount"] = parse_amount(payload.get("收款金额"))
        values["payment_amount"] = parse_amount(payload.get("付款金额"))
        values["entry_time"] = clean(payload.get("录入时间")) or None
        assignments = []
        params = []
        for field_name, value in values.items():
            if value in (None, ""):
                continue
            assignments.append(f"{field_name} = %s")
            params.append(value)
            updates[field_name] += 1
        if not assignments:
            continue
        params.append(record_id)
        env.cr.execute(  # noqa: F821
            "UPDATE sc_business_entity SET %s WHERE id = %%s" % ", ".join(assignments),
            params,
        )
        updated_rows += 1
    if updated_rows:
        env.cr.commit()  # noqa: F821
    print(json.dumps({"status": "PASS", "candidate_rows": len(rows), "updated_rows": updated_rows, "touched_fields": updates}, ensure_ascii=False, sort_keys=True))


main()
