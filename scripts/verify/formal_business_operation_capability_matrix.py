# -*- coding: utf-8 -*-
"""Audit released formal handling entries as operational business capabilities.

Run with:
    odoo shell -d <db> -c <conf> < scripts/verify/formal_business_operation_capability_matrix.py
"""

from __future__ import annotations

import json
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from odoo.exceptions import AccessError
from odoo.tools.safe_eval import safe_eval

from odoo.addons.smart_core.handlers.ui_contract_v2 import UiContractV2Handler


PRODUCT_KEY = "construction.standard"
PRODUCT_ROOT_XMLID = "smart_construction_core.menu_sc_root"
PRODUCT_ROOT_LABEL = "智慧施工管理平台"
ARTIFACT_PATH = Path(os.getenv(
    "FORMAL_BUSINESS_OPERATION_CAPABILITY_MATRIX_JSON",
    "/tmp/sce-product-artifacts/formal_business_operation_capability_matrix_v1.json",
))
REPORT_PATH = Path(os.getenv(
    "FORMAL_BUSINESS_OPERATION_CAPABILITY_MATRIX_MD",
    "/tmp/sce-product-artifacts/formal_business_operation_capability_matrix_v1.md",
))
REQUIRED_VIEW_TYPES = ("tree", "form", "search")
FORMAL_CENTER_ORDER = [
    "基础资料",
    "项目中心",
    "合同中心",
    "施工管理",
    "物资与分包",
    "财务中心",
    "人事行政",
    "资料证照",
    "税务中心",
]


def _text(value) -> str:
    return str(value or "").strip()


def _escape(value) -> str:
    return _text(value).replace("|", "\\|")


def _unwrap(result):
    return result.to_legacy_dict() if hasattr(result, "to_legacy_dict") else (result if isinstance(result, dict) else {})


def _write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _path_parts(path: str) -> list[str]:
    return [part.strip() for part in _text(path).replace("/", " / ").split(" / ") if part.strip()]


def _center_from_path(path: str) -> str:
    parts = _path_parts(path)
    if parts and parts[0] == PRODUCT_ROOT_LABEL and len(parts) > 1:
        return parts[1]
    return ""


def _domain_from_path(path: str, center: str) -> str:
    parts = _path_parts(path)
    if center in parts:
        index = parts.index(center)
        if index + 1 < len(parts) - 1:
            return parts[index + 1]
    return ""


def _sort_key(row: dict):
    center = _text(row.get("center"))
    return (
        FORMAL_CENTER_ORDER.index(center) if center in FORMAL_CENTER_ORDER else 99,
        _text(row.get("domain")),
        _text(row.get("label")),
        _text(row.get("menu_xmlid")),
    )


def _field_count_from_tree(nodes) -> int:
    total = 0
    for node in nodes if isinstance(nodes, list) else []:
        if not isinstance(node, dict):
            continue
        node_type = _text(node.get("type") or node.get("containerType")).lower()
        if node_type == "field" or _text(node.get("name") or node.get("field")):
            total += 1
        for key in ("children", "pages", "tabs", "nodes", "items", "widgetList"):
            total += _field_count_from_tree(node.get(key))
    return total


def _field_names_from_tree(nodes) -> list[str]:
    names = []
    for node in nodes if isinstance(nodes, list) else []:
        if not isinstance(node, dict):
            continue
        name = _text(node.get("name") or node.get("field"))
        node_type = _text(node.get("type") or node.get("containerType")).lower()
        if name and (node_type == "field" or node.get("field") or node.get("name")):
            names.append(name)
        for key in ("children", "pages", "tabs", "nodes", "items", "widgetList"):
            names.extend(_field_names_from_tree(node.get(key)))
    return names


def _column_names(columns) -> list[str]:
    names = []
    for column in columns if isinstance(columns, list) else []:
        if isinstance(column, str):
            names.append(column)
        elif isinstance(column, dict):
            value = _text(column.get("name") or column.get("field") or column.get("key"))
            if value:
                names.append(value)
    return names


def _contract_payload(env_obj, *, action_id: int, menu_id: int, model: str, view_type: str) -> dict:
    payload = {
        "action_id": action_id,
        "menu_id": menu_id,
        "model": model,
        "view_type": view_type,
        "op": "model",
    }
    handler = UiContractV2Handler(env=env_obj, su_env=env_obj["ir.model"].sudo().env, payload=payload)
    return _unwrap(handler.handle(payload, None))


def _safe_action_context(action) -> dict:
    try:
        value = safe_eval(action.context or "{}", {})
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def _action_domain_history_scoped(action) -> bool:
    domain_text = _text(action.domain)
    return any(token in domain_text for token in ("legacy_", "legacy_source_", "source_table", "history_", "uc_"))


def _view_looks_user_confirmed(view) -> bool:
    if not view:
        return False
    value = " ".join([
        _text(view.name),
        _text(view.key),
        _text(view.xml_id),
    ]).lower()
    return "user_confirmed" in value or "用户确认" in value


def _action_user_confirmed_view_scoped(action) -> bool:
    if _view_looks_user_confirmed(action.view_id):
        return True
    for view_link in action.view_ids:
        if _view_looks_user_confirmed(view_link.view_id):
            return True
    return False


def _contract_summary(env_obj, *, action_id: int, menu_id: int, model: str, view_type: str) -> dict:
    try:
        result = _contract_payload(env_obj, action_id=action_id, menu_id=menu_id, model=model, view_type=view_type)
        data = result.get("data") if isinstance(result, dict) else {}
        layout = data.get("layoutContract") if isinstance(data, dict) and isinstance(data.get("layoutContract"), dict) else {}
        if view_type in {"tree", "list"}:
            profile = layout.get("listProfile") if isinstance(layout.get("listProfile"), dict) else {}
            columns = list(profile.get("columns") or [])
            return {"ok": bool(result.get("ok")), "count": len(columns), "fields": _column_names(columns), "head": columns[:8]}
        if view_type == "form":
            tree = layout.get("containerTree") if isinstance(layout.get("containerTree"), list) else []
            return {"ok": bool(result.get("ok")), "count": _field_count_from_tree(tree), "fields": sorted(set(_field_names_from_tree(tree)))}
        if view_type == "search":
            search = layout.get("searchProfile") if isinstance(layout.get("searchProfile"), dict) else {}
            filters = list(search.get("filters") or [])
            group_by = list(search.get("groupBy") or search.get("group_by") or [])
            return {"ok": bool(result.get("ok")), "count": len(filters) + len(group_by)}
        return {"ok": bool(result.get("ok")), "count": 0}
    except Exception as exc:
        return {"ok": False, "count": 0, "error": repr(exc)}


def _action_defaults(action) -> dict:
    return {
        key.replace("default_", "", 1): value
        for key, value in _safe_action_context(action).items()
        if isinstance(key, str) and key.startswith("default_")
    }


def _is_stored_input_field(field) -> bool:
    return not bool(getattr(field, "compute", False)) and not bool(getattr(field, "related", False))


def _required_user_input_fields(env_obj, model: str, action) -> list[str]:
    Model = env_obj[model].with_context(**_safe_action_context(action))
    required_names = []
    for name, field in Model._fields.items():
        if name == "id" or name.startswith("__"):
            continue
        if not bool(getattr(field, "required", False)) or not _is_stored_input_field(field):
            continue
        if getattr(field, "type", "") in {"boolean", "one2many", "many2many"}:
            continue
        required_names.append(name)
    defaults = {}
    try:
        defaults.update(Model.default_get(required_names))
    except Exception:
        defaults = {}
    defaults.update(_action_defaults(action))
    return sorted(name for name in required_names if defaults.get(name) in (None, False, ""))


def _has_contract(env_obj, *, action_id: int, model: str, view_type: str) -> bool:
    Contract = env_obj["ui.business.config.contract"].sudo()
    domain = [
        ("model", "=", model),
        ("view_type", "=", view_type),
        ("action_id", "=", action_id),
        ("status", "=", "published"),
    ]
    return bool(Contract.search_count(domain))


def _access(env_obj, model: str) -> dict:
    result = {}
    Model = env_obj[model].with_context(active_test=False)
    for op in ("read", "create", "write"):
        try:
            result[op] = bool(Model.check_access_rights(op, raise_exception=False))
        except AccessError:
            result[op] = False
    return result


def _policy_rows(env_obj) -> list[dict]:
    policy = env_obj["sc.product.policy"].sudo().with_context(active_test=False).search([("product_key", "=", PRODUCT_KEY)], limit=1)
    if not policy:
        raise AssertionError("missing product policy: %s" % PRODUCT_KEY)
    rows = []
    for group in policy.menu_groups or []:
        if not isinstance(group, dict):
            continue
        center = _text(group.get("group_label") or group.get("label"))
        for menu in group.get("menus") or []:
            if not isinstance(menu, dict):
                continue
            if _text(menu.get("entry_intent")) != "handling":
                continue
            if not bool(menu.get("enabled", True)) or _text(menu.get("release_state") or "released") != "released":
                continue
            path = _text(menu.get("visible_menu_path"))
            rows.append({
                "center": center or _center_from_path(path),
                "domain": _domain_from_path(path, center),
                "label": _text(menu.get("label") or menu.get("page_label")),
                "path": path,
                "model": _text(menu.get("integration_model") or menu.get("fact_model") or menu.get("res_model")),
                "menu_xmlid": _text(menu.get("menu_xmlid") or menu.get("page_key") or menu.get("menu_key")),
                "default_business_category_code": _text(menu.get("default_business_category_code")),
                "integration_target": _text(menu.get("integration_target")),
            })
    return sorted(rows, key=_sort_key)


def _menu_action(env_obj, xmlid: str):
    menu = env_obj.ref(xmlid, raise_if_not_found=False)
    if not menu:
        return None, None
    return menu, menu.action if menu.action and menu.action._name == "ir.actions.act_window" else None


def _audit_row(env_obj, row: dict) -> dict:
    menu, action = _menu_action(env_obj, row["menu_xmlid"])
    model = row["model"]
    issues = []
    if not menu:
        issues.append("menu_missing")
    elif not menu.active:
        issues.append("menu_inactive")
    if not action:
        issues.append("act_window_missing")
    elif _text(action.res_model) != model:
        issues.append("action_model_mismatch")
    elif action:
        action_context = _safe_action_context(action)
        if action_context.get("create") is False:
            issues.append("action_create_disabled")
        if _action_domain_history_scoped(action):
            issues.append("action_domain_history_scoped")
        if _action_user_confirmed_view_scoped(action):
            issues.append("action_user_confirmed_view_scoped")
    if model not in env_obj:
        issues.append("model_missing")

    action_id = int(action.id) if action else 0
    menu_id = int(menu.id) if menu else 0
    access = _access(env_obj, model) if model in env_obj else {"read": False, "create": False, "write": False}
    for op, ok in access.items():
        if not ok:
            issues.append("access_%s_missing" % op)

    contracts = {}
    runtime = {}
    if action_id and menu_id and model in env_obj:
        for view_type in REQUIRED_VIEW_TYPES:
            contracts[view_type] = _has_contract(env_obj, action_id=action_id, model=model, view_type=view_type)
            runtime[view_type] = _contract_summary(env_obj, action_id=action_id, menu_id=menu_id, model=model, view_type=view_type)
            if not runtime[view_type].get("ok"):
                issues.append("runtime_%s_contract_failed" % view_type)
        if not contracts.get("tree"):
            issues.append("published_tree_contract_missing")
        if not contracts.get("form"):
            issues.append("published_form_contract_missing")
        if not contracts.get("search"):
            issues.append("published_search_contract_missing")
        if runtime.get("tree", {}).get("count", 0) <= 0:
            issues.append("runtime_list_fields_empty")
        if runtime.get("form", {}).get("count", 0) <= 0:
            issues.append("runtime_form_fields_empty")
        required_form_fields = _required_user_input_fields(env_obj, model, action)
        form_fields = set(runtime.get("form", {}).get("fields") or [])
        missing_required_form_fields = sorted(name for name in required_form_fields if name not in form_fields)
        if missing_required_form_fields:
            issues.append("runtime_form_required_fields_missing")
    else:
        required_form_fields = []
        missing_required_form_fields = []

    return {
        **row,
        "status": "pass" if not issues else "fail",
        "issues": sorted(set(issues)),
        "menu_id": menu_id,
        "action_id": action_id,
        "action_name": _text(action.name) if action else "",
        "action_model": _text(action.res_model) if action else "",
        "view_mode": _text(action.view_mode) if action else "",
        "access": access,
        "published_contracts": contracts,
        "runtime": runtime,
        "required_form_fields": required_form_fields,
        "missing_required_form_fields": missing_required_form_fields,
        "runtime_url": "/a/%s?menu_id=%s" % (action_id, menu_id) if action_id and menu_id else "",
    }


def _render_markdown(payload: dict) -> str:
    lines = [
        "# 正式办理能力运行矩阵 V1",
        "",
        "本矩阵以产品策略中已发布、启用且 `entry_intent=handling` 的正式办理入口为准，检查每个入口是否具备菜单、动作、模型、CRUD 权限、运行态合同和可访问办理 URL。",
        "",
        "## 摘要",
        "",
        f"- 数据库：`{payload['database']}`",
        f"- 正式办理入口：`{payload['summary']['entry_count']}`",
        f"- 通过入口：`{payload['summary']['pass_count']}`",
        f"- 失败入口：`{payload['summary']['fail_count']}`",
        f"- issue 分布：`{json.dumps(payload['summary']['issue_counts'], ensure_ascii=False, sort_keys=True)}`",
        "",
        "## 矩阵",
        "",
        "| 中心 | 业务域 | 能力入口 | 模型 | CRUD | 合同 | 运行态字段 | URL | 问题 |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in payload["rows"]:
        access = row.get("access") or {}
        contracts = row.get("published_contracts") or {}
        runtime = row.get("runtime") or {}
        crud = "".join(op[0].upper() if access.get(op) else "-" for op in ("read", "create", "write"))
        contract_text = "/".join("%s:%s" % (key, "Y" if contracts.get(key) else "N") for key in REQUIRED_VIEW_TYPES)
        runtime_text = "list=%s form=%s search=%s" % (
            runtime.get("tree", {}).get("count", 0),
            runtime.get("form", {}).get("count", 0),
            runtime.get("search", {}).get("count", 0),
        )
        lines.append("| %s | %s | %s | `%s` | `%s` | `%s` | `%s` | `%s` | %s |" % (
            _escape(row.get("center")),
            _escape(row.get("domain")),
            _escape(row.get("label")),
            _escape(row.get("model")),
            crud,
            contract_text,
            runtime_text,
            _escape(row.get("runtime_url")),
            _escape(", ".join(row.get("issues") or []) or "PASS"),
        ))
    return "\n".join(lines) + "\n"


def main() -> int:
    env_obj = globals()["env"]
    rows = [_audit_row(env_obj, row) for row in _policy_rows(env_obj)]
    issue_counter = Counter(issue for row in rows for issue in row.get("issues", []))
    failed = [row for row in rows if row.get("status") != "pass"]
    payload = {
        "schema_version": "formal_business_operation_capability_matrix.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "database": env_obj.cr.dbname,
        "product_key": PRODUCT_KEY,
        "summary": {
            "entry_count": len(rows),
            "pass_count": len(rows) - len(failed),
            "fail_count": len(failed),
            "issue_counts": dict(sorted(issue_counter.items())),
        },
        "rows": rows,
    }
    artifact_path = _write(ARTIFACT_PATH, json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n")
    report_path = _write(REPORT_PATH, _render_markdown(payload))
    print(json.dumps({
        "status": "PASS" if not failed else "FAIL",
        "artifact": str(artifact_path),
        "report": str(report_path),
        **payload["summary"],
    }, ensure_ascii=False, sort_keys=True))
    if failed:
        raise AssertionError("formal business operation matrix failed: %s" % payload["summary"]["issue_counts"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
