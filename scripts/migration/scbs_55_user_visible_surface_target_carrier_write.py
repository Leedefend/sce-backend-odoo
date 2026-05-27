#!/usr/bin/env python3
"""Map SCBS 55 live visible surfaces to current Odoo carrier models."""

from __future__ import annotations

import json
import os
from pathlib import Path


SOURCE_DOCUMENT = "/home/odoo/workspace/partner_import_source/5.6优化（老系统菜单，字段列表展示）1.docx"
OUTPUT_JSON_NAME = "scbs_55_user_visible_surface_target_carrier_write_result_v1.json"


def artifact_root() -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.append(Path("/mnt/artifacts/migration"))
    candidates.append(Path(f"/tmp/scbs_55_visible_surface/{env.cr.dbname}"))  # noqa: F821
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return candidate
        except Exception:
            continue
    return Path(f"/tmp/scbs_55_visible_surface/{env.cr.dbname}")  # noqa: F821


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


def carrier(model: str, *candidates: str, note: str = "") -> dict[str, object]:
    ordered = [model]
    ordered.extend(item for item in candidates if item and item not in ordered)
    return {"target_model": model, "candidate_models": ordered, "note": note}


CARRIER_MAP = {
    "供应商/合作单位": carrier("sc.business.entity", "res.partner", "sc.partner.import.review"),
    "往来单位": carrier("sc.business.entity", "res.partner"),
    "施工合同": carrier("construction.contract", "sc.income.contract.ledger"),
    "公司资料存档": carrier("sc.document.admin.document", "sc.office.admin.document", "sc.project.document"),
    "请假/休假审批单": carrier("sc.office.admin.document"),
    "印章使用审批表": carrier("sc.office.admin.document"),
    "组织机构": carrier("hr.department", "sc.legacy.department", note="legacy custom page maps to organization department"),
    "公司人员名册（配置）": carrier("sc.legacy.user.profile", "res.users"),
    "社保人员登记": carrier("sc.hr.payroll.document", "sc.legacy.salary.line"),
    "社保登记": carrier("sc.hr.payroll.document", "sc.salary.summary"),
    "工资登记": carrier("sc.hr.payroll.document", "sc.legacy.salary.line", "sc.salary.summary"),
    "补助": carrier("sc.hr.payroll.document", "sc.legacy.salary.line"),
    "奖金": carrier("sc.hr.payroll.document", "sc.legacy.salary.line"),
    "证照登记": carrier("sc.document.admin.document", "sc.legacy.file.index"),
    "借阅申请": carrier("sc.document.admin.document", "sc.office.admin.document"),
    "投标报名管理": carrier("tender.bid", "sc.legacy.tender.registration.fact"),
    "投标报名费申请": carrier("payment.request", "tender.bid"),
    "自筹保证金": carrier("tender.guarantee", "sc.legacy.self.funding.fact"),
    "自筹保证金退回": carrier("tender.guarantee", "sc.fund.account.operation"),
    "付款还保证金": carrier("tender.guarantee", "payment.request", "sc.payment.execution"),
    "付款还保证金退回": carrier("tender.guarantee", "sc.fund.account.operation"),
    "借款申请": carrier("sc.financing.loan", "sc.legacy.financing.loan.fact"),
    "还款登记": carrier("sc.financing.loan", "sc.fund.account.operation"),
    "报销申请": carrier("sc.expense.claim", "sc.legacy.expense.reimbursement.line"),
    "收入": carrier("sc.receipt.income", "sc.legacy.receipt.income.fact"),
    "公司财务支出": carrier("sc.expense.claim", "sc.payment.execution", "sc.legacy.finance.auxiliary.fact"),
    "承包人还项目款": carrier("sc.financing.loan", "sc.fund.account.operation"),
    "承包人借项目款": carrier("sc.financing.loan", "sc.legacy.project.fund.balance.fact"),
    "支付申请": carrier("payment.request", "payment.request.line"),
    "扣款单": carrier("sc.tax.deduction.registration", "sc.legacy.deduction.adjustment.line"),
    "往来单位付款": carrier("sc.payment.execution", "payment.request"),
    "账户间资金往来": carrier("sc.fund.account.operation", "sc.legacy.account.transaction.line"),
    "扣款实缴登记": carrier("sc.tax.deduction.registration", "sc.fund.account.operation"),
    "扣款实缴退回": carrier("sc.tax.deduction.registration", "sc.fund.account.operation"),
    "到款确认表": carrier("sc.legacy.fund.confirmation.document", "sc.legacy.fund.confirmation.line", "sc.receipt.income"),
    "资金日报表": carrier("sc.legacy.fund.daily.line", "sc.legacy.fund.daily.snapshot.fact", "sc.fund.daily.summary"),
    "项目借公司款登记": carrier("sc.financing.loan", "sc.legacy.project.fund.balance.fact"),
    "项目还公司款登记": carrier("sc.financing.loan", "sc.fund.account.operation"),
    "开票申请": carrier("sc.invoice.registration", "sc.legacy.invoice.registration.line"),
    "开票登记": carrier("sc.invoice.registration", "sc.legacy.income.invoice.fact"),
    "预缴税款": carrier("sc.invoice.registration", "sc.legacy.income.invoice.fact"),
    "进项上报": carrier("sc.legacy.invoice.tax.fact", "sc.tax.deduction.registration"),
    "抵扣登记": carrier("sc.tax.deduction.registration", "sc.legacy.tax.deduction.fact"),
    "外经证登记": carrier("sc.legacy.finance.auxiliary.fact", "sc.legacy.business.fact.residual"),
    "供货合同分析": carrier("sc.legacy.report.inventory", "sc.expense.contract.ledger"),
    "库存统计表（新）": carrier("sc.material.stock.summary", "sc.legacy.material.stock.fact"),
    "账户收支统计表": carrier("sc.account.income.expense.summary", "sc.legacy.account.transaction.line"),
    "成本统计表（综合）": carrier("sc.comprehensive.cost.summary", "project.cost.ledger"),
    "投标保证金报表": carrier("sc.legacy.tender.registration.fact", "tender.guarantee"),
    "发票成本进度报表": carrier("sc.invoice.category.summary", "sc.invoice.registration"),
    "发票分析报表": carrier("sc.invoice.category.summary", "sc.invoice.registration"),
    "项目经营统计表": carrier("sc.company.operation.summary", "sc.operating.metrics.project"),
    "应收应付报表": carrier("sc.ar.ap.project.summary", "sc.ar.ap.company.summary"),
    "成本大屏": carrier("sc.operating.metrics.project", "sc.comprehensive.cost.summary"),
    "经营大屏": carrier("sc.operating.metrics.project", "sc.company.operation.summary"),
}


def first_action_for_model(model: str):
    return env["ir.actions.act_window"].sudo().search([("res_model", "=", model)], order="id", limit=1)  # noqa: F821


ensure_allowed_db()
artifact_dir = artifact_root()
Plan = env["sc.legacy.user.priority.menu.plan"].sudo().with_context(active_test=False)  # noqa: F821
IrModel = env["ir.model"].sudo()  # noqa: F821

domain = [("source_document", "=", SOURCE_DOCUMENT)]
rows = Plan.search(domain, order="priority_sequence")
updated = 0
missing_map: list[str] = []
missing_model: list[dict[str, str]] = []
without_action: list[dict[str, str]] = []

for record in rows:
    mapping = CARRIER_MAP.get(record.legacy_menu_name)
    if not mapping:
        missing_map.append(record.legacy_menu_name)
        record.write({"surface_contract_status": "view_gap_audit_required"})
        continue

    candidates = mapping["candidate_models"]
    target_model = mapping["target_model"]
    target_model_record = IrModel.search([("model", "=", target_model)], limit=1)
    if not target_model_record:
        missing_model.append({"name": record.legacy_menu_name, "target_model": target_model})
        target_model = ""

    action = first_action_for_model(target_model) if target_model else env["ir.actions.act_window"].browse()  # noqa: F821
    if target_model and not action:
        without_action.append({"name": record.legacy_menu_name, "target_model": target_model})

    candidate_payload = [
        {
            "model": model,
            "exists": bool(IrModel.search([("model", "=", model)], limit=1)),
            "role": "primary" if index == 0 else "candidate",
        }
        for index, model in enumerate(candidates)
    ]
    status = "runtime_spec_landed" if target_model_record else "view_gap_audit_required"
    if record.surface_contract_status == "view_gap_audit_required":
        status = "view_gap_audit_required"

    record.write(
        {
            "target_model": target_model or mapping["target_model"],
            "target_model_id": target_model_record.id if target_model_record else False,
            "target_action_id": action.id if action else False,
            "candidate_models_json": candidate_payload,
            "surface_contract_status": status,
            "runtime_gap_summary": "; ".join(
                part
                for part in [
                    record.runtime_gap_summary or "",
                    mapping.get("note", ""),
                    "target_action_missing" if target_model and not action else "",
                ]
                if part
            ),
        }
    )
    updated += 1

env.cr.commit()  # noqa: F821

payload = {
    "status": "PASS" if updated == len(rows) and not missing_map and not missing_model else "FAIL",
    "mode": "scbs_55_user_visible_surface_target_carrier_write",
    "database": env.cr.dbname,  # noqa: F821
    "source_document": SOURCE_DOCUMENT,
    "expected_rows": len(CARRIER_MAP),
    "row_count": len(rows),
    "updated": updated,
    "missing_map": missing_map,
    "missing_model": missing_model,
    "without_action": without_action,
    "db_writes": updated,
    "decision": "scbs_55_target_carriers_landed" if updated == len(rows) and not missing_map and not missing_model else "STOP_REVIEW_REQUIRED",
}
write_json(artifact_dir / OUTPUT_JSON_NAME, payload)
print("SCBS_55_USER_VISIBLE_SURFACE_TARGET_CARRIER_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
if payload["status"] != "PASS":
    raise SystemExit(2)
