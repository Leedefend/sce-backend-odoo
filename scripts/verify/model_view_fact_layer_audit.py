# -*- coding: utf-8 -*-
"""Audit model/view facts as the governance baseline.

Run inside ``odoo shell``.  The source of truth is the runtime-visible Odoo
menu/action/model graph, not frontend routes.  This keeps the audit at the
contract/fact boundary before browser validation.
"""

from __future__ import annotations

import json
import os
from collections import Counter, defaultdict
from pathlib import Path

from lxml import etree
from odoo.exceptions import AccessError


ROOT = Path(os.getenv("SC_REPO_ROOT") or "/mnt").resolve()
REPORT_JSON = ROOT / "artifacts/backend/model_view_fact_layer_audit.json"
REPORT_MD = ROOT / "artifacts/backend/model_view_fact_layer_audit.md"

AUDIT_LOGIN = os.getenv("MODEL_VIEW_AUDIT_LOGIN") or os.getenv("E2E_LOGIN") or "wutao"

BUSINESS_PREFIXES = (
    "construction.",
    "payment.",
    "project.",
    "purchase.",
    "quota.",
    "sc.",
    "tender.",
)
BUSINESS_EXACT = {
    "hr.department",
    "res.partner",
    "res.users",
}
INTERNAL_PREFIXES = (
    "ir.",
    "mail.",
    "bus.",
    "base.",
    "web.",
)
TECHNICAL_TOKENS = (
    ".wizard",
    ".settings",
)

FOUNDATION_FIELD_CANDIDATES = {
    "company": ("company_id",),
    "project": ("project_id", "project_name", "legacy_project_name"),
    "partner": ("partner_id", "partner_name", "owner_id", "supplier_id", "customer_id"),
    "amount": (
        "amount",
        "amount_total",
        "amount_untaxed",
        "payment_amount",
        "receipt_amount",
        "total_amount",
        "contract_amount",
        "budget_amount",
    ),
    "date": ("date", "document_date", "request_date", "payment_date", "receipt_date", "create_date"),
    "state": (
        "state",
        "status",
        "validation_status",
        "approval_state",
        "review_state",
        "mapping_state",
        "runtime_state",
        "business_state",
        "lifecycle_state",
        "health_state",
        "result",
        "is_active",
        "active",
    ),
    "attachment": ("attachment_ids", "sc_attachment_ids", "message_attachment_count", "attachment_count"),
    "chatter": ("message_ids", "message_follower_ids", "activity_ids"),
    "legacy_trace": ("legacy_id", "legacy_source_id", "legacy_source_model", "legacy_document_no", "source_system"),
    "creator": ("create_uid", "creator_id", "source_created_by", "legacy_creator_name"),
}


def _env():
    return globals()["env"]


def text(value) -> str:
    return str(value or "").strip()


def is_business_model(model: str) -> bool:
    if not model or model.startswith(INTERNAL_PREFIXES):
        return False
    if any(token in model for token in TECHNICAL_TOKENS):
        return False
    return model in BUSINESS_EXACT or model.startswith(BUSINESS_PREFIXES)


def lane_for_model(model: str) -> str:
    if model.startswith("sc.legacy."):
        return "legacy_fact"
    if model.startswith(("sc.dashboard.", "sc.treasury.", "sc.operating.", "sc.company.", "sc.account.", "sc.invoice.category.", "sc.salary.", "sc.expense.reimbursement.", "sc.material.stock.", "sc.comprehensive.")):
        return "report_summary"
    if model.startswith(("sc.capability", "sc.scene", "sc.pack.", "sc.workflow", "sc.approval", "sc.dictionary", "project.dictionary", "quota.")):
        return "configuration"
    if model in {"res.users", "hr.department"}:
        return "organization_security"
    if model == "res.partner":
        return "partner_master"
    return "business_document"


def domain_for_model(model: str) -> str:
    if model.startswith("project."):
        return "project"
    if model.startswith("construction."):
        return "contract"
    if model.startswith("tender."):
        return "tender"
    if model.startswith(("payment.", "sc.payment", "sc.receipt", "sc.expense", "sc.financing", "sc.fund", "sc.invoice", "sc.tax", "sc.treasury")):
        return "finance"
    if model.startswith("sc.material"):
        return "material"
    if model.startswith("sc.subcontract"):
        return "subcontract"
    if model.startswith("sc.labor"):
        return "labor"
    if model.startswith("sc.equipment"):
        return "equipment"
    if model.startswith("sc.safety"):
        return "safety"
    if model.startswith("sc.quality"):
        return "quality"
    if model.startswith("sc.legacy"):
        return "legacy"
    if model in {"res.partner", "res.users", "hr.department"}:
        return "master_data"
    return "other"


def extract_arch_fields(arch: str) -> list[str]:
    if not arch:
        return []
    try:
        root = etree.fromstring(arch.encode("utf-8"))
    except Exception:
        return []
    fields = []
    for node in root.xpath(".//field[@name]"):
        name = text(node.get("name"))
        if name and name not in fields:
            fields.append(name)
    return fields


def extract_arch_search_controls(arch: str) -> list[str]:
    if not arch:
        return []
    try:
        root = etree.fromstring(arch.encode("utf-8"))
    except Exception:
        return []
    controls = []
    for node in root.xpath(".//field[@name] | .//filter[@name]"):
        name = text(node.get("string") or node.get("name"))
        if name and name not in controls:
            controls.append(name)
    return controls


def get_runtime_view(Model, view_type: str) -> dict:
    try:
        return Model.get_view(view_type=view_type) or {}
    except Exception as exc:
        return {"__error": text(exc)}


def fields_from_runtime_view(view: dict) -> list[str]:
    arch = text(view.get("arch"))
    fields = extract_arch_fields(arch)
    if fields:
        return fields
    meta = view.get("fields") if isinstance(view.get("fields"), dict) else {}
    return list(meta.keys())


def model_foundation_signals(Model) -> dict[str, bool]:
    names = set(Model._fields)
    signals = {
        key: any(candidate in names for candidate in candidates)
        for key, candidates in FOUNDATION_FIELD_CANDIDATES.items()
    }
    signals["legacy_trace"] = signals["legacy_trace"] or any(
        name.startswith(("legacy_", "source_"))
        or name.endswith("_legacy_id")
        or name in {"legacy_record_id", "legacy_pid", "source_table", "source_dataset"}
        for name in names
    )
    return signals


def count_records(Model) -> tuple[int | None, str]:
    try:
        return int(Model.search_count([])), ""
    except Exception as exc:
        return None, text(exc)


def access_matrix(Model) -> dict[str, bool | str]:
    result = {}
    for mode in ("read", "create", "write", "unlink"):
        try:
            result[mode] = bool(Model.check_access_rights(mode, raise_exception=False))
        except AccessError:
            result[mode] = False
        except Exception as exc:
            result[mode] = f"error:{text(exc)[:120]}"
    return result


def collect_menu_action_rows(user_env):
    Menu = user_env["ir.ui.menu"]
    rows = []
    for menu in Menu.search([]):
        try:
            action = menu.action
        except Exception:
            continue
        if not action or getattr(action, "_name", "") != "ir.actions.act_window":
            continue
        try:
            action_id = int(action.id)
            action_name = text(action.name)
            model = text(action.res_model)
            view_mode = text(action.view_mode)
            domain = text(action.domain)
            context = text(action.context)
        except Exception:
            continue
        if not is_business_model(model):
            continue
        rows.append(
            {
                "menu_id": menu.id,
                "menu_name": menu.complete_name or menu.name,
                "menu_xmlid": text(menu.get_external_id().get(menu.id)),
                "action_id": action_id,
                "action_name": action_name,
                "model": model,
                "view_mode": view_mode,
                "domain": domain,
                "context": context,
            }
        )
    rows.sort(key=lambda row: (row["model"], row["menu_id"], row["action_id"]))
    return rows


def audit_model(user_env, model: str, rows: list[dict]) -> dict:
    Model = user_env[model]
    model_meta = user_env["ir.model"].sudo().search([("model", "=", model)], limit=1)
    field_count = len(Model._fields)
    tree_view = get_runtime_view(Model, "tree")
    form_view = get_runtime_view(Model, "form")
    search_view = get_runtime_view(Model, "search")
    tree_fields = fields_from_runtime_view(tree_view)
    form_fields = fields_from_runtime_view(form_view)
    search_controls = extract_arch_search_controls(text(search_view.get("arch")))
    signals = model_foundation_signals(Model)
    record_count, count_error = count_records(Model)
    access = access_matrix(Model)
    gaps = []
    if not tree_fields:
        gaps.append("missing_tree_fields")
    if not form_fields:
        gaps.append("missing_form_fields")
    if not search_controls:
        gaps.append("missing_search_controls")
    if access.get("read") is not True:
        gaps.append("read_access_gap")
    if record_count == 0:
        gaps.append("no_business_data")
    if record_count is None:
        gaps.append("record_count_error")
    if not signals["attachment"]:
        gaps.append("missing_attachment_signal")
    if not signals["chatter"]:
        gaps.append("missing_chatter_signal")
    if lane_for_model(model) == "business_document":
        for key in ("state", "date"):
            if not signals[key]:
                gaps.append(f"missing_{key}_signal")
    return {
        "model": model,
        "model_label": text(model_meta.name),
        "lane": lane_for_model(model),
        "domain": domain_for_model(model),
        "menu_count": len({row["menu_id"] for row in rows}),
        "action_count": len({row["action_id"] for row in rows}),
        "field_count": field_count,
        "record_count": record_count,
        "record_count_error": count_error,
        "access": access,
        "foundation_signals": signals,
        "tree_field_count": len(tree_fields),
        "form_field_count": len(form_fields),
        "search_control_count": len(search_controls),
        "tree_fields": tree_fields,
        "form_fields": form_fields,
        "search_controls": search_controls,
        "view_errors": {
            "tree": text(tree_view.get("__error")),
            "form": text(form_view.get("__error")),
            "search": text(search_view.get("__error")),
        },
        "gaps": gaps,
        "menus": rows,
    }


def write_reports(payload: dict) -> None:
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Model View Fact Layer Audit",
        "",
        f"- audit_login: {payload['audit_login']}",
        f"- model_count: {payload['summary']['model_count']}",
        f"- menu_entry_count: {payload['summary']['menu_entry_count']}",
        f"- model_with_gap_count: {payload['summary']['model_with_gap_count']}",
        f"- no_data_model_count: {payload['summary']['no_data_model_count']}",
        f"- missing_attachment_signal_count: {payload['summary']['missing_attachment_signal_count']}",
        f"- missing_chatter_signal_count: {payload['summary']['missing_chatter_signal_count']}",
        "",
        "| lane | domain | model | menus | records | tree | form | search | gaps |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in payload["rows"]:
        lines.append(
            "| {lane} | {domain} | `{model}` | {menus} | {records} | {tree} | {form} | {search} | {gaps} |".format(
                lane=row["lane"],
                domain=row["domain"],
                model=row["model"],
                menus=row["menu_count"],
                records="-" if row["record_count"] is None else row["record_count"],
                tree=row["tree_field_count"],
                form=row["form_field_count"],
                search=row["search_control_count"],
                gaps=len(row["gaps"]),
            )
        )
    lines.extend(["", "## Gap Index", ""])
    for row in payload["rows"]:
        if not row["gaps"]:
            continue
        lines.append(f"- `{row['model']}` ({row['lane']}): {', '.join(row['gaps'])}")
    REPORT_MD.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main():
    base_env = _env()
    user = base_env["res.users"].sudo().search([("login", "=", AUDIT_LOGIN)], limit=1)
    if not user:
        raise RuntimeError(f"audit user not found: {AUDIT_LOGIN}")
    user_env = base_env(user=user)
    menu_rows = collect_menu_action_rows(user_env)
    by_model = defaultdict(list)
    for row in menu_rows:
        by_model[row["model"]].append(row)
    rows = [audit_model(user_env, model, model_rows) for model, model_rows in sorted(by_model.items())]
    gap_counter = Counter(gap for row in rows for gap in row["gaps"])
    lane_counter = Counter(row["lane"] for row in rows)
    summary = {
        "model_count": len(rows),
        "menu_entry_count": len(menu_rows),
        "model_with_gap_count": sum(1 for row in rows if row["gaps"]),
        "no_data_model_count": gap_counter.get("no_business_data", 0),
        "missing_attachment_signal_count": gap_counter.get("missing_attachment_signal", 0),
        "missing_chatter_signal_count": gap_counter.get("missing_chatter_signal", 0),
        "gap_counts": dict(sorted(gap_counter.items())),
        "lane_counts": dict(sorted(lane_counter.items())),
    }
    payload = {
        "ok": True,
        "scope": "runtime visible menu/action/model/view fact layer",
        "audit_login": AUDIT_LOGIN,
        "summary": summary,
        "rows": rows,
    }
    write_reports(payload)
    print(str(REPORT_MD))
    print(str(REPORT_JSON))
    print("[model_view_fact_layer_audit] PASS")


main()
