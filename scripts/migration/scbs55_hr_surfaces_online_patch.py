#!/usr/bin/env python3
"""Mirror old SCBS HR/payroll visible list surfaces."""

from __future__ import annotations

import gzip
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


SPECS = {
    8: {
        "path": "/tmp/scbs_55_old_live_full_rows_seq008_user_profile.json.gz",
        "action_id": 859,
        "model": "sc.legacy.user.profile",
        "surface": "online_old_scbs:BASE_SYSTEM_USER:list859",
        "table": "BASE_SYSTEM_USER",
        "labels": ["操作", "姓名", "用户名", "部门", "职务", "岗位", "电话号码", "性别", "账号类型", "是否测试账号", "证件类型", "证件号", "居住地址", "是否购买社保", "是否购买社保", "员工工号", "出生日期", "政治面貌", "民族", "籍贯", "毕业院校", "毕业时间", "所学专业", "学历", "入职日期", "人员类型", "录入人", "录入时间"],
    },
    9: {
        "path": "/tmp/scbs_55_old_live_full_rows_seq009_social_person.json.gz",
        "action_id": 860,
        "surface": "online_old_scbs:D_SCBSJS_BGGL_XZ_SBRY:list860",
        "table": "D_SCBSJS_BGGL_XZ_SBRY",
        "fact_type": "social_person_registration",
        "labels": ["单据编号", "单据日期", "姓名", "人员类型", "身份证号码", "联系方式", "证书费用", "个人证书", "社保基数", "社保购买单位", "人员状态", "备注", "录入人", "录入时间"],
    },
    10: {
        "path": "/tmp/scbs_55_old_live_full_rows_seq010_social_registration.json.gz",
        "action_id": 861,
        "surface": "online_old_scbs:BGGL_XZ_JXDJ_ZB:list861",
        "table": "BGGL_XZ_JXDJ_ZB",
        "fact_type": "social_registration",
        "child": "Id$BGGL_XZ_JXDJ",
        "labels": ["单据状态", "单据编号", "社保购买单位", "姓名", "类型", "购买人数", "年度", "月份", "缴费金额", "联系方式", "备注", "登记人", "登记时间"],
    },
    11: {
        "path": "/tmp/scbs_55_old_live_full_rows_seq011_salary.json.gz",
        "action_id": 862,
        "surface": "online_old_scbs:BGGL_XZ_GZ:list862",
        "table": "BGGL_XZ_GZ",
        "fact_type": "salary_registration",
        "child": "Id$BGGL_XZ_GZ_CB",
        "labels": ["单据状态", "单据编号", "标题", "年份", "月份", "部门", "姓名", "发放单位", "应发工资", "实发工资", "备注", "发放人数", "附件", "财务支出登记状态", "录入人", "录入时间"],
    },
    12: {
        "path": "/tmp/scbs_55_old_live_full_rows_seq012_subsidy.json.gz",
        "action_id": 863,
        "surface": "online_old_scbs:BGGL_XZ_BZ:list863",
        "table": "BGGL_XZ_BZ",
        "fact_type": "subsidy",
        "child": "Id$BGGL_XZ_BZ_CB",
        "labels": ["状态", "项目名称", "单据编号", "补助事由", "年度", "月份", "补助人", "部门", "补助金额", "录入人", "录入时间"],
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


def intval(value: object) -> int:
    try:
        return int(float(clean(value)))
    except ValueError:
        return 0


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


def row_key(seq: int, row: dict[str, Any], index: int) -> str:
    spec = SPECS[seq]
    header = clean(row.get("Id") or row.get("ID") or row.get("PID") or row.get("pid"))
    child_key = spec.get("child")
    if child_key:
        child = clean(row.get(child_key) or row.get("Pid" + child_key[2:]) or row.get("RowIndex") or index)
        return f"{header}:{child}"
    return header or str(index)


def visible_values(seq: int, row: dict[str, Any]) -> dict[str, str]:
    values = {
        "操作": clean(row.get("PERSON_NAME")),
        "姓名": clean(row.get("PERSON_NAME") or row.get("XM") or row.get("RY$BGGL_XZ_JXDJ") or row.get("XM$BGGL_XZ_GZ_CB")),
        "用户名": clean(row.get("USERNAME")),
        "部门": clean(row.get("BM") or row.get("BM$BGGL_XZ_GZ_CB") or row.get("BMGW$BGGL_XZ_BZ_CB")),
        "职务": clean(row.get("ZW")),
        "岗位": clean(row.get("GW")),
        "电话号码": clean(row.get("PHONE_NUMBER")),
        "性别": clean(row.get("SEX")),
        "账号类型": clean(row.get("ZHLX")),
        "是否测试账号": clean(row.get("SFCSZH")),
        "证件类型": clean(row.get("ZJLX")),
        "证件号": clean(row.get("ZJH")),
        "居住地址": clean(row.get("JZDZ")),
        "是否购买社保": clean(row.get("SFGMSB") or row.get("ORDER_NUM")),
        "员工工号": clean(row.get("YGGH")),
        "出生日期": clean(row.get("CSRQ"))[:10],
        "政治面貌": clean(row.get("ZZMM")),
        "民族": clean(row.get("MZ")),
        "籍贯": clean(row.get("JG")),
        "毕业院校": clean(row.get("BYYX")),
        "毕业时间": clean(row.get("BYSJ"))[:10],
        "所学专业": clean(row.get("SXZY")),
        "学历": clean(row.get("XL")),
        "入职日期": clean(row.get("RZRQ"))[:10],
        "人员类型": clean(row.get("RYLX")),
        "单据编号": clean(row.get("DJBH")),
        "单据日期": clean(row.get("DJRQ"))[:10],
        "身份证号码": clean(row.get("SFZHM")),
        "联系方式": clean(row.get("LXFS") or row.get("D_SCBSJS_LXFS$BGGL_XZ_JXDJ")),
        "证书费用": amount_text(row.get("ZSFY")),
        "个人证书": clean(row.get("GRZS")),
        "社保基数": amount_text(row.get("SBJS")),
        "社保购买单位": clean(row.get("ZS") or row.get("SSGS$BGGL_XZ_JXDJ")),
        "人员状态": clean(row.get("RYZT")),
        "单据状态": state_label(row.get("DJZT")),
        "状态": state_label(row.get("DJZT")),
        "类型": clean(row.get("D_SCBSJS_RYLX$BGGL_XZ_JXDJ")),
        "购买人数": clean(row.get("D_SCBSJS_GMRS")),
        "年度": clean(row.get("ND") or row.get("NF") or row.get("ND$BGGL_XZ_BZ_CB")),
        "年份": clean(row.get("NF")),
        "月份": clean(row.get("YF") or row.get("YF$BGGL_XZ_BZ_CB")),
        "缴费金额": amount_text(row.get("JXGZ$BGGL_XZ_JXDJ")),
        "备注": clean(row.get("BZ") or row.get("JL$BGGL_XZ_JXDJ") or row.get("BZ$BGGL_XZ_GZ_CB")),
        "登记人": clean(row.get("LRR")),
        "登记时间": clean(row.get("LRSJ")),
        "标题": clean(row.get("BT")),
        "发放单位": clean(row.get("D_SCBSJS_FFDW$BGGL_XZ_GZ_CB")),
        "应发工资": amount_text(row.get("HJ$BGGL_XZ_GZ_CB")),
        "实发工资": amount_text(row.get("SFGZ$BGGL_XZ_GZ_CB")),
        "发放人数": clean(row.get("FFRS")),
        "附件": clean(row.get("f_FJ") or row.get("FJ")),
        "财务支出登记状态": clean(row.get("SFDJ")),
        "项目名称": clean(row.get("XMMC")),
        "补助事由": clean(row.get("D_SCBSJS_BZSX$BGGL_XZ_BZ_CB")),
        "补助人": clean(row.get("BZR$BGGL_XZ_BZ_CB")),
        "补助金额": amount_text(row.get("BZJE$BGGL_XZ_BZ_CB")),
        "录入人": clean(row.get("LRR")),
        "录入时间": clean(row.get("LRSJ")),
    }
    return {label: values.get(label, "") for label in SPECS[seq]["labels"]}


def import_profiles(rows: list[dict[str, Any]]) -> tuple[int, int, int, int]:
    spec = SPECS[8]
    Profile = env["sc.legacy.user.profile"].sudo().with_context(active_test=False)  # noqa: F821
    created = updated = 0
    seen: set[str] = set()
    for index, row in enumerate(rows, start=1):
        key = row_key(8, row, index)
        seen.add(key)
        rec = Profile.search([("source_table", "=", spec["surface"]), ("legacy_user_id", "=", key)], limit=1)
        vals = {
            "legacy_user_id": key,
            "generated_login": clean(row.get("USERNAME") or row.get("PHONE_NUMBER")),
            "source_login": clean(row.get("USERNAME")),
            "display_name": clean(row.get("PERSON_NAME")),
            "phone": clean(row.get("PHONE_NUMBER")),
            "legacy_created_at": parse_dt(row.get("LRSJ")),
            "department_scope_summary": clean(row.get("BM")),
            "account_state_label": clean(row.get("PERSON_STATE")),
            "email": clean(row.get("EMAIL")),
            "employee_no": clean(row.get("YGGH")),
            "credential_type": clean(row.get("ZJLX")),
            "credential_no": clean(row.get("ZJH")),
            "residence_address": clean(row.get("JZDZ")),
            "archive_no": clean(row.get("DABH")),
            "birth_date": parse_date(row.get("CSRQ")),
            "political_status": clean(row.get("ZZMM")),
            "nation": clean(row.get("MZ")),
            "native_place": clean(row.get("JG")),
            "graduation_school": clean(row.get("BYYX")),
            "graduation_date": parse_date(row.get("BYSJ")),
            "major": clean(row.get("SXZY")),
            "education": clean(row.get("XL")),
            "professional_title": clean(row.get("ZC")),
            "professional_qualification": clean(row.get("ZYZG")),
            "person_state": clean(row.get("PERSON_STATE")),
            "deleted_flag": clean(row.get("DEL")),
            "locked_flag": clean(row.get("ISLOCK")),
            "is_admin_flag": clean(row.get("ISADMIN")),
            "sex": clean(row.get("SEX")),
            "account_type": clean(row.get("ZHLX")),
            "user_type": clean(row.get("USER_TYPE")),
            "personnel_type": clean(row.get("RYLX")),
            "department_name": clean(row.get("BM")),
            "work_unit": clean(row.get("D_AXB_DWMC")),
            "project_name": clean(row.get("D_AXB_XMMC")),
            "company_email": clean(row.get("GSYX")),
            "emergency_contact": clean(row.get("JJLXR")),
            "emergency_phone": clean(row.get("JJLXDH")),
            "emergency_relation": clean(row.get("GX")),
            "bank_name": clean(row.get("KHH")),
            "bank_account": clean(row.get("KH")),
            "onboarding_date": parse_date(row.get("RZRQ")),
            "post_salary": clean(row.get("D_AXB_GWGZ")),
            "construction_site": clean(row.get("D_AXB_SGD")),
            "age": clean(row.get("D_AXB_NL")),
            "source_table": spec["surface"],
            "source_evidence": "SCBS55 old visible surface mirror; password fields intentionally excluded",
            "active": True,
        }
        if rec:
            rec.write(vals)
            updated += 1
        else:
            rec = Profile.create(vals)
            created += 1
        write_payload(rec, visible_values(8, row))
    stale = Profile.search([("source_table", "=", spec["surface"]), ("legacy_user_id", "not in", list(seen) or ["__none__"])])
    stale_count = len(stale)
    if stale:
        stale.write({"source_table": f"{spec['surface']}:hidden", "active": False})
    return created, updated, stale_count, Profile.search_count([("source_table", "=", spec["surface"])])


def import_payroll(seq: int, rows: list[dict[str, Any]]) -> tuple[int, int, int, int]:
    spec = SPECS[seq]
    Doc = env["sc.hr.payroll.document"].sudo().with_context(active_test=False)  # noqa: F821
    Currency = env.ref("base.CNY", raise_if_not_found=False)  # noqa: F821
    created = updated = 0
    seen: set[str] = set()
    for index, row in enumerate(rows, start=1):
        key = row_key(seq, row, index)
        seen.add(key)
        rec = Doc.search([("legacy_source_table", "=", spec["surface"]), ("legacy_source_id", "=", key)], limit=1)
        if seq == 9:
            employee = clean(row.get("XM"))
            period_year, period_month = 0, 0
            money = row.get("SBJS")
            business_date = row.get("DJRQ")
        elif seq == 10:
            employee = clean(row.get("RY$BGGL_XZ_JXDJ"))
            period_year, period_month = intval(row.get("ND")), intval(row.get("YF"))
            money = row.get("JXGZ$BGGL_XZ_JXDJ")
            business_date = row.get("LRSJ")
        elif seq == 11:
            employee = clean(row.get("XM$BGGL_XZ_GZ_CB"))
            period_year, period_month = intval(row.get("NF")), intval(row.get("YF"))
            money = row.get("SFGZ$BGGL_XZ_GZ_CB") or row.get("HJ$BGGL_XZ_GZ_CB")
            business_date = row.get("LRSJ")
        else:
            employee = clean(row.get("BZR$BGGL_XZ_BZ_CB"))
            period_year, period_month = intval(row.get("ND$BGGL_XZ_BZ_CB")), intval(row.get("YF$BGGL_XZ_BZ_CB"))
            money = row.get("BZJE$BGGL_XZ_BZ_CB")
            business_date = row.get("LRSJ")
        vals = {
            "name": clean(row.get("DJBH")) or key,
            "document_no": clean(row.get("DJBH")),
            "fact_type": spec["fact_type"],
            "business_date": parse_date(business_date),
            "currency_id": Currency.id,
            "state": "done",
            "employee_name": employee,
            "id_number": clean(row.get("SFZHM") or row.get("SFZHM$BGGL_XZ_GZ_CB")),
            "period_year": period_year,
            "period_month": period_month,
            "payer_unit": clean(row.get("ZS") or row.get("SSGS$BGGL_XZ_JXDJ") or row.get("SSGS")),
            "social_security_base": amount(row.get("SBJS") or row.get("JXGZ$BGGL_XZ_JXDJ")),
            "company_amount": amount(row.get("GSJE") or row.get("DKSBGS$BGGL_XZ_GZ_CB")),
            "individual_amount": amount(row.get("YLJE") or row.get("DKSBGR$BGGL_XZ_GZ_CB")),
            "salary_base": amount(row.get("XJ$BGGL_XZ_GZ_CB")),
            "gross_amount": amount(row.get("HJ$BGGL_XZ_GZ_CB")),
            "deduction_amount": amount(row.get("KK$BGGL_XZ_GZ_CB")),
            "net_salary": amount(row.get("SFGZ$BGGL_XZ_GZ_CB")),
            "item_type": clean(row.get("D_SCBSJS_BZSX$BGGL_XZ_BZ_CB") or row.get("RYLX") or row.get("D_SCBSJS_RYLX$BGGL_XZ_JXDJ")),
            "amount": amount(money),
            "occurrence_date": parse_date(business_date),
            "legacy_document_no": clean(row.get("DJBH")),
            "legacy_document_state": clean(row.get("DJZT")),
            "legacy_source_table": spec["surface"],
            "legacy_source_id": key,
            "legacy_visible_creator_name": clean(row.get("LRR")),
            "legacy_visible_created_time": parse_dt(row.get("LRSJ")),
            "legacy_visible_people_count": clean(row.get("D_SCBSJS_GMRS") or row.get("FFRS")),
            "legacy_visible_type": clean(row.get("RYLX") or row.get("D_SCBSJS_RYLX$BGGL_XZ_JXDJ")),
            "legacy_visible_note": clean(row.get("BZ") or row.get("JL$BGGL_XZ_JXDJ") or row.get("BZ$BGGL_XZ_GZ_CB")),
            "legacy_visible_certificate_fee": amount_text(row.get("ZSFY")),
            "legacy_visible_item_type": clean(row.get("D_SCBSJS_BZSX$BGGL_XZ_BZ_CB")),
            "active": True,
        }
        if rec:
            rec.write(vals)
            updated += 1
        else:
            rec = Doc.create(vals)
            created += 1
        write_payload(rec, visible_values(seq, row))
    stale = Doc.search([("legacy_source_table", "=", spec["surface"]), ("legacy_source_id", "not in", list(seen) or ["__none__"])])
    stale_count = len(stale)
    if stale:
        stale.write({"legacy_source_table": f"{spec['surface']}:hidden", "active": False})
    return created, updated, stale_count, Doc.search_count([("legacy_source_table", "=", spec["surface"])])


ensure_payload_table()
Action = env["ir.actions.act_window"].sudo()  # noqa: F821
results = []
for seq in sorted(SPECS):
    spec = SPECS[seq]
    with gzip.open(Path(spec["path"]), "rt", encoding="utf-8") as handle:
        rows = json.load(handle)["rows"]
    if seq == 8:
        created, updated, stale_hidden, final_count = import_profiles(rows)
        domain = [("source_table", "=", spec["surface"])]
    else:
        created, updated, stale_hidden, final_count = import_payroll(seq, rows)
        domain = [("legacy_source_table", "=", spec["surface"])]
    Action.browse(spec["action_id"]).write({"domain": repr(domain)})
    results.append({"seq": seq, "surface": spec["surface"], "old": len(rows), "created": created, "updated": updated, "stale_hidden": stale_hidden, "final_count": final_count, "domain": repr(domain), "status": "OK" if final_count == len(rows) else "COUNT_MISMATCH"})
env.cr.commit()  # noqa: F821
print(json.dumps({"surfaces": results}, ensure_ascii=False, indent=2, sort_keys=True))
