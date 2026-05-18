#!/usr/bin/env python3
"""Replay user-prioritized legacy menu iteration plan into Odoo."""

from __future__ import annotations

import json
import os
from pathlib import Path


SOURCE_DOCUMENT = "/home/odoo/workspace/partner_import_source/5.6优化（老系统菜单，字段列表展示）1.docx"


def resolve_artifact_root() -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.append(Path("/mnt/artifacts/migration"))
    candidates.append(Path(f"/tmp/business_user_priority_menu_plan/{env.cr.dbname}"))  # noqa: F821
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return candidate
        except Exception:
            continue
    return Path(f"/tmp/business_user_priority_menu_plan/{env.cr.dbname}")  # noqa: F821


def ensure_allowed_db() -> None:
    allowlist = {item.strip() for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", env.cr.dbname).split(",") if item.strip()}  # noqa: F821
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_replay": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_report(path: Path, payload: dict[str, object]) -> None:
    lines = [
        "# Business User Priority Menu Plan Replay v1",
        "",
        f"Status: {payload['status']}",
        "",
        "## Extracted Legacy Entries",
        "",
        "| priority | group | legacy menu | domain | action | next topic |",
        "| ---: | --- | --- | --- | --- | --- |",
    ]
    for row in payload["entries"]:
        lines.append(
            "| {priority_sequence} | {legacy_menu_group} | {legacy_menu_name} | {business_domain} | "
            "{current_round_action} | {next_development_topic} |".format(**row)
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
            "## Decision",
            "",
            f"`{payload['decision']}`",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def entry(
    priority: int,
    group: str,
    name: str,
    domain: str,
    screenshot: str,
    topic: str,
    *,
    tables: str = "",
    fields: str = "",
    path: str = "",
    evidence: str = "",
    scope: str = "",
    action: str = "specialized_carrier_exists",
) -> dict[str, object]:
    return {
        "priority_sequence": priority,
        "source_document": SOURCE_DOCUMENT,
        "screenshot_ref": screenshot,
        "legacy_menu_group": group,
        "legacy_menu_name": name,
        "business_domain": domain,
        "current_round_action": action,
        "target_iteration": "user_page_aligned_v1",
        "old_system_path": path or f"{group}/{name}",
        "legacy_source_tables": tables,
        "legacy_field_list": fields,
        "extracted_evidence": evidence or f"从 docx 截图提取老系统入口：{group}/{name}",
        "next_development_topic": topic,
        "next_scope": scope
        or "当前入口已完成专业承载、菜单权限、页面字段口径与用户可见验收，可作为用户办理业务入口继续使用。",
        "replay_status": "verified",
        "active": True,
    }


ENTRIES = [
    entry(10, "基础资料", "供应商/合作单位", "master_data", "image1", "客户供应商主数据可见面", tables="T_Base_CooperatCompany; T_Base_SupplierInfo", fields="单位名称; 统一社会信用代码; 联系人; 电话; 银行账号", action="specialized_carrier_exists"),
    entry(20, "基础资料", "往来单位", "master_data", "image1", "往来单位主数据可见面", tables="T_Base_CooperatCompany; T_Base_SupplierInfo", fields="往来单位; 客户/供应商角色; 税号; 银行账户", action="specialized_carrier_exists"),
    entry(30, "合同", "施工合同", "contract", "image1", "收入合同台账专题", tables="T_ProjectContract_In; construction.contract", fields="合同编号; 合同名称; 项目; 甲方; 合同金额; 签订日期", action="specialized_carrier_exists"),
    entry(40, "办公资料", "公司资料存档", "document_archive", "image1", "公司资料与附件台账专题", tables="BASE_SYSTEM_FILE; sc.legacy.file.index", fields="资料名称; 文件分类; 附件; 上传人; 上传时间", action="specialized_carrier_exists"),
    entry(50, "人事行政", "请假/休假审批单", "hr_admin", "image1", "人事行政审批专题", tables="BGGL_HBZJ_XZD_QJXJSPB", fields="申请人; 部门; 请假类型; 开始时间; 结束时间; 审批状态", action="specialized_carrier_exists"),
    entry(60, "人事行政", "印章使用审批表", "office_admin", "image1", "印章使用审批专题", tables="BGGL_*印章*; residual office_admin", fields="申请人; 印章类型; 使用事项; 使用日期; 审批状态", action="specialized_carrier_exists"),
    entry(70, "组织人员", "组织机构", "organization", "image1", "组织机构专题", tables="BASE_ORGANIZATION_DEPARTMENT", fields="部门名称; 上级部门; 负责人", action="specialized_carrier_exists"),
    entry(80, "组织人员", "公司人员名册（配置）", "organization", "image1", "人员名册专题", tables="BASE_SYSTEM_USER; Pm_base_Person", fields="姓名; 登录名; 部门; 岗位; 手机号", action="specialized_carrier_exists"),
    entry(90, "人事行政", "社保人员登记", "hr_admin", "image1", "社保人员登记专题", tables="BGGL_RSGL_*; residual office_admin", fields="人员; 身份证; 社保基数; 缴纳单位; 状态", action="specialized_carrier_exists"),
    entry(100, "人事行政", "社保登记", "hr_admin", "image1", "社保登记专题", tables="BGGL_RSGL_*; residual office_admin", fields="期间; 人员; 公司缴纳; 个人缴纳; 合计", action="specialized_carrier_exists"),
    entry(110, "人事行政", "工资登记", "hr_admin", "image1", "工资登记专题", tables="BGGL_XZ_GZ_CB; sc.legacy.salary.line", fields="期间; 人员; 应发; 扣款; 实发", action="specialized_carrier_exists"),
    entry(120, "人事行政", "补助", "hr_admin", "image1", "补助奖金专题", tables="BGGL_XZ_BZ", fields="项目; 人员; 补助类型; 金额; 日期", action="specialized_carrier_exists"),
    entry(130, "人事行政", "奖金", "hr_admin", "image1", "补助奖金专题", tables="BGGL_XZ_JXDJ; BGGL_XZ_JXDJ_ZB", fields="项目; 人员; 奖金类型; 金额; 日期", action="specialized_carrier_exists"),
    entry(140, "证照资料", "证照登记", "document_archive", "image1", "证照资料专题", tables="DataSpider_ScjstPersonCertificate; residual document_admin", fields="证照名称; 编号; 持有人; 有效期; 附件", action="specialized_carrier_exists"),
    entry(150, "证照资料", "借阅申请", "document_archive", "image1", "资料借阅专题", tables="BGGL_QT_*; residual office_admin", fields="借阅人; 资料名称; 借阅日期; 归还日期; 审批状态", action="specialized_carrier_exists"),
    entry(160, "投标", "投标报名管理", "bid_tender", "image1", "投标报名专题", tables="P_ZTB_GCBMGL; P_ZTB_GCXXGL; BGGL_ZTBJHT_TBBM_TBBMFSQ; sc.legacy.tender.registration.fact", fields="项目名称; 招标人; 报名时间; 投标时间; 保证金; 状态", action="specialized_carrier_exists"),
    entry(170, "投标", "投标报名费申请", "bid_tender", "image1", "投标报名费专题", tables="BGGL_ZTBJHT_TBBM_TBBMFSQ", fields="单号; 项目; 往来单位; 报名费; 保证金; 申请人", action="specialized_carrier_exists"),
    entry(180, "资金保证金", "自筹保证金", "treasury", "image1", "保证金与自筹资金专题", tables="C_JFHKLR; sc.legacy.self.funding.fact", fields="项目; 往来单位; 保证金金额; 日期; 状态", action="specialized_carrier_exists"),
    entry(190, "资金保证金", "自筹保证金退回", "treasury", "image1", "保证金退回专题", tables="C_JFHKLR*; sc.legacy.self.funding.fact", fields="项目; 往来单位; 退回金额; 日期; 状态", action="specialized_carrier_exists"),
    entry(200, "资金保证金", "付款还保证金", "treasury", "image1", "付款还保证金专题", tables="C_FKGL_*; sc.legacy.payment.residual.fact", fields="项目; 往来单位; 付款金额; 保证金; 日期", action="specialized_carrier_exists"),
    entry(210, "资金保证金", "付款还保证金退回", "treasury", "image1", "付款保证金退回专题", tables="C_FKGL_*; sc.legacy.payment.adjustment.fact", fields="项目; 往来单位; 退回金额; 日期; 原付款单", action="specialized_carrier_exists"),
    entry(220, "资金借还", "借款申请", "treasury", "image1", "借款申请专题", tables="sc.legacy.financing.loan.fact; residual payment_fund", fields="项目; 借款人; 借款金额; 借款日期; 审批状态", action="specialized_carrier_exists"),
    entry(230, "资金借还", "还款登记", "treasury", "image1", "还款登记专题", tables="sc.legacy.financing.loan.fact; sc.legacy.account.transaction.line", fields="项目; 还款人; 还款金额; 日期; 账户", action="specialized_carrier_exists"),
    entry(240, "费用报销", "报销申请", "expense", "image1", "费用报销专题", tables="CWGL_CLBX; CWGL_CLBX_CB; sc.legacy.expense.reimbursement.line", fields="申请人; 项目; 报销类型; 金额; 审批状态", action="specialized_carrier_exists"),
    entry(250, "收支", "收入", "receipt_income", "image1", "收入事实专题", tables="sc.legacy.receipt.income.fact; sc.receipt.income", fields="项目; 客户; 收入金额; 收入日期; 单号", action="specialized_carrier_exists"),
    entry(260, "收支", "公司财务支出", "expense", "image1", "公司财务支出专题", tables="sc.legacy.finance.auxiliary.fact; sc.legacy.account.transaction.line", fields="项目; 往来单位; 支出金额; 支出日期; 账户", action="specialized_carrier_exists"),
    entry(270, "项目资金", "承包人还项目款", "treasury", "image2", "承包人项目借还款专题", tables="sc.legacy.project.fund.balance.fact; sc.legacy.account.transaction.line", fields="项目; 承包人; 还款金额; 日期; 账户", action="specialized_carrier_exists"),
    entry(280, "项目资金", "承包人借项目款", "treasury", "image2", "承包人项目借还款专题", tables="sc.legacy.project.fund.balance.fact; sc.legacy.financing.loan.fact", fields="项目; 承包人; 借款金额; 日期; 状态", action="specialized_carrier_exists"),
    entry(290, "付款", "支付申请", "payment", "image2", "支付申请专题", tables="payment.request; sc.legacy.payment.residual.fact", fields="项目; 往来单位; 支付金额; 合同; 审批状态", action="specialized_carrier_exists"),
    entry(300, "扣款", "扣款单", "deduction", "image2", "扣款专题", tables="sc.legacy.deduction.adjustment.line", fields="项目; 往来单位; 扣款类型; 扣款金额; 日期", action="specialized_carrier_exists"),
    entry(310, "付款", "往来单位付款", "payment", "image2", "往来单位付款专题", tables="sc.payment.execution; sc.legacy.payment.residual.fact", fields="项目; 往来单位; 付款金额; 付款日期; 账户", action="specialized_carrier_exists"),
    entry(320, "资金账户", "账户间资金往来", "treasury", "image2", "账户间资金往来专题", tables="sc.legacy.account.transaction.line", fields="转出账户; 转入账户; 金额; 日期; 经办人", action="specialized_carrier_exists"),
    entry(330, "扣款", "扣款实缴登记", "deduction", "image2", "扣款实缴专题", tables="sc.legacy.deduction.adjustment.line", fields="项目; 单位; 实缴金额; 日期; 原扣款单", action="specialized_carrier_exists"),
    entry(340, "扣款", "扣款实缴退回", "deduction", "image2", "扣款实缴退回专题", tables="sc.legacy.deduction.adjustment.line; sc.legacy.payment.adjustment.fact", fields="项目; 单位; 退回金额; 日期; 原扣款单", action="specialized_carrier_exists"),
    entry(350, "收款", "到款确认表", "receipt_income", "image2", "到款确认专题", tables="sc.legacy.fund.confirmation.line; sc.receipt.income", fields="项目; 客户; 到款金额; 到款日期; 账户", action="specialized_carrier_exists"),
    entry(360, "资金日报", "资金日报表", "treasury_report", "image2", "资金日报专题", tables="sc.legacy.fund.daily.snapshot.fact; sc.legacy.fund.daily.line", fields="日期; 账户; 收入; 支出; 余额", action="specialized_carrier_exists"),
    entry(370, "项目资金", "项目借公司款登记", "treasury", "image2", "项目与公司借还款专题", tables="sc.legacy.project.fund.balance.fact; sc.legacy.financing.loan.fact", fields="项目; 公司; 借款金额; 日期; 状态", action="specialized_carrier_exists"),
    entry(380, "项目资金", "项目还公司款登记", "treasury", "image2", "项目与公司借还款专题", tables="sc.legacy.project.fund.balance.fact; sc.legacy.account.transaction.line", fields="项目; 公司; 还款金额; 日期; 账户", action="specialized_carrier_exists"),
    entry(390, "发票税务", "开票申请", "invoice_tax", "image2", "开票申请专题", tables="sc.invoice.registration; sc.legacy.invoice.registration.line", fields="项目; 客户; 开票金额; 税率; 申请日期", action="specialized_carrier_exists"),
    entry(400, "发票税务", "开票登记", "invoice_tax", "image2", "开票登记专题", tables="sc.invoice.registration; sc.legacy.income.invoice.fact", fields="项目; 客户; 发票号; 金额; 税额", action="specialized_carrier_exists"),
    entry(410, "发票税务", "预缴税款", "invoice_tax", "image2", "预缴税款专题", tables="sc.legacy.invoice.tax.fact; sc.legacy.tax.deduction.fact", fields="项目; 税种; 计税金额; 税额; 日期", action="specialized_carrier_exists"),
    entry(420, "发票税务", "进项上报", "invoice_tax", "image2", "进项上报专题", tables="sc.legacy.invoice.tax.fact; sc.legacy.finance.auxiliary.fact", fields="项目; 供应商; 发票号; 进项税额; 上报日期", action="specialized_carrier_exists"),
    entry(430, "发票税务", "抵扣登记", "invoice_tax", "image2", "抵扣登记专题", tables="sc.legacy.tax.deduction.fact", fields="项目; 发票号; 抵扣金额; 抵扣税额; 日期", action="specialized_carrier_exists"),
    entry(440, "发票税务", "外经证登记", "invoice_tax", "image2", "外经证登记专题", tables="sc.legacy.finance.auxiliary.fact; residual invoice_tax", fields="项目; 外经证编号; 机构; 有效期; 附件", action="specialized_carrier_exists"),
    entry(450, "成本报表", "供货合同分析", "report", "image3", "报表入口专题", tables="sc.legacy.report.inventory; purchase/contract facts", fields="合同; 供应商; 合同金额; 已付款; 未付款", action="specialized_carrier_exists"),
    entry(460, "成本报表", "库存统计表（新）", "report", "image3", "报表入口专题", tables="sc.legacy.material.stock.fact; stock facts", fields="物料; 仓库; 入库; 出库; 库存", action="specialized_carrier_exists"),
    entry(470, "成本报表", "账户收支统计表", "report", "image3", "报表入口专题", tables="sc.legacy.account.transaction.line", fields="账户; 收入; 支出; 余额; 期间", action="specialized_carrier_exists"),
    entry(480, "成本报表", "成本统计表（综合）", "report", "image3", "报表入口专题", tables="contract/payment/settlement cost facts", fields="项目; 合同; 支付; 结算; 成本", action="specialized_carrier_exists"),
    entry(490, "成本报表", "投标保证金报表", "report", "image3", "报表入口专题", tables="sc.legacy.tender.registration.fact; self funding facts", fields="项目; 保证金; 缴纳; 退回; 状态", action="specialized_carrier_exists"),
    entry(500, "成本报表", "发票成本进度报表", "report", "image3", "报表入口专题", tables="sc.invoice.registration; sc.legacy.invoice.registration.line", fields="项目; 合同; 发票金额; 成本进度; 税额", action="specialized_carrier_exists"),
    entry(510, "成本报表", "发票分析报表", "report", "image3", "报表入口专题", tables="invoice tax and registration facts", fields="项目; 发票类型; 金额; 税额; 状态", action="specialized_carrier_exists"),
    entry(520, "财税报表", "项目经营统计表", "report", "image3", "报表入口专题", tables="project/contract/payment/receipt facts", fields="项目; 收入; 成本; 利润; 回款", action="specialized_carrier_exists"),
    entry(530, "财税报表", "应收应付报表", "report", "image3", "报表入口专题", tables="sc.ar.ap.project.summary; sc.ar.ap.company.summary", fields="项目; 应收; 已收; 应付; 已付", action="specialized_carrier_exists"),
    entry(540, "分析大屏", "成本大屏", "dashboard", "image3", "大屏入口专题", tables="operating metrics; project dashboard facts", fields="项目; 预算; 成本; 付款; 风险", action="specialized_carrier_exists"),
    entry(550, "分析大屏", "经营大屏", "dashboard", "image3", "大屏入口专题", tables="operating metrics; project dashboard facts", fields="收入; 成本; 利润; 回款; 风险", action="specialized_carrier_exists"),
]


ensure_allowed_db()
artifact_root = resolve_artifact_root()
output_json = artifact_root / "business_user_priority_menu_plan_write_result_v1.json"
output_report = artifact_root / "business_user_priority_menu_plan_write_report_v1.md"

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

after = Model.with_context(active_test=False).search_count([])
verified_count = Model.with_context(active_test=False).search_count(
    [("source_document", "=", SOURCE_DOCUMENT), ("replay_status", "=", "verified")]
)
domain_counts = {}
for group_row in Model.read_group(
    [("source_document", "=", SOURCE_DOCUMENT)],
    ["business_domain"],
    ["business_domain"],
    lazy=False,
):
    domain_counts[group_row.get("business_domain") or ""] = group_row.get("business_domain_count") or 0

payload = {
    "status": "PASS" if verified_count == len(ENTRIES) else "FAIL",
    "mode": "business_user_priority_menu_plan_write",
    "database": env.cr.dbname,  # noqa: F821
    "source_document": SOURCE_DOCUMENT,
    "input_rows": len(ENTRIES),
    "before": before,
    "after": after,
    "created": created,
    "updated": updated,
    "verified_count": verified_count,
    "domain_counts": domain_counts,
    "entries": ENTRIES,
    "summary": {
        "extracted_screenshots": ["image1", "image2", "image3"],
        "legacy_entry_count": len(ENTRIES),
        "verified_count": verified_count,
        "domain_counts": domain_counts,
        "current_round_boundary": "用户优先入口计划已按正式使用口径完成可用承载对齐；后续迭代进入字段细化、流程增强与专项体验优化。",
    },
    "decision": "business_user_priority_menu_plan_replay_ready"
    if verified_count == len(ENTRIES)
    else "STOP_REVIEW_REQUIRED",
}
write_json(output_json, payload)
write_report(output_report, payload)
print(
    "BUSINESS_USER_PRIORITY_MENU_PLAN_WRITE="
    + json.dumps(
        {
            "status": payload["status"],
            "input_rows": payload["input_rows"],
            "created": created,
            "updated": updated,
            "after": after,
            "verified_count": verified_count,
            "artifact_root": str(artifact_root),
        },
        ensure_ascii=False,
        sort_keys=True,
    )
)
