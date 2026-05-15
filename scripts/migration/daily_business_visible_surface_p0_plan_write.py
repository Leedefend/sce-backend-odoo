#!/usr/bin/env python3
"""Replay P0 daily business visible-surface alignment tasks into Odoo."""

from __future__ import annotations

import json
import os
from pathlib import Path


SOURCE_DOCUMENT = "/home/odoo/workspace/partner_import_source/老系统列表，填单页面截图.docx"


def resolve_artifact_root() -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.append(Path("/mnt/artifacts/migration"))
    candidates.append(Path(f"/tmp/daily_business_visible_surface_p0/{env.cr.dbname}"))  # noqa: F821
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return candidate
        except Exception:
            continue
    return Path(f"/tmp/daily_business_visible_surface_p0/{env.cr.dbname}")  # noqa: F821


def ensure_allowed_db() -> None:
    allowlist = {
        item.strip()
        for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", env.cr.dbname).split(",")  # noqa: F821
        if item.strip()
    }
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_replay": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_report(path: Path, payload: dict[str, object]) -> None:
    lines = [
        "# Daily Business Visible Surface P0 Replay v1",
        "",
        f"Status: {payload['status']}",
        f"Database: {payload['database']}",
        "",
        "## P0 Entries",
        "",
        "| priority | group | legacy entry | domain | screenshots | carrier |",
        "| ---: | --- | --- | --- | --- | --- |",
    ]
    for row in payload["entries"]:
        lines.append(
            "| {priority_sequence} | {legacy_menu_group} | {legacy_menu_name} | {business_domain} | "
            "{screenshot_ref} | {legacy_source_tables} |".format(**row)
        )
    lines.extend(
        [
            "",
            "## Summary",
            "",
            "```json",
            json.dumps(payload["summary"], ensure_ascii=False, indent=2, sort_keys=True),
            "```",
            "",
            "## Boundary",
            "",
            "P0 visible-surface alignment is replayed as backend business facts. The frontend must consume native view and contract output; it must not hard-code these business fields.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def entry(
    priority: int,
    group: str,
    name: str,
    domain: str,
    screenshots: str,
    carrier: str,
    fields: str,
    scope: str,
) -> dict[str, object]:
    return {
        "priority_sequence": priority,
        "source_document": SOURCE_DOCUMENT,
        "screenshot_ref": screenshots,
        "legacy_menu_group": group,
        "legacy_menu_name": name,
        "business_domain": domain,
        "current_round_action": "plan_fact_landed",
        "target_iteration": "p0_daily_business_visible_surface",
        "old_system_path": f"{group}/{name}",
        "legacy_source_tables": carrier,
        "legacy_field_list": fields,
        "extracted_evidence": f"从老系统 docx 截图 {screenshots} 提取 P0 可见面对齐字段。",
        "next_development_topic": f"{name} 可见面对齐",
        "next_scope": scope,
        "replay_status": "verified",
        "active": True,
    }


ENTRIES = [
    entry(10, "基础资料", "供应商/合作单位", "master_data", "image1,image2", "sc.business.entity;res.partner;sc.partner.import.review", "单据状态;推送结果;项目名称;单位编号;合作类型;单位名称;开户银行;账号;统一社会信用代码;主税率;录入人;录入时间;账户信息;营业执照;开户信息或法人账号", "对齐供应商/合作单位列表列序、状态页签、基本信息、账户子表、财税信息、附件与日志。"),
    entry(20, "基础资料", "往来单位", "master_data", "image3", "sc.business.entity;res.partner", "单据状态;项目名称;单位名称;收款金额;付款金额;开户姓名;开户账号;开户银行;录入人;录入时间;银行账号", "对齐往来单位列表列序、项目/单位筛选、账户子表、附件与日志。"),
    entry(30, "合同", "施工合同", "contract", "image4,image5", "construction.contract", "合同订立日期;原件是否归档;发包人;项目名称;工程类别;合同标题;合同编号;合同金额;结算金额;累计开票;累计收款;未收款;未收款比例;挂靠人;工程地址;工程内容;录入人;录入时间;附件", "对齐施工合同列表、搜索项、付款方式、工程概况、工期、合同价、项目经理、签订时间、附件与日志。"),
    entry(40, "办公资料", "公司资料存档", "document_archive", "image6,image7", "sc.document.admin.document;sc.office.admin.document;sc.project.document", "单据状态;项目名称;资料类型;资料说明;录入人;备注;录入时间;工程名称;上传人;上传时间;资料信息;附件", "对齐资料存档列表、基本信息、资料信息子表、附件与日志。"),
    entry(50, "人事行政", "请假/休假审批单", "hr_admin", "image8,image9", "sc.office.admin.document", "单据状态;单据编号;项目名称;申请人姓名;所在部门;请假天数;请假类型;请假时间;销假时间;备注;请假时长;录入人;录入时间;附件信息", "对齐请假审批列表、基本信息、附件、审批日志和状态。"),
    entry(60, "人事行政", "社保人员登记", "hr_admin", "image10,image11", "sc.office.admin.document", "单据编号;单据日期;姓名;人员类型;身份证号码;联系方式;证书费用;个人证书;社保基数;社保购买单位;人员状态;备注;录入人;录入时间;养老金额;失业金额;工伤金额;缴费金额;附件", "对齐社保人员登记列表、姓名/单位/类型筛选、金额字段、附件与日志。"),
    entry(70, "人事行政", "社保登记", "hr_admin", "image12,image13", "sc.office.admin.document", "单据状态;单据编号;社保购买单位;姓名;类型;购买人数;年度;月份;缴费金额;联系方式;备注;登记人;登记时间;缴效详情;附件", "对齐社保登记列表、年度筛选、缴效时间、缴效详情子表、附件与日志。"),
    entry(80, "人事行政", "工资登记", "hr_admin", "image14,image15", "sc.hr.payroll.document;sc.legacy.salary.line", "单据状态;单据编号;标题;年份;月份;部门;姓名;发放单位;应发工资;实发工资;备注;发放人数;附件;财务支出登记状态;录入人;录入时间;工资详情", "对齐工资登记列表、工资范围、工资详情子表、附件、财务支出联动与日志。"),
    entry(90, "人事行政", "补助", "hr_admin", "image16,image17", "sc.hr.payroll.document", "状态;项目名称;单据编号;补助事由;年度;月份;补助人;部门;补助金额;录入人;录入时间;表单信息;附件", "对齐补助列表、表单信息子表、附件与日志。"),
    entry(100, "资金", "自筹垫付收入", "treasury", "image18,image19", "sc.fund.account.operation;sc.legacy.self.funding.fact;sc.receipt.income", "单据状态;推送结果;金蝶单据编号;单据编号;日期;项目名称;对方单位/付款;自筹金额;收入类别;收款账户;自筹垫付退回金额;未退金额;标题;是否需要退回;附件;录入人;录入时间", "对齐自筹垫付收入列表、基本信息、收款用途、退回关联、附件与日志。"),
    entry(110, "资金", "自筹垫付退回", "treasury", "image20,image21", "sc.fund.account.operation;sc.legacy.self.funding.fact", "单据状态;推送结果;单据日期;单据编号;项目名称;退回金额;往来单位/付款单位;备注;附件;录入人;录入时间;退回详情", "对齐自筹垫付退回列表、退回详情子表、其它信息附件与日志。"),
    entry(120, "保证金", "自筹保证金", "treasury", "image22,image23", "tender.guarantee;sc.fund.account.operation;sc.legacy.self.funding.fact", "状态;单据编号;投标项目名称;项目名称;所属公司;金额;已退保证金金额;转款单位;汇款方式;保证金类型;收款账户;收款账户名称;备注;附件;录入人;录入时间", "对齐自筹保证金列表、付款信息、收款信息、退回关联、附件与日志。"),
    entry(130, "保证金", "自筹保证金退回", "treasury", "image24,image25", "tender.guarantee;sc.fund.account.operation", "状态;收保证金单号;单据编号;项目名称;投标项目名称;退还金额;备注;退还账号;退还开户行;单位;收款开户行;收款账号;录入人;录入时间;附件", "对齐自筹保证金退回列表、退还信息、收款信息、原单关联、附件与日志。"),
    entry(140, "保证金", "付保证金", "treasury", "image26,image27", "tender.guarantee;payment.request;sc.payment.execution", "状态;推送结果;金蝶单据编号;单据编号;投标项目;工程项目;保证金类型;所属公司;保证金金额;已退金额;未退金额;是否需要退回;收款单位;支付账户;备注;附件;录入人;录入时间", "对齐付保证金列表、投标项目、付款信息、保证金信息、金蝶推送、附件与日志。"),
    entry(150, "保证金", "付保证金退回", "treasury", "image28,image29", "tender.guarantee;sc.fund.account.operation", "状态;推送结果;退回单编号;所属公司;投标项目名称;保证金类型;退回项目;退回金额;退回账户;收款单位;备注;录入人;退回日期;附件", "对齐付保证金退回列表、退回登记、账户信息、原单关联、附件与日志。"),
    entry(160, "资金", "借款/还款登记", "treasury", "image30,image31,image32", "sc.financing.loan;sc.legacy.financing.loan.fact;sc.fund.account.operation", "项目名称;单据状态;单据编号;申请部门;申请时间;申请人;是否预算内;借款金额;往来单位名称;附件;录入人;录入时间", "对齐借款/还款列表、申请信息、借款信息、还款信息、账户信息、附件与日志。"),
    entry(170, "收支", "收入", "receipt_income", "image33,image34", "sc.receipt.income;sc.legacy.receipt.income.fact", "单据状态;项目名称;单据编号;填写人;收款账户;进账金额;收入类别;收款时间;备注;附件;录入人;录入时间", "对齐收入列表、项目收款、收入类别、开票/到款关联、附件与日志。"),
    entry(180, "公司财务", "公司财务支出", "expense", "image35,image36", "sc.expense.claim;sc.payment.execution;sc.legacy.finance.auxiliary.fact", "单据状态;推送结果;单据编号;付款时间;付款金额;成本类别;收款单位名称;付款账户名称;备注;录入人;录入时间;附件", "对齐公司财务支出列表、付款信息、成本类别、收款单位、账户信息、金蝶推送、附件与日志。"),
]


ensure_allowed_db()
artifact_root = resolve_artifact_root()
output_json = artifact_root / "daily_business_visible_surface_p0_plan_write_result_v1.json"
output_report = artifact_root / "daily_business_visible_surface_p0_plan_write_report_v1.md"

Model = env["sc.legacy.user.priority.menu.plan"].sudo()  # noqa: F821
before = Model.with_context(active_test=False).search_count([])
created = 0
updated = 0
for vals in ENTRIES:
    domain = [
        ("source_document", "=", vals["source_document"]),
        ("legacy_menu_group", "=", vals["legacy_menu_group"]),
        ("legacy_menu_name", "=", vals["legacy_menu_name"]),
    ]
    record = Model.with_context(active_test=False).search(domain, limit=1)
    if record:
        record.write(vals)
        updated += 1
    else:
        Model.create(vals)
        created += 1
env.cr.commit()  # noqa: F821

domain = [("source_document", "=", SOURCE_DOCUMENT)]
row_count = Model.with_context(active_test=False).search_count(domain)
verified_count = Model.with_context(active_test=False).search_count(domain + [("replay_status", "=", "verified")])
domain_counts = {
    row.get("business_domain") or "": row.get("business_domain_count") or row.get("__count") or 0
    for row in Model.read_group(domain, ["business_domain"], ["business_domain"], lazy=False)
}
payload = {
    "status": "PASS" if row_count == len(ENTRIES) and verified_count == len(ENTRIES) else "FAIL",
    "mode": "daily_business_visible_surface_p0_plan_write",
    "database": env.cr.dbname,  # noqa: F821
    "source_document": SOURCE_DOCUMENT,
    "input_rows": len(ENTRIES),
    "before": before,
    "after": Model.with_context(active_test=False).search_count([]),
    "created": created,
    "updated": updated,
    "row_count": row_count,
    "verified_count": verified_count,
    "domain_counts": domain_counts,
    "entries": ENTRIES,
    "summary": {
        "p0_entry_count": len(ENTRIES),
        "verified_count": verified_count,
        "screenshots": "image1-image36",
        "boundary": "backend_contract_driven_visible_surface_alignment",
    },
    "decision": "daily_business_visible_surface_p0_plan_replayed"
    if row_count == len(ENTRIES) and verified_count == len(ENTRIES)
    else "STOP_REVIEW_REQUIRED",
}
write_json(output_json, payload)
write_report(output_report, payload)
print(
    "DAILY_BUSINESS_VISIBLE_SURFACE_P0_PLAN_WRITE="
    + json.dumps(
        {
            "status": payload["status"],
            "input_rows": payload["input_rows"],
            "created": created,
            "updated": updated,
            "row_count": row_count,
            "verified_count": verified_count,
            "artifact_root": str(artifact_root),
        },
        ensure_ascii=False,
        sort_keys=True,
    )
)
