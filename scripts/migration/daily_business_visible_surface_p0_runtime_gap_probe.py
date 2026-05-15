#!/usr/bin/env python3
"""Read-only runtime gap probe for P0 daily business visible-surface specs."""

from __future__ import annotations

import json
import os
from pathlib import Path
from xml.etree import ElementTree


SOURCE_DOCUMENT = "/home/odoo/workspace/partner_import_source/老系统列表，填单页面截图.docx"
EXPECTED_ROWS = 18
LEGACY_LABEL_ALIASES = {
    "单据状态": {"state", "legacy_document_state", "状态", "历史状态", "历史单据状态"},
    "状态": {"state", "legacy_document_state", "状态", "历史状态", "历史单据状态"},
    "推送结果": {"sync_state", "push_state", "kingdee_state", "金蝶状态", "推送状态"},
    "金蝶单据编号": {"kingdee_bill_no", "kingdee_no", "金蝶单据编号"},
    "项目名称": {"project_id", "project_name", "项目", "项目名称"},
    "工程项目": {"project_id", "project_name", "项目", "工程项目"},
    "投标项目": {"project_id", "tender_project_id", "tender_project_name", "项目", "投标项目"},
    "投标项目名称": {"project_id", "tender_project_id", "tender_project_name", "项目", "投标项目名称"},
    "单据编号": {"name", "document_no", "business_no", "单据编号", "业务编号"},
    "单位编号": {"code", "legacy_partner_id", "partner_code", "单位编号"},
    "单位名称": {"partner_id", "name", "display_name", "关联往来单位", "往来单位", "单位名称"},
    "往来单位名称": {"partner_id", "关联往来单位", "往来单位", "往来单位名称"},
    "往来单位/付款单位": {"partner_id", "payer_id", "付款单位", "往来单位"},
    "对方单位/付款": {"partner_id", "payer_id", "付款单位", "往来单位"},
    "收款单位": {"partner_id", "payee", "收款人", "往来单位"},
    "收款单位名称": {"partner_id", "payee", "收款人", "往来单位"},
    "录入人": {"source_created_by", "creator_name", "create_uid", "历史录入人", "录入人", "Createdby"},
    "填写人": {"source_created_by", "creator_name", "create_uid", "填写人", "历史录入人", "录入人"},
    "登记人": {"source_created_by", "creator_name", "create_uid", "登记人", "历史录入人", "录入人"},
    "录入时间": {"source_created_at", "created_time", "create_date", "历史录入时间", "录入时间", "Createdon"},
    "登记时间": {"source_created_at", "created_time", "create_date", "历史录入时间", "登记时间"},
    "备注": {"note", "remark", "description", "备注"},
    "附件": {"attachment_ids", "legacy_attachment_ref", "附件", "历史附件引用"},
    "附件信息": {"attachment_ids", "legacy_attachment_ref", "附件", "附件信息"},
    "开户银行": {"bank_id", "bank_name", "receiving_bank_name", "payer_bank", "开户行", "开户银行"},
    "开户行": {"bank_id", "bank_name", "receiving_bank_name", "payer_bank", "开户行", "开户银行"},
    "账号": {"bank_account_id", "account_no", "receiving_account_no", "payee_account", "账号"},
    "银行账号": {"bank_account_id", "account_no", "receiving_account_no", "payee_account", "银行账号"},
    "开户账号": {"bank_account_id", "account_no", "receiving_account_no", "payee_account", "开户账号"},
    "收款账号": {"receiving_account_no", "payee_account", "receipt_bank_account_id", "收款账号"},
    "付款账号": {"source_account_id", "payer_account", "bank_account_id", "付款账户", "付款账号"},
    "付款账户": {"source_account_id", "payer_account", "bank_account_id", "付款账户"},
    "收款账户": {"target_account_id", "receiving_account", "receipt_bank_account_id", "收款账户"},
    "退回账户": {"target_account_id", "receiving_account", "receipt_bank_account_id", "退回账户"},
    "金额": {"amount", "金额"},
    "付款金额": {"amount", "approved_amount", "申请金额", "批准金额", "付款金额"},
    "收款金额": {"amount", "收款金额"},
    "进账金额": {"amount", "收款金额", "进账金额"},
    "自筹金额": {"amount", "金额", "自筹金额"},
    "退回金额": {"amount", "金额", "退回金额"},
    "退还金额": {"amount", "金额", "退还金额"},
    "保证金金额": {"amount", "金额", "保证金金额"},
    "借款金额": {"amount", "金额", "借款金额"},
    "付款时间": {"operation_date", "date_claim", "business_date", "单据日期", "付款时间"},
    "收款时间": {"date_receipt", "operation_date", "business_date", "单据日期", "收款时间"},
    "日期": {"operation_date", "business_date", "date", "date_receipt", "date_claim", "单据日期"},
    "单据日期": {"operation_date", "business_date", "document_date", "date", "date_receipt", "date_claim", "单据日期"},
    "申请时间": {"business_date", "document_date", "created_time", "申请时间"},
    "申请人": {"employee_user_id", "employee_name", "source_created_by", "creator_name", "申请人"},
    "申请人姓名": {"employee_user_id", "employee_name", "人员姓名", "申请人姓名"},
    "姓名": {"employee_user_id", "employee_name", "人员姓名", "姓名"},
    "人员类型": {"fact_type", "item_type", "业务类型", "事项类型", "人员类型"},
    "类型": {"type", "fact_type", "item_type", "业务类型", "类型"},
    "业务类型": {"type", "fact_type", "operation_type", "loan_type", "claim_type", "source_kind", "业务类型"},
    "请假类型": {"leave_type", "请假类型"},
    "年度": {"period_year", "年度"},
    "年份": {"period_year", "年度"},
    "月份": {"period_month", "月份"},
    "应发工资": {"gross_amount", "应发工资"},
    "实发工资": {"net_salary", "实发工资"},
    "发放单位": {"payer_unit", "缴纳单位", "发放单位"},
    "收款账户名称": {"receiving_account_name", "receipt_account_name", "收款账户名称"},
    "付款账户名称": {"payment_account_name", "付款账户名称"},
    "保证金类型": {"type", "guarantee_type", "类型", "保证金类型"},
    "收入类别": {"receipt_type", "source_kind", "收款类型", "业务类型", "收入类别"},
    "成本类别": {"expense_type", "claim_type", "费用类型", "业务类型", "成本类别"},
}


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


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_report(path: Path, payload: dict[str, object]) -> None:
    lines = [
        "# Daily Business Visible Surface P0 Runtime Gap Probe v1",
        "",
        f"Status: {payload['status']}",
        f"Database: {payload['database']}",
        "",
        "## Runtime Gaps",
        "",
        "| priority | entry | target model | list fields | tree matched | form matched | missing model labels |",
        "| ---: | --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for row in payload["entries"]:
        lines.append(
            "| {priority_sequence} | {legacy_menu_group}/{legacy_menu_name} | {target_model} | "
            "{list_field_count} | {tree_matched_count} | {form_matched_count} | {missing_model_label_count} |".format(
                **row
            )
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
            "## Detail",
            "",
            "```json",
            json.dumps(payload["entries"], ensure_ascii=False, indent=2),
            "```",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def normalize(value: object) -> str:
    return str(value or "").strip().replace(" ", "").replace("\u3000", "")


def alias_tokens(label: str) -> set[str]:
    normalized = normalize(label)
    values = {normalized}
    values.update(normalize(item) for item in LEGACY_LABEL_ALIASES.get(label, set()))
    values.update(normalize(item) for item in LEGACY_LABEL_ALIASES.get(normalized, set()))
    return {item for item in values if item}


def field_nodes_from_arch(arch: str) -> list[ElementTree.Element]:
    if not arch:
        return []
    try:
        root = ElementTree.fromstring(arch.encode("utf-8"))
    except Exception:
        return []
    return list(root.iter("field"))


def view_field_index(model_name: str, view_type: str, fields_meta: dict[str, dict[str, object]]) -> dict[str, dict[str, str]]:
    try:
        views = env[model_name].sudo().get_views([(False, view_type)], {})  # noqa: F821
    except Exception:
        return {}
    view = ((views.get("views") or {}).get(view_type) or {}) if isinstance(views, dict) else {}
    index = {}
    for node in field_nodes_from_arch(str(view.get("arch") or "")):
        name = str(node.attrib.get("name") or "").strip()
        label = str(node.attrib.get("string") or "").strip()
        if not label and name:
            meta = fields_meta.get(name) or {}
            label = str(meta.get("string") or "").strip()
        if name:
            index[name] = {"field": name, "label": label}
    return index


def model_field_index(fields_meta: dict[str, dict[str, object]]) -> dict[str, dict[str, str]]:
    return {
        name: {"field": name, "label": str((meta or {}).get("string") or "").strip()}
        for name, meta in fields_meta.items()
    }


def match_label(label: str, index: dict[str, dict[str, str]]) -> dict[str, str] | None:
    aliases = alias_tokens(label)
    for field_name, meta in index.items():
        candidates = {normalize(field_name), normalize(meta.get("label"))}
        if aliases & candidates:
            return {"legacy_label": label, "field": field_name, "field_label": meta.get("label") or field_name}
    return None


artifact_root = resolve_artifact_root()
output_json = artifact_root / "daily_business_visible_surface_p0_runtime_gap_probe_result_v1.json"
output_report = artifact_root / "daily_business_visible_surface_p0_runtime_gap_probe_report_v1.md"

Plan = env["sc.legacy.user.priority.menu.plan"].sudo().with_context(active_test=False)  # noqa: F821
records = Plan.search(
    [
        ("source_document", "=", SOURCE_DOCUMENT),
        ("target_iteration", "=", "p0_daily_business_visible_surface"),
    ],
    order="priority_sequence, legacy_menu_group, legacy_menu_name",
)

entries = []
for record in records:
    target_model = str(record.target_model or "").strip()
    labels = [
        str(row.get("legacy_label") or "").strip()
        for row in (record.list_field_contract or [])
        if isinstance(row, dict) and str(row.get("legacy_label") or "").strip()
    ]
    model_exists = bool(target_model and target_model in env)  # noqa: F821
    fields_meta = env[target_model].sudo().fields_get() if model_exists else {}  # noqa: F821
    model_index = model_field_index(fields_meta) if model_exists else {}
    tree_index = view_field_index(target_model, "tree", fields_meta) if model_exists else {}
    form_index = view_field_index(target_model, "form", fields_meta) if model_exists else {}
    model_matches = [match for label in labels if (match := match_label(label, model_index))]
    tree_matches = [match for label in labels if (match := match_label(label, tree_index))]
    form_matches = [match for label in labels if (match := match_label(label, form_index))]
    model_matched_labels = {normalize(match["legacy_label"]) for match in model_matches}
    tree_matched_labels = {normalize(match["legacy_label"]) for match in tree_matches}
    form_matched_labels = {normalize(match["legacy_label"]) for match in form_matches}
    model_missing = sorted(label for label in labels if normalize(label) not in model_matched_labels)
    tree_missing = sorted(label for label in labels if normalize(label) not in tree_matched_labels)
    form_missing = sorted(label for label in labels if normalize(label) not in form_matched_labels)
    entries.append(
        {
            "priority_sequence": record.priority_sequence,
            "legacy_menu_group": record.legacy_menu_group,
            "legacy_menu_name": record.legacy_menu_name,
            "target_model": target_model,
            "model_exists": model_exists,
            "target_action_id": int(record.target_action_id.id or 0),
            "list_field_count": len(labels),
            "tree_matched_count": len(tree_matches),
            "form_matched_count": len(form_matches),
            "model_matched_count": len(model_matches),
            "tree_matches": tree_matches,
            "form_matches": form_matches,
            "model_matches": model_matches,
            "missing_tree_labels": tree_missing,
            "missing_form_labels": form_missing,
            "missing_model_labels": model_missing,
            "missing_model_label_count": len(model_missing),
        }
    )

errors = []
if len(records) != EXPECTED_ROWS:
    errors.append({"check": "row_count", "expected": EXPECTED_ROWS, "actual": len(records)})
if any(not row["model_exists"] for row in entries):
    errors.append({"check": "target_model_exists", "entries": [row["legacy_menu_name"] for row in entries if not row["model_exists"]]})

total_field_count = sum(int(row["list_field_count"]) for row in entries)
summary = {
    "total_field_count": total_field_count,
    "model_matched_count": sum(int(row["model_matched_count"]) for row in entries),
    "tree_matched_count": sum(int(row["tree_matched_count"]) for row in entries),
    "form_matched_count": sum(int(row["form_matched_count"]) for row in entries),
    "model_missing_count": sum(int(row["missing_model_label_count"]) for row in entries),
    "tree_missing_count": sum(len(row["missing_tree_labels"]) for row in entries),
    "form_missing_count": sum(len(row["missing_form_labels"]) for row in entries),
    "fully_model_aligned_entries": [
        row["legacy_menu_name"] for row in entries if int(row["model_matched_count"]) == int(row["list_field_count"])
    ],
    "fully_tree_aligned_entries": [
        row["legacy_menu_name"] for row in entries if int(row["tree_matched_count"]) == int(row["list_field_count"])
    ],
    "fully_form_aligned_entries": [
        row["legacy_menu_name"] for row in entries if int(row["form_matched_count"]) == int(row["list_field_count"])
    ],
}

payload = {
    "status": "PASS" if not errors else "FAIL",
    "mode": "daily_business_visible_surface_p0_runtime_gap_probe",
    "database": env.cr.dbname,  # noqa: F821
    "source_document": SOURCE_DOCUMENT,
    "expected_rows": EXPECTED_ROWS,
    "row_count": len(records),
    "summary": summary,
    "entries": entries,
    "errors": errors,
    "db_writes": 0,
    "decision": "daily_business_visible_surface_p0_runtime_gap_audited" if not errors else "STOP_REVIEW_REQUIRED",
}
write_json(output_json, payload)
write_report(output_report, payload)
print("DAILY_BUSINESS_VISIBLE_SURFACE_P0_RUNTIME_GAP_PROBE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
if errors:
    raise SystemExit(2)
