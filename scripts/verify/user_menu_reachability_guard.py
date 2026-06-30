# -*- coding: utf-8 -*-
"""Verify configured business menus are actually reachable by the target user.

Run through ``scripts/ops/odoo_shell_exec.sh`` so the global ``env`` is provided.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from lxml import etree
from odoo import SUPERUSER_ID, api
from odoo.exceptions import MissingError
from odoo.addons.smart_core.adapters.nav_tree_cleaner import NavTreeCleaner
from odoo.addons.smart_core.adapters.odoo_nav_adapter import OdooNavAdapter
from odoo.addons.smart_core.app_config_engine.services.dispatchers.nav_dispatcher import NavDispatcher
from odoo.addons.smart_core.delivery.delivery_engine import DeliveryEngine
from odoo.addons.smart_core.handlers.system_init import (
    _apply_user_menu_config_to_delivery_nav,
    _filter_nav_by_release_gate,
    _filter_nav_for_user_data_acceptance_only,
    _load_platform_release_gate,
    _remove_nav_groups_by_label,
)


DEFAULT_LOGIN = "wutao"
DEFAULT_ROOT_XMLID = "smart_construction_core.menu_sc_root"
ACTION_TYPES_TO_CHECK = {"ir.actions.act_window"}
RELATIONAL_TYPES_TO_CHECK = {"many2one", "one2many", "many2many"}
VIEW_TYPES_TO_CHECK = {"tree", "list", "form", "kanban"}
ARTIFACT_BASENAME = "user_menu_reachability_guard"


def _text(value) -> str:
    return str(value or "").strip()


def _int(value) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _artifact_root() -> Path:
    raw = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(raw)] if raw else []
    candidates.extend([Path("/mnt/artifacts/backend"), Path.cwd() / "artifacts", Path("/tmp")])
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return candidate
        except OSError:
            continue
    return Path("/tmp")


def _write_artifacts(result: dict) -> None:
    root = _artifact_root()
    json_path = root / f"{ARTIFACT_BASENAME}.{env.cr.dbname}.json"  # noqa: F821
    md_path = root / f"{ARTIFACT_BASENAME}.{env.cr.dbname}.md"  # noqa: F821
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True, default=str), encoding="utf-8")
    lines = [
        "# User Menu Reachability Guard",
        "",
        f"- database: `{env.cr.dbname}`",  # noqa: F821
        f"- login: `{result.get('login')}`",
        f"- checked actions: `{result.get('checked_actions')}`",
        f"- checked relation models: `{result.get('checked_relation_models')}`",
        f"- skipped nodes: `{result.get('skipped_nodes')}`",
        f"- failures: `{len(result.get('failures') or [])}`",
    ]
    failures = result.get("failures") or []
    if failures:
        lines.extend(["", "## Failures", ""])
        for item in failures[:100]:
            lines.append(
                "- `{stage}` `{path}` action=`{action_id}` model=`{model}` detail=`{detail}`".format(
                    stage=_text(item.get("stage")),
                    path=_text(item.get("path")),
                    action_id=_text(item.get("action_id")),
                    model=_text(item.get("model")),
                    detail=_text(item.get("detail")),
                )
            )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    result["artifact_json"] = str(json_path)
    result["artifact_report"] = str(md_path)


def _node_label(node: dict) -> str:
    return _text(node.get("label") or node.get("title") or node.get("name") or node.get("display_name"))


def _walk(nodes, path=()):
    for node in nodes or []:
        if not isinstance(node, dict):
            continue
        current = path + (_node_label(node),)
        yield current, node
        children = node.get("children") if isinstance(node.get("children"), list) else []
        yield from _walk(children, current)


def _node_meta(node: dict) -> dict:
    meta = node.get("meta") if isinstance(node.get("meta"), dict) else {}
    target = node.get("target") if isinstance(node.get("target"), dict) else {}
    action = node.get("action") if isinstance(node.get("action"), dict) else {}
    return {
        "menu_id": _int(node.get("menu_id") or meta.get("menu_id") or target.get("menu_id")),
        "menu_xmlid": _text(node.get("menu_xmlid") or meta.get("menu_xmlid") or target.get("menu_xmlid")),
        "action_id": _int(
            node.get("action_id")
            or meta.get("action_id")
            or target.get("action_id")
            or action.get("id")
            or action.get("action_id")
        ),
        "action_type": _text(node.get("action_type") or meta.get("action_type") or target.get("action_type") or action.get("type")),
    }


def _runtime_delivery_nav(user_env) -> list[dict]:
    su_env = api.Environment(env.cr, SUPERUSER_ID, dict(user_env.context or {}))  # noqa: F821
    nav_data, _versions = NavDispatcher(user_env, su_env).build_nav(
        {"subject": "nav", "scene": "web", "root_xmlid": os.getenv("USER_MENU_REACHABILITY_ROOT_XMLID") or DEFAULT_ROOT_XMLID}
    )
    native_nav = NavTreeCleaner().clean(nav_data.get("nav") or [])
    OdooNavAdapter().enrich(user_env, native_nav)
    payload = DeliveryEngine(user_env).build(
        data={},
        product_key="",
        edition_key="standard",
        base_product_key="",
        native_nav=native_nav,
    )
    delivery_nav = payload.get("nav") if isinstance(payload.get("nav"), list) else []
    release_gate = _load_platform_release_gate(
        user_env,
        product_key=_text(payload.get("product_key")) or "construction.standard",
    )
    delivery_nav, _gate_meta = _filter_nav_by_release_gate(delivery_nav, release_gate)
    delivery_nav, acceptance_meta = _filter_nav_for_user_data_acceptance_only(user_env, delivery_nav)
    if acceptance_meta.get("applied"):
        delivery_nav = _remove_nav_groups_by_label(delivery_nav, {"用户核对菜单"})
    delivery_nav, _config_meta = _apply_user_menu_config_to_delivery_nav(user_env, delivery_nav)
    return delivery_nav


def _extract_action_nodes(nav: list[dict]) -> list[dict]:
    rows = []
    for path, node in _walk(nav):
        meta = _node_meta(node)
        if not meta["action_id"]:
            continue
        rows.append(
            {
                "path": " / ".join(part for part in path if part),
                "label": _node_label(node),
                **meta,
            }
        )
    return rows


def _failure(row: dict, stage: str, detail, model: str = "") -> dict:
    return {
        "stage": stage,
        "detail": _text(detail),
        "path": row.get("path"),
        "label": row.get("label"),
        "menu_id": row.get("menu_id"),
        "menu_xmlid": row.get("menu_xmlid"),
        "action_id": row.get("action_id"),
        "model": model,
    }


def _action_payload(user_env, row: dict) -> dict | None:
    try:
        # ``ir.actions.actions`` is a technical parent table restricted to Settings.
        # Resolve only the action type with sudo; business model probes below still
        # run through the target user's environment.
        action = env["ir.actions.actions"].sudo().browse(row["action_id"])  # noqa: F821
        if not action.exists():
            raise MissingError("action does not exist")
        action_type = _text(action.type)
        if action_type not in ACTION_TYPES_TO_CHECK:
            row["resolved_action_type"] = action_type
            return {"type": action_type, "skipped": True}
        # Action metadata contains technical relations such as
        # ``ir.actions.act_window.view``. Business users reach these actions
        # through menu delivery, but direct reads of that technical model are
        # intentionally restricted to Settings. Resolve the action shape with
        # sudo, then keep all business model probes on the target user env.
        payload = env["ir.actions.act_window"].sudo().browse(row["action_id"]).read(  # noqa: F821
            ["name", "type", "res_model", "view_mode", "views", "view_id", "view_ids", "domain", "context"]
        )
        if not payload:
            raise MissingError("act_window action payload is empty")
        return payload[0]
    except Exception as exc:  # noqa: BLE001 - report exact menu context to artifact.
        row.setdefault("failures", []).append(_failure(row, "action_read", exc))
        return None


def _model_read_probe(user_env, row: dict, model_name: str) -> list[dict]:
    failures = []
    if model_name not in user_env:
        return [_failure(row, "model_registry", "model is not registered", model_name)]
    Model = user_env[model_name]
    try:
        if not Model.check_access_rights("read", raise_exception=False):
            failures.append(_failure(row, "model_acl", "read access is false", model_name))
            return failures
    except Exception as exc:  # noqa: BLE001
        failures.append(_failure(row, "model_acl", exc, model_name))
        return failures
    try:
        Model.search_read([], ["display_name"], limit=1)
    except Exception as exc:  # noqa: BLE001
        failures.append(_failure(row, "model_search_read", exc, model_name))
    return failures


def _view_specs(action_payload: dict) -> list[tuple[int, str]]:
    out: list[tuple[int, str]] = []
    for pair in action_payload.get("views") or []:
        if not isinstance(pair, (list, tuple)) or len(pair) < 2:
            continue
        view_type = "tree" if _text(pair[1]) == "list" else _text(pair[1])
        if view_type in VIEW_TYPES_TO_CHECK:
            out.append((_int(pair[0]), view_type))
    view_mode = _text(action_payload.get("view_mode"))
    for view_type in [("tree" if item.strip() == "list" else item.strip()) for item in view_mode.split(",") if item.strip()]:
        if view_type in VIEW_TYPES_TO_CHECK and (0, view_type) not in out and not any(existing[1] == view_type for existing in out):
            out.append((0, view_type))
    return out


def _view_arch(user_env, model_name: str, view_id: int, view_type: str) -> str:
    Model = user_env[model_name]
    if hasattr(Model, "get_view"):
        payload = Model.get_view(view_id=view_id or None, view_type=view_type)
    else:
        payload = Model.fields_view_get(view_id=view_id or None, view_type=view_type)
    return _text((payload or {}).get("arch"))


def _field_names_from_arch(arch: str) -> set[str]:
    if not arch:
        return set()
    try:
        root = etree.fromstring(arch.encode("utf-8"))
    except etree.XMLSyntaxError:
        return set()
    return {_text(node.get("name")) for node in root.xpath(".//field[@name]") if _text(node.get("name"))}


def _relation_read_probe(user_env, row: dict, model_name: str, action_payload: dict) -> tuple[list[dict], int]:
    failures = []
    checked_relations = set()
    if model_name not in user_env:
        return failures, 0
    Model = user_env[model_name]
    try:
        fields_meta = Model.fields_get(attributes=["type", "relation"])
    except Exception as exc:  # noqa: BLE001
        return [_failure(row, "fields_get", exc, model_name)], 0

    for view_id, view_type in _view_specs(action_payload):
        try:
            arch = _view_arch(user_env, model_name, view_id, view_type)
        except Exception as exc:  # noqa: BLE001
            failures.append(_failure(row, "view_arch", exc, model_name))
            continue
        for field_name in _field_names_from_arch(arch):
            field_meta = fields_meta.get(field_name) or {}
            field_type = _text(field_meta.get("type"))
            relation = _text(field_meta.get("relation"))
            if field_type not in RELATIONAL_TYPES_TO_CHECK or not relation:
                continue
            key = (field_name, relation)
            if key in checked_relations:
                continue
            checked_relations.add(key)
            if relation not in user_env:
                failures.append(_failure(row, "relation_registry", f"{field_name}: {relation} is not registered", model_name))
                continue
            try:
                if not user_env[relation].check_access_rights("read", raise_exception=False):
                    failures.append(_failure(row, "relation_acl", f"{field_name}: {relation} read access is false", model_name))
            except Exception as exc:  # noqa: BLE001
                failures.append(_failure(row, "relation_acl", f"{field_name}: {relation}: {exc}", model_name))
    return failures, len(checked_relations)


def _limit_rows(rows: list[dict]) -> list[dict]:
    raw_ids = _text(os.getenv("USER_MENU_REACHABILITY_ACTION_IDS"))
    if raw_ids:
        wanted = {_int(item) for item in raw_ids.replace(";", ",").split(",") if _int(item)}
        rows = [row for row in rows if row.get("action_id") in wanted]
    limit = _int(os.getenv("USER_MENU_REACHABILITY_LIMIT"))
    if limit > 0:
        return rows[:limit]
    return rows


def main() -> None:
    login = os.getenv("USER_MENU_REACHABILITY_LOGIN") or DEFAULT_LOGIN
    user = env["res.users"].sudo().search([("login", "=", login)], limit=1)  # noqa: F821
    if not user:
        raise AssertionError("missing verification user: %s" % login)
    user_env = env(user=user.id)  # noqa: F821
    nav = _runtime_delivery_nav(user_env)
    rows = _limit_rows(_extract_action_nodes(nav))

    failures = []
    checked_actions = 0
    checked_relation_models = 0
    skipped_nodes = 0
    checked_action_ids = set()
    for row in rows:
        action_payload = _action_payload(user_env, row)
        failures.extend(row.pop("failures", []))
        if not action_payload:
            continue
        if action_payload.get("skipped"):
            skipped_nodes += 1
            continue
        if row["action_id"] in checked_action_ids:
            continue
        checked_action_ids.add(row["action_id"])
        checked_actions += 1
        model_name = _text(action_payload.get("res_model"))
        if not model_name:
            failures.append(_failure(row, "action_model", "act_window action has no res_model"))
            continue
        failures.extend(_model_read_probe(user_env, row, model_name))
        relation_failures, relation_count = _relation_read_probe(user_env, row, model_name, action_payload)
        failures.extend(relation_failures)
        checked_relation_models += relation_count

    result = {
        "mode": ARTIFACT_BASENAME,
        "database": env.cr.dbname,  # noqa: F821
        "login": login,
        "nav_action_nodes": len(rows),
        "checked_actions": checked_actions,
        "checked_relation_models": checked_relation_models,
        "skipped_nodes": skipped_nodes,
        "failures": failures,
    }
    _write_artifacts(result)
    if failures:
        print(
            "[user_menu_reachability_guard] FAIL checked_actions=%s failures=%s artifact=%s"
            % (checked_actions, len(failures), result.get("artifact_json"))
        )
        raise AssertionError(json.dumps(failures[:20], ensure_ascii=False, default=str))
    print(
        "[user_menu_reachability_guard] PASS checked_actions=%s relation_models=%s skipped=%s artifact=%s"
        % (checked_actions, checked_relation_models, skipped_nodes, result.get("artifact_json"))
    )


main()
