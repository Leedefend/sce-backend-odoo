#!/usr/bin/env python3
"""Audit runtime Unified Page Contract v2 form structure coverage.

This audit reads the v2 contract delivered to clients.  It is intentionally
separate from the native XML/runtime arch audit because form structure can be
standardized by projection without mutating business XML views.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


ROOT = Path(os.environ.get("SC_REPO_ROOT") or Path.cwd()).resolve()
DEFAULT_OUTPUT_DIR = ROOT / "docs/audit/native/form_structure_contract_runtime"

BUSINESS_MODEL_PREFIXES = (
    "construction.",
    "project.",
    "quota.",
    "sc.",
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
    "res.config.",
    "res.config",
    "res.users.",
    "web.",
)
TECHNICAL_MODEL_TOKENS = (
    ".wizard",
    ".settings",
    ".config",
    ".installer",
)
LOW_PRIORITY_PREFIXES = (
    "sc.legacy.",
)
PLATFORM_PREFIXES = (
    "sc.capability",
    "sc.entitlement",
    "sc.ops.",
    "sc.pack.",
    "sc.scene",
    "sc.subscription",
    "sc.usage.",
    "sc.workbench.",
    "ui.form.",
)


@dataclass
class ContractFormAuditRow:
    model: str
    surface_lane: str
    domain_group: str
    status: str
    boundary_status: str
    has_form_structure_contract: str
    governance_field_count: int
    structure_field_count: int
    layout_field_count: int
    boundary_issue_count: int
    boundary_issues: str
    layout_outside_structure: str
    group_count: int
    semantic_group_count: int
    unlabeled_group_count: int
    notebook_count: int
    page_count: int
    projected_notebook_count: int
    projected_semantic_group_count: int
    native_chatter: str
    attachments_enabled: str
    timeline_enabled: str
    collaboration_actions: str
    classification: str
    gaps: str


def _text(value: Any) -> str:
    return str(value or "").strip()


def is_business_model(model: str) -> bool:
    if not model:
        return False
    if model.startswith(TECHNICAL_MODEL_PREFIXES):
        return False
    if is_transient_or_setup(model):
        return False
    if model in BUSINESS_MODEL_EXACT:
        return True
    return model.startswith(BUSINESS_MODEL_PREFIXES)


def is_transient_or_setup(model: str) -> bool:
    return any(token in model for token in TECHNICAL_MODEL_TOKENS) or model.endswith(".wizard")


def surface_lane(model: str) -> str:
    if is_transient_or_setup(model):
        return "setup_or_wizard"
    if model.startswith(LOW_PRIORITY_PREFIXES):
        return "legacy_fact_carrier"
    if model.startswith(PLATFORM_PREFIXES):
        return "platform_configuration"
    return "business_document"


def domain_group(model: str) -> str:
    if model.startswith("project."):
        return "project"
    if model.startswith("construction."):
        return "contract"
    if model in BUSINESS_MODEL_EXACT:
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
        for key in ("children", "tabs", "pages", "nodes", "items"):
            value = node.get(key)
            if isinstance(value, list):
                stack.extend(item for item in value if isinstance(item, dict))


def collect_layout_field_names(nodes: list[dict[str, Any]]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for node in iter_nodes(nodes):
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


def collect_structure_field_refs(structure: dict[str, Any]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()

    def add(name_raw: Any) -> None:
        name = _text(name_raw)
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


def runtime_boundary_issues(contract: dict[str, Any]) -> list[str]:
    from odoo.addons.smart_core.core.unified_page_contract_v2_runtime import find_form_structure_contract_issues

    return find_form_structure_contract_issues(contract)


def is_runtime_control_field(name: str) -> bool:
    from odoo.addons.smart_core.core.unified_page_contract_v2_runtime import _is_form_structure_runtime_control_field

    return _is_form_structure_runtime_control_field(name)


def node_type(node: dict[str, Any]) -> str:
    return _text(node.get("containerType") or node.get("type") or node.get("kind")).lower()


def source_carrier(node: dict[str, Any]) -> str:
    source = node.get("sourceAuthority")
    return _text(source.get("runtime_carrier") if isinstance(source, dict) else "")


def is_unlabeled_group(node: dict[str, Any]) -> bool:
    generic = {"", node_type(node)}
    container_id = _text(node.get("containerId")).lower()
    node_name = _text(node.get("name")).lower()
    if is_technical_container_identifier(container_id):
        generic.add(container_id)
    if is_technical_container_identifier(node_name):
        generic.add(node_name)
    semantic_title = _text(node.get("semanticTitle")).lower()
    if semantic_title and semantic_title not in generic:
        return False
    labels = {
        _text(node.get("title")).lower(),
        _text(node.get("label")).lower(),
        _text(node.get("string")).lower(),
        semantic_title,
    }
    return bool(labels & generic) or all(not label for label in labels)


def is_technical_container_identifier(value: str) -> bool:
    if not value:
        return False
    return bool(re.fullmatch(r"[a-z0-9_.:-]+", value))


def collaboration_from_contract(contract: dict[str, Any]) -> dict[str, Any]:
    runtime = contract.get("runtimeContract")
    if not isinstance(runtime, dict):
        return {}
    collaboration = runtime.get("collaboration")
    return collaboration if isinstance(collaboration, dict) else {}


def bool_text(value: Any) -> str:
    return "true" if bool(value) else "false"


def call_v2_contract(env, model: str) -> dict[str, Any]:
    from odoo import SUPERUSER_ID, api
    from odoo.addons.smart_core.core.intent_execution_result import IntentExecutionResult
    from odoo.addons.smart_core.handlers.ui_contract_v2 import UiContractV2Handler

    su_env = api.Environment(env.cr, SUPERUSER_ID, dict(env.context or {}))
    params = {"source_type": "ui.contract", "model": model, "view_type": "form"}
    result = UiContractV2Handler(env, su_env=su_env, payload=params, context={}).handle(params, {})
    envelope = result.to_legacy_dict() if isinstance(result, IntentExecutionResult) else result
    if not isinstance(envelope, dict) or not envelope.get("ok", True):
        message = envelope.get("error") if isinstance(envelope, dict) else ""
        raise RuntimeError(str(message or "contract handler failed"))
    data = envelope.get("data")
    if not isinstance(data, dict):
        raise RuntimeError("contract handler returned no data")
    return data


def audit_model(env, model: str) -> ContractFormAuditRow:
    try:
        contract = call_v2_contract(env, model)
    except Exception as exc:  # pragma: no cover - exercised inside Odoo shell
        return ContractFormAuditRow(
            model=model,
            surface_lane=surface_lane(model),
            domain_group=domain_group(model),
            status=f"error:{exc}",
            boundary_status="contract_error",
            has_form_structure_contract="false",
            governance_field_count=0,
            structure_field_count=0,
            layout_field_count=0,
            boundary_issue_count=1,
            boundary_issues="contract_error",
            layout_outside_structure="",
            group_count=0,
            semantic_group_count=0,
            unlabeled_group_count=0,
            notebook_count=0,
            page_count=0,
            projected_notebook_count=0,
            projected_semantic_group_count=0,
            native_chatter="false",
            attachments_enabled="false",
            timeline_enabled="false",
            collaboration_actions="",
            classification="contract_error",
            gaps="contract_error",
        )

    layout = contract.get("layoutContract") if isinstance(contract.get("layoutContract"), dict) else {}
    tree = layout.get("containerTree") if isinstance(layout.get("containerTree"), list) else []
    structure = contract.get("formStructureContract") if isinstance(contract.get("formStructureContract"), dict) else {}
    structure_refs = collect_structure_field_refs(structure)
    layout_fields = collect_layout_field_names(tree)
    governance_source = (
        structure.get("sourceAuthority", {}).get("governance_source", {})
        if isinstance(structure.get("sourceAuthority"), dict)
        else {}
    )
    governance_fields = (
        governance_source.get("field_names") or governance_source.get("fieldNames") or []
        if isinstance(governance_source, dict)
        else []
    )
    boundary_issues = runtime_boundary_issues(contract)
    layout_outside_structure = [
        name
        for name in layout_fields
        if structure_refs and name not in structure_refs and not is_runtime_control_field(name)
    ]
    nodes = list(iter_nodes(tree))
    groups = [node for node in nodes if node_type(node) == "group"]
    notebooks = [node for node in nodes if node_type(node) == "notebook"]
    pages = [node for node in nodes if node_type(node) == "page"]
    semantic_groups = [node for node in groups if _text(node.get("semanticTitle") or node.get("title")) and not is_unlabeled_group(node)]
    projected_notebooks = [
        node for node in notebooks
        if source_carrier(node) == "business_form_default_tab_standardizer"
    ]
    projected_semantic_groups = [
        node for node in groups
        if source_carrier(node) == "business_form_semantic_label_standardizer"
    ]
    collaboration = collaboration_from_contract(contract)
    attachments = collaboration.get("attachments") if isinstance(collaboration.get("attachments"), dict) else {}
    timeline = collaboration.get("timeline") if isinstance(collaboration.get("timeline"), dict) else {}
    chatter = collaboration.get("chatter") if isinstance(collaboration.get("chatter"), dict) else {}
    actions = collaboration.get("actions") if isinstance(collaboration.get("actions"), list) else []

    gaps: list[str] = []
    if not notebooks:
        gaps.append("missing_contract_notebook")
    if not pages:
        gaps.append("missing_contract_page")
    if groups and len(semantic_groups) < len(groups):
        gaps.append("missing_group_semantics")
    if not collaboration:
        gaps.append("missing_collaboration_runtime")
    if not attachments.get("enabled"):
        gaps.append("missing_attachment_contract")
    if not timeline.get("enabled"):
        gaps.append("missing_timeline_contract")

    if boundary_issues:
        boundary_status = "boundary_violation"
    elif structure:
        boundary_status = "boundary_ok"
    else:
        boundary_status = "native_form_no_structure_contract"

    classification = "contract_standardized" if not gaps else "contract_needs_attention"
    return ContractFormAuditRow(
        model=model,
        surface_lane=surface_lane(model),
        domain_group=domain_group(model),
        status="ok",
        boundary_status=boundary_status,
        has_form_structure_contract=bool_text(bool(structure)),
        governance_field_count=len([_text(item) for item in governance_fields if _text(item)]),
        structure_field_count=len(structure_refs),
        layout_field_count=len(layout_fields),
        boundary_issue_count=len(boundary_issues),
        boundary_issues=";".join(boundary_issues),
        layout_outside_structure=";".join(layout_outside_structure),
        group_count=len(groups),
        semantic_group_count=len(semantic_groups),
        unlabeled_group_count=max(len(groups) - len(semantic_groups), 0),
        notebook_count=len(notebooks),
        page_count=len(pages),
        projected_notebook_count=len(projected_notebooks),
        projected_semantic_group_count=len(projected_semantic_groups),
        native_chatter=bool_text(chatter.get("enabled")),
        attachments_enabled=bool_text(attachments.get("enabled")),
        timeline_enabled=bool_text(timeline.get("enabled")),
        collaboration_actions=";".join(_text(action.get("type") or action.get("kind")) for action in actions if isinstance(action, dict)),
        classification=classification,
        gaps=";".join(gaps),
    )


def candidate_models(env, limit: int = 0) -> list[str]:
    View = env["ir.ui.view"].sudo()
    rows = View.search([("type", "=", "form"), ("model", "!=", False)], order="model,id")
    out: list[str] = []
    seen: set[str] = set()
    for view in rows:
        model = _text(view.model)
        if not model or model in seen or model not in env:
            continue
        if not is_business_model(model):
            continue
        if surface_lane(model) != "business_document":
            continue
        seen.add(model)
        out.append(model)
        if limit and len(out) >= limit:
            break
    return out


def write_csv(path: Path, rows: list[ContractFormAuditRow]) -> None:
    fieldnames = list(ContractFormAuditRow.__dataclass_fields__.keys())
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


def write_markdown(path: Path, rows: list[ContractFormAuditRow], summary: dict[str, Any]) -> None:
    needs_attention = [asdict(row) for row in rows if row.classification != "contract_standardized"][:60]
    boundary_violations = [asdict(row) for row in rows if row.boundary_status == "boundary_violation"][:80]
    structured = [asdict(row) for row in rows if row.has_form_structure_contract == "true"][:80]
    projected = [asdict(row) for row in rows if row.projected_notebook_count or row.projected_semantic_group_count][:40]
    fields = ["domain_group", "model", "classification", "notebook_count", "page_count", "semantic_group_count", "gaps"]
    boundary_fields = ["domain_group", "model", "boundary_status", "governance_field_count", "structure_field_count", "layout_field_count", "boundary_issues", "layout_outside_structure"]
    text = f"""# v2 表单结构运行态契约审计

## 摘要

- 运行态业务表单契约：{summary["total_models"]}
- 已满足 contract 结构标准：{summary["by_classification"].get("contract_standardized", 0)}
- 仍需关注：{summary["by_classification"].get("contract_needs_attention", 0)}
- 契约错误：{summary["by_classification"].get("contract_error", 0)}
- 边界违规：{summary["by_boundary_status"].get("boundary_violation", 0)}
- 已启用结构合同且边界通过：{summary["by_boundary_status"].get("boundary_ok", 0)}
- 未启用结构合同，保留原生表单：{summary["by_boundary_status"].get("native_form_no_structure_contract", 0)}
- 契约默认页签投影覆盖：{summary["projected_notebook_models"]}
- 契约分组语义投影覆盖：{summary["projected_semantic_group_models"]}
- 附件契约覆盖：{summary["attachment_enabled_models"]}
- 时间线/日志契约覆盖：{summary["timeline_enabled_models"]}

本报告审计前端实际接收的 Unified Page Contract v2。它用于补充原生 XML/运行态 arch 审计，避免把可由契约层投影解决的缺口误判为需要逐个业务视图改 XML。

## 仍需关注

{md_table(needs_attention, fields)}

## 边界违规

{md_table(boundary_violations, boundary_fields)}

## 已启用结构合同样本

{md_table(structured, boundary_fields)}

## 契约投影覆盖样本

{md_table(projected, fields)}
"""
    path.write_text(text, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args(argv)

    runtime_env = globals().get("env")
    if runtime_env is None:
        print("This audit must be executed inside `odoo shell` with global env.", file=sys.stderr)
        return 2

    models = candidate_models(runtime_env, limit=args.limit)
    rows = [audit_model(runtime_env, model) for model in models]
    rows.sort(key=lambda row: (row.classification, row.domain_group, row.model))
    by_classification = Counter(row.classification for row in rows)
    by_boundary_status = Counter(row.boundary_status for row in rows)
    summary = {
        "total_models": len(rows),
        "by_classification": dict(by_classification),
        "by_boundary_status": dict(by_boundary_status),
        "projected_notebook_models": sum(1 for row in rows if row.projected_notebook_count > 0),
        "projected_semantic_group_models": sum(1 for row in rows if row.projected_semantic_group_count > 0),
        "attachment_enabled_models": sum(1 for row in rows if row.attachments_enabled == "true"),
        "timeline_enabled_models": sum(1 for row in rows if row.timeline_enabled == "true"),
    }

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(out_dir / "form_structure_contract_runtime_audit.csv", rows)
    (out_dir / "form_structure_contract_runtime_audit.json").write_text(
        json.dumps({"summary": summary, "rows": [asdict(row) for row in rows]}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    write_markdown(out_dir / "form_structure_contract_runtime_audit.md", rows, summary)
    print(f"runtime v2 form contract audit written to {out_dir}")
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
