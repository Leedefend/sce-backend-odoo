#!/usr/bin/env python3
"""Mirror remaining old SCBS list surfaces with page-specific source markers."""

from __future__ import annotations

import gzip
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


SPECS = {
    5: {
        "path": "/tmp/scbs_55_old_live_full_rows_seq005_请假_休假审批单.json.gz",
        "model": "sc.office.admin.document",
        "surface": "online_old_scbs:BGGL_HBZJ_XZD_QJXJSPB:list857",
        "table": "BGGL_HBZJ_XZD_QJXJSPB",
        "labels": ["单据状态", "单据编号", "项目名称", "申请人姓名", "所在部门", "请假天数", "请假类型", "请假时间", "销假时间", "备注", "请假时长", "录入人", "录入时间"],
    },
    6: {
        "path": "/tmp/scbs_55_old_live_full_rows_seq006_印章使用审批表.json.gz",
        "model": "sc.office.admin.document",
        "surface": "online_old_scbs:BGGL_XZD_YZSYSPB:list858",
        "table": "BGGL_XZD_YZSYSPB",
        "labels": ["单据状态", "单据编号", "用印时间", "用印部门", "用印申请人", "用印部门负责人签字", "用印种类", "用印文本名称及文号", "经办人签字", "领导签字", "份数", "备注", "归还时间", "合同金额", "合同编号", "所属公司", "使用印章公司", "是否外带", "附件", "录入人", "录入时间"],
    },
    15: {
        "path": "/tmp/scbs_55_old_live_full_rows_seq015_借阅申请.json.gz",
        "model": "sc.document.admin.document",
        "surface": "online_old_scbs:ZJGL_ZSJYGL:list865",
        "table": "ZJGL_ZSJYGL",
        "labels": ["单据状态", "单据编号", "借阅项目名称", "证件名称", "申请日期", "借阅部门或项目部名称", "借阅人", "联系方式", "借阅形式", "借阅日期", "负责人", "归还申请日期", "申请归还时间", "是否归还", "确认归还时间", "归还日期", "附件", "录入人", "录入时间", "备注", "修改人", "修改日期", "修改备注", "审定人", "审定时间", "审定意见"],
    },
    16: {
        "path": "/tmp/scbs_55_old_live_full_rows_seq016_投标报名管理.json.gz",
        "model": "tender.bid",
        "surface": "online_old_scbs:P_ZTB_GCBMGL:list866",
        "table": "P_ZTB_GCBMGL",
        "labels": ["单据状态", "推送结果", "单据编号", "开标时间", "项目名称", "登记时间", "录入人"],
    },
    17: {
        "path": "/tmp/scbs_55_old_live_full_rows_seq017_投标报名费申请.json.gz",
        "model": "tender.doc.purchase",
        "surface": "online_old_scbs:BGGL_ZTBJHT_TBBM_TBBMFSQ:list895",
        "table": "BGGL_ZTBJHT_TBBM_TBBMFSQ",
        "labels": ["单据状态", "项目名称", "单据编号", "申请人", "申请日期", "收款账号", "开户行", "金额", "备注", "收款人", "付款方式", "附件", "录入人", "录入时间"],
    },
    35: {
        "path": "/tmp/scbs_55_old_live_full_rows_seq035_到款确认表.json.gz",
        "model": "sc.legacy.fund.confirmation.header",
        "surface": "online_old_scbs:ZJGL_SZQR_DKQRB:list885",
        "table": "ZJGL_SZQR_DKQRB",
        "labels": ["单据状态", "单据编号", "时间", "项目名称", "期数", "本期收款", "本期代扣代缴合计", "本期拨付金额合计", "附件", "施工单位", "合同金额", "目前形象进度", "累计开票金额", "上期留存余额", "录入人", "录入时间"],
    },
    36: {
        "path": "/tmp/scbs_55_old_live_full_rows_seq036_资金日报表.json.gz",
        "model": "sc.legacy.fund.daily.line",
        "surface": "online_old_scbs:D_SCBSJS_ZJGL_ZJSZ_ZJRBB:list886",
        "table": "D_SCBSJS_ZJGL_ZJSZ_ZJRBB",
        "labels": ["单据状态", "单据编号", "单据日期", "账号名称", "银行账号", "当前账户余额", "当前账户银行余额", "银行系统差额", "当日累计收入", "当日累计支出", "账户往来", "备注", "录入人", "录入时间"],
    },
    43: {
        "path": "/tmp/scbs_55_old_live_full_rows_seq043_抵扣登记.json.gz",
        "model": "sc.tax.deduction.registration",
        "surface": "online_old_scbs:C_JXXP_DKDJ_New:list893",
        "table": "C_JXXP_DKDJ_New",
        "labels": ["单据状态", "单据编号", "是否转出", "项目名称", "开票单位", "发票号", "抵扣税额", "抵扣总额", "抵扣附加税", "备注", "录入人", "单据日期"],
    },
    44: {
        "path": "/tmp/scbs_55_old_live_full_rows_seq044_外经证登记.json.gz",
        "model": "sc.legacy.payment.residual.fact",
        "surface": "online_old_scbs:ZJGL_WJZ_WJZDJB:list894",
        "table": "ZJGL_WJZ_WJZDJB",
        "labels": ["单据状态", "单据编号", "项目名称", "纳税人名称", "纳税人识别号", "经办人手机", "区域涉税事项联系人", "区域涉税事项联系人座机手机", "跨区域经营地址", "经营方式", "合同名称", "合同金额", "合同开始日期", "合同结束日期", "合同相对方名称", "合同相对方名称编号", "跨区域涉税事项报验管理编号", "附件", "录入人", "录入时间"],
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


def number_text(value: object) -> str:
    text = clean(value)
    if not text:
        return ""
    try:
        return ("%.2f" % float(text)).rstrip("0").rstrip(".")
    except ValueError:
        return text


def state_label(value: object) -> str:
    text = clean(value)
    return {"-1": "已作废", "0": "未审核", "1": "审核中", "2": "审核通过", "3": "已驳回", "4": "已作废"}.get(text, text)


def yes_no(value: object, *, blank_as_no: bool = False) -> str:
    text = clean(value)
    if not text:
        return "否" if blank_as_no else ""
    lowered = text.lower()
    if lowered in {"1", "true", "yes", "y", "是"}:
        return "是"
    if lowered in {"0", "false", "no", "n", "否"}:
        return "否"
    return text


def key_for(row: dict[str, Any], index: int) -> str:
    return clean(row.get("Id") or row.get("ID") or row.get("pid") or row.get("PID")) or str(index)


def project_for(row: dict[str, Any]):
    Project = env["project.project"].sudo().with_context(active_test=False)  # noqa: F821
    legacy_project_id = clean(row.get("XMID") or row.get("f_GLGCXXID"))
    if legacy_project_id and "legacy_project_id" in Project._fields:
        rec = Project.search([("legacy_project_id", "=", legacy_project_id)], limit=1)
        if rec:
            return rec
    name = clean(row.get("XMMC") or row.get("f_GCMC") or row.get("TBXMMC") or row.get("JYXMMC"))
    if name:
        rec = Project.search([("name", "ilike", name[:60])], limit=1)
        if rec:
            return rec
    return Project.search([], limit=1)


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


def write_payload(model: str, res_id: int, payload: dict[str, str]) -> None:
    env.cr.execute(  # noqa: F821
        """
        INSERT INTO sc_p1_legacy_visible_alias_payload(model, res_id, payload, write_date)
        VALUES (%s, %s, %s::jsonb, now())
        ON CONFLICT (model, res_id)
        DO UPDATE SET payload = EXCLUDED.payload, write_date = now()
        """,
        [model, res_id, json.dumps(payload, ensure_ascii=False)],
    )


def visible(seq: int, row: dict[str, Any]) -> dict[str, str]:
    v = {
        "单据状态": state_label(row.get("DJZT")),
        "推送结果": clean(row.get("TSJG")),
        "单据编号": clean(row.get("DJBH")),
        "项目名称": clean(row.get("XMMC") or row.get("f_GCMC") or row.get("TBXMMC")),
        "申请人姓名": clean(row.get("SQRXM")),
        "所在部门": clean(row.get("SZBM")),
        "请假天数": number_text(row.get("QJTS")),
        "请假类型": clean(row.get("QJLX")),
        "请假时间": clean(row.get("QJSJ")),
        "销假时间": clean(row.get("XJSJ")),
        "请假时长": number_text(row.get("QJSC")),
        "用印时间": clean(row.get("YYSJ")),
        "用印部门": clean(row.get("YYBM")),
        "用印申请人": clean(row.get("YYSQR")),
        "用印部门负责人签字": clean(row.get("YYBMFZRQZ")),
        "用印种类": clean(row.get("YYZL")),
        "用印文本名称及文号": clean(row.get("YYWBMCJWH") or row.get("GZWJNBGY")),
        "经办人签字": clean(row.get("JBRQZ")),
        "领导签字": clean(row.get("LDQZ")),
        "份数": clean(row.get("FS")),
        "归还时间": clean(row.get("GHSJ")),
        "合同金额": number_text(row.get("HTJE")),
        "合同编号": clean(row.get("HTBH")),
        "所属公司": clean(row.get("SSGS")),
        "使用印章公司": clean(row.get("D_JCLY_SYYZGS")),
        "是否外带": clean(row.get("D_JCLY_SFWD")),
        "借阅项目名称": clean(row.get("JYXMMC")),
        "证件名称": clean(row.get("ZJMC")),
        "申请日期": clean(row.get("SQRQ")),
        "借阅部门或项目部名称": clean(row.get("JYBMMC")),
        "借阅人": clean(row.get("JYR")),
        "联系方式": clean(row.get("LXFS")),
        "借阅形式": clean(row.get("JYXS")),
        "借阅日期": clean(row.get("JYRQ")),
        "负责人": clean(row.get("FZRMC")),
        "归还申请日期": clean(row.get("GHSQRQ")),
        "申请归还时间": clean(row.get("SQGHSJ")),
        "是否归还": clean(row.get("SFGH")),
        "确认归还时间": clean(row.get("QRGHSJ")),
        "归还日期": clean(row.get("GHRQ")),
        "修改人": clean(row.get("XGR")),
        "修改日期": clean(row.get("XGRQ")),
        "修改备注": clean(row.get("XGBZ")),
        "审定人": clean(row.get("SDR")),
        "审定时间": clean(row.get("SDSJ")),
        "审定意见": clean(row.get("SDYJ")),
        "开标时间": clean(row.get("KBSJ")),
        "登记时间": clean(row.get("f_BMSJ")),
        "申请人": clean(row.get("SQR")),
        "收款账号": clean(row.get("SKZH")),
        "开户行": clean(row.get("KHH")),
        "金额": number_text(row.get("JE")),
        "收款人": clean(row.get("SKR")),
        "付款方式": clean(row.get("FKFS")),
        "时间": clean(row.get("SJ")),
        "期数": clean(row.get("QS")),
        "本期收款": number_text(row.get("KPSKQK_BQS")),
        "本期代扣代缴合计": number_text(row.get("BQDKDJHJ")),
        "本期拨付金额合计": number_text(row.get("YFSGDGCK_2")),
        "施工单位": clean(row.get("SGD")),
        "目前形象进度": clean(row.get("MQXXJD")),
        "累计开票金额": number_text(row.get("LJKPJE")),
        "上期留存余额": number_text(row.get("SQLCYE_SQLJS")),
        "单据日期": clean(row.get("DJRQ")),
        "账号名称": clean(row.get("ZHMC$D_SCBSJS_ZJGL_ZJSZ_ZJRBB_CB")),
        "银行账号": clean(row.get("YHZH$D_SCBSJS_ZJGL_ZJSZ_ZJRBB_CB")),
        "当前账户余额": number_text(row.get("DQZHYE$D_SCBSJS_ZJGL_ZJSZ_ZJRBB_CB")),
        "当前账户银行余额": number_text(row.get("DQZHYHYE$D_SCBSJS_ZJGL_ZJSZ_ZJRBB_CB")),
        "银行系统差额": number_text(row.get("YHXTCE$D_SCBSJS_ZJGL_ZJSZ_ZJRBB_CB")),
        "当日累计收入": number_text(row.get("DRLJSR$D_SCBSJS_ZJGL_ZJSZ_ZJRBB_CB")),
        "当日累计支出": number_text(row.get("DRLJZC$D_SCBSJS_ZJGL_ZJSZ_ZJRBB_CB")),
        "账户往来": number_text(row.get("ZHWL$D_SCBSJS_ZJGL_ZJSZ_ZJRBB_CB")),
        "是否转出": yes_no(row.get("SFZC"), blank_as_no=seq == 43),
        "开票单位": clean(row.get("KPDW$C_JXXP_DKDJ_CB")),
        "发票号": clean(row.get("FPHM$C_JXXP_DKDJ_CB")),
        "抵扣税额": number_text(row.get("DKSE$C_JXXP_DKDJ_CB")),
        "抵扣总额": number_text(row.get("DKJE$C_JXXP_DKDJ_CB")),
        "抵扣附加税": number_text(row.get("D_SCBSJS_DKFJS$C_JXXP_DKDJ_CB")),
        "纳税人名称": clean(row.get("NSRMC")),
        "纳税人识别号": clean(row.get("NSRSBH")),
        "经办人手机": clean(row.get("JBRSJ")),
        "区域涉税事项联系人": clean(row.get("QYSSSXLXR")),
        "区域涉税事项联系人座机手机": clean(row.get("QYSSSXLXRSJ")),
        "跨区域经营地址": clean(row.get("KQYJYDZ")),
        "经营方式": clean(row.get("JYFS")),
        "合同名称": clean(row.get("HTMC")),
        "合同开始日期": clean(row.get("HTKSRQ")),
        "合同结束日期": clean(row.get("HTJSRQ")),
        "合同相对方名称": clean(row.get("HTXDFMC")),
        "合同相对方名称编号": clean(row.get("HTXDFMCNSRSBH")),
        "跨区域涉税事项报验管理编号": clean(row.get("KQYSSSXBYGLBH")),
        "附件": clean(row.get("f_FJ") or row.get("FJ")),
        "备注": clean(row.get("BZ") or row.get("BZ$D_SCBSJS_ZJGL_ZJSZ_ZJRBB_CB")),
        "录入人": clean(row.get("LRR") or row.get("f_LRR")),
        "录入时间": clean(row.get("LRSJ") or row.get("f_LRSJ")),
    }
    return {label: v.get(label, "") for label in SPECS[seq]["labels"]}


def vals_for(seq: int, spec: dict[str, Any], row: dict[str, Any], key: str) -> dict[str, Any]:
    if seq in (5, 6):
        return {
            "name": clean(row.get("DJBH")) or spec["table"],
            "fact_type": "leave_request" if seq == 5 else "seal_use",
            "project_id": project_for(row).id or False,
            "business_date": parse_date(row.get("QJSJ") or row.get("YYSJ") or row.get("LRSJ")),
            "amount": amount(row.get("HTJE")),
            "state": "done",
            "description": clean(row.get("BZ")),
            "leave_type": "other",
            "start_datetime": parse_dt(row.get("QJSJ")),
            "end_datetime": parse_dt(row.get("XJSJ")),
            "duration_days": amount(row.get("QJTS")),
            "seal_type": "other",
            "use_purpose": clean(row.get("YYWBMCJWH") or row.get("GZWJNBGY") or row.get("BZ")),
            "use_date": parse_date(row.get("YYSJ")),
            "return_date": parse_date(row.get("GHSJ")),
            "legacy_document_no": clean(row.get("DJBH")),
            "legacy_document_state": clean(row.get("DJZT")),
            "legacy_source_table": spec["surface"],
            "legacy_source_id": key,
            "legacy_visible_project_name": clean(row.get("XMMC")),
            "legacy_visible_applicant": clean(row.get("SQRXM") or row.get("YYSQR")),
            "legacy_visible_department": clean(row.get("SZBM") or row.get("YYBM")),
            "legacy_visible_leave_days": number_text(row.get("QJTS")),
            "legacy_visible_leave_type": clean(row.get("QJLX")),
            "legacy_visible_leave_time": clean(row.get("QJSJ")),
            "legacy_visible_cancel_time": clean(row.get("XJSJ")),
            "legacy_visible_note": clean(row.get("BZ")),
            "legacy_visible_leave_duration": number_text(row.get("QJSC")),
            "legacy_visible_creator_name": clean(row.get("LRR")),
            "legacy_visible_created_time": parse_dt(row.get("LRSJ")),
            "legacy_visible_seal_use_time": parse_date(row.get("YYSJ")),
            "legacy_visible_department_manager_sign": clean(row.get("YYBMFZRQZ")),
            "legacy_visible_seal_type": clean(row.get("YYZL")),
            "legacy_visible_seal_text": clean(row.get("YYWBMCJWH") or row.get("GZWJNBGY")),
            "legacy_visible_handler_sign": clean(row.get("JBRQZ")),
            "legacy_visible_leader_sign": clean(row.get("LDQZ")),
            "legacy_visible_copy_count": clean(row.get("FS")),
            "legacy_visible_return_time": parse_date(row.get("GHSJ")),
            "legacy_visible_contract_amount": number_text(row.get("HTJE")),
            "legacy_visible_contract_no": clean(row.get("HTBH")),
            "legacy_visible_company": clean(row.get("SSGS")),
            "legacy_visible_seal_company": clean(row.get("D_JCLY_SYYZGS")),
            "legacy_visible_take_out": clean(row.get("D_JCLY_SFWD")),
            "legacy_visible_attachment": clean(row.get("f_FJ") or row.get("FJ")),
            "active": True,
        }
    if seq == 15:
        return {
            "name": clean(row.get("DJBH")) or "借阅申请",
            "fact_type": "document_borrow",
            "project_id": project_for(row).id or False,
            "business_date": parse_date(row.get("SQRQ") or row.get("LRSJ")),
            "state": "done",
            "document_title": clean(row.get("ZJMC") or row.get("DJBH")),
            "borrow_date": parse_date(row.get("JYRQ") or row.get("SQRQ")),
            "expected_return_date": parse_date(row.get("GHSQRQ") or row.get("GHRQ") or row.get("SQRQ")),
            "actual_return_date": parse_date(row.get("GHRQ")),
            "legacy_document_no": clean(row.get("DJBH")),
            "legacy_document_state": clean(row.get("DJZT")),
            "legacy_source_table": spec["surface"],
            "legacy_source_id": key,
            "legacy_visible_project_name": clean(row.get("JYXMMC")),
            "legacy_visible_document_type": clean(row.get("ZJMC")),
            "legacy_visible_description": clean(row.get("BZ")),
            "legacy_visible_creator_name": clean(row.get("LRR")),
            "legacy_visible_note": clean(row.get("BZ")),
            "legacy_visible_created_time": parse_dt(row.get("LRSJ")),
            "legacy_visible_application_date": parse_date(row.get("SQRQ")),
            "legacy_visible_department": clean(row.get("JYBMMC")),
            "legacy_visible_borrower": clean(row.get("JYR")),
            "legacy_visible_contact": clean(row.get("LXFS")),
            "legacy_visible_borrow_form": clean(row.get("JYXS")),
            "legacy_visible_borrow_date": parse_date(row.get("JYRQ")),
            "legacy_visible_responsible_person": clean(row.get("FZRMC")),
            "legacy_visible_return_request_date": parse_date(row.get("GHSQRQ")),
            "legacy_visible_return_apply_time": parse_dt(row.get("SQGHSJ")),
            "legacy_visible_returned": clean(row.get("SFGH")),
            "legacy_visible_return_confirm_time": parse_dt(row.get("QRGHSJ")),
            "legacy_visible_return_date": parse_date(row.get("GHRQ")),
            "legacy_visible_modifier": clean(row.get("XGR")),
            "legacy_visible_modified_date": parse_dt(row.get("XGRQ")),
            "legacy_visible_modify_note": clean(row.get("XGBZ")),
            "legacy_visible_reviewer": clean(row.get("SDR")),
            "legacy_visible_review_time": parse_dt(row.get("SDSJ")),
            "legacy_visible_review_opinion": clean(row.get("SDYJ")),
            "active": True,
        }
    if seq == 16:
        return {
            "name": clean(row.get("DJBH")) or key,
            "tender_name": clean(row.get("f_GCMC") or row.get("DJBH") or key),
            "project_id": project_for(row).id,
            "state": "submitted",
            "open_date": parse_dt(row.get("KBSJ")),
            "legacy_fact_model": spec["surface"],
            "legacy_fact_id": int(clean(row.get("RowIndex")) or 0),
            "legacy_fact_type": "tender_registration",
            "legacy_note": "old_key=%s; push=%s" % (key, clean(row.get("TSJG"))),
            "legacy_visible_document_state": clean(row.get("DJZT")),
            "legacy_visible_opening_time": parse_dt(row.get("KBSJ")),
            "legacy_visible_project_name": clean(row.get("f_GCMC")),
            "legacy_visible_registration_time": parse_dt(row.get("f_BMSJ")),
            "legacy_visible_creator_name": clean(row.get("f_LRR")),
        }
    if seq == 17:
        bid = env["tender.bid"].sudo().search([("legacy_fact_model", "=", "online_old_scbs:P_ZTB_GCBMGL:list866"), ("tender_name", "=", clean(row.get("TBXMMC")))], limit=1)  # noqa: F821
        if not bid:
            bid = env["tender.bid"].sudo().create({"tender_name": clean(row.get("TBXMMC") or row.get("DJBH") or key), "project_id": project_for(row).id, "legacy_fact_model": spec["surface"] + ":bid", "legacy_fact_id": int(clean(row.get("RowIndex")) or 0)})  # noqa: F821
        return {
            "bid_id": bid.id,
            "apply_date": parse_date(row.get("SQRQ")),
            "amount": amount(row.get("JE")),
            "payment_method": clean(row.get("FKFS")),
            "receipt_partner_name": clean(row.get("SKDW")),
            "receipt_payee_name": clean(row.get("SKR")),
            "receipt_bank_name": clean(row.get("KHH")),
            "receipt_bank_account": clean(row.get("SKZH")),
            "remark": clean(row.get("BZ")),
            "legacy_visible_applicant_name": clean(row.get("SQR")),
            "legacy_visible_document_state": clean(row.get("DJZT")),
            "legacy_source_created_by": clean(row.get("LRR")),
            "legacy_source_created_at": parse_dt(row.get("LRSJ")),
            "legacy_record_id": key,
            "legacy_source_table": spec["surface"],
            "legacy_attachment_ref": clean(row.get("FJ")),
            "state": "approved",
        }
    if seq == 35:
        return {
            "legacy_header_id": "%s:%s" % (spec["surface"], key),
            "legacy_pid": clean(row.get("pid")),
            "project_legacy_id": clean(row.get("XMID")),
            "project_name": clean(row.get("XMMC")),
            "project_id": project_for(row).id or False,
            "document_no": clean(row.get("DJBH")),
            "period_no": clean(row.get("QS")),
            "receipt_time": parse_dt(row.get("SJ")),
            "contract_name": clean(row.get("SGD")),
            "contract_amount": amount(row.get("HTJE")),
            "current_project_stage": clean(row.get("MQXXJD")),
            "actual_fund_amount": amount(row.get("KPSKQK_BQS")),
            "accumulated_invoice_amount": amount(row.get("LJKPJE")),
            "document_state": clean(row.get("DJZT")),
            "creator_legacy_user_id": clean(row.get("LRRID")),
            "creator_name": clean(row.get("LRR")),
            "created_time": parse_dt(row.get("LRSJ")),
            "attachment_ref": clean(row.get("FJ")),
            "source_table": spec["surface"],
            "active": True,
        }
    if seq == 36:
        return {
            "legacy_line_id": "%s:%s" % (spec["surface"], clean(row.get("ID$D_SCBSJS_ZJGL_ZJSZ_ZJRBB_CB") or key)),
            "legacy_header_id": clean(row.get("ID") or row.get("ZBID$D_SCBSJS_ZJGL_ZJSZ_ZJRBB_CB")),
            "legacy_pid": clean(row.get("PID$D_SCBSJS_ZJGL_ZJSZ_ZJRBB_CB")),
            "document_no": clean(row.get("DJBH")),
            "document_date": parse_date(row.get("DJRQ")),
            "document_state": clean(row.get("DJZT")),
            "title": clean(row.get("BT")),
            "project_legacy_id": clean(row.get("XMID")),
            "project_name": clean(row.get("XMMC")),
            "project_id": project_for(row).id or False,
            "period_start": parse_dt(row.get("KSSJ")),
            "period_end": parse_dt(row.get("JSSJ")),
            "account_legacy_id": clean(row.get("ZHID$D_SCBSJS_ZJGL_ZJSZ_ZJRBB_CB")),
            "account_name": clean(row.get("ZHMC$D_SCBSJS_ZJGL_ZJSZ_ZJRBB_CB")),
            "bank_account_no": clean(row.get("YHZH$D_SCBSJS_ZJGL_ZJSZ_ZJRBB_CB")),
            "daily_income": amount(row.get("DRLJSR$D_SCBSJS_ZJGL_ZJSZ_ZJRBB_CB")),
            "daily_expense": amount(row.get("DRLJZC$D_SCBSJS_ZJGL_ZJSZ_ZJRBB_CB")),
            "current_account_balance": amount(row.get("DQZHYE$D_SCBSJS_ZJGL_ZJSZ_ZJRBB_CB")),
            "current_bank_balance": amount(row.get("DQZHYHYE$D_SCBSJS_ZJGL_ZJSZ_ZJRBB_CB")),
            "bank_system_difference": amount(row.get("YHXTCE$D_SCBSJS_ZJGL_ZJSZ_ZJRBB_CB")),
            "creator_legacy_user_id": clean(row.get("LRRID")),
            "creator_name": clean(row.get("LRR")),
            "created_time": parse_dt(row.get("LRSJ")),
            "attachment_ref": clean(row.get("FJ")),
            "line_attachment_ref": clean(row.get("FJ$D_SCBSJS_ZJGL_ZJSZ_ZJRBB_CB")),
            "note": clean(row.get("BZ$D_SCBSJS_ZJGL_ZJSZ_ZJRBB_CB")),
            "source_table": spec["surface"],
            "active": True,
        }
    if seq == 43:
        return {
            "source_origin": "legacy",
            "state": "deducted",
            "project_id": project_for(row).id,
            "name": clean(row.get("DJBH")) or key,
            "document_no": clean(row.get("DJBH")),
            "document_date": parse_date(row.get("DJRQ")),
            "deduction_confirm_date": parse_date(row.get("RZDKRQ$C_JXXP_DKDJ_CB") or row.get("DJRQ")),
            "legacy_visible_project_name": clean(row.get("XMMC")),
            "partner_name": clean(row.get("KPDW$C_JXXP_DKDJ_CB")),
            "invoice_no": clean(row.get("FPHM$C_JXXP_DKDJ_CB")),
            "invoice_code": clean(row.get("FPDM$C_JXXP_DKDJ_CB")),
            "invoice_date": parse_date(row.get("KPRQ$C_JXXP_DKDJ_CB")),
            "invoice_amount_untaxed": amount(row.get("JE_NO$C_JXXP_DKDJ_CB")),
            "invoice_tax_amount": amount(row.get("SE$C_JXXP_DKDJ_CB")),
            "invoice_amount_total": amount(row.get("JE$C_JXXP_DKDJ_CB")),
            "deduction_amount": amount(row.get("DKJE$C_JXXP_DKDJ_CB")),
            "deduction_tax_amount": amount(row.get("DKSE$C_JXXP_DKDJ_CB")),
            "deduction_surcharge_amount": amount(row.get("D_SCBSJS_DKFJS$C_JXXP_DKDJ_CB")),
            "legacy_source_model": spec["surface"],
            "legacy_source_table": spec["table"],
            "legacy_record_id": clean(row.get("Id$C_JXXP_DKDJ_CB") or key),
            "legacy_document_state": clean(row.get("DJZT")),
            "creator_legacy_user_id": clean(row.get("LRRID")),
            "creator_name": clean(row.get("LRR")),
            "created_time": parse_dt(row.get("LRSJ")),
            "note": clean(row.get("BZ")),
            "active": True,
        }
    return {
        "source_table": spec["surface"],
        "legacy_record_id": key,
        "legacy_pid": clean(row.get("pid")),
        "payment_family": "external_tax_certificate",
        "document_no": clean(row.get("DJBH")),
        "document_date": parse_date(row.get("LRSJ")),
        "document_state": clean(row.get("DJZT")),
        "project_legacy_id": clean(row.get("XMID")),
        "project_name": clean(row.get("XMMC")),
        "project_id": project_for(row).id or False,
        "taxpayer_name": clean(row.get("NSRMC")),
        "taxpayer_identifier": clean(row.get("NSRSBH")),
        "partner_name": clean(row.get("HTXDFMC")),
        "counterparty_tax_identifier": clean(row.get("HTXDFMCNSRSBH")),
        "contract_no": clean(row.get("HTBH")),
        "contract_name": clean(row.get("HTMC")),
        "contract_start_date": parse_date(row.get("HTKSRQ")),
        "contract_end_date": parse_date(row.get("HTJSRQ")),
        "planned_amount": amount(row.get("HTJE")),
        "payment_method": clean(row.get("JYFS")),
        "handler_name": clean(row.get("JBR")),
        "handler_phone": clean(row.get("JBRSJ")),
        "regional_tax_contact": clean(row.get("QYSSSXLXR")),
        "regional_tax_contact_phone": clean(row.get("QYSSSXLXRSJ")),
        "operation_address": clean(row.get("KQYJYDZ")),
        "tax_report_management_no": clean(row.get("KQYSSSXBYGLBH")),
        "creator_legacy_user_id": clean(row.get("LRRID")),
        "creator_name": clean(row.get("LRR")),
        "created_time": parse_dt(row.get("LRSJ")),
        "attachment_ref": clean(row.get("FJ")),
        "active": True,
    }


def import_one(seq: int) -> dict[str, Any]:
    spec = SPECS[seq]
    rows = json.load(gzip.open(spec["path"], "rt", encoding="utf-8")).get("rows") or []
    Model = env[spec["model"]].sudo().with_context(active_test=False)  # noqa: F821
    created = updated = 0
    seen: set[str] = set()
    for index, row in enumerate(rows, start=1):
        key = key_for(row, index)
        search_key = key
        vals = vals_for(seq, spec, row, key)
        if seq == 35:
            rec = Model.search([("legacy_header_id", "=", vals["legacy_header_id"])], limit=1)
            search_key = vals["legacy_header_id"]
        elif seq == 36:
            rec = Model.search([("legacy_line_id", "=", vals["legacy_line_id"])], limit=1)
            search_key = vals["legacy_line_id"]
        elif seq == 43:
            rec = Model.search([("legacy_source_model", "=", spec["surface"]), ("legacy_record_id", "=", vals["legacy_record_id"])], limit=1)
            search_key = vals["legacy_record_id"]
        elif seq == 16:
            rec = Model.search([("legacy_fact_model", "=", spec["surface"]), ("legacy_fact_id", "=", vals["legacy_fact_id"])], limit=1)
            search_key = vals["legacy_fact_id"]
        elif seq == 17:
            rec = Model.search([("legacy_source_table", "=", spec["surface"]), ("legacy_record_id", "=", key)], limit=1)
        elif seq == 44:
            rec = Model.search([("source_table", "=", spec["surface"]), ("legacy_record_id", "=", key)], limit=1)
        else:
            rec = Model.search([("legacy_source_table", "=", spec["surface"]), ("legacy_source_id", "=", key)], limit=1)
        seen.add(search_key)
        if rec:
            rec.write(vals)
            updated += 1
        else:
            rec = Model.create(vals)
            created += 1
        payload_model = "sc.legacy.fund.confirmation.document" if seq == 35 else spec["model"]
        payload_id = rec.id
        write_payload(payload_model, payload_id, visible(seq, row))
    if seq == 35:
        stale = Model.search([("source_table", "=", spec["surface"]), ("legacy_header_id", "not in", list(seen) or ["__none__"])])
    elif seq == 36:
        stale = Model.search([("source_table", "=", spec["surface"]), ("legacy_line_id", "not in", list(seen) or ["__none__"])])
    elif seq == 43:
        stale = Model.search([("legacy_source_model", "=", spec["surface"]), ("legacy_record_id", "not in", list(seen) or ["__none__"])])
    elif seq == 16:
        stale = Model.search([("legacy_fact_model", "=", spec["surface"]), ("legacy_fact_id", "not in", list(seen) or [-1])])
    elif seq == 17:
        stale = Model.search([("legacy_source_table", "=", spec["surface"]), ("legacy_record_id", "not in", list(seen) or ["__none__"])])
    elif seq == 44:
        stale = Model.search([("source_table", "=", spec["surface"]), ("legacy_record_id", "not in", list(seen) or ["__none__"])])
    else:
        stale = Model.search([("legacy_source_table", "=", spec["surface"]), ("legacy_source_id", "not in", list(seen) or ["__none__"])])
    stale_count = len(stale)
    if stale and "active" in Model._fields:
        stale.write({"active": False})
    if seq == 35:
        visible_count = env["sc.legacy.fund.confirmation.document"].sudo().with_context(active_test=False).search_count([("legacy_header_id", "like", spec["surface"] + ":%")])  # noqa: F821
    elif seq == 16:
        visible_count = Model.search_count([("legacy_fact_model", "=", spec["surface"])])
    elif seq == 17:
        visible_count = Model.search_count([("legacy_source_table", "=", spec["surface"])])
    elif seq == 36:
        visible_count = Model.search_count([("source_table", "=", spec["surface"])])
    elif seq == 43:
        visible_count = Model.search_count([("legacy_source_model", "=", spec["surface"])])
    elif seq == 44:
        visible_count = Model.search_count([("source_table", "=", spec["surface"])])
    else:
        visible_count = Model.search_count([("legacy_source_table", "=", spec["surface"])])
    return {"seq": seq, "model": spec["model"], "surface": spec["surface"], "old_rows": len(rows), "created": created, "updated": updated, "stale_hidden": stale_count, "new_visible": visible_count}


ensure_payload_table()
results = [import_one(seq) for seq in sorted(SPECS)]
Path("/tmp/scbs55_admin_tender_fund_tax_surfaces_online_patch_result.json").write_text(json.dumps({"results": results}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
env.cr.commit()  # noqa: F821
print(json.dumps({"results": results}, ensure_ascii=False, indent=2))
