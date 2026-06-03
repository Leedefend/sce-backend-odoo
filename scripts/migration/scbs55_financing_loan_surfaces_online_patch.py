#!/usr/bin/env python3
"""Mirror old SCBS borrowing/repayment list surfaces at old page grain."""

from __future__ import annotations

import gzip
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any


SPECS = {
    22: {
        "path": "/tmp/scbs_55_old_live_full_rows_seq022_借款申请.json.gz",
        "action_id": 872,
        "model": "sc.financing.loan",
        "surface": "online_old_scbs:BGGL_JHK_JKSQ:list872",
        "table": "BGGL_JHK_JKSQ",
        "labels": [
            "单据状态", "项目名称", "单据编号", "申请部门", "申请时间", "申请人", "是否预算内", "实际借款金额",
            "主要资金使用安排", "收款人", "收款账户", "开户银行", "公司名称", "备注", "付款单位", "收款单位",
            "往来单位名称", "往来单位账户", "借款账号", "实际批复金额", "申请金额", "预计归还时间", "借款类型",
            "附件", "录入人", "录入时间",
        ],
    },
    23: {
        "path": "/tmp/scbs_55_old_live_full_rows_seq023_还款登记.json.gz",
        "action_id": 873,
        "model": "sc.financing.loan",
        "surface": "online_old_scbs:BGGL_JHK_HKDJ:list873",
        "table": "BGGL_JHK_HKDJ",
        "labels": ["项目名称", "单据状态", "单据编号", "申请部门", "申请时间", "申请人", "是否预算内", "借款金额", "往来单位名称", "附件", "录入人", "录入时间"],
    },
    27: {
        "path": "/tmp/scbs_55_old_live_full_rows_seq027_承包人还项目款.json.gz",
        "action_id": 896,
        "model": "sc.expense.claim",
        "surface": "online_old_scbs:ZJGL_ZCDFSZ_FXJK_HK:list896",
        "table": "ZJGL_ZCDFSZ_FXJK_HK",
        "labels": ["单据状态", "单据编号", "项目名称", "借款人", "借款金额", "还款金额", "用途", "借款利率", "利息", "还款时间", "备注", "附件", "录入人", "录入时间"],
    },
    28: {
        "path": "/tmp/scbs_55_old_live_full_rows_seq028_承包人借项目款.json.gz",
        "action_id": 878,
        "model": "sc.financing.loan",
        "surface": "online_old_scbs:ZJGL_ZCDFSZ_FXJK_JK:list878",
        "table": "ZJGL_ZCDFSZ_FXJK_JK",
        "labels": ["单据状态", "单据编号", "项目名称", "借款人", "借款金额", "用途", "约定期限", "借款利息", "备注", "附件", "录入人", "录入时间"],
    },
    30: {
        "path": "/tmp/scbs_55_old_live_full_rows_seq030_扣款单.json.gz",
        "action_id": 880,
        "model": "sc.tax.deduction.registration",
        "surface": "online_old_scbs:C_ZFSQGL_KKD:list880",
        "table": "C_ZFSQGL_KKD",
        "labels": ["单据状态", "单据编号", "项目名称", "扣款单位", "扣款金额", "扣款事由", "单据日期", "附件", "录入人", "录入时间"],
    },
    37: {
        "path": "/tmp/scbs_55_old_live_full_rows_seq037_项目借公司款登记.json.gz",
        "action_id": 887,
        "model": "sc.financing.loan",
        "surface": "online_old_scbs:ZJGL_ZJSZ_DKGL_DKDJ:list887",
        "table": "ZJGL_ZJSZ_DKGL_DKDJ",
        "labels": ["单据状态", "单据编号", "项目名称", "贷款金额", "到期利息", "还款金额", "未还款金额", "贷款日期", "还款日期", "贷款天数", "年利率", "贷款账户", "贷款银行", "备注", "附件", "录入人", "录入时间"],
    },
    38: {
        "path": "/tmp/scbs_55_old_live_full_rows_seq038_项目还公司款登记.json.gz",
        "action_id": 888,
        "model": "sc.financing.loan",
        "surface": "online_old_scbs:ZJGL_ZJSZ_DKGL_HKDJ:list888",
        "table": "ZJGL_ZJSZ_DKGL_HKDJ",
        "labels": ["单据状态", "单据编号", "项目名称", "还款金额", "实际还款天数", "实际年利率", "贷款利息", "贷款银行", "贷款账户", "还款账户", "填写人", "备注", "附件", "录入人", "录入时间"],
    },
}


def clean(value: object) -> str:
    if value is None or value is False:
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


def visible_number(value: object) -> str:
    text = clean(value)
    if not text:
        return ""
    try:
        number = float(text)
    except ValueError:
        return text
    return ("%.2f" % number).rstrip("0").rstrip(".")


def visible_attachment(value: object) -> str:
    return "历史附件" if clean(value) else ""


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


def project_for(row: dict[str, Any]):
    Project = env["project.project"].sudo().with_context(active_test=False)  # noqa: F821
    legacy_project_id = clean(row.get("XMID"))
    if legacy_project_id and "legacy_project_id" in Project._fields:
        project = Project.search([("legacy_project_id", "=", legacy_project_id)], limit=1)
        if project:
            return project
    name = clean(row.get("XMMC"))
    if name:
        project = Project.search([("name", "ilike", name[:60])], limit=1)
        if project:
            return project
    return Project.search([], limit=1)


def row_key(row: dict[str, Any], index: int) -> str:
    return clean(row.get("Id") or row.get("ID") or row.get("pid")) or str(index)


def visible_values(seq: int, row: dict[str, Any]) -> dict[str, str]:
    values = {
        "单据状态": state_label(row.get("DJZT")),
        "项目名称": clean(row.get("XMMC")),
        "单据编号": clean(row.get("DJBH")),
        "申请部门": clean(row.get("SQBM")),
        "申请时间": clean(row.get("SQSJ")),
        "申请人": clean(row.get("SQR")),
        "是否预算内": clean(row.get("SFYSN")),
        "实际借款金额": visible_number(row.get("JKJE")),
        "主要资金使用安排": clean(row.get("ZYZJSYAP")),
        "收款人": clean(row.get("SKR")),
        "收款账户": clean(row.get("SKZH")),
        "开户银行": clean(row.get("KHYH")),
        "公司名称": clean(row.get("GSMC")),
        "备注": clean(row.get("BZ")),
        "付款单位": clean(row.get("FKDW")),
        "收款单位": clean(row.get("SKDW")),
        "往来单位名称": clean(row.get("WLDWMC")),
        "往来单位账户": clean(row.get("WLDWZH")),
        "借款账号": clean(row.get("ZKZH")),
        "实际批复金额": visible_number(row.get("SJPFJE")),
        "申请金额": visible_number(row.get("SQJE")),
        "预计归还时间": clean(row.get("YJGHSJ")),
        "借款类型": clean(row.get("FKFSMC")),
        "借款人": clean(row.get("JKR") or row.get("SQR")),
        "借款金额": visible_number(row.get("JKJE") or row.get("DKJE")),
        "还款金额": visible_number(row.get("HKJE")),
        "用途": clean(row.get("YT") or row.get("ZYZJSYAP")),
        "借款利率": visible_number(row.get("JKLX")),
        "利息": visible_number(row.get("LX")),
        "还款时间": clean(row.get("HKSJ")),
        "约定期限": clean(row.get("YDQX")),
        "借款利息": visible_number(row.get("JKLX")),
        "扣款单位": clean(row.get("KKDW")),
        "扣款金额": visible_number(row.get("KKJE")),
        "扣款事由": clean(row.get("KKSY")),
        "单据日期": clean(row.get("DJRQ")),
        "贷款金额": visible_number(row.get("DKJE")),
        "到期利息": visible_number(row.get("D_SCBSJS_DQLX")),
        "未还款金额": visible_number(row.get("HKSYJE")),
        "贷款日期": clean(row.get("DKRQ")),
        "还款日期": clean(row.get("HKRQ")),
        "贷款天数": visible_number(row.get("DKSJ")),
        "年利率": visible_number(row.get("DKLL")),
        "贷款账户": clean(row.get("DKZH")),
        "贷款银行": clean(row.get("DKYH")),
        "实际还款天数": visible_number(row.get("D_SCBSJS_SJHKTS")),
        "实际年利率": visible_number(row.get("D_SCBSJS_SJNLL")),
        "贷款利息": visible_number(row.get("DKLX")),
        "还款账户": clean(row.get("HKZH")),
        "填写人": clean(row.get("TXR")),
        "附件": visible_attachment(row.get("f_FJ") or row.get("FJ")),
        "录入人": clean(row.get("LRR")),
        "录入时间": clean(row.get("LRSJ")),
    }
    return {label: values.get(label, "") for label in SPECS[seq]["labels"]}


def loan_vals(seq: int, spec: dict[str, Any], row: dict[str, Any], key: str) -> dict[str, Any]:
    project = project_for(row)
    money = row.get("HKJE") if seq in (23, 38) else row.get("JKJE") or row.get("DKJE")
    date_value = row.get("SQSJ") or row.get("TXRQ") or row.get("DKRQ") or row.get("HKRQ") or row.get("LRSJ")
    return {
        "source_origin": "legacy",
        "loan_type": "borrowing_request",
        "direction": "borrowed_fund",
        "state": "done",
        "project_id": project.id,
        "name": clean(row.get("DJBH")) or key,
        "document_no": clean(row.get("DJBH")),
        "document_date": parse_date(date_value),
        "due_date": parse_date(row.get("YJGHSJ") or row.get("YDQX") or row.get("HKRQ")),
        "amount": amount(money),
        "currency_id": env.company.currency_id.id,  # noqa: F821
        "purpose": clean(row.get("ZYZJSYAP") or row.get("YT") or row.get("BZ")),
        "rate_label": clean(row.get("JKLX") or row.get("DKLL") or row.get("D_SCBSJS_SJNLL")),
        "extra_ref": clean(row.get("ZKZH") or row.get("DKZH") or row.get("HKZH")),
        "legacy_source_model": spec["surface"],
        "legacy_source_table": spec["table"],
        "legacy_record_id": key,
        "legacy_document_state": clean(row.get("DJZT")),
        "legacy_counterparty_id": clean(row.get("WLDWID")),
        "legacy_counterparty_name": clean(row.get("WLDWMC") or row.get("JKR")),
        "legacy_amount_field": "HKJE" if seq in (23, 38) else "JKJE/DKJE",
        "legacy_attachment_ref": clean(row.get("f_FJ") or row.get("FJ")),
        "creator_legacy_user_id": clean(row.get("LRRID")),
        "creator_name": clean(row.get("LRR")),
        "created_time": parse_dt(row.get("LRSJ")),
        "legacy_visible_project_name": clean(row.get("XMMC")),
        "legacy_visible_request_department": clean(row.get("SQBM")),
        "legacy_visible_request_time": parse_dt(row.get("SQSJ")),
        "legacy_visible_applicant": clean(row.get("SQR") or row.get("JKR")),
        "legacy_visible_budget_included": clean(row.get("SFYSN")),
        "legacy_visible_actual_loan_amount": visible_number(row.get("JKJE") or row.get("DKJE")),
        "legacy_visible_fund_usage_plan": clean(row.get("ZYZJSYAP") or row.get("YT")),
        "legacy_visible_payee": clean(row.get("SKR")),
        "legacy_visible_receipt_account": clean(row.get("SKZH")),
        "legacy_visible_bank_name": clean(row.get("KHYH")),
        "legacy_visible_company_name": clean(row.get("GSMC")),
        "legacy_visible_note": clean(row.get("BZ")),
        "legacy_visible_payer_unit": clean(row.get("FKDW")),
        "legacy_visible_receiver_unit": clean(row.get("SKDW")),
        "legacy_visible_counterparty_name": clean(row.get("WLDWMC")),
        "legacy_visible_counterparty_account": clean(row.get("WLDWZH")),
        "legacy_visible_loan_account": clean(row.get("ZKZH") or row.get("DKZH")),
        "legacy_visible_approved_amount": visible_number(row.get("SJPFJE")),
        "legacy_visible_request_amount": visible_number(row.get("SQJE")),
        "legacy_visible_expected_return_time": parse_dt(row.get("YJGHSJ") or row.get("YDQX")),
        "legacy_visible_loan_type": clean(row.get("FKFSMC")),
        "legacy_visible_loan_bank": clean(row.get("DKYH")),
        "legacy_visible_due_interest": visible_number(row.get("D_SCBSJS_DQLX")),
        "legacy_visible_repayment_amount": visible_number(row.get("HKJE")),
        "legacy_visible_unpaid_amount": visible_number(row.get("HKSYJE")),
        "legacy_visible_loan_date": parse_dt(row.get("DKRQ")),
        "legacy_visible_repayment_date": parse_dt(row.get("HKRQ")),
        "legacy_visible_loan_days": visible_number(row.get("DKSJ")),
        "legacy_visible_annual_rate": visible_number(row.get("DKLL")),
        "legacy_visible_repayment_account": clean(row.get("HKZH")),
        "legacy_visible_writer": clean(row.get("TXR")),
        "legacy_visible_actual_repayment_days": visible_number(row.get("D_SCBSJS_SJHKTS")),
        "legacy_visible_actual_annual_rate": visible_number(row.get("D_SCBSJS_SJNLL")),
        "legacy_visible_loan_interest": visible_number(row.get("DKLX") or row.get("JKLX")),
        "note": "SCBS55 old visible surface mirror: %s; old_key=%s; attachment=%s" % (spec["surface"], key, clean(row.get("f_FJ") or row.get("FJ"))),
        "active": True,
    }


def expense_vals(spec: dict[str, Any], row: dict[str, Any], key: str) -> dict[str, Any]:
    project = project_for(row)
    return {
        "source_origin": "legacy",
        "claim_type": "project_company_repay",
        "state": "done",
        "project_id": project.id,
        "name": clean(row.get("DJBH")) or key,
        "date_claim": parse_date(row.get("HKSJ") or row.get("TXRQ") or row.get("LRSJ")),
        "fill_date": parse_date(row.get("TXRQ") or row.get("HKSJ") or row.get("LRSJ")),
        "expense_type": "承包人还项目款",
        "summary": clean(row.get("YT") or row.get("BZ") or row.get("JKR")),
        "amount": amount(row.get("HKJE")),
        "approved_amount": amount(row.get("HKJE")),
        "currency_id": env.company.currency_id.id,  # noqa: F821
        "legacy_source_model": spec["surface"],
        "legacy_source_table": spec["table"],
        "legacy_record_id": key,
        "legacy_document_no": clean(row.get("DJBH")),
        "legacy_document_state": clean(row.get("DJZT")),
        "legacy_visible_document_state": clean(row.get("DJZT")),
        "legacy_visible_document_no": clean(row.get("DJBH")),
        "legacy_visible_project_name": clean(row.get("XMMC")),
        "legacy_visible_summary": clean(row.get("YT")),
        "legacy_visible_amount": visible_number(row.get("HKJE")),
        "legacy_visible_note": clean(row.get("BZ")),
        "legacy_visible_borrower": clean(row.get("JKR")),
        "legacy_visible_loan_amount": visible_number(row.get("JKJE")),
        "legacy_visible_repayment_amount": visible_number(row.get("HKJE")),
        "legacy_visible_loan_rate": visible_number(row.get("JKLX")),
        "legacy_visible_interest": visible_number(row.get("LX")),
        "legacy_visible_repayment_time": parse_dt(row.get("HKSJ")),
        "creator_legacy_user_id": clean(row.get("LRRID")),
        "creator_name": clean(row.get("LRR")),
        "created_time": parse_dt(row.get("LRSJ")),
        "note": "SCBS55 old visible surface mirror: %s; old_key=%s; attachment=%s" % (spec["surface"], key, clean(row.get("f_FJ") or row.get("FJ"))),
        "active": True,
    }


def tax_vals(spec: dict[str, Any], row: dict[str, Any], key: str) -> dict[str, Any]:
    project = project_for(row)
    return {
        "source_origin": "legacy",
        "state": "deducted",
        "project_id": project.id,
        "name": clean(row.get("DJBH")) or key,
        "document_no": clean(row.get("DJBH")),
        "document_date": parse_date(row.get("DJRQ") or row.get("LRSJ")),
        "deduction_confirm_date": parse_date(row.get("DJRQ") or row.get("LRSJ")),
        "legacy_visible_project_name": clean(row.get("XMMC")),
        "partner_name": clean(row.get("KKDW")),
        "deduction_amount": amount(row.get("KKJE")),
        "deduction_tax_amount": amount(row.get("KKJE")),
        "currency_id": env.company.currency_id.id,  # noqa: F821
        "legacy_source_model": spec["surface"],
        "legacy_source_table": spec["table"],
        "legacy_record_id": key,
        "legacy_document_state": clean(row.get("DJZT")),
        "creator_legacy_user_id": clean(row.get("LRRID")),
        "creator_name": clean(row.get("LRR")),
        "created_time": parse_dt(row.get("LRSJ")),
        "note": "SCBS55 old visible surface mirror: %s; old_key=%s; reason=%s; attachment=%s"
        % (spec["surface"], key, clean(row.get("KKSY")), clean(row.get("f_FJ") or row.get("FJ"))),
        "active": True,
    }


def import_surface(seq: int) -> dict[str, Any]:
    spec = SPECS[seq]
    data = json.load(gzip.open(spec["path"], "rt", encoding="utf-8"))
    rows = data.get("rows") or []
    Model = env[spec["model"]].sudo().with_context(active_test=False)  # noqa: F821
    created = updated = 0
    seen: set[str] = set()
    for index, row in enumerate(rows, start=1):
        key = row_key(row, index)
        seen.add(key)
        rec = Model.search([("legacy_source_model", "=", spec["surface"]), ("legacy_record_id", "=", key)], limit=1)
        if seq == 27:
            vals = expense_vals(spec, row, key)
        elif seq == 30:
            vals = tax_vals(spec, row, key)
        else:
            vals = loan_vals(seq, spec, row, key)
        if rec:
            rec.write(vals)
            updated += 1
        else:
            rec = Model.create(vals)
            created += 1
        write_payload(rec, visible_values(seq, row))
    stale = Model.search([("legacy_source_model", "=", spec["surface"]), ("legacy_record_id", "not in", list(seen) or ["__none__"])])
    stale_count = len(stale)
    if stale:
        stale.write({"legacy_source_model": f"{spec['surface']}:hidden", "active": False})
    return {
        "seq": seq,
        "action_id": spec["action_id"],
        "model": spec["model"],
        "surface": spec["surface"],
        "old_rows": len(rows),
        "created": created,
        "updated": updated,
        "stale_hidden": stale_count,
        "new_visible": Model.search_count([("legacy_source_model", "=", spec["surface"])]),
    }


def selected_sequences() -> list[int]:
    raw = os.getenv("SCBS55_FINANCING_SURFACE_SEQS") or os.getenv("SCBS55_FINANCING_SURFACE_SEQ") or ""
    if not raw:
        return sorted(SPECS)
    seqs: list[int] = []
    for item in re.split(r"[,，;；\s]+", raw):
        if not item:
            continue
        seq = int(item)
        if seq not in SPECS:
            raise RuntimeError({"unsupported_financing_surface_seq": seq, "supported": sorted(SPECS)})
        seqs.append(seq)
    return sorted(set(seqs))


ensure_payload_table()
results = [import_surface(seq) for seq in selected_sequences()]
out = Path("/tmp/scbs55_financing_loan_surfaces_online_patch_result.json")
out.write_text(json.dumps({"results": results}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
env.cr.commit()  # noqa: F821
print(json.dumps({"results": results, "output": str(out)}, ensure_ascii=False, indent=2))
