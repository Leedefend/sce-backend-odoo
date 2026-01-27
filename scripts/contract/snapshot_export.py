# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import os
import json
import uuid
from datetime import datetime

import odoo
from odoo import api, SUPERUSER_ID
from odoo.tools import config


def parse_args():
    parser = argparse.ArgumentParser(description="Export UI contract snapshots")
    parser.add_argument("--db", required=True, help="Database name")
    parser.add_argument("--user", required=True, help="User login or id")
    parser.add_argument("--case", required=True, help="Snapshot case name")
    parser.add_argument("--model", default="", help="Model name")
    parser.add_argument("--id", dest="record_id", type=int, default=0, help="Record id (optional)")
    parser.add_argument(
        "--view_type",
        default="form",
        choices=["form", "list", "kanban"],
        help="View type (default: form)",
    )
    parser.add_argument("--project_id", type=int, default=0, help="Project id (required for meta.describe_project_capabilities)")
    parser.add_argument("--menu_id", type=int, default=0, help="Menu id (optional)")
    parser.add_argument("--action_xmlid", default="", help="Action xmlid (optional)")
    parser.add_argument(
        "--op",
        default="",
        help="Operation (nav/menu/action_open/model/ui.contract/meta.describe_project_capabilities)",
    )
    parser.add_argument("--route", default="", help="Route for ui.contract (required when op=ui.contract)")
    parser.add_argument("--trace_id", default="", help="Trace id override for ui.contract (optional)")
    parser.add_argument("--execute_method", default="", help="Execute object method (optional)")
    parser.add_argument("--config", default=os.environ.get("ODOO_CONF", "/etc/odoo/odoo.conf"))
    parser.add_argument("--outdir", default="docs/contract/snapshots")
    parser.add_argument("--include_meta", action="store_true")
    parser.add_argument(
        "--stable",
        action="store_true",
        help="Enable stable snapshot output (strip volatile metadata and sort keys)",
    )
    parser.add_argument("--stdout", action="store_true", help="Print snapshot JSON to stdout")
    return parser.parse_args()


def find_user(env, user_ref):
    if str(user_ref).isdigit():
        user = env["res.users"].browse(int(user_ref)).exists()
        if user:
            return user
    user = env["res.users"].search([("login", "=", user_ref)], limit=1)
    if user:
        return user
    return env["res.users"].search([("name", "=", user_ref)], limit=1)


def normalize_contract(env, data, model, view_type):
    views = (data or {}).get("views") or {}
    if view_type == "form":
        form = views.get("form") or {}
        title_field = getattr(env[model], "_rec_name", None) or "name"
        return {
            "model": model,
            "view_type": "form",
            "titleField": title_field,
            "headerButtons": form.get("header_buttons") or [],
            "statButtons": form.get("stat_buttons") or form.get("button_box") or [],
            "ribbon": form.get("ribbon"),
            "sheet": form.get("layout") or [],
            "chatter": form.get("chatter") or {},
        }
    if view_type == "kanban":
        kanban = views.get("kanban") or {}
        fields = kanban.get("fields") or kanban.get("columns") or []
        if not fields and kanban.get("arch"):
            fields = _extract_fields_from_arch(kanban.get("arch"))
        return {
            "model": model,
            "view_type": "kanban",
            "fields": fields or [],
        }
    tree = views.get("tree") or views.get("list") or {}
    return {
        "model": model,
        "view_type": "list",
        "columns": tree.get("columns") or [],
        "columnsSchema": tree.get("columns_schema") or [],
    }


def build_menu_tree(env):
    Menu = env["ir.ui.menu"]
    roots = Menu.search([("parent_id", "=", False)], order="sequence,id")

    def _build(node):
        children = sorted(node.child_id, key=lambda c: (c.sequence, c.id))
        return {
            "id": node.id,
            "name": node.name,
            "action": node.action._name if node.action else None,
            "action_id": node.action.id if node.action else None,
            "children": [_build(child) for child in children],
        }

    return [_build(root) for root in roots]


def _extract_fields_from_arch(arch):
    if not arch:
        return []
    try:
        from lxml import etree
    except Exception:
        return []
    try:
        root = etree.fromstring(arch.encode("utf-8"))
    except Exception:
        return []
    return [node.get("name") for node in root.xpath(".//field[@name]") if node.get("name")]


def fallback_contract(env, model, view_type):
    model_env = env[model]
    view_type_odo = "tree" if view_type == "list" else view_type
    try:
        if hasattr(model_env, "fields_view_get"):
            view = model_env.fields_view_get(view_type=view_type_odo)
        else:
            view = model_env.get_view(view_type=view_type_odo)
    except Exception:
        view = {"arch": None, "fields": {}}
    arch = view.get("arch")
    fields = view.get("fields", {})
    field_names = _extract_fields_from_arch(arch) or list(fields.keys())
    if view_type == "form":
        layout = [{"type": "field", "name": name} for name in field_names]
        data = {
            "views": {"form": {"layout": layout, "header_buttons": [], "stat_buttons": [], "chatter": {}}},
            "fields": fields,
        }
    elif view_type == "kanban":
        data = {
            "views": {"kanban": {"fields": field_names}},
            "fields": fields,
        }
    else:
        data = {
            "views": {"tree": {"columns": field_names, "columns_schema": []}},
            "fields": fields,
        }
    return data


def _strip_runtime_record_fields(record):
    if not isinstance(record, dict):
        return record
    ignore = {"create_date", "write_date", "__last_update", "create_uid", "write_uid"}
    return {k: v for k, v in record.items() if k not in ignore}


def _normalize_domain(domain):
    if isinstance(domain, dict):
        return {k: _normalize_domain(v) for k, v in domain.items()}
    if isinstance(domain, (list, tuple)):
        normalized = []
        for item in domain:
            if isinstance(item, (list, tuple)):
                item_list = list(item)
                if len(item_list) >= 3 and item_list[1] in ("in", "not in") and isinstance(item_list[2], list):
                    values = item_list[2]
                    if all(isinstance(v, (str, int, float)) for v in values):
                        item_list[2] = sorted(values, key=lambda v: str(v))
                normalized.append(_normalize_domain(item_list))
            elif isinstance(item, dict):
                normalized.append({k: _normalize_domain(v) for k, v in item.items()})
            else:
                normalized.append(item)
        return normalized
    return domain


def _normalize_meta_fields(meta_fields):
    if not isinstance(meta_fields, list):
        return meta_fields
    cleaned = []
    for field in meta_fields:
        if not isinstance(field, dict):
            cleaned.append(field)
            continue
        normalized = dict(field)
        if "domain" in normalized:
            normalized["domain"] = _normalize_domain(normalized.get("domain"))
        cleaned.append(normalized)
    cleaned.sort(key=lambda item: item.get("name", "") if isinstance(item, dict) else "")
    return cleaned


VOLATILE_KEYS = {"trace_id", "exported_at", "generated_at", "request_id"}
UNORDERED_LIST_KEYS = {"actions", "reports", "buttons"}


def _strip_volatile(value):
    if isinstance(value, dict):
        cleaned = {}
        for key, item in value.items():
            if key in VOLATILE_KEYS:
                continue
            cleaned[key] = _strip_volatile(item)
        return cleaned
    if isinstance(value, list):
        return [_strip_volatile(item) for item in value]
    return value


def _stable_sort_list(items, key_name):
    if not items:
        return items
    if all(isinstance(item, (str, int, float)) for item in items):
        return sorted(items, key=lambda item: str(item))
    if all(isinstance(item, dict) for item in items):
        for sort_key in ("xml_id", "id", "name", "code"):
            if all(sort_key in item for item in items):
                return sorted(items, key=lambda item: str(item.get(sort_key)))
    return items


def _stable_normalize(value, path=None):
    if path is None:
        path = []
    if isinstance(value, dict):
        return {key: _stable_normalize(item, path + [key]) for key, item in value.items()}
    if isinstance(value, list):
        normalized = [_stable_normalize(item, path) for item in value]
        if path and path[-1] in UNORDERED_LIST_KEYS:
            return _stable_sort_list(normalized, path[-1])
        return normalized
    return value


def export_snapshot():
    args = parse_args()
    stable = args.stable or os.environ.get("SC_CONTRACT_STABLE") in ("1", "true", "yes")
    config.parse_config(["-c", args.config, "-d", args.db])
    os.environ.setdefault("SC_LIGHT_IMPORT", "1")
    from odoo.addons.smart_core.handlers.ui_contract import UiContractHandler

    registry = odoo.registry(args.db)
    with registry.cursor() as cr:
        su_env = api.Environment(cr, SUPERUSER_ID, {})
        user = find_user(su_env, args.user)
        user_fallback = None
        if not user:
            user = find_user(su_env, "admin")
            if user:
                user_fallback = "admin"
            else:
                raise SystemExit("user not found")

        env = api.Environment(cr, user.id, {})
        view_type = args.view_type

        op = (args.op or "model").strip().lower()
        payload = {"op": op}
        if op == "model":
            if not args.model:
                raise SystemExit("model required for op=model")
            payload.update({"model": args.model, "view_type": view_type})
        if op == "meta.describe_project_capabilities":
            payload.update({"project_id": args.project_id})
        if op == "ui.contract":
            payload.update({"route": args.route})
            if args.trace_id:
                payload.update({"trace_id": args.trace_id})

        action_data = None
        if op == "menu" or args.menu_id:
            if not args.menu_id:
                raise SystemExit("menu_id required for op=menu")
            payload = {"op": "menu", "menu_id": args.menu_id}
        elif op == "action_open" or args.action_xmlid:
            if not args.action_xmlid:
                raise SystemExit("action_xmlid required for op=action_open")
            action = env.ref(args.action_xmlid, raise_if_not_found=False)
            if not action:
                raise SystemExit("action xmlid not found")
            payload = {"op": "action_open", "action_id": action.id}

        fallback_used = False
        if op == "meta.describe_project_capabilities":
            if not args.project_id:
                raise SystemExit("project_id required for meta.describe_project_capabilities")
            project = env["project.project"].browse(args.project_id).exists()
            if not project:
                raise SystemExit("project not found")
            from odoo.addons.smart_construction_core.services.lifecycle_capability_service import (
                LifecycleCapabilityService,
            )

            service = LifecycleCapabilityService(env)
            res = {"data": service.describe_project(project)}
        elif op == "ui.contract":
            if not args.route:
                raise SystemExit("route required for ui.contract")
            from odoo.addons.smart_construction_portal.services.portal_contract_service import (
                PortalContractService,
            )

            service = PortalContractService(env)
            res = {
                "data": service.build_lifecycle_dashboard(
                    route=args.route, trace_id=args.trace_id or None
                )
            }
        else:
            handler = UiContractHandler(env, request=None, payload=payload)
            try:
                res = handler.handle(payload=payload)
                if isinstance(res, dict) and res.get("ok") is False:
                    raise SystemExit(res.get("error"))
            except Exception as exc:
                if payload.get("op") == "nav":
                    fallback_used = True
                    res = {"data": {"nav": build_menu_tree(env), "fallback": True, "error": str(exc)}}
                elif payload.get("op") == "model":
                    fallback_used = True
                    data = fallback_contract(env, args.model, view_type)
                    res = {"data": data, "fallback": True, "error": str(exc)}
                else:
                    raise

        data = res.get("data") if isinstance(res, dict) else {}
        if payload.get("op") in ("menu", "action_open"):
            action_data = data.get("action") or data.get("entry")

        ui_contract = None
        if payload.get("op") == "model":
            ui_contract = normalize_contract(env, data, args.model, view_type)

        record_data = None
        record_error = None
        if payload.get("op") == "model" and view_type == "form" and args.record_id:
            record = env[args.model].browse(args.record_id).exists()
            if record:
                fields_info = data.get("fields") or {}
                field_names = list(fields_info.keys()) if isinstance(fields_info, dict) else []
                try:
                    record_data = record.read(field_names or None)[0]
                except Exception as exc:
                    record_error = str(exc)

        meta_fields = None
        if args.include_meta and args.model:
            fields_info = env[args.model].fields_get()
            meta_fields = [
                {
                    "name": name,
                    "string": info.get("string"),
                    "ttype": info.get("type"),
                    "required": bool(info.get("required")),
                    "readonly": bool(info.get("readonly")),
                    "relation": info.get("relation"),
                    "selection": info.get("selection"),
                    "domain": info.get("domain"),
                    "help": info.get("help"),
                }
                for name, info in fields_info.items()
            ]

        execute_result = None
        execute_error = None
        if args.execute_method:
            if not args.model or not args.record_id:
                raise SystemExit("execute_method requires --model and --id")
            try:
                execute_result = env["sc.execute_button.service"].execute(
                    args.model, args.record_id, args.execute_method, context={}
                )
            except Exception as exc:
                execute_error = str(exc)

        snapshot = {
            "case": args.case,
            "trace_id": str(uuid.uuid4()),
            "exported_at": datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
            "contract_version": "v1",
            "model": args.model or None,
            "view_type": view_type if payload.get("op") == "model" else None,
            "op": payload.get("op"),
            "user": args.user,
            "user_fallback": user_fallback,
            "fallback": fallback_used,
            "action": action_data,
            "ui_contract": ui_contract,
            "ui_contract_raw": data,
            "record": _strip_runtime_record_fields(record_data),
            "record_error": record_error,
            "meta_fields": meta_fields,
            "execute_result": execute_result,
            "execute_error": execute_error,
        }

        snapshot["meta_fields"] = _normalize_meta_fields(snapshot.get("meta_fields"))
        if stable:
            snapshot = _stable_normalize(_strip_volatile(snapshot))

        if args.stdout:
            print(json.dumps(snapshot, ensure_ascii=False, indent=2, sort_keys=stable, default=str))
        else:
            outdir = args.outdir
            os.makedirs(outdir, exist_ok=True)
            outpath = os.path.join(outdir, f"{args.case}.json")
            with open(outpath, "w", encoding="utf-8") as f:
                json.dump(snapshot, f, ensure_ascii=False, indent=2, sort_keys=stable, default=str)
            print(outpath)


if __name__ == "__main__":
    export_snapshot()
