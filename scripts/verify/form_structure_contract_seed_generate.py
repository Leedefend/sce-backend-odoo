#!/usr/bin/env python3
"""Generate governed form-structure seed contracts for business forms.

The generated contracts deliberately use the current runtime form layout as the
field source.  They do not scan all model fields, so enabling
formStructureContract for more models does not widen the user-facing field set.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape, quoteattr


ROOT = Path(os.environ.get("SC_REPO_ROOT") or Path.cwd()).resolve()
DEFAULT_OUTPUT = ROOT / "addons/smart_construction_core/data/view_orchestration_contract_generated_data.xml"

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


def node_type(node: dict[str, Any]) -> str:
    return _text(node.get("containerType") or node.get("type") or node.get("kind")).lower()


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


def call_v2_contract(env, model: str) -> dict[str, Any]:
    from odoo import SUPERUSER_ID, api
    from odoo.addons.smart_core.core.intent_execution_result import IntentExecutionResult
    from odoo.addons.smart_core.handlers.ui_contract_v2 import UiContractV2Handler

    su_env = api.Environment(env.cr, SUPERUSER_ID, dict(env.context or {}))
    params = {"source_type": "ui.contract", "model": model, "view_type": "form"}
    result = UiContractV2Handler(env, su_env=su_env, payload=params, context={}).handle(params, {})
    envelope = result.to_legacy_dict() if isinstance(result, IntentExecutionResult) else result
    if not isinstance(envelope, dict) or not envelope.get("ok", True):
        raise RuntimeError(str(envelope.get("error") if isinstance(envelope, dict) else "contract handler failed"))
    data = envelope.get("data")
    if not isinstance(data, dict):
        raise RuntimeError("contract handler returned no data")
    return data


def has_effective_form_contract(env, model: str) -> bool:
    if "ui.business.config.contract" not in env:
        return False
    contracts = env["ui.business.config.contract"]._effective_view_orchestration_contracts(model, view_type="form")
    for contract in contracts:
        payload = contract.contract_json if isinstance(contract.contract_json, dict) else {}
        orchestration = payload.get("view_orchestration") if isinstance(payload.get("view_orchestration"), dict) else {}
        views = orchestration.get("views") if isinstance(orchestration.get("views"), dict) else {}
        form = views.get("form") if isinstance(views.get("form"), dict) else {}
        fields = form.get("fields") if isinstance(form.get("fields"), list) else []
        if fields:
            return True
    return False


def xml_id_for_model(model: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_]+", "_", model).strip("_").lower()
    return f"business_config_contract_{slug}_form_structure_generated"


def build_record_xml(model: str, field_names: list[str], sequence: int) -> str:
    fields = [{"name": name, "sequence": (index + 1) * 10} for index, name in enumerate(field_names)]
    payload = {"view_orchestration": {"views": {"form": {"fields": fields}}}}
    # Odoo XML ``eval`` uses Python safe_eval, not JSON parsing.  Keep this as a
    # Python literal so booleans are emitted as True/False instead of true/false.
    eval_payload = quoteattr(repr(payload))
    xml_id = escape(xml_id_for_model(model))
    name = escape(f"{model.replace('.', '_')}_form_structure_generated_v1")
    priority = 60 + sequence
    return "\n".join([
        f'    <record id="{xml_id}" model="ui.business.config.contract">',
        f"        <field name=\"name\">{name}</field>",
        f"        <field name=\"model\">{escape(model)}</field>",
        "        <field name=\"view_type\">form</field>",
        f"        <field name=\"priority\">{priority}</field>",
        "        <field name=\"company_id\" eval=\"False\"/>",
        "        <field name=\"active\" eval=\"True\"/>",
        "        <field name=\"status\">published</field>",
        "        <field name=\"version_no\">1</field>",
        f"        <field name=\"contract_json\" eval={eval_payload}/>",
        "    </record>",
    ])


def generate(env, *, limit: int = 0) -> tuple[str, dict[str, Any]]:
    from odoo.addons.smart_core.core.unified_page_contract_v2_runtime import _is_form_structure_internal_field

    records: list[str] = []
    skipped_existing: list[str] = []
    skipped_empty: list[str] = []
    errors: dict[str, str] = {}
    for model in candidate_models(env, limit=limit):
        if has_effective_form_contract(env, model):
            skipped_existing.append(model)
            continue
        try:
            contract = call_v2_contract(env, model)
            layout = contract.get("layoutContract") if isinstance(contract.get("layoutContract"), dict) else {}
            tree = layout.get("containerTree") if isinstance(layout.get("containerTree"), list) else []
            names: list[str] = []
            seen: set[str] = set()
            for name in collect_layout_field_names(tree):
                if not name or name in seen:
                    continue
                if name not in env[model]._fields:
                    continue
                if _is_form_structure_internal_field(name):
                    continue
                seen.add(name)
                names.append(name)
            if not names:
                skipped_empty.append(model)
                continue
            records.append(build_record_xml(model, names, len(records)))
        except Exception as exc:  # pragma: no cover - exercised in Odoo shell
            errors[model] = str(exc)

    body = ["<?xml version=\"1.0\" encoding=\"utf-8\"?>", "<odoo noupdate=\"1\">"]
    body.extend(records)
    body.append("</odoo>")
    summary = {
        "generated": len(records),
        "skipped_existing": skipped_existing,
        "skipped_empty": skipped_empty,
        "errors": errors,
    }
    return "\n".join(body) + "\n", summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args(argv)

    runtime_env = globals().get("env")
    if runtime_env is None:
        print("This generator must be executed inside `odoo shell` with global env.", file=sys.stderr)
        return 2

    xml, summary = generate(runtime_env, limit=args.limit)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(xml, encoding="utf-8")
    print(json.dumps({"output": str(output), **summary}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
