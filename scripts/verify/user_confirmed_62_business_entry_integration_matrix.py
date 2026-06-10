# -*- coding: utf-8 -*-
"""Build the product-entry integration matrix from the locked 62 menu baseline.

This script is intentionally read-only. It does not inspect or mutate runtime
menu configuration; the locked user-visible baseline is the source of truth.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


PRODUCT_KEY = "construction.standard"
EXPECTED_MENU_COUNT = 62
BASELINE = Path("scripts/verify/baselines/user_confirmed_formal_menu_policy_62.json")
OUTPUT_JSON = Path("artifacts/user_confirmed_62_business_entry_integration_matrix.json")
OUTPUT_MD = Path("artifacts/user_confirmed_62_business_entry_integration_matrix.md")


FAMILY_BY_MODEL = {
    "res.partner": "master_data",
    "project.project": "project_center",
    "tender.bid": "tender_management",
    "tender.doc.purchase": "tender_management",
    "sc.general.contract": "contract_settlement",
    "construction.contract.income": "contract_settlement",
    "construction.contract.expense": "contract_settlement",
    "sc.settlement.order": "contract_settlement",
    "sc.construction.diary": "site_management",
    "project.material.plan": "materials_inventory",
    "sc.material.rfq": "materials_inventory",
    "sc.material.inbound": "materials_inventory",
    "sc.material.outbound": "materials_inventory",
    "sc.subcontract.request": "subcontract_labor_equipment",
    "sc.labor.usage": "subcontract_labor_equipment",
    "sc.equipment.usage": "subcontract_labor_equipment",
    "sc.receipt.income": "income_receivable",
    "sc.expense.claim": "payment_expense",
    "payment.request": "payment_expense",
    "sc.payment.execution": "payment_expense",
    "sc.financing.loan": "interfund_capital",
    "sc.fund.account.operation": "interfund_capital",
    "tender.guarantee": "guarantee_deposit",
    "sc.invoice.registration": "tax_invoice",
    "sc.tax.deduction.registration": "tax_invoice",
    "sc.office.admin.document": "hr_admin",
    "sc.legacy.user.profile": "hr_admin",
    "sc.hr.payroll.document": "hr_admin",
    "sc.document.admin.document": "document_certificate",
    "ui.menu.config.policy": "system_config",
}

FAMILY_LABELS = {
    "master_data": "主数据",
    "project_center": "项目中心",
    "tender_management": "投标管理",
    "contract_settlement": "合同与结算",
    "site_management": "施工现场",
    "materials_inventory": "材料与库存",
    "subcontract_labor_equipment": "分包劳务机械",
    "income_receivable": "收入与收款",
    "payment_expense": "付款与费用",
    "interfund_capital": "资金往来",
    "guarantee_deposit": "保证金",
    "tax_invoice": "发票税务",
    "hr_admin": "人事行政",
    "document_certificate": "资料证照",
    "system_config": "系统配置",
    "legacy_source_fact": "历史事实来源",
}

ENTRY_ROLES = {
    "master_data_entry": "主数据入口",
    "formal_handling_entry": "正式办理入口",
    "source_fact_detail": "锁定事实明细",
    "summary_analysis": "汇总分析入口",
    "config_entry": "配置入口",
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

SUMMARY_LABELS = {"资金日报表"}
CONFIG_LABELS = {"菜单配置"}
MASTER_DATA_MODELS = {"res.partner", "project.project"}

TARGET_BY_FAMILY = {
    "master_data": "基础资料与项目台账",
    "project_center": "项目台账",
    "tender_management": "投标管理办理",
    "contract_settlement": "合同与结算办理",
    "site_management": "施工现场办理",
    "materials_inventory": "材料采购库存办理",
    "subcontract_labor_equipment": "分包劳务机械办理",
    "income_receivable": "项目收入与收款办理",
    "payment_expense": "付款与费用办理",
    "interfund_capital": "资金往来与账户调拨办理",
    "guarantee_deposit": "保证金办理",
    "tax_invoice": "发票税务办理",
    "hr_admin": "人事行政办理",
    "document_certificate": "资料证照办理",
    "system_config": "系统配置",
    "legacy_source_fact": "来源事实明细",
}

REQUIRED_RELATIONSHIPS = {
    "master_data": ["company_id", "partner_id", "project_id"],
    "project_center": ["project_id", "partner_id"],
    "tender_management": ["project_id", "partner_id", "tender_id"],
    "contract_settlement": ["project_id", "partner_id", "contract_id"],
    "site_management": ["project_id", "date", "responsible_user_id"],
    "materials_inventory": ["project_id", "partner_id", "material_id", "warehouse_id"],
    "subcontract_labor_equipment": ["project_id", "partner_id", "contract_id", "cost_item_id"],
    "income_receivable": ["project_id", "partner_id", "contract_id", "fund_account_id"],
    "payment_expense": ["project_id", "partner_id", "contract_id", "fund_account_id", "cost_item_id"],
    "interfund_capital": ["source_project_id", "target_project_id", "partner_id", "fund_account_id"],
    "guarantee_deposit": ["project_id", "partner_id", "contract_id", "guarantee_type"],
    "tax_invoice": ["project_id", "partner_id", "contract_id", "invoice_type"],
    "hr_admin": ["project_id", "employee_id", "period_id"],
    "document_certificate": ["company_id", "project_id", "document_type"],
    "system_config": ["product_key", "user_id"],
    "legacy_source_fact": ["source_record_id", "project_id", "partner_id"],
}

LABEL_TARGET_OVERRIDES = {
    "客户": "客户主数据",
    "供应商": "供应商主数据",
    "项目台账": "项目台账",
    "收入合同执行": "收入合同办理",
    "支出合同执行": "支出合同办理",
    "收入合同结算": "收入合同结算办理",
    "支出合同结算": "支出合同结算办理",
    "收入": "项目收款登记",
    "工程进度款收入登记": "项目收款登记",
    "到款确认表": "到款确认来源明细",
    "付款还保证金": "保证金退还办理",
    "付款还保证金退回": "保证金退还办理",
    "自筹保证金": "保证金办理",
    "自筹保证金退回": "保证金退回办理",
    "扣款单": "扣款办理",
    "扣款实缴登记": "扣款办理",
    "扣款实缴退回": "扣款退回办理",
    "报销申请": "费用报销办理",
    "项目费用报销单": "费用报销办理",
    "公司财务支出": "付款执行",
    "往来单位付款": "付款执行",
    "支付申请": "付款申请",
    "承包人还项目款": "资金往来与账户调拨办理",
    "承包人借项目款": "资金往来与账户调拨办理",
    "项目借公司款登记": "资金往来与账户调拨办理",
    "项目还公司款登记": "资金往来与账户调拨办理",
    "账户间资金往来": "资金往来与账户调拨办理",
    "进项发票": "进项发票登记",
    "预缴税款": "税款预缴登记",
    "销项开票申请": "销项开票办理",
    "销项开票登记": "销项开票登记",
    "抵扣登记": "抵扣登记",
    "外经证登记": "外经证来源明细",
    "油卡登记": "油卡费用来源明细",
    "充值登记": "油卡充值来源明细",
    "租入": "租赁来源明细",
    "还租": "租赁来源明细",
    "方单": "劳务用工办理",
    "零星用工": "劳务用工办理",
    "机械台班记录": "机械台班办理",
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


def _family(label: str, model: str) -> str:
    if model in SOURCE_FACT_MODELS or label in SOURCE_FACT_LABELS:
        if label in {"油卡登记", "充值登记"}:
            return "payment_expense"
        if label in {"自筹垫付收入", "自筹垫付退回"}:
            return "income_receivable"
        if label in {"外经证登记"}:
            return "tax_invoice"
        if label in {"租入", "还租"}:
            return "materials_inventory"
        if label in {"公司人员名册"}:
            return "hr_admin"
        return "legacy_source_fact"
    return FAMILY_BY_MODEL.get(model, "legacy_source_fact")


def _entry_role(label: str, model: str, family: str) -> str:
    if label in CONFIG_LABELS:
        return "config_entry"
    if label in SUMMARY_LABELS:
        return "summary_analysis"
    if model in MASTER_DATA_MODELS:
        return "master_data_entry"
    if model in SOURCE_FACT_MODELS or label in SOURCE_FACT_LABELS:
        return "source_fact_detail"
    return "formal_handling_entry"


def _integration_target(label: str, family: str, role: str) -> str:
    if label in LABEL_TARGET_OVERRIDES:
        return LABEL_TARGET_OVERRIDES[label]
    if role == "source_fact_detail":
        return f"{TARGET_BY_FAMILY.get(family, '正式办理入口')}的来源明细"
    return TARGET_BY_FAMILY.get(family, "正式办理入口")


def _next_action(role: str, label: str, target: str) -> str:
    if role == "source_fact_detail":
        return f"保留只读追溯；通过非侵入式映射进入“{target}”，不作为新增办理主入口。"
    if role == "summary_analysis":
        return "保留为分析口径；不得替代正式办理单据。"
    if role == "config_entry":
        return "保留给实施/配置人员；不作为普通业务办理入口。"
    if label == target or role == "master_data_entry":
        return "作为正式入口继续完善新增、编辑、状态、附件和关系字段。"
    return f"保留用户已确认入口名；底层能力向“{target}”统一，减少重复认知。"


def _build_matrix() -> dict:
    menus = _load_menus()
    if len(menus) != EXPECTED_MENU_COUNT:
        raise AssertionError(f"expected {EXPECTED_MENU_COUNT} menus, got {len(menus)}")

    rows = []
    for index, menu in enumerate(menus, 1):
        label = menu.get("label") or menu.get("name") or ""
        model = menu.get("res_model") or ""
        family = _family(label, model)
        role = _entry_role(label, model, family)
        target = _integration_target(label, family, role)
        rows.append(
            {
                "index": index,
                "group": menu.get("group_label") or "",
                "menu": label,
                "model": model,
                "menu_xmlid": menu.get("menu_xmlid") or "",
                "action_id": menu.get("action_id") or 0,
                "sequence": menu.get("sequence") or 0,
                "business_family": family,
                "business_family_label": FAMILY_LABELS.get(family, family),
                "entry_role": role,
                "entry_role_label": ENTRY_ROLES[role],
                "integration_target": target,
                "required_relationships": REQUIRED_RELATIONSHIPS.get(family, []),
                "next_action": _next_action(role, label, target),
                "locked_data_policy": "read_only_source_facts_no_rewrite",
            }
        )

    family_counts = Counter(row["business_family"] for row in rows)
    role_counts = Counter(row["entry_role"] for row in rows)
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
            "menu_count_must_equal": EXPECTED_MENU_COUNT,
            "locked_user_visible_surface": True,
            "locked_fact_data_must_not_be_rewritten": True,
            "purpose": "classify confirmed list pages into formal handling entries, source fact details, summary analysis, and consolidation targets",
        },
        "summary": {
            "menu_count": len(rows),
            "group_counts": dict(sorted(group_counts.items())),
            "family_counts": dict(sorted(family_counts.items())),
            "entry_role_counts": dict(sorted(role_counts.items())),
            "merge_target_count": len(merge_targets),
            "formal_handling_menu_count": role_counts["formal_handling_entry"],
            "source_fact_detail_menu_count": role_counts["source_fact_detail"],
        },
        "merge_targets": merge_targets,
        "rows": rows,
    }


def _write_markdown(payload: dict) -> str:
    lines = [
        "# 用户确认 62 可见列表业务入口整合矩阵",
        "",
        "本文件由 `scripts/verify/user_confirmed_62_business_entry_integration_matrix.py` 生成。",
        "",
        "## 判定边界",
        "",
        "- 62 个用户已确认可见列表是入口设计基线，不在本轮改名、隐藏或重排。",
        "- 用户锁定的业务事实数据只读，不写回、不覆盖。",
        "- 正式办理能力通过正式模型、新单据、派生视图或非侵入式映射承接。",
        "- 旧入口名称不等于产品化办理口径；可保留用户已确认入口，同时向统一业务口径收敛。",
        "",
        "## 汇总",
        "",
        f"- 菜单数：{payload['summary']['menu_count']}",
        f"- 正式办理入口：{payload['summary']['formal_handling_menu_count']}",
        f"- 来源事实明细：{payload['summary']['source_fact_detail_menu_count']}",
        f"- 需要合并承接的目标口径：{payload['summary']['merge_target_count']}",
        "",
        "### 入口角色",
        "",
    ]
    for role, count in sorted(payload["summary"]["entry_role_counts"].items()):
        lines.append(f"- {ENTRY_ROLES.get(role, role)}：{count}")
    lines.extend(["", "### 业务域", ""])
    for family, count in sorted(payload["summary"]["family_counts"].items()):
        lines.append(f"- {FAMILY_LABELS.get(family, family)}：{count}")
    lines.extend(["", "## 合并承接口径", ""])
    lines.append("| 承接目标 | 菜单数 |")
    lines.append("| --- | ---: |")
    for item in payload["merge_targets"]:
        lines.append(f"| {item['integration_target']} | {item['menu_count']} |")
    lines.extend(["", "## 62 菜单逐项矩阵", ""])
    lines.append("| # | 分组 | 菜单 | 模型 | 角色 | 业务域 | 承接目标 | 下一步 |")
    lines.append("| ---: | --- | --- | --- | --- | --- | --- | --- |")
    for row in payload["rows"]:
        lines.append(
            "| {index} | {group} | {menu} | `{model}` | {role} | {family} | {target} | {next_action} |".format(
                index=row["index"],
                group=row["group"],
                menu=row["menu"],
                model=row["model"],
                role=row["entry_role_label"],
                family=row["business_family_label"],
                target=row["integration_target"],
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
