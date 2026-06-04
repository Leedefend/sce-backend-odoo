#!/usr/bin/env python3
"""Seed the direct-project business menu supplement beside the SCBS55 baseline."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


SOURCE_DOCUMENT = "user:direct_project_business_menu:2026-05-30"
OUTPUT_JSON_NAME = "direct_project_business_menu_plan_write_result_v1.json"


MENU_GROUPS: list[tuple[str, list[str]]] = [
    ("合同类单据", ["施工合同", "分包合同", "租赁合同", "供货合同", "劳务合同", "机械合同（合同）"]),
    ("材料管理类单据", ["材料计划", "报价单", "入库", "材料结算单", "库存统计表（新）"]),
    ("劳务管理类单据", ["方单", "零星用工", "劳务结算"]),
    ("分包管理类单据", ["分包方单", "分包结算单"]),
    ("机械与租赁管理类单据", ["机械台班记录", "机械结算单", "租入", "还租", "租赁结算单"]),
    (
        "费用与资金管理类单据",
        [
            "项目费用报销单",
            "管理人员工资表",
            "油卡登记",
            "充值登记",
            "加油登记",
            "支付申请",
            "工程进度收款",
            "往来单位付款",
            "工程结算单",
            "进项上报",
            "总包进项上报",
            "成本统计表（数据）",
        ],
    ),
    ("项目管理类单据", ["施工日志（新）"]),
]


TARGETS: dict[str, dict[str, Any]] = {
    "施工合同": {"model": "construction.contract", "domain": "合同", "aliases": ["SCBS55#3 施工合同"]},
    "分包合同": {"model": "sc.subcontract.register", "domain": "分包", "fallback": "construction.contract"},
    "租赁合同": {"model": "sc.material.rental.order", "domain": "租赁", "fallback": "construction.contract"},
    "供货合同": {"model": "sc.expense.contract.ledger", "domain": "材料", "fallback": "sc.legacy.supplier.contract.pricing.fact"},
    "劳务合同": {"model": "sc.labor.contract", "domain": "劳务", "fallback": "sc.legacy.labor.subcontract.fact"},
    "机械合同（合同）": {"model": "sc.equipment.contract", "domain": "机械", "fallback": "sc.legacy.equipment.lease.fact"},
    "材料计划": {"model": "project.material.plan", "domain": "材料"},
    "报价单": {"model": "sc.material.rfq", "domain": "材料"},
    "入库": {"model": "sc.material.inbound", "domain": "材料"},
    "材料结算单": {"model": "sc.material.settlement", "domain": "材料"},
    "库存统计表（新）": {"model": "sc.material.stock.summary", "domain": "材料", "aliases": ["SCBS55#46 库存统计表（新）"]},
    "方单": {"model": "sc.labor.request", "domain": "劳务"},
    "零星用工": {"model": "sc.labor.usage", "domain": "劳务"},
    "劳务结算": {"model": "sc.labor.settlement", "domain": "劳务"},
    "分包方单": {"model": "sc.subcontract.register", "domain": "分包"},
    "分包结算单": {"model": "sc.subcontract.settlement", "domain": "分包"},
    "机械台班记录": {"model": "sc.equipment.usage", "domain": "机械"},
    "机械结算单": {"model": "sc.equipment.settlement", "domain": "机械"},
    "租入": {"model": "sc.material.rental.order", "domain": "租赁"},
    "还租": {"model": "sc.material.rental.order", "domain": "租赁"},
    "租赁结算单": {"model": "sc.material.rental.settlement", "domain": "租赁"},
    "项目费用报销单": {"model": "sc.expense.claim", "domain": "费用", "aliases": ["SCBS55#24 报销申请"]},
    "管理人员工资表": {"model": "sc.hr.payroll.document", "domain": "薪资"},
    "油卡登记": {"model": "sc.fund.account.operation", "domain": "资金", "action_name": "余额调整"},
    "充值登记": {"model": "sc.fund.account.operation", "domain": "资金", "action_name": "余额调整"},
    "加油登记": {"model": "sc.fund.account.operation", "domain": "资金", "action_name": "余额调整"},
    "支付申请": {"model": "payment.request", "domain": "资金", "aliases": ["SCBS55#29 支付申请"]},
    "工程进度收款": {"model": "sc.receipt.income", "domain": "收款", "aliases": ["SCBS55#35 到款确认表"]},
    "往来单位付款": {"model": "sc.payment.execution", "domain": "付款", "aliases": ["SCBS55#31 往来单位付款"]},
    "工程结算单": {"model": "sc.settlement.order", "domain": "结算"},
    "进项上报": {"model": "sc.legacy.invoice.tax.fact", "domain": "税务", "aliases": ["SCBS55#42 进项上报"]},
    "总包进项上报": {"model": "sc.general.contract.input.invoice", "domain": "税务", "fallback": "sc.legacy.invoice.tax.fact"},
    "成本统计表（数据）": {"model": "sc.comprehensive.cost.summary", "domain": "报表", "aliases": ["SCBS55#48 成本统计表（综合）"]},
    "施工日志（新）": {"model": "sc.construction.diary", "domain": "项目", "aliases": ["施工日志"]},
}


def artifact_root() -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.append(Path("/mnt/artifacts/migration"))
    candidates.append(Path(f"/tmp/direct_project_business_menu/{env.cr.dbname}"))  # noqa: F821
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return candidate
        except Exception:
            continue
    return Path(f"/tmp/direct_project_business_menu/{env.cr.dbname}")  # noqa: F821


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


def action_for(model: str, menu_name: str):
    Action = env["ir.actions.act_window"].sudo()  # noqa: F821
    action = Action.search([("res_model", "=", model), ("name", "=", menu_name)], order="id", limit=1)
    return action or Action.search([("res_model", "=", model)], order="id", limit=1)


def target_action_for(target: dict[str, Any], model: str, menu_name: str):
    action_name = target.get("action_name")
    if action_name:
        Action = env["ir.actions.act_window"].sudo()  # noqa: F821
        action = Action.search([("res_model", "=", model), ("name", "=", action_name)], order="id", limit=1)
        if action:
            return action
    if menu_name == "管理人员工资表":
        Action = env["ir.actions.act_window"].sudo()  # noqa: F821
        action = Action.search([("res_model", "=", model), ("name", "=", "工资登记")], order="id", limit=1)
        if action:
            return action
    return action_for(model, menu_name)


ensure_allowed_db()
artifact_dir = artifact_root()
Plan = env["sc.legacy.user.priority.menu.plan"].sudo().with_context(active_test=False)  # noqa: F821
IrModel = env["ir.model"].sudo()  # noqa: F821

created = 0
updated = 0
missing_models: list[dict[str, str]] = []
missing_actions: list[dict[str, str]] = []
sequence = 10

for group, names in MENU_GROUPS:
    for name in names:
        target = TARGETS[name]
        target_model = target["model"]
        model_record = IrModel.search([("model", "=", target_model)], limit=1)
        fallback_model = target.get("fallback")
        if not model_record and fallback_model:
            target_model = fallback_model
            model_record = IrModel.search([("model", "=", target_model)], limit=1)
        action = target_action_for(target, target_model, name) if model_record else env["ir.actions.act_window"].browse()  # noqa: F821
        status = "runtime_spec_landed" if model_record and action else "view_gap_audit_required"
        if not model_record:
            missing_models.append({"name": name, "target_model": target_model})
        elif not action:
            missing_actions.append({"name": name, "target_model": target_model})
        values = {
            "priority_sequence": sequence,
            "source_document": SOURCE_DOCUMENT,
            "legacy_menu_group": group,
            "legacy_menu_name": name,
            "business_domain": target["domain"],
            "target_model": target_model if model_record else "",
            "target_model_id": model_record.id if model_record else False,
            "target_action_id": action.id if action else False,
            "candidate_models_json": [
                {"model": target["model"], "role": "primary", "exists": bool(IrModel.search([("model", "=", target["model"])], limit=1))},
                *(
                    [{"model": fallback_model, "role": "fallback", "exists": bool(model_record)}]
                    if fallback_model and fallback_model != target["model"]
                    else []
                ),
            ],
            "list_field_contract": [],
            "search_contract": {
                "source": "user_direct_project_business_menu",
                "related_scbs55_entries": target.get("aliases", []),
                "menu_set": "direct_project",
                "must_not_overwrite_scbs55": True,
            },
            "form_section_contract": [],
            "surface_contract_status": status,
            "runtime_gap_summary": "" if status == "runtime_spec_landed" else "direct_project_menu_target_missing_or_action_missing",
            "current_round_action": "specialized_carrier_exists" if status == "runtime_spec_landed" else "next_topic_required",
            "target_iteration": "direct_project_business_data_enrichment_20260530",
            "old_system_path": f"直营项目系统菜单/{group}/{name}",
            "legacy_source_tables": "",
            "legacy_field_list": "",
            "extracted_evidence": "User-provided direct-project menu supplement; seeded as an overlay beside SCBS55, not a replacement.",
            "next_development_topic": "" if status == "runtime_spec_landed" else f"补齐{name}承载模型或独立 action/domain",
            "next_scope": "补旧系统字段/数据采集、目标投影和用户可见验收。" if status != "runtime_spec_landed" else "",
            "replay_status": "pending",
            "active": True,
        }
        existing = Plan.search(
            [
                ("source_document", "=", SOURCE_DOCUMENT),
                ("legacy_menu_group", "=", group),
                ("legacy_menu_name", "=", name),
            ],
            limit=1,
        )
        if existing:
            existing.write(values)
            updated += 1
        else:
            Plan.create(values)
            created += 1
        sequence += 10

env.cr.commit()  # noqa: F821

payload = {
    "status": "PASS" if not missing_models and not missing_actions else "REVIEW",
    "mode": "direct_project_business_menu_plan_write",
    "database": env.cr.dbname,  # noqa: F821
    "source_document": SOURCE_DOCUMENT,
    "expected_rows": sum(len(names) for _, names in MENU_GROUPS),
    "created": created,
    "updated": updated,
    "missing_models": missing_models,
    "missing_actions": missing_actions,
    "decision": "direct_project_menu_overlay_landed_without_overwriting_scbs55",
}
write_json(artifact_dir / OUTPUT_JSON_NAME, payload)
print("DIRECT_PROJECT_BUSINESS_MENU_PLAN_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
