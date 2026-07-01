# -*- coding: utf-8 -*-
"""Build the product-entry disposition matrix from the locked 62 menu baseline.

This script is intentionally read-only. It does not inspect or mutate runtime
menu configuration; the locked user-visible baseline is the source of truth.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


PRODUCT_KEY = "construction.standard"
MIN_MENU_COUNT = 1
ROOT = Path(__file__).resolve().parents[2]
BASELINE = ROOT / "scripts/verify/baselines/user_confirmed_formal_menu_policy_62.json"
OUTPUT_JSON = ROOT / "artifacts/user_confirmed_62_business_entry_integration_matrix.json"
OUTPUT_MD = ROOT / "artifacts/user_confirmed_62_business_entry_integration_matrix.md"


PRODUCT_DOMAIN_BY_MODEL = {
    "res.partner": "master_data",
    "project.project": "project",
    "tender.bid": "tender",
    "tender.doc.purchase": "tender",
    "sc.general.contract": "contract",
    "construction.contract.income": "contract",
    "construction.contract.expense": "contract",
    "sc.settlement.order": "contract",
    "sc.construction.diary": "site",
    "project.material.plan": "material",
    "sc.material.rfq": "material",
    "sc.material.inbound": "material",
    "sc.material.outbound": "material",
    "sc.subcontract.request": "subcontract",
    "sc.labor.usage": "labor",
    "sc.equipment.usage": "equipment",
    "sc.receipt.income": "finance",
    "sc.expense.claim": "finance",
    "payment.request": "finance",
    "sc.payment.execution": "finance",
    "sc.financing.loan": "finance",
    "sc.fund.account.operation": "finance",
    "tender.guarantee": "finance",
    "sc.invoice.registration": "invoice_tax",
    "sc.tax.deduction.registration": "invoice_tax",
    "sc.legacy.payment.residual.fact": "invoice_tax",
    "sc.office.admin.document": "hr_admin",
    "sc.legacy.user.profile": "hr_admin",
    "sc.hr.payroll.document": "hr_admin",
    "sc.document.admin.document": "document",
    "ui.menu.config.policy": "system_config",
}

DOMAIN_LABELS = {
    "master_data": "主数据",
    "project": "项目域",
    "tender": "投标域",
    "contract": "合同结算域",
    "site": "现场履约域",
    "material": "物资域",
    "subcontract": "分包域",
    "labor": "劳务域",
    "equipment": "设备域",
    "finance": "资金财务域",
    "invoice_tax": "票税域",
    "hr_admin": "人事行政域",
    "document": "资料证照域",
    "system_config": "系统配置",
    "legacy_source": "历史来源事实",
}

ENTRY_INTENTS = {
    "handling": "办理",
    "query": "查询",
    "analysis": "分析",
    "config": "配置",
    "master_data": "主数据",
    "source_fact": "来源事实",
}

SOURCE_FACT_MODELS = {
    "sc.legacy.direct.acceptance.fact",
    "sc.legacy.fund.confirmation.document",
    "sc.legacy.fuel.card.fact",
    "sc.legacy.fuel.card.recharge.fact",
    "sc.legacy.self.funding.fact",
    "sc.legacy.payment.residual.fact",
    "sc.legacy.user.profile",
}

SOURCE_FACT_LABELS = {
    "到款确认表",
    "租入",
    "还租",
    "油卡登记",
    "充值登记",
    "自筹垫付收入",
    "自筹垫付退回",
    "外经证登记",
    "公司人员名册",
}

ANALYSIS_LABELS = {
    "资金日报表",
}
CONFIG_LABELS = {"菜单配置"}
MASTER_DATA_MODELS = {"res.partner", "project.project"}

DOMAIN_RELATIONSHIPS = {
    "master_data": ["company_id", "partner_id", "project_id"],
    "project": ["project_id", "partner_id"],
    "tender": ["project_id", "partner_id", "tender_id"],
    "contract": ["project_id", "partner_id", "contract_id"],
    "site": ["project_id", "date", "responsible_user_id"],
    "material": ["project_id", "partner_id", "material_id", "warehouse_id"],
    "subcontract": ["project_id", "partner_id", "contract_id", "cost_item_id"],
    "labor": ["project_id", "partner_id", "contract_id", "cost_item_id"],
    "equipment": ["project_id", "partner_id", "equipment_id", "cost_item_id"],
    "finance": ["project_id", "partner_id", "contract_id", "fund_account_id", "cost_item_id"],
    "invoice_tax": ["project_id", "partner_id", "contract_id", "invoice_type"],
    "hr_admin": ["project_id", "employee_id", "period_id"],
    "document": ["company_id", "project_id", "document_type"],
    "system_config": ["product_key", "user_id"],
    "legacy_source": ["source_record_id", "project_id", "partner_id"],
}

DISPOSITION_BY_LABEL = {
    "客户": ("master_data", "res.partner 客户主数据", "keep_entry", ""),
    "供应商": ("master_data", "res.partner 供应商主数据", "keep_entry", ""),
    "项目台账": ("query", "project.project 项目台账", "keep_query", ""),
    "投标报名管理": ("handling", "tender.bid 投标报名办理", "keep_list_form", ""),
    "投标报名费申请": ("handling", "tender.doc.purchase 投标报名费办理", "keep_list_form", ""),
    "一般合同（公司）": ("handling", "sc.general.contract 一般合同办理", "keep_list_form", ""),
    "补充合同": ("handling", "construction.contract.expense 支出合同办理", "merge_by_category", "contract.expense.supplement"),
    "收入合同执行": ("handling", "construction.contract.income 收入合同办理", "merge_by_category", "contract.income"),
    "支出合同执行": ("handling", "construction.contract.expense 支出合同办理", "merge_by_category", "contract.expense"),
    "收入合同结算": ("handling", "sc.settlement.order 结算办理", "merge_by_category", "settlement.income"),
    "支出合同结算": ("handling", "sc.settlement.order 结算办理", "merge_by_category", "settlement.expense"),
    "施工日志": ("handling", "sc.construction.diary 施工日志", "keep_list_form", "site.construction.diary"),
    "材料计划": ("handling", "project.material.plan 材料计划", "keep_list_form", "material.plan"),
    "租入": ("source_fact", "设备/租赁来源事实明细", "source_readonly", ""),
    "还租": ("source_fact", "设备/租赁来源事实明细", "source_readonly", ""),
    "分包方单": ("handling", "sc.subcontract.request 分包办理", "keep_list_form", ""),
    "方单": ("handling", "sc.labor.usage 劳务办理", "merge_by_category", "labor.usage.ticket"),
    "零星用工": ("handling", "sc.labor.usage 劳务办理", "merge_by_category", "labor.usage.casual"),
    "机械台班记录": ("handling", "sc.equipment.usage 设备台班办理", "keep_list_form", ""),
    "报价单": ("handling", "sc.material.rfq 询比价/报价办理", "keep_list_form", "material.rfq"),
    "入库单": ("handling", "sc.material.inbound 入库办理", "keep_list_form", "material.inbound"),
    "出库单": ("handling", "sc.material.outbound 出库办理", "merge_by_category", "material.outbound"),
    "收入": ("handling", "sc.receipt.income 收款登记", "merge_by_category", "finance.receipt.income.project"),
    "工程进度款收入登记": ("handling", "sc.receipt.income 收款登记", "merge_by_category", "finance.receipt.income.progress"),
    "支付申请": ("handling", "payment.request 收付款申请办理", "merge_by_category", "finance.payment.apply.pay"),
    "公司财务支出": ("handling", "sc.payment.execution 付款执行", "merge_by_category", "finance.payment.execution.company"),
    "往来单位付款": ("handling", "sc.payment.execution 付款执行", "merge_by_category", "finance.payment.execution.partner"),
    "报销申请": ("handling", "sc.expense.claim 费用/扣款/保证金办理", "merge_by_category", "finance.expense.reimbursement"),
    "项目费用报销单": ("handling", "sc.expense.claim 费用/扣款/保证金办理", "merge_by_category", "finance.expense.project"),
    "扣款单": ("handling", "sc.expense.claim 费用/扣款/保证金办理", "merge_by_category", "finance.deduction.bill"),
    "扣款实缴登记": ("handling", "sc.expense.claim 费用/扣款/保证金办理", "merge_by_category", "finance.deduction.paid"),
    "扣款实缴退回": ("handling", "sc.expense.claim 费用/扣款/保证金办理", "merge_by_category", "finance.deduction.refund"),
    "承包人还项目款": ("handling", "sc.expense.claim 还款办理", "merge_by_category", "finance.repayment.contractor_project"),
    "项目还公司款登记": ("handling", "sc.expense.claim 还款办理", "merge_by_category", "finance.repayment.project_company"),
    "付款还保证金": ("handling", "sc.expense.claim 费用/扣款/保证金办理", "merge_by_category", "finance.deposit.bid.return"),
    "承包人借项目款": ("handling", "sc.financing.loan 借款办理", "merge_by_category", "finance.loan.contractor_project_borrow"),
    "项目借公司款登记": ("handling", "sc.financing.loan 借款办理", "merge_by_category", "finance.loan.project_borrow_company"),
    "账户间资金往来": ("handling", "sc.fund.account.operation 账户资金操作", "merge_by_category", "finance.fund.transfer"),
    "资金日报表": ("analysis", "资金日报/账户资金分析", "keep_analysis", "finance.fund.daily_report"),
    "到款确认表": ("source_fact", "到款确认来源事实明细", "source_readonly", ""),
    "付款还保证金退回": ("handling", "sc.expense.claim 费用/扣款/保证金办理", "merge_by_category", "finance.deposit.bid.return"),
    "油卡登记": ("source_fact", "油卡费用来源事实明细", "source_readonly", ""),
    "充值登记": ("source_fact", "油卡充值来源事实明细", "source_readonly", ""),
    "自筹垫付收入": ("handling", "sc.self.funding.registration 自筹垫付办理", "merge_by_category", "finance.self_funding.income"),
    "自筹垫付退回": ("handling", "sc.expense.claim 费用/扣款/保证金办理", "merge_by_category", "finance.deposit.self_funding.return"),
    "自筹保证金": ("handling", "sc.expense.claim 费用/扣款/保证金办理", "merge_by_category", "finance.deposit.bid.pay"),
    "自筹保证金退回": ("handling", "sc.expense.claim 费用/扣款/保证金办理", "merge_by_category", "finance.deposit.bid.return"),
    "进项发票": ("handling", "sc.invoice.registration 票税办理", "merge_by_category", "invoice.input.report"),
    "预缴税款": ("handling", "sc.invoice.registration 票税办理", "merge_by_category", "invoice.prepaid_tax"),
    "销项开票申请": ("handling", "sc.invoice.registration 票税办理", "merge_by_category", "invoice.output.application"),
    "销项开票登记": ("handling", "sc.invoice.registration 票税办理", "merge_by_category", "invoice.output.registration"),
    "抵扣登记": ("handling", "sc.tax.deduction.registration 抵扣办理", "keep_list_form", "tax.deduction.registration"),
    "外经证登记": ("handling", "外经证登记", "keep_list_form", "tax.certificate.registration"),
    "请假/休假审批单": ("handling", "sc.office.admin.document 请假审批", "keep_list_form", ""),
    "公司人员名册": ("query", "人员名册查询", "keep_query", ""),
    "项目管理人员工资登记": ("handling", "sc.hr.payroll.document 薪资办理", "merge_by_category", "hr.payroll.salary"),
    "社保人员登记": ("handling", "sc.hr.payroll.document 社保办理", "merge_by_category", "hr.payroll.social.person"),
    "社保登记": ("handling", "sc.hr.payroll.document 社保办理", "merge_by_category", "hr.payroll.social.registration"),
    "补助": ("handling", "sc.hr.payroll.document 补助办理", "merge_by_category", "hr.payroll.subsidy"),
    "公司资料存档": ("handling", "sc.document.admin.document 资料证照归档", "keep_list_form", ""),
    "菜单配置": ("config", "ui.menu.config.policy 菜单配置", "config_only", ""),
}

ALLOWED_CATEGORY_CODES_BY_TARGET = {
    "sc.receipt.income 收款登记": [
        "finance.receipt.income.project",
        "finance.receipt.income.progress",
        "finance.receipt.income.residual",
    ],
    "payment.request 收付款申请办理": [
        "finance.payment.apply.pay",
        "finance.payment.apply.receive",
    ],
    "sc.expense.claim 费用/扣款/保证金办理": [
        "finance.expense.reimbursement",
        "finance.expense.project",
        "finance.deduction.bill",
        "finance.deduction.paid",
        "finance.deduction.refund",
        "finance.deposit.bid.pay",
        "finance.deposit.bid.return",
        "finance.deposit.self_funding.return",
        "finance.deposit.contract.pay",
        "finance.deposit.contract.return",
    ],
    "sc.expense.claim 还款办理": [
        "finance.repayment.registration",
        "finance.repayment.contractor_project",
        "finance.repayment.project_company",
    ],
    "sc.self.funding.registration 自筹垫付办理": ["finance.self_funding.income"],
}


def _load_menus() -> list[dict]:
    payload = json.loads(BASELINE.read_text(encoding="utf-8"))
    for product in payload.get("products") or []:
        if product.get("product_key") != PRODUCT_KEY:
            continue
        rows = []
        for group in product.get("menu_groups") or []:
            group_label = group.get("group_label") or group.get("label") or ""
            for menu in group.get("menus") or []:
                if not menu.get("enabled", True):
                    continue
                row = dict(menu)
                row["group_label"] = group_label
                rows.append(row)
        return rows
    raise RuntimeError(f"missing product policy: {PRODUCT_KEY}")


def _product_domain(label: str, model: str) -> str:
    if model in SOURCE_FACT_MODELS or label in SOURCE_FACT_LABELS:
        if label in {"到款确认表", "油卡登记", "充值登记", "自筹垫付收入", "自筹垫付退回"}:
            return "finance"
        if label == "外经证登记":
            return "invoice_tax"
        if label in {"租入", "还租"}:
            return "equipment"
        if label == "公司人员名册":
            return "hr_admin"
        return "legacy_source"
    return PRODUCT_DOMAIN_BY_MODEL.get(model, "legacy_source")


def _entry_intent(label: str, model: str) -> str:
    disposition = DISPOSITION_BY_LABEL.get(label)
    if disposition:
        return disposition[0]
    if label in CONFIG_LABELS:
        return "config"
    if label in ANALYSIS_LABELS:
        return "analysis"
    if model in MASTER_DATA_MODELS:
        return "master_data"
    if model in SOURCE_FACT_MODELS or label in SOURCE_FACT_LABELS:
        return "source_fact"
    return "handling"


def _disposition(label: str, model: str) -> tuple[str, str, str]:
    row = DISPOSITION_BY_LABEL.get(label)
    if row:
        _intent, target, policy, category = row
        return target, policy, category
    if model in MASTER_DATA_MODELS:
        return f"{model} 主数据/台账", "keep_entry", ""
    if model in SOURCE_FACT_MODELS or label in SOURCE_FACT_LABELS:
        return f"{model or '来源事实'} 明细", "source_readonly", ""
    return f"{model or '未知模型'} 办理", "keep_list_form", ""


def _next_action(intent: str, policy: str, target: str, category: str) -> str:
    if policy == "source_readonly":
        return f"保留只读追溯；通过非侵入式映射进入“{target}”，不作为新增办理入口。"
    if policy == "keep_analysis":
        return "保留为分析/报表入口；不得替代正式办理单据。"
    if policy == "config_only":
        return "保留给实施/配置人员；不作为普通业务办理入口。"
    if policy == "keep_query":
        return "保留为查询/台账入口；默认不承担新增办理主入口。"
    if policy == "merge_by_category":
        suffix = f"，新建默认分类 `{category}`" if category else ""
        return f"菜单可向“{target}”收敛；列表/表单保持，新建时通过业务分类承接旧语义{suffix}。"
    if intent == "master_data":
        return "保留为主数据入口；服务办理单据关系选择，不混入业务办理菜单。"
    return "保留列表/表单办理模式；完善新增、编辑、状态、附件和关系字段。"


def _build_matrix() -> dict:
    menus = _load_menus()
    if len(menus) < MIN_MENU_COUNT:
        raise AssertionError("locked menu baseline must contain at least one enabled menu")

    rows = []
    for index, menu in enumerate(menus, 1):
        label = menu.get("label") or menu.get("name") or ""
        model = menu.get("res_model") or ""
        product_domain = _product_domain(label, model)
        intent = _entry_intent(label, model)
        target, disposition_policy, category_code = _disposition(label, model)
        rows.append(
            {
                "index": index,
                "group": menu.get("group_label") or "",
                "menu": label,
                "model": model,
                "menu_xmlid": menu.get("menu_xmlid") or "",
                "action_id": menu.get("action_id") or 0,
                "sequence": menu.get("sequence") or 0,
                "product_domain": product_domain,
                "product_domain_label": DOMAIN_LABELS.get(product_domain, product_domain),
                "entry_intent": intent,
                "entry_intent_label": ENTRY_INTENTS[intent],
                "fact_model": model,
                "disposition_policy": disposition_policy,
                "integration_target": target,
                "default_business_category_code": category_code,
                "allowed_business_category_codes": ALLOWED_CATEGORY_CODES_BY_TARGET.get(
                    target,
                    [category_code] if category_code else [],
                ),
                "required_relationships": DOMAIN_RELATIONSHIPS.get(product_domain, []),
                "next_action": _next_action(intent, disposition_policy, target, category_code),
                "locked_data_policy": "read_only_source_facts_no_rewrite",
            }
        )

    domain_counts = Counter(row["product_domain"] for row in rows)
    intent_counts = Counter(row["entry_intent"] for row in rows)
    policy_counts = Counter(row["disposition_policy"] for row in rows)
    target_counts = Counter(row["integration_target"] for row in rows)
    group_counts = Counter(row["group"] for row in rows)

    merge_targets = [
        {"integration_target": target, "menu_count": count}
        for target, count in sorted(target_counts.items(), key=lambda item: (-item[1], item[0]))
        if count > 1
    ]

    return {
        "ok": True,
        "product_key": PRODUCT_KEY,
        "source_baseline": str(BASELINE),
        "policy": {
            "menu_count_source": "locked_enabled_menu_baseline",
            "locked_user_visible_surface": True,
            "locked_fact_data_must_not_be_rewritten": True,
            "purpose": "classify confirmed list pages into formal handling entries, source fact details, summary analysis, and consolidation targets",
        },
        "summary": {
            "menu_count": len(rows),
            "group_counts": dict(sorted(group_counts.items())),
            "product_domain_counts": dict(sorted(domain_counts.items())),
            "entry_intent_counts": dict(sorted(intent_counts.items())),
            "disposition_policy_counts": dict(sorted(policy_counts.items())),
            "merge_target_count": len(merge_targets),
            "handling_menu_count": intent_counts["handling"],
            "source_fact_menu_count": intent_counts["source_fact"],
        },
        "merge_targets": merge_targets,
        "rows": rows,
    }


def _write_markdown(payload: dict) -> str:
    menu_count = payload["summary"]["menu_count"]
    lines = [
        f"# 用户确认 {menu_count} 可见列表业务入口整合矩阵",
        "",
        "本文件由 `scripts/verify/user_confirmed_62_business_entry_integration_matrix.py` 生成。",
        "",
        "## 判定边界",
        "",
        f"- {menu_count} 个锁定基线启用的用户已确认可见列表是入口设计基线，不在本轮改名、隐藏或重排。",
        "- 用户锁定的业务事实数据只读，不写回、不覆盖。",
        "- 新系统菜单整合按产品域、事实模型和用户意图判定，不按旧菜单分组硬套。",
        "- 办理入口保持列表/表单模式；能合并的入口通过业务分类承接旧语义。",
        "- 查询、分析、配置和来源事实不并入办理表单。",
        "",
        "## 汇总",
        "",
        f"- 菜单数：{payload['summary']['menu_count']}",
        f"- 办理入口：{payload['summary']['handling_menu_count']}",
        f"- 来源事实入口：{payload['summary']['source_fact_menu_count']}",
        f"- 需要合并承接的目标口径：{payload['summary']['merge_target_count']}",
        "",
        "### 用户意图",
        "",
    ]
    for intent, count in sorted(payload["summary"]["entry_intent_counts"].items()):
        lines.append(f"- {ENTRY_INTENTS.get(intent, intent)}：{count}")
    lines.extend(["", "### 产品域", ""])
    for domain, count in sorted(payload["summary"]["product_domain_counts"].items()):
        lines.append(f"- {DOMAIN_LABELS.get(domain, domain)}：{count}")
    lines.extend(["", "### 处置策略", ""])
    for policy, count in sorted(payload["summary"]["disposition_policy_counts"].items()):
        lines.append(f"- `{policy}`：{count}")
    lines.extend(["", "## 合并承接口径", ""])
    lines.append("| 承接目标 | 菜单数 |")
    lines.append("| --- | ---: |")
    for item in payload["merge_targets"]:
        lines.append(f"| {item['integration_target']} | {item['menu_count']} |")
    lines.extend(["", "## 62 菜单逐项矩阵", ""])
    lines.append("| # | 旧分组 | 旧菜单 | 产品域 | 用户意图 | 事实模型 | 处置策略 | 承接目标 | 默认分类 | 下一步 |")
    lines.append("| ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for row in payload["rows"]:
        lines.append(
            "| {index} | {group} | {menu} | {domain} | {intent} | `{model}` | `{policy}` | {target} | `{category}` | {next_action} |".format(
                index=row["index"],
                group=row["group"],
                menu=row["menu"],
                model=row["model"],
                domain=row["product_domain_label"],
                intent=row["entry_intent_label"],
                policy=row["disposition_policy"],
                target=row["integration_target"],
                category=row["default_business_category_code"] or "",
                next_action=row["next_action"],
            )
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    payload = _build_matrix()
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    OUTPUT_MD.write_text(_write_markdown(payload), encoding="utf-8")
    print(json.dumps({"ok": True, "output_json": str(OUTPUT_JSON), "output_md": str(OUTPUT_MD), **payload["summary"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
