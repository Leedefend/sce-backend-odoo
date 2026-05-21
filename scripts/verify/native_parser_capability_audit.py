#!/usr/bin/env python3
"""Audit native parser capability against runtime Odoo views.

The parser layer is allowed to observe and normalize runtime Odoo views.  It is
not allowed to decide business facts or widen governed UI fields.  This audit
therefore checks whether the parser is strong enough as an observation adapter:
it compares runtime arch evidence, parser output, fallback output, and v2
contract output for business-document views.
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

from lxml import etree


ROOT = Path(os.environ.get("SC_REPO_ROOT") or Path.cwd()).resolve()
DEFAULT_OUTPUT_DIR = ROOT / "docs/audit/native/parser_capability"

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
class ParserCapabilityRow:
    model: str
    view_type: str
    domain_group: str
    status: str
    parser_ok: str
    fallback_ok: str
    v2_ok: str
    arch_field_count: int
    parser_field_count: int
    v2_field_count: int
    control_field_count: int
    ignored_control_fields: str
    missing_parser_fields: str
    extra_parser_fields: str
    arch_group_count: int
    parser_group_count: int
    arch_notebook_count: int
    parser_notebook_count: int
    arch_page_count: int
    parser_page_count: int
    arch_header_button_count: int
    parser_header_button_count: int
    arch_stat_button_count: int
    parser_stat_button_count: int
    arch_modifier_field_count: int
    parser_modifier_field_count: int
    missing_modifier_fields: str
    arch_x2many_field_count: int
    parser_subview_count: int
    missing_subviews: str
    arch_chatter: str
    parser_chatter: str
    arch_attachment: str
    parser_attachment: str
    boundary_status: str
    gaps: str


def _text(value: Any) -> str:
    return str(value or "").strip()


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
    if model.startswith("sc."):
        return "sc_other"
    return "other"


def candidate_models(env, limit: int = 0) -> list[str]:
    rows = env["ir.ui.view"].sudo().search([("type", "=", "form"), ("model", "!=", False)], order="model,id")
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


def bool_text(value: Any) -> str:
    return "true" if bool(value) else "false"


def parse_xml(arch: str | None):
    if not arch:
        return None
    try:
        return etree.fromstring(str(arch).encode("utf-8"))
    except Exception:
        return None


def list_join(items: list[str], limit: int = 40) -> str:
    return ";".join(items[:limit])


def iter_nodes(nodes: Any):
    stack = list(nodes or []) if isinstance(nodes, list) else []
    while stack:
        node = stack.pop(0)
        if not isinstance(node, dict):
            continue
        yield node
        for key in ("children", "tabs", "pages", "nodes", "items"):
            value = node.get(key)
            if isinstance(value, list):
                stack.extend(item for item in value if isinstance(item, dict))


def node_type(node: dict[str, Any]) -> str:
    return _text(node.get("type") or node.get("containerType") or node.get("kind")).lower()


def layout_fields(layout: Any) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for node in iter_nodes(layout):
        if node_type(node) == "field":
            name = _text(node.get("name") or node.get("fieldCode") or node.get("field_code"))
            if name and name not in seen:
                seen.add(name)
                out.append(name)
    return out


def layout_type_count(layout: Any, wanted: str) -> int:
    return sum(1 for node in iter_nodes(layout) if node_type(node) == wanted)


def top_level_arch_fields(root) -> list[str]:
    if root is None:
        return []
    out: list[str] = []
    seen: set[str] = set()
    for node in root.xpath(
        ".//field[@name and not(ancestor::field) and not(ancestor::button) "
        "and not(ancestor::*[contains(concat(' ', normalize-space(@class), ' '), ' oe_chatter ')])]"
    ):
        name = _text(node.get("name"))
        if name and name not in seen:
            seen.add(name)
            out.append(name)
    return out


def control_arch_fields(root) -> list[str]:
    """Fields carried by native controls, not by the editable business layout."""
    if root is None:
        return []
    out: list[str] = []
    seen: set[str] = set()
    for node in root.xpath(
        ".//field[@name and not(ancestor::field) and "
        "(ancestor::button or ancestor::*[contains(concat(' ', normalize-space(@class), ' '), ' oe_chatter ')])]"
    ):
        name = _text(node.get("name"))
        if name and name not in seen:
            seen.add(name)
            out.append(name)
    return out


def tree_arch_columns(root) -> list[str]:
    if root is None:
        return []
    tree = root if root.tag in ("tree", "list") else (root.xpath(".//tree|.//list") or [None])[0]
    if tree is None:
        return []
    out: list[str] = []
    seen: set[str] = set()
    for node in tree.xpath("./field[@name]"):
        name = _text(node.get("name"))
        invisible = _text(node.get("column_invisible") or node.get("invisible"))
        if name and name not in seen and invisible not in {"1", "True", "true"}:
            seen.add(name)
            out.append(name)
    return out


def arch_modifier_fields(root) -> list[str]:
    if root is None:
        return []
    out: list[str] = []
    seen: set[str] = set()
    attrs = ("attrs", "readonly", "required", "invisible", "column_invisible", "domain", "context", "groups")
    for node in root.xpath(".//field[@name and not(ancestor::field)]"):
        name = _text(node.get("name"))
        if not name or name in seen:
            continue
        if any(node.get(attr) is not None for attr in attrs):
            seen.add(name)
            out.append(name)
    return out


def arch_x2many_fields(root, fields_info: dict[str, Any]) -> list[str]:
    if root is None:
        return []
    out: list[str] = []
    seen: set[str] = set()
    for node in root.xpath(".//field[@name and not(ancestor::field)]"):
        name = _text(node.get("name"))
        if not name or name in seen:
            continue
        meta = fields_info.get(name) if isinstance(fields_info, dict) else {}
        if isinstance(meta, dict) and meta.get("type") in {"one2many", "many2many"}:
            seen.add(name)
            out.append(name)
    return out


def arch_chatter_enabled(root, fields_info: dict[str, Any]) -> bool:
    if any(name in fields_info for name in ("message_ids", "message_follower_ids", "activity_ids", "website_message_ids")):
        return True
    if root is None:
        return False
    return bool(root.xpath(".//*[contains(concat(' ', normalize-space(@class), ' '), ' oe_chatter ')]"))


def arch_attachment_enabled(root, fields_info: dict[str, Any]) -> bool:
    if any(name in fields_info for name in ("message_attachment_count", "attachment_ids", "doc_count")):
        return True
    if root is None:
        return False
    return bool(root.xpath(".//*[@widget='many2many_binary']|.//*[contains(concat(' ', normalize-space(@class), ' '), ' oe_attachment_box ')]"))


def get_view_data(env, model: str, view_type: str) -> dict[str, Any]:
    try:
        data = env[model].get_view(view_type=view_type)
    except Exception:
        data = {}
    return data if isinstance(data, dict) else {}


def call_v2_contract(env, model: str, view_type: str) -> dict[str, Any]:
    from odoo import SUPERUSER_ID, api
    from odoo.addons.smart_core.core.intent_execution_result import IntentExecutionResult
    from odoo.addons.smart_core.handlers.ui_contract_v2 import UiContractV2Handler

    su_env = api.Environment(env.cr, SUPERUSER_ID, dict(env.context or {}))
    params = {"source_type": "ui.contract", "model": model, "view_type": view_type}
    result = UiContractV2Handler(env, su_env=su_env, payload=params, context={}).handle(params, {})
    envelope = result.to_legacy_dict() if isinstance(result, IntentExecutionResult) else result
    if not isinstance(envelope, dict) or not envelope.get("ok", True):
        raise RuntimeError(str(envelope.get("error") if isinstance(envelope, dict) else "contract handler failed"))
    data = envelope.get("data")
    return data if isinstance(data, dict) else {}


def parsed_ok(env, view_type: str, parsed: Any) -> bool:
    return bool(env["app.view.config"]._parsed_ok(view_type, parsed))


def fallback_ok(env, model: str, view_type: str) -> bool:
    cfg = env["app.view.config"].with_context(
        contract_projection_readonly=True,
        contract_force_fallback=True,
    )._generate_from_fields_view_get(model, view_type)
    parsed = cfg.arch_parsed if hasattr(cfg, "arch_parsed") else {}
    return parsed_ok(env, view_type, parsed)


def audit_form(env, model: str) -> ParserCapabilityRow:
    view_type = "form"
    view_data = get_view_data(env, model, view_type)
    root = parse_xml(view_data.get("arch"))
    fields_info = view_data.get("fields") if isinstance(view_data.get("fields"), dict) else {}
    parser_payload = env["app.view.parser"].parse_odoo_view(model, view_type)
    v2 = call_v2_contract(env, model, view_type)

    arch_fields = top_level_arch_fields(root)
    control_fields = control_arch_fields(root)
    parser_fields = layout_fields(parser_payload.get("layout"))
    v2_layout = (v2.get("layoutContract") or {}).get("containerTree") if isinstance(v2.get("layoutContract"), dict) else []
    v2_fields = layout_fields(v2_layout)

    arch_mods = arch_modifier_fields(root)
    parser_mods = parser_payload.get("field_modifiers") if isinstance(parser_payload.get("field_modifiers"), dict) else {}
    x2many_fields = arch_x2many_fields(root, fields_info)
    subviews = parser_payload.get("subviews") if isinstance(parser_payload.get("subviews"), dict) else {}

    gaps: list[str] = []
    if not parsed_ok(env, view_type, parser_payload):
        gaps.append("primary_parser_not_ok")
    if not fallback_ok(env, model, view_type):
        gaps.append("fallback_not_ok")
    missing_parser = [name for name in arch_fields if name not in parser_fields]
    extra_parser = [name for name in parser_fields if name not in arch_fields]
    if missing_parser:
        gaps.append("missing_parser_layout_fields")
    missing_mods = [name for name in arch_mods if name not in parser_mods]
    if missing_mods:
        gaps.append("missing_modifier_fields")
    missing_subviews = [name for name in x2many_fields if name not in subviews]
    if missing_subviews:
        gaps.append("missing_x2many_subviews")
    arch_chatter = arch_chatter_enabled(root, fields_info)
    parser_chatter = bool((parser_payload.get("chatter") or {}).get("enabled")) if isinstance(parser_payload.get("chatter"), dict) else False
    if arch_chatter and not parser_chatter:
        gaps.append("missing_chatter_detection")
    arch_attachment = arch_attachment_enabled(root, fields_info)
    parser_attachment = bool((parser_payload.get("attachments") or {}).get("enabled")) if isinstance(parser_payload.get("attachments"), dict) else False
    if arch_attachment and not parser_attachment:
        gaps.append("missing_attachment_detection")

    boundary_status = "parser_capability_ok" if not gaps else "parser_capability_gap"
    return ParserCapabilityRow(
        model=model,
        view_type=view_type,
        domain_group=domain_group(model),
        status="ok",
        parser_ok=bool_text(parsed_ok(env, view_type, parser_payload)),
        fallback_ok=bool_text(fallback_ok(env, model, view_type)),
        v2_ok=bool_text(bool(v2.get("layoutContract"))),
        arch_field_count=len(arch_fields),
        parser_field_count=len(parser_fields),
        v2_field_count=len(v2_fields),
        control_field_count=len(control_fields),
        ignored_control_fields=list_join(control_fields),
        missing_parser_fields=list_join(missing_parser),
        extra_parser_fields=list_join(extra_parser),
        arch_group_count=len(root.xpath(".//group")) if root is not None else 0,
        parser_group_count=layout_type_count(parser_payload.get("layout"), "group"),
        arch_notebook_count=len(root.xpath(".//notebook")) if root is not None else 0,
        parser_notebook_count=layout_type_count(parser_payload.get("layout"), "notebook"),
        arch_page_count=len(root.xpath(".//page")) if root is not None else 0,
        parser_page_count=layout_type_count(parser_payload.get("layout"), "page"),
        arch_header_button_count=len(root.xpath(".//header//button")) if root is not None else 0,
        parser_header_button_count=len(parser_payload.get("header_buttons") or []),
        arch_stat_button_count=len(root.xpath(".//*[contains(concat(' ', normalize-space(@class), ' '), ' oe_stat_button ')]")) if root is not None else 0,
        parser_stat_button_count=len(parser_payload.get("stat_buttons") or []),
        arch_modifier_field_count=len(arch_mods),
        parser_modifier_field_count=len(parser_mods),
        missing_modifier_fields=list_join(missing_mods),
        arch_x2many_field_count=len(x2many_fields),
        parser_subview_count=len(subviews),
        missing_subviews=list_join(missing_subviews),
        arch_chatter=bool_text(arch_chatter),
        parser_chatter=bool_text(parser_chatter),
        arch_attachment=bool_text(arch_attachment),
        parser_attachment=bool_text(parser_attachment),
        boundary_status=boundary_status,
        gaps=";".join(gaps),
    )


def audit_tree(env, model: str) -> ParserCapabilityRow:
    view_type = "tree"
    view_data = get_view_data(env, model, view_type)
    root = parse_xml(view_data.get("arch"))
    parser_payload = env["app.view.parser"].parse_odoo_view(model, view_type)
    arch_fields = tree_arch_columns(root)
    parser_fields = [_text(item) for item in (parser_payload.get("columns") or []) if _text(item)]

    gaps: list[str] = []
    if not parsed_ok(env, view_type, parser_payload):
        gaps.append("primary_parser_not_ok")
    if not fallback_ok(env, model, view_type):
        gaps.append("fallback_not_ok")
    missing_parser = [name for name in arch_fields if name not in parser_fields]
    extra_parser = [name for name in parser_fields if name not in arch_fields]
    if missing_parser:
        gaps.append("missing_parser_columns")

    return ParserCapabilityRow(
        model=model,
        view_type=view_type,
        domain_group=domain_group(model),
        status="ok",
        parser_ok=bool_text(parsed_ok(env, view_type, parser_payload)),
        fallback_ok=bool_text(fallback_ok(env, model, view_type)),
        v2_ok="n/a",
        arch_field_count=len(arch_fields),
        parser_field_count=len(parser_fields),
        v2_field_count=0,
        control_field_count=0,
        ignored_control_fields="",
        missing_parser_fields=list_join(missing_parser),
        extra_parser_fields=list_join(extra_parser),
        arch_group_count=0,
        parser_group_count=0,
        arch_notebook_count=0,
        parser_notebook_count=0,
        arch_page_count=0,
        parser_page_count=0,
        arch_header_button_count=len(root.xpath(".//header//button")) if root is not None else 0,
        parser_header_button_count=len([item for item in (parser_payload.get("row_actions") or []) if isinstance(item, dict)]),
        arch_stat_button_count=0,
        parser_stat_button_count=0,
        arch_modifier_field_count=0,
        parser_modifier_field_count=len(parser_payload.get("modifiers") or {}) if isinstance(parser_payload.get("modifiers"), dict) else 0,
        missing_modifier_fields="",
        arch_x2many_field_count=0,
        parser_subview_count=0,
        missing_subviews="",
        arch_chatter="n/a",
        parser_chatter="n/a",
        arch_attachment="n/a",
        parser_attachment="n/a",
        boundary_status="parser_capability_ok" if not gaps else "parser_capability_gap",
        gaps=";".join(gaps),
    )


def audit_model(env, model: str) -> list[ParserCapabilityRow]:
    rows: list[ParserCapabilityRow] = []
    for view_type, fn in (("form", audit_form), ("tree", audit_tree)):
        try:
            rows.append(fn(env, model))
        except Exception as exc:  # pragma: no cover - runs inside Odoo shell
            rows.append(ParserCapabilityRow(
                model=model,
                view_type=view_type,
                domain_group=domain_group(model),
                status=f"error:{exc}",
                parser_ok="false",
                fallback_ok="false",
                v2_ok="false" if view_type == "form" else "n/a",
                arch_field_count=0,
                parser_field_count=0,
                v2_field_count=0,
                control_field_count=0,
                ignored_control_fields="",
                missing_parser_fields="",
                extra_parser_fields="",
                arch_group_count=0,
                parser_group_count=0,
                arch_notebook_count=0,
                parser_notebook_count=0,
                arch_page_count=0,
                parser_page_count=0,
                arch_header_button_count=0,
                parser_header_button_count=0,
                arch_stat_button_count=0,
                parser_stat_button_count=0,
                arch_modifier_field_count=0,
                parser_modifier_field_count=0,
                missing_modifier_fields="",
                arch_x2many_field_count=0,
                parser_subview_count=0,
                missing_subviews="",
                arch_chatter="false",
                parser_chatter="false",
                arch_attachment="false",
                parser_attachment="false",
                boundary_status="parser_error",
                gaps="parser_error",
            ))
    return rows


def md_table(rows: list[dict[str, Any]], fields: list[str]) -> str:
    if not rows:
        return ""
    out = ["| " + " | ".join(fields) + " |", "| " + " | ".join(["---"] * len(fields)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(_text(row.get(field)).replace("|", "\\|") for field in fields) + " |")
    return "\n".join(out)


def write_outputs(out_dir: Path, rows: list[ParserCapabilityRow], summary: dict[str, Any]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {"summary": summary, "rows": [asdict(row) for row in rows]}
    (out_dir / "native_parser_capability_audit.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    with (out_dir / "native_parser_capability_audit.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(ParserCapabilityRow.__dataclass_fields__.keys()))
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))

    gaps = [asdict(row) for row in rows if row.boundary_status != "parser_capability_ok"][:80]
    form_samples = [asdict(row) for row in rows if row.view_type == "form"][:40]
    tree_samples = [asdict(row) for row in rows if row.view_type == "tree"][:40]
    fields = ["domain_group", "model", "view_type", "boundary_status", "parser_ok", "fallback_ok", "arch_field_count", "parser_field_count", "gaps"]
    detail_fields = [
        "domain_group", "model", "view_type", "boundary_status", "missing_parser_fields",
        "ignored_control_fields", "missing_modifier_fields", "missing_subviews", "arch_chatter", "parser_chatter",
        "arch_attachment", "parser_attachment",
    ]
    text = f"""# 原生动态解析层能力专项审计

## 摘要

- 业务模型数：{summary["total_models"]}
- 审计视图数：{summary["total_views"]}
- 解析能力达标视图：{summary["by_boundary_status"].get("parser_capability_ok", 0)}
- 解析能力缺口视图：{summary["by_boundary_status"].get("parser_capability_gap", 0)}
- 解析错误视图：{summary["by_boundary_status"].get("parser_error", 0)}
- form 主解析通过：{summary["form_primary_ok"]}
- form fallback 通过：{summary["form_fallback_ok"]}
- tree 主解析通过：{summary["tree_primary_ok"]}
- tree fallback 通过：{summary["tree_fallback_ok"]}

本报告审计后端动态实时页面解析层作为“运行态观察与契约适配器”的能力。它只判断解析层能否完整观察 Odoo 原生运行态，并不把解析结果作为业务事实或展示授权来源。

## 缺口清单

{md_table(gaps, detail_fields)}

## form 样本

{md_table(form_samples, fields)}

## tree 样本

{md_table(tree_samples, fields)}
"""
    (out_dir / "native_parser_capability_audit.md").write_text(text, encoding="utf-8")


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
    rows: list[ParserCapabilityRow] = []
    for model in models:
        rows.extend(audit_model(runtime_env, model))
    rows.sort(key=lambda row: (row.boundary_status, row.domain_group, row.model, row.view_type))
    by_boundary = Counter(row.boundary_status for row in rows)
    summary = {
        "total_models": len(models),
        "total_views": len(rows),
        "by_boundary_status": dict(by_boundary),
        "form_primary_ok": sum(1 for row in rows if row.view_type == "form" and row.parser_ok == "true"),
        "form_fallback_ok": sum(1 for row in rows if row.view_type == "form" and row.fallback_ok == "true"),
        "tree_primary_ok": sum(1 for row in rows if row.view_type == "tree" and row.parser_ok == "true"),
        "tree_fallback_ok": sum(1 for row in rows if row.view_type == "tree" and row.fallback_ok == "true"),
    }
    write_outputs(Path(args.out_dir), rows, summary)
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
