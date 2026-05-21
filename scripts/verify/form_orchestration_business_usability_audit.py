#!/usr/bin/env python3
"""Audit whether v2 form orchestration still supports business form use.

This is intentionally a read-only audit.  It inspects the runtime
Unified Page Contract v2 after the orchestration layer has assembled the form.
"""

from __future__ import annotations

import argparse
import ast
import csv
import json
import os
import re
import sys
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


ROOT = Path(os.environ.get("SC_REPO_ROOT") or Path.cwd()).resolve()
DEFAULT_OUTPUT_DIR = ROOT / "docs/audit/native/form_orchestration_business_usability"

BUSINESS_MODEL_PREFIXES = (
    "construction.",
    "project.",
    "quota.",
    "sc.equipment.",
    "sc.financing.",
    "sc.fund.",
    "sc.invoice.",
    "sc.labor.",
    "sc.material.",
    "sc.payment.",
    "sc.quality.",
    "sc.receipt.",
    "sc.safety.",
    "sc.subcontract.",
    "sc.tax.",
    "tender.",
)
BUSINESS_MODEL_EXACT = {
    "payment.ledger",
    "payment.request",
    "payment.request.line",
}
TECHNICAL_MODEL_PREFIXES = (
    "base.",
    "bus.",
    "digest.",
    "fetchmail.",
    "iap.",
    "ir.",
    "mail.",
    "portal.",
    "res.config",
    "web.",
)
TECHNICAL_MODEL_TOKENS = (
    ".wizard",
    ".settings",
    ".config",
    ".installer",
)
TECHNICAL_MODEL_EXACT = {
    "payment.provider",
    "payment.token",
    "payment.transaction",
}
REPORT_OR_SUMMARY_SUFFIXES = (
    ".report",
    ".summary",
)
SYSTEM_FIELD_NAMES = {
    "id",
    "display_name",
    "__last_update",
    "create_uid",
    "create_date",
    "write_uid",
    "write_date",
    "message_follower_ids",
    "message_ids",
    "message_main_attachment_id",
    "activity_ids",
}
SYSTEM_FIELD_PREFIXES = (
    "access_",
    "activity_",
    "message_",
    "website_",
)
EXPLICIT_IDENTITY_FIELD_NAMES = {
    "name",
    "display_name",
    "code",
    "number",
    "sequence",
    "ref",
    "reference",
    "doc_no",
    "document_no",
    "bill_no",
    "contract_no",
    "request_no",
}
PARENT_ANCHOR_FIELD_NAMES = {
    "bid_id",
    "issue_id",
    "payment_request_id",
    "request_id",
    "settlement_id",
    "invoice_id",
    "receipt_id",
    "contract_id",
    "order_id",
    "plan_id",
    "ledger_id",
    "baseline_id",
    "wbs_id",
    "task_id",
    "line_id",
}
TEMPORAL_FIELD_NAMES = {
    "date",
    "paid_at",
    "open_time",
    "recheck_date",
    "rectification_date",
    "entry_date",
    "request_date",
    "settlement_date",
    "invoice_date",
    "receipt_date",
    "period_id",
}
EXPLICIT_IDENTITY_LABEL_TOKENS = (
    "名称",
    "编号",
    "单据号",
    "合同编号",
    "流水号",
    "引用",
    "参考",
)


@dataclass
class FormBusinessUsabilityRow:
    model: str
    source: str
    domain_group: str
    status: str
    business_ready: str
    contract_ok: str
    boundary_ok: str
    structure_ok: str
    create_allowed: str
    write_allowed: str
    structure_field_count: int
    layout_field_count: int
    editable_business_field_count: int
    required_business_field_count: int
    missing_required_fields: str
    relation_field_count: int
    relation_missing_metadata: str
    x2many_field_count: int
    attachment_enabled: str
    timeline_enabled: str
    identity_signal: str
    state_signal: str
    amount_signal: str
    project_signal: str
    partner_signal: str
    gaps: str
    gap_owner_layer: str
    remediation_rule: str


@dataclass
class P1BusinessExpectationRow:
    entry_id: str
    entry_name: str
    domain: str
    selected_model: str
    status: str
    missing_sections: str
    missing_fields: str
    gaps: str


def _text(value: Any) -> str:
    return str(value or "").strip()


def _norm(value: Any) -> str:
    return re.sub(r"\s+", "", str(value or "")).strip()


def is_transient_or_setup(model: str) -> bool:
    return any(token in model for token in TECHNICAL_MODEL_TOKENS) or model.endswith(".wizard")


def is_business_model(model: str) -> bool:
    if not model:
        return False
    if model.startswith(TECHNICAL_MODEL_PREFIXES):
        return False
    if model in TECHNICAL_MODEL_EXACT:
        return False
    if is_transient_or_setup(model):
        return False
    if model.endswith(REPORT_OR_SUMMARY_SUFFIXES):
        return False
    return model in BUSINESS_MODEL_EXACT or model.startswith(BUSINESS_MODEL_PREFIXES)


def domain_group(model: str) -> str:
    if model.startswith("project."):
        return "project"
    if model.startswith("construction."):
        return "contract"
    if model.startswith("payment."):
        return "finance"
    if model.startswith("tender."):
        return "tender"
    if model.startswith("sc.material."):
        return "material"
    if model.startswith("sc.subcontract."):
        return "subcontract"
    if model.startswith("sc.labor."):
        return "labor"
    if model.startswith("sc.equipment."):
        return "equipment"
    if model.startswith("sc.safety."):
        return "safety"
    if model.startswith("sc.quality."):
        return "quality"
    if model.startswith("sc.invoice.") or model.startswith("sc.tax.") or model.startswith("sc.fund.") or model.startswith("sc.financing.") or model.startswith("sc.receipt."):
        return "finance"
    if model.startswith("sc.legacy."):
        return "legacy"
    if model.startswith("sc."):
        return "sc_other"
    return "other"


def iter_nodes(nodes: list[dict[str, Any]]):
    stack = list(nodes)
    while stack:
        node = stack.pop(0)
        if not isinstance(node, dict):
            continue
        yield node
        for key in ("children", "tabs", "pages", "nodes", "items", "groups"):
            value = node.get(key)
            if isinstance(value, list):
                stack.extend(item for item in value if isinstance(item, dict))


def node_type(node: dict[str, Any]) -> str:
    return _text(node.get("containerType") or node.get("type") or node.get("kind")).lower()


def collect_layout_fields(contract: dict[str, Any]) -> list[str]:
    layout = contract.get("layoutContract") if isinstance(contract.get("layoutContract"), dict) else {}
    tree = layout.get("containerTree") if isinstance(layout.get("containerTree"), list) else []
    out: list[str] = []
    seen: set[str] = set()
    for node in iter_nodes(tree):
        if node_type(node) == "field":
            name = _text(node.get("name") or node.get("fieldCode") or node.get("field_code"))
            if name and name not in seen:
                seen.add(name)
                out.append(name)
        widgets = node.get("widgetList") or node.get("widget_list")
        if isinstance(widgets, list):
            for widget in widgets:
                if not isinstance(widget, dict):
                    continue
                name = _text(widget.get("fieldCode") or widget.get("field_code"))
                if name and name not in seen:
                    seen.add(name)
                    out.append(name)
    return out


def collect_structure_refs(contract: dict[str, Any]) -> list[str]:
    structure = contract.get("formStructureContract") if isinstance(contract.get("formStructureContract"), dict) else {}
    out: list[str] = []
    seen: set[str] = set()

    def add(raw: Any) -> None:
        name = _text(raw)
        if name and name not in seen:
            seen.add(name)
            out.append(name)

    def visit(row: dict[str, Any]) -> None:
        for item in row.get("fieldRefs") or row.get("field_refs") or row.get("fields") or []:
            add(item)
        groups = row.get("groups")
        if isinstance(groups, list):
            for group in groups:
                if isinstance(group, dict):
                    visit(group)

    for slot in structure.get("slots") or []:
        if isinstance(slot, dict):
            visit(slot)
    return out


def collect_field_labels(contract: dict[str, Any]) -> dict[str, str]:
    fields = contract.get("fields") if isinstance(contract.get("fields"), dict) else {}
    out: dict[str, str] = {}
    for name, meta in fields.items():
        if not isinstance(meta, dict):
            continue
        out[_text(name)] = _text(meta.get("string") or meta.get("label") or name)
    return out


def has_business_identity_signal(projected: set[str], text_blob: str) -> bool:
    """A form can be identifiable by an explicit number or by business anchors.

    Not every carried business object owns a standalone code. Ledger rows,
    recheck records, opening records, and detail rows are often identified by a
    parent document plus project/date/amount/state. Treating those as missing a
    business identity would incorrectly mark usable read or detail forms as
    attention items.
    """

    if EXPLICIT_IDENTITY_FIELD_NAMES & projected:
        return True
    if any(token in text_blob for token in EXPLICIT_IDENTITY_LABEL_TOKENS):
        return True
    if PARENT_ANCHOR_FIELD_NAMES & projected:
        return True
    has_project = "project_id" in projected or "项目" in text_blob
    has_temporal = bool(TEMPORAL_FIELD_NAMES & projected) or any(token in text_blob for token in ("日期", "时间", "期次"))
    has_amount = any(token in text_blob for token in ("金额", "价税", "合同额", "总价", "余额", "单价", "数量", "比例"))
    has_state = any(name in projected for name in ("state", "status", "stage_id", "lifecycle_state")) or "状态" in text_blob
    has_partner = any(name in projected for name in ("partner_id", "customer_id", "supplier_id", "counterparty_id", "responsible_party_id")) or any(
        token in text_blob for token in ("客户", "供应商", "往来单位", "发包人", "承包人", "责任方")
    )
    return has_project and (has_temporal or has_amount or has_state or has_partner)


def classify_gap_owner(gaps: list[str]) -> tuple[str, str]:
    gap_set = set(gaps)
    if not gap_set:
        return "", ""
    if "contract_error" in gap_set:
        return "platform_contract_runtime", "修复统一意图、handler、解析器或运行时契约返回。"
    if gap_set & {"boundary_violation", "missing_form_structure_contract", "missing_layout_fields"}:
        return "orchestration_layer", "修复编排层：只消费业务视图/业务配置给出的字段，并保持结构、布局、治理字段一致。"
    if gap_set & {"missing_required_business_fields", "relation_missing_metadata", "missing_identity_signal", "no_editable_business_fields"}:
        return "business_fact_model_view", "修复业务事实模型或原生业务视图：补字段、字段标签、必填字段投影、关系元数据或业务配置字段清单。"
    if gap_set & {"missing_attachment_contract", "missing_timeline_contract"}:
        return "platform_collaboration_contract", "修复平台协作契约，不在表单编排中补业务字段。"
    return "undetermined", "先按事实模型/视图、编排、前端渲染三段定位，禁止在平台契约硬编码业务术语。"


def collaboration(contract: dict[str, Any]) -> dict[str, Any]:
    runtime = contract.get("runtimeContract") if isinstance(contract.get("runtimeContract"), dict) else {}
    data = runtime.get("collaboration") if isinstance(runtime.get("collaboration"), dict) else {}
    return data


def permission(contract: dict[str, Any], key: str) -> bool:
    head = contract.get("head") if isinstance(contract.get("head"), dict) else {}
    permissions = head.get("permissions") if isinstance(head.get("permissions"), dict) else {}
    if key in permissions:
        return bool(permissions.get(key))
    top = contract.get("permissions") if isinstance(contract.get("permissions"), dict) else {}
    effective = top.get("effective") if isinstance(top.get("effective"), dict) else {}
    rights = effective.get("rights") if isinstance(effective.get("rights"), dict) else {}
    return bool(rights.get(key))


def is_system_field(name: str) -> bool:
    return name in SYSTEM_FIELD_NAMES or name.startswith(SYSTEM_FIELD_PREFIXES)


def is_business_editable_field(field: Any) -> bool:
    name = _text(getattr(field, "name", ""))
    if is_system_field(name):
        return False
    if getattr(field, "readonly", False) or getattr(field, "compute", False):
        return False
    if getattr(field, "type", "") in {"binary", "properties"}:
        return False
    return True


def field_type(field: Any) -> str:
    return _text(getattr(field, "type", ""))


def call_v2_contract(env, model: str, *, login: str = "", render_profile: str = "edit") -> dict[str, Any]:
    from odoo import SUPERUSER_ID, api
    from odoo.addons.smart_core.core.intent_execution_result import IntentExecutionResult
    from odoo.addons.smart_core.handlers.ui_contract_v2 import UiContractV2Handler

    audit_context = dict(env.context or {})
    audit_context.update({
        "contract_projection_readonly": True,
        "form_orchestration_business_usability_audit": True,
    })
    su_env = api.Environment(env.cr, SUPERUSER_ID, audit_context)
    runtime_env = env
    if login:
        user = su_env["res.users"].search([("login", "=", login)], limit=1)
        if user:
            runtime_env = api.Environment(env.cr, int(user.id), audit_context)
    params = {
        "source_type": "ui.contract",
        "model": model,
        "view_type": "form",
        "render_profile": render_profile,
    }
    result = UiContractV2Handler(runtime_env, su_env=su_env, payload=params, context={}).handle(params, {})
    envelope = result.to_legacy_dict() if isinstance(result, IntentExecutionResult) else result
    if not isinstance(envelope, dict) or not envelope.get("ok", True):
        raise RuntimeError(str(envelope.get("error") if isinstance(envelope, dict) else "contract_error"))
    data = envelope.get("data")
    if not isinstance(data, dict):
        raise RuntimeError("contract handler returned no data")
    return data


def runtime_boundary_issues(contract: dict[str, Any]) -> list[str]:
    from odoo.addons.smart_core.core.unified_page_contract_v2_runtime import find_form_structure_contract_issues

    return find_form_structure_contract_issues(contract)


def candidate_models(env, limit: int = 0) -> list[tuple[str, str]]:
    seen: set[str] = set()
    out: list[tuple[str, str]] = []

    menus = env["ir.ui.menu"].sudo().search([], order="sequence,id")
    for menu in menus:
        action = getattr(menu, "action", False)
        model = _text(getattr(action, "res_model", "") if action else "")
        view_mode = _text(getattr(action, "view_mode", "") if action else "")
        if model and model in env and is_business_model(model) and "form" in view_mode and model not in seen:
            seen.add(model)
            out.append((model, "menu_action"))
            if limit and len(out) >= limit:
                return out

    views = env["ir.ui.view"].sudo().search([("type", "=", "form"), ("model", "!=", False)], order="model,id")
    for view in views:
        model = _text(view.model)
        if model and model in env and is_business_model(model) and model not in seen:
            seen.add(model)
            out.append((model, "form_view"))
            if limit and len(out) >= limit:
                return out
    return out


def audit_model(env, model: str, source: str, login: str = "") -> FormBusinessUsabilityRow:
    gaps: list[str] = []
    try:
        contract = call_v2_contract(env, model, login=login)
    except Exception as exc:
        owner_layer, remediation_rule = classify_gap_owner(["contract_error"])
        return FormBusinessUsabilityRow(
            model=model,
            source=source,
            domain_group=domain_group(model),
            status=f"contract_error:{exc}",
            business_ready="false",
            contract_ok="false",
            boundary_ok="false",
            structure_ok="false",
            create_allowed="false",
            write_allowed="false",
            structure_field_count=0,
            layout_field_count=0,
            editable_business_field_count=0,
            required_business_field_count=0,
            missing_required_fields="",
            relation_field_count=0,
            relation_missing_metadata="",
            x2many_field_count=0,
            attachment_enabled="false",
            timeline_enabled="false",
            identity_signal="false",
            state_signal="false",
            amount_signal="false",
            project_signal="false",
            partner_signal="false",
            gaps="contract_error",
            gap_owner_layer=owner_layer,
            remediation_rule=remediation_rule,
        )

    boundary_issues = runtime_boundary_issues(contract)
    if boundary_issues:
        gaps.append("boundary_violation")
    structure_refs = collect_structure_refs(contract)
    layout_fields = collect_layout_fields(contract)
    projected = set(structure_refs) | set(layout_fields)
    if not structure_refs:
        gaps.append("missing_form_structure_contract")
    if not layout_fields:
        gaps.append("missing_layout_fields")

    model_obj = env[model].sudo()
    model_fields = getattr(model_obj, "_fields", {}) or {}
    editable_business_fields = [
        name for name, field in model_fields.items()
        if name in projected and is_business_editable_field(field)
    ]
    if (permission(contract, "write") or permission(contract, "create")) and not editable_business_fields:
        gaps.append("no_editable_business_fields")

    required_business_fields = [
        name for name, field in model_fields.items()
        if bool(getattr(field, "required", False)) and is_business_editable_field(field)
    ]
    missing_required = [name for name in required_business_fields if name not in projected]
    if missing_required and permission(contract, "create"):
        gaps.append("missing_required_business_fields")

    relation_fields = [
        name for name in projected
        if name in model_fields and field_type(model_fields[name]) in {"many2one", "one2many", "many2many"}
    ]
    relation_missing_metadata = [
        name for name in relation_fields
        if not _text(getattr(model_fields[name], "comodel_name", ""))
    ]
    if relation_missing_metadata:
        gaps.append("relation_missing_metadata")

    collab = collaboration(contract)
    attachments = collab.get("attachments") if isinstance(collab.get("attachments"), dict) else {}
    timeline = collab.get("timeline") if isinstance(collab.get("timeline"), dict) else {}
    if not attachments.get("enabled"):
        gaps.append("missing_attachment_contract")
    if not timeline.get("enabled"):
        gaps.append("missing_timeline_contract")

    labels = collect_field_labels(contract)
    text_blob = _norm(json.dumps({
        "fields": {name: labels.get(name, name) for name in projected},
        "structure": contract.get("formStructureContract"),
    }, ensure_ascii=False))
    identity_signal = has_business_identity_signal(projected, text_blob)
    state_signal = any(name in projected for name in ("state", "status", "stage_id", "lifecycle_state")) or "状态" in text_blob
    amount_signal = any(token in text_blob for token in ("金额", "价税", "合同额", "总价", "余额"))
    project_signal = "project_id" in projected or "项目" in text_blob
    partner_signal = any(name in projected for name in ("partner_id", "customer_id", "supplier_id", "counterparty_id")) or any(token in text_blob for token in ("客户", "供应商", "往来单位", "发包人", "承包人"))
    if not identity_signal:
        gaps.append("missing_identity_signal")
    owner_layer, remediation_rule = classify_gap_owner(gaps)

    return FormBusinessUsabilityRow(
        model=model,
        source=source,
        domain_group=domain_group(model),
        status="ok",
        business_ready="true" if not gaps else "false",
        contract_ok="true",
        boundary_ok="true" if not boundary_issues else "false",
        structure_ok="true" if structure_refs and layout_fields else "false",
        create_allowed="true" if permission(contract, "create") else "false",
        write_allowed="true" if permission(contract, "write") else "false",
        structure_field_count=len(structure_refs),
        layout_field_count=len(layout_fields),
        editable_business_field_count=len(editable_business_fields),
        required_business_field_count=len(required_business_fields),
        missing_required_fields=";".join(missing_required),
        relation_field_count=len(relation_fields),
        relation_missing_metadata=";".join(relation_missing_metadata),
        x2many_field_count=len([name for name in relation_fields if field_type(model_fields[name]) in {"one2many", "many2many"}]),
        attachment_enabled="true" if attachments.get("enabled") else "false",
        timeline_enabled="true" if timeline.get("enabled") else "false",
        identity_signal="true" if identity_signal else "false",
        state_signal="true" if state_signal else "false",
        amount_signal="true" if amount_signal else "false",
        project_signal="true" if project_signal else "false",
        partner_signal="true" if partner_signal else "false",
        gaps=";".join(gaps),
        gap_owner_layer=owner_layer,
        remediation_rule=remediation_rule,
    )


SECTION_SIGNAL_ALIASES: dict[str, list[str]] = {
    "基本信息": ["单据号", "单据编号", "状态", "项目", "业务类型", "账户信息"],
    "申请信息": ["申请单号", "申请日期", "申请金额", "申请人", "项目"],
    "关联单据": ["合同", "结算单", "付款记录", "明细", "line_ids"],
    "收支账户信息": ["往来单位", "资金方向", "币种", "金额", "账户", "收款账户", "付款账户"],
    "其它信息": ["备注", "说明", "用途说明", "历史录入人", "历史录入时间"],
    "附件": ["附件", "attachment"],
}


def missing_tokens(expected: list[str], contract: dict[str, Any], aliases: dict[str, list[str]] | None = None) -> list[str]:
    labels = collect_field_labels(contract)
    text = _norm(json.dumps({
        "labels": labels,
        "structure": contract.get("formStructureContract"),
        "layout": contract.get("layoutContract"),
        "runtime": contract.get("runtimeContract"),
    }, ensure_ascii=False))
    missing: list[str] = []
    for item in expected:
        token = _norm(item)
        candidates = [token] + [_norm(alias) for alias in (aliases or {}).get(token, [])]
        if not any(candidate and candidate in text for candidate in candidates):
            missing.append(token)
    return missing


def p1_entries() -> list[dict[str, Any]]:
    candidates = (
        ROOT / "scripts" / "verify" / "p1_daily_business_visible_contract_audit.py",
        Path("/tmp") / "p1_daily_business_visible_contract_audit.py",
    )
    for path in candidates:
        if not path.exists():
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        for node in tree.body:
            value = None
            if isinstance(node, ast.AnnAssign) and getattr(node.target, "id", "") == "P1_ENTRIES":
                value = node.value
            elif isinstance(node, ast.Assign) and any(getattr(target, "id", "") == "P1_ENTRIES" for target in node.targets):
                value = node.value
            if value is None:
                continue
            try:
                entries = ast.literal_eval(value)
            except Exception:
                return []
            return list(entries) if isinstance(entries, list) else []
    return []


def audit_p1_entry(env, entry: dict[str, Any], login: str = "") -> P1BusinessExpectationRow:
    attempts: list[str] = []
    selected_model = ""
    contract: dict[str, Any] = {}
    for model in entry.get("candidates") or []:
        model = _text(model)
        if not model or model not in env:
            continue
        attempts.append(model)
        try:
            contract = call_v2_contract(env, model, login=login)
        except Exception:
            continue
        selected_model = model
        break
    if not selected_model:
        return P1BusinessExpectationRow(
            entry_id=_text(entry.get("id")),
            entry_name=_text(entry.get("name")),
            domain=_text(entry.get("domain")),
            selected_model="",
            status="no_contract",
            missing_sections="",
            missing_fields="",
            gaps="no_readable_v2_contract",
        )
    missing_sections = missing_tokens(list(entry.get("expected_form_sections") or []), contract, SECTION_SIGNAL_ALIASES)
    missing_fields = missing_tokens(list(entry.get("expected_form_fields") or []), contract, {})
    gaps: list[str] = []
    if missing_sections:
        gaps.append("missing_expected_sections")
    if missing_fields:
        gaps.append("missing_expected_fields")
    return P1BusinessExpectationRow(
        entry_id=_text(entry.get("id")),
        entry_name=_text(entry.get("name")),
        domain=_text(entry.get("domain")),
        selected_model=selected_model,
        status="ready" if not gaps else "needs_attention",
        missing_sections=";".join(missing_sections),
        missing_fields=";".join(missing_fields),
        gaps=";".join(gaps),
    )


def write_csv(path: Path, rows: list[Any], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def md_table(rows: list[dict[str, Any]], fields: list[str]) -> str:
    if not rows:
        return ""
    out = ["| " + " | ".join(fields) + " |", "| " + " | ".join(["---"] * len(fields)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(_text(row.get(field)).replace("|", "\\|") for field in fields) + " |")
    return "\n".join(out)


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    form_rows = payload["form_rows"]
    p1_rows = payload["p1_rows"]
    attention = [row for row in form_rows if row["business_ready"] != "true"][:80]
    p1_attention = [row for row in p1_rows if row["status"] != "ready"][:80]
    form_fields = ["domain_group", "model", "business_ready", "gap_owner_layer", "create_allowed", "write_allowed", "structure_field_count", "editable_business_field_count", "relation_field_count", "gaps", "remediation_rule"]
    p1_fields = ["entry_id", "entry_name", "domain", "selected_model", "status", "missing_sections", "missing_fields", "gaps"]
    summary = payload["summary"]
    text = f"""# Form Orchestration Business Usability Audit

## Summary

- audit_login: {payload.get("audit_login") or "-"}
- form_model_count: {summary["form_model_count"]}
- business_ready_count: {summary["business_ready_count"]}
- business_attention_count: {summary["business_attention_count"]}
- contract_error_count: {summary["contract_error_count"]}
- boundary_gap_count: {summary["boundary_gap_count"]}
- missing_required_field_model_count: {summary["missing_required_field_model_count"]}
- editable_business_model_count: {summary["editable_business_model_count"]}
- relation_model_count: {summary["relation_model_count"]}
- attachment_enabled_count: {summary["attachment_enabled_count"]}
- timeline_enabled_count: {summary["timeline_enabled_count"]}
- p1_entry_count: {summary["p1_entry_count"]}
- p1_ready_count: {summary["p1_ready_count"]}
- p1_attention_count: {summary["p1_attention_count"]}

This report checks the runtime v2 form after the orchestration layer is enabled.  It is not a raw XML audit: the question is whether the product contract still exposes enough structure, editable fields, relations, attachments, and business signals for real work.

## Business Attention

{md_table(attention, form_fields)}

## P1 Business Expectation Attention

{md_table(p1_attention, p1_fields)}
"""
    path.write_text(text, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--login", default=os.environ.get("AUDIT_LOGIN", "wutao"))
    args = parser.parse_args(argv)

    runtime_env = globals().get("env")
    if runtime_env is None:
        print("This audit must be executed inside `odoo shell` with global env.", file=sys.stderr)
        return 2

    models = candidate_models(runtime_env, limit=args.limit)
    try:
        rows = [audit_model(runtime_env, model, source, login=args.login) for model, source in models]
        rows.sort(key=lambda row: (row.business_ready != "true", row.domain_group, row.model))
        p1_rows = [audit_p1_entry(runtime_env, entry, login=args.login) for entry in p1_entries()]
    finally:
        # ui.contract.v2 still lazily refreshes several projection config models.
        # Keep this verification script non-mutating while the runtime layer is hardened.
        runtime_env.cr.rollback()

    gap_counter: Counter[str] = Counter()
    for row in rows:
        for gap in filter(None, row.gaps.split(";")):
            gap_counter[gap] += 1
    summary = {
        "form_model_count": len(rows),
        "business_ready_count": sum(1 for row in rows if row.business_ready == "true"),
        "business_attention_count": sum(1 for row in rows if row.business_ready != "true"),
        "contract_error_count": sum(1 for row in rows if row.contract_ok != "true"),
        "boundary_gap_count": gap_counter.get("boundary_violation", 0),
        "missing_required_field_model_count": gap_counter.get("missing_required_business_fields", 0),
        "editable_business_model_count": sum(1 for row in rows if row.editable_business_field_count > 0),
        "relation_model_count": sum(1 for row in rows if row.relation_field_count > 0),
        "attachment_enabled_count": sum(1 for row in rows if row.attachment_enabled == "true"),
        "timeline_enabled_count": sum(1 for row in rows if row.timeline_enabled == "true"),
        "gap_counts": dict(gap_counter),
        "by_domain_group": dict(Counter(row.domain_group for row in rows)),
        "p1_entry_count": len(p1_rows),
        "p1_ready_count": sum(1 for row in p1_rows if row.status == "ready"),
        "p1_attention_count": sum(1 for row in p1_rows if row.status != "ready"),
    }
    payload = {
        "ok": True,
        "audit_login": args.login,
        "database_rollback_after_audit": True,
        "summary": summary,
        "form_rows": [asdict(row) for row in rows],
        "p1_rows": [asdict(row) for row in p1_rows],
    }
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "form_orchestration_business_usability_audit.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_csv(
        out_dir / "form_orchestration_business_usability_audit.csv",
        rows,
        list(FormBusinessUsabilityRow.__dataclass_fields__.keys()),
    )
    write_csv(
        out_dir / "form_orchestration_p1_expectation_audit.csv",
        p1_rows,
        list(P1BusinessExpectationRow.__dataclass_fields__.keys()),
    )
    write_markdown(out_dir / "form_orchestration_business_usability_audit.md", payload)
    print(f"form orchestration business usability audit written to {out_dir}")
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
