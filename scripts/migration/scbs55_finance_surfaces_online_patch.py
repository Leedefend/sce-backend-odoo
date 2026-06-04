#!/usr/bin/env python3
"""Mirror old SCBS finance receipt/expense/account-transfer list surfaces."""

from __future__ import annotations

import gzip
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


SPECS = {
    24: {
        "path": "/tmp/scbs_55_old_live_full_rows_seq024_expense_reimburse.json.gz",
        "action_id": 874,
        "model": "sc.expense.claim",
        "surface": "online_old_scbs:CWGL_FYBX:list874",
        "table": "CWGL_FYBX",
        "child": "Id$CWGL_FYBX_CB",
        "labels": ["单据状态", "单据编号", "所属公司", "日期", "部门", "报销人", "报销类别", "事项说明", "报销金额", "收款人", "附件", "录入人", "录入时间"],
    },
    25: {
        "path": "/tmp/scbs_55_old_live_full_rows_seq025_receipt_income.json.gz",
        "action_id": 875,
        "model": "sc.receipt.income",
        "surface": "online_old_scbs:C_CWSFK_GSCWSR:list875",
        "table": "C_CWSFK_GSCWSR",
        "labels": ["单据状态", "项目名称", "单据编号", "填写人", "收款账户", "进账金额", "收入类别", "收款时间", "备注", "附件", "录入人", "录入时间"],
    },
    26: {
        "path": "/tmp/scbs_55_old_live_full_rows_seq026_company_expense.json.gz",
        "action_id": 876,
        "model": "sc.expense.claim",
        "surface": "online_old_scbs:C_CWSFK_GSCWZC:list876",
        "table": "C_CWSFK_GSCWZC",
        "labels": ["单据状态", "推送结果", "单据编号", "付款时间", "付款金额", "成本类别", "收款单位名称", "付款账户名称", "备注", "录入人", "录入时间", "附件"],
    },
    32: {
        "path": "/tmp/scbs_55_old_live_full_rows_seq032_account_transfer.json.gz",
        "action_id": 882,
        "model": "sc.fund.account.operation",
        "surface": "online_old_scbs:C_FKGL_ZHJZJWL:list882",
        "table": "C_FKGL_ZHJZJWL",
        "labels": ["单据状态", "项目名称", "单据编号", "发生时间", "账户号码", "收款账户", "金额", "转账类别", "事由", "备注", "附件", "录入人", "录入时间"],
    },
}


def clean(value: object) -> str:
    if value in (None, False):
        return ""
    text = re.sub(r"\s+", " ", str(value).replace("\u3000", " ").strip())
    return "" if text in {"False", "false", "None", "NULL"} else text


def parse_date(value: object):
    text = clean(value)
    if not text:
        return False
    try:
        return datetime.strptime(text[:10], "%Y-%m-%d").date()
    except ValueError:
        return False


def parse_dt(value: object):
    text = clean(value)
    if not text:
        return False
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(text[:19] if "%H" in fmt else text[:10], fmt)
        except ValueError:
            continue
    return False


def amount(value: object) -> float:
    text = clean(value)
    if not text:
        return 0.0
    try:
        return abs(float(text))
    except ValueError:
        return 0.0


def amount_text(value: object) -> str:
    number = amount(value)
    return ("%.2f" % number).rstrip("0").rstrip(".")


def state_label(value: object) -> str:
    text = clean(value)
    return {"-1": "已作废", "0": "未审核", "1": "审核中", "2": "审核通过", "3": "已驳回", "4": "已作废"}.get(text, text)


def ensure_payload_table() -> None:
    env.cr.execute(  # noqa: F821
        """
        CREATE TABLE IF NOT EXISTS sc_p1_legacy_visible_alias_payload (
            model varchar NOT NULL,
            res_id integer NOT NULL,
            payload jsonb NOT NULL DEFAULT '{}'::jsonb,
            write_date timestamp without time zone NOT NULL DEFAULT now(),
            PRIMARY KEY (model, res_id)
        )
        """
    )


def write_payload(record, payload: dict[str, str]) -> None:
    env.cr.execute(  # noqa: F821
        """
        INSERT INTO sc_p1_legacy_visible_alias_payload(model, res_id, payload, write_date)
        VALUES (%s, %s, %s::jsonb, now())
        ON CONFLICT (model, res_id)
        DO UPDATE SET payload = EXCLUDED.payload, write_date = now()
        """,
        [record._name, record.id, json.dumps(payload, ensure_ascii=False)],
    )


def safe_vals(model, vals: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in vals.items() if key in model._fields}


def project_for(row: dict[str, Any]):
    Project = env["project.project"].sudo().with_context(active_test=False)  # noqa: F821
    legacy_project_id = clean(row.get("XMID") or row.get("XMID$CWGL_FYBX_CB"))
    if legacy_project_id and "legacy_project_id" in Project._fields:
        project = Project.search([("legacy_project_id", "=", legacy_project_id)], limit=1)
        if project:
            return project
    name = clean(row.get("XMMC") or row.get("XMMC$CWGL_FYBX_CB"))
    if name:
        project = Project.search([("name", "ilike", name[:60])], limit=1)
        if project:
            return project
    return Project.search([], limit=1)


def row_key(seq: int, row: dict[str, Any], index: int) -> str:
    spec = SPECS[seq]
    header = clean(row.get("Id") or row.get("ID") or row.get("PID") or row.get("pid"))
    child_key = spec.get("child")
    if child_key:
        child = clean(row.get(child_key) or row.get("RowIndex") or index)
        return f"{header}:{child}"
    return header or str(index)


def visible_values(seq: int, row: dict[str, Any]) -> dict[str, str]:
    values = {
        "单据状态": state_label(row.get("DJZT")),
        "单据编号": clean(row.get("DJBH")),
        "所属公司": clean(row.get("SSGS")),
        "日期": clean(row.get("RQ"))[:10],
        "部门": clean(row.get("BM")),
        "报销人": clean(row.get("XM")),
        "报销类别": clean(row.get("BXLB$CWGL_FYBX_CB")),
        "事项说明": clean(row.get("SXSM$CWGL_FYBX_CB")),
        "报销金额": amount_text(row.get("JE$CWGL_FYBX_CB")),
        "收款人": clean(row.get("SKR")),
        "项目名称": clean(row.get("XMMC")),
        "填写人": clean(row.get("TXR")),
        "收款账户": clean(row.get("SKZH")),
        "进账金额": amount_text(row.get("JZJE")),
        "收入类别": clean(row.get("D_SCBSJS_CWSRLB") or row.get("SKLB")),
        "收款时间": clean(row.get("SKSJ"))[:10],
        "推送结果": clean(row.get("TSJG") or row.get("D_SCBSJS_IsPush")),
        "付款时间": clean(row.get("FKSJ"))[:10],
        "付款金额": amount_text(row.get("FKJE")),
        "成本类别": clean(row.get("D_SCBSJS_CWZCLB") or row.get("CBLBMC")),
        "收款单位名称": clean(row.get("SKDWMC")),
        "付款账户名称": clean(row.get("FKZHMC")),
        "发生时间": clean(row.get("FSSJ"))[:10],
        "账户号码": clean(row.get("ZCZH")),
        "金额": amount_text(row.get("JE")),
        "转账类别": clean(row.get("f_LB")),
        "事由": clean(row.get("SY")),
        "备注": clean(row.get("BZ") or row.get("BZ$CWGL_FYBX_CB")),
        "附件": clean(row.get("f_FJ") or row.get("FJ") or row.get("FJ$CWGL_FYBX_CB")),
        "录入人": clean(row.get("LRR")),
        "录入时间": clean(row.get("LRSJ")),
    }
    return {label: values.get(label, "") for label in SPECS[seq]["labels"]}


def import_expense(seq: int, rows: list[dict[str, Any]]) -> dict[str, Any]:
    spec = SPECS[seq]
    Claim = env["sc.expense.claim"].sudo().with_context(active_test=False)  # noqa: F821
    Currency = env.company.currency_id  # noqa: F821
    created = updated = 0
    seen: set[str] = set()
    for index, row in enumerate(rows, start=1):
        key = row_key(seq, row, index)
        seen.add(key)
        rec = Claim.search([("legacy_source_model", "=", spec["surface"]), ("legacy_record_id", "=", key)], limit=1)
        project = project_for(row)
        if seq == 24:
            claim_type = "expense"
            date = row.get("RQ$CWGL_FYBX_CB") or row.get("RQ")
            expense_type = clean(row.get("BXLB$CWGL_FYBX_CB") or "报销申请")
            summary = clean(row.get("SXSM$CWGL_FYBX_CB") or row.get("BZ") or row.get("DJBH"))
            money = row.get("JE$CWGL_FYBX_CB")
        else:
            claim_type = "expense"
            date = row.get("FKSJ")
            expense_type = clean(row.get("D_SCBSJS_CWZCLB") or row.get("CBLBMC") or "公司财务支出")
            summary = clean(row.get("BZ") or row.get("SKDWMC") or row.get("DJBH"))
            money = row.get("FKJE")
        vals = {
            "source_origin": "legacy",
            "claim_type": claim_type,
            "state": "legacy_confirmed",
            "project_id": project.id,
            "name": clean(row.get("DJBH")) or key,
            "date_claim": parse_date(date),
            "fill_date": parse_date(date),
            "expense_type": expense_type,
            "summary": summary,
            "amount": amount(money),
            "approved_amount": amount(money),
            "currency_id": Currency.id,
            "legacy_source_model": spec["surface"],
            "legacy_source_table": spec["table"],
            "legacy_record_id": key,
            "legacy_document_no": clean(row.get("DJBH")),
            "legacy_document_state": clean(row.get("DJZT")),
            "legacy_visible_document_state": clean(row.get("DJZT")),
            "legacy_visible_document_no": clean(row.get("DJBH")),
            "legacy_visible_date": parse_dt(date),
            "legacy_visible_project_name": clean(row.get("XMMC")),
            "legacy_visible_department": clean(row.get("BM")),
            "legacy_visible_summary": summary,
            "legacy_visible_amount": amount_text(money),
            "legacy_visible_payment_time": clean(row.get("FKSJ"))[:10],
            "legacy_visible_push_result": clean(row.get("TSJG") or row.get("D_SCBSJS_IsPush")),
            "legacy_visible_expense_type": expense_type,
            "legacy_visible_note": clean(row.get("BZ") or row.get("BZ$CWGL_FYBX_CB")),
            "creator_legacy_user_id": clean(row.get("LRRID")),
            "creator_name": clean(row.get("LRR")),
            "created_time": parse_dt(row.get("LRSJ")),
            "note": "SCBS55 old visible surface mirror: %s; old_key=%s; attachment=%s"
            % (spec["surface"], key, clean(row.get("FJ") or row.get("f_FJ"))),
            "active": True,
        }
        if rec:
            rec.write(safe_vals(Claim, vals))
            updated += 1
        else:
            rec = Claim.create(safe_vals(Claim, vals))
            created += 1
        write_payload(rec, visible_values(seq, row))
    stale = Claim.search([("legacy_source_model", "=", spec["surface"]), ("legacy_record_id", "not in", list(seen) or ["__none__"])])
    stale_count = len(stale)
    if stale:
        stale.write({"legacy_source_model": f"{spec['surface']}:hidden", "active": False})
    return created, updated, stale_count, Claim.search_count([("legacy_source_model", "=", spec["surface"])])


def import_receipt(seq: int, rows: list[dict[str, Any]]) -> dict[str, Any]:
    spec = SPECS[seq]
    Receipt = env["sc.receipt.income"].sudo().with_context(active_test=False)  # noqa: F821
    Currency = env.company.currency_id  # noqa: F821
    created = updated = 0
    seen: set[str] = set()
    for index, row in enumerate(rows, start=1):
        key = row_key(seq, row, index)
        seen.add(key)
        rec = Receipt.search([("legacy_source_model", "=", spec["surface"]), ("legacy_record_id", "=", key)], limit=1)
        project = project_for(row)
        vals = {
            "source_origin": "legacy",
            "source_kind": "receipt_income",
            "state": "legacy_confirmed",
            "project_id": project.id,
            "name": clean(row.get("DJBH")) or key,
            "date_receipt": parse_date(row.get("SKSJ")),
            "document_no": clean(row.get("DJBH")),
            "receipt_type": clean(row.get("D_SCBSJS_CWSRLB") or row.get("SKLB")),
            "legacy_receipt_type": clean(row.get("SKLB")),
            "income_category": clean(row.get("D_SCBSJS_CWSRLB") or row.get("SKLB")),
            "payment_method": clean(row.get("ZZFS")),
            "receiving_account": clean(row.get("SKZH")),
            "amount": amount(row.get("JZJE")),
            "currency_id": Currency.id,
            "legacy_source_model": spec["surface"],
            "legacy_source_table": spec["table"],
            "legacy_record_id": key,
            "legacy_document_state": clean(row.get("DJZT")),
            "legacy_attachment_ref": clean(row.get("FJ") or row.get("f_FJ")),
            "creator_legacy_user_id": clean(row.get("LRRID")),
            "creator_name": clean(row.get("LRR")),
            "created_time": parse_dt(row.get("LRSJ")),
            "note": clean(row.get("BZ")) or f"SCBS55 old visible surface mirror: {spec['surface']}; old_key={key}",
            "active": True,
        }
        if rec:
            rec.write(safe_vals(Receipt, vals))
            updated += 1
        else:
            rec = Receipt.create(safe_vals(Receipt, vals))
            created += 1
        write_payload(rec, visible_values(seq, row))
    stale = Receipt.search([("legacy_source_model", "=", spec["surface"]), ("legacy_record_id", "not in", list(seen) or ["__none__"])])
    stale_count = len(stale)
    if stale:
        stale.write({"legacy_source_model": f"{spec['surface']}:hidden", "active": False})
    return created, updated, stale_count, Receipt.search_count([("legacy_source_model", "=", spec["surface"])])


def import_fund_operation(seq: int, rows: list[dict[str, Any]]) -> dict[str, Any]:
    spec = SPECS[seq]
    Operation = env["sc.fund.account.operation"].sudo().with_context(active_test=False)  # noqa: F821
    Currency = env.company.currency_id  # noqa: F821
    created = updated = 0
    seen: set[str] = set()
    for index, row in enumerate(rows, start=1):
        key = row_key(seq, row, index)
        seen.add(key)
        rec = Operation.search([("legacy_source_model", "=", spec["surface"]), ("legacy_record_id", "=", key)], limit=1)
        vals = {
            "name": clean(row.get("DJBH")) or key,
            "operation_type": "balance_adjustment",
            "operation_date": parse_date(row.get("FSSJ")),
            "project_id": project_for(row).id,
            "company_id": env.company.id,  # noqa: F821
            "currency_id": Currency.id,
            "amount": amount(row.get("JE")),
            "before_balance": 0.0,
            "after_balance": amount(row.get("JE")),
            "operation_reason": clean(row.get("SY") or row.get("BZ") or "账户间资金往来"),
            "state": "done",
            "note": clean(row.get("BZ")) or f"SCBS55 old visible surface mirror: {spec['surface']}; old_key={key}",
            "legacy_source_model": spec["surface"],
            "legacy_source_table": spec["table"],
            "legacy_record_id": key,
            "legacy_document_state": clean(row.get("DJZT")),
            "legacy_visible_document_no": clean(row.get("DJBH")),
            "legacy_visible_project_name": clean(row.get("XMMC")),
            "legacy_visible_account_name": clean(row.get("ZCZH")),
            "legacy_visible_counterparty_account_name": clean(row.get("SKZH")),
            "legacy_visible_transfer_type": clean(row.get("f_LB")),
            "legacy_visible_reason": clean(row.get("SY")),
            "legacy_visible_note": clean(row.get("BZ")),
            "creator_legacy_user_id": clean(row.get("LRRID")),
            "creator_name": clean(row.get("LRR")),
            "created_time": parse_dt(row.get("LRSJ")),
            "active": True,
        }
        if rec:
            rec.write(safe_vals(Operation, vals))
            updated += 1
        else:
            rec = Operation.create(safe_vals(Operation, vals))
            created += 1
        write_payload(rec, visible_values(seq, row))
    stale = Operation.search([("legacy_source_model", "=", spec["surface"]), ("legacy_record_id", "not in", list(seen) or ["__none__"])])
    stale_count = len(stale)
    if stale:
        stale.write({"legacy_source_model": f"{spec['surface']}:hidden", "active": False})
    return created, updated, stale_count, Operation.search_count([("legacy_source_model", "=", spec["surface"])])


ensure_payload_table()
Action = env["ir.actions.act_window"].sudo()  # noqa: F821
results = []
for seq in sorted(SPECS):
    spec = SPECS[seq]
    with gzip.open(Path(spec["path"]), "rt", encoding="utf-8") as handle:
        rows = json.load(handle)["rows"]
    if seq in (24, 26):
        created, updated, stale_hidden, final_count = import_expense(seq, rows)
    elif seq == 25:
        created, updated, stale_hidden, final_count = import_receipt(seq, rows)
    elif seq == 32:
        created, updated, stale_hidden, final_count = import_fund_operation(seq, rows)
    domain = [("legacy_source_model", "=", spec["surface"])]
    action = Action.browse(spec["action_id"]).exists()
    if action:
        action.write({"domain": repr(domain)})
    results.append(
        {
            "seq": seq,
            "surface": spec["surface"],
            "old": len(rows),
            "created": created,
            "updated": updated,
            "stale_hidden": stale_hidden,
            "final_count": final_count,
            "domain": repr(domain),
            "status": "OK" if final_count == len(rows) else "COUNT_MISMATCH",
        }
    )
env.cr.commit()  # noqa: F821
print(json.dumps({"surfaces": results}, ensure_ascii=False, indent=2, sort_keys=True))
