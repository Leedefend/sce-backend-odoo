# -*- coding: utf-8 -*-
"""Export the runtime product menu catalog from Odoo native menu facts."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

try:
    from odoo.addons.smart_core.utils.backend_contract_boundaries import LOWCODE_SYSTEM_CONFIG_MENU_XMLIDS
except Exception:  # pragma: no cover - fallback for partially installed runtimes
    LOWCODE_SYSTEM_CONFIG_MENU_XMLIDS = set()


ROOT_XMLIDS = tuple(
    item.strip()
    for item in os.getenv(
        "PRODUCT_MENU_CATALOG_ROOT_XMLIDS",
        "smart_construction_core.menu_sc_root,smart_core.menu_smart_core_platform_root",
    ).split(",")
    if item.strip()
)
OUTPUT_PATH = Path(os.getenv("PRODUCT_MENU_CATALOG_RUNTIME_PATH", "/tmp/product_menu_catalog_runtime_v1.json"))
VISIBLE_LOGINS = tuple(
    item.strip()
    for item in os.getenv(
        "PRODUCT_MENU_CATALOG_VISIBLE_LOGINS",
        "admin,wutao,demo_business_full,demo_role_project_manager,demo_role_finance,demo_role_executive",
    ).split(",")
    if item.strip()
)
BUSINESS_VISIBLE_LOGINS = {
    item.strip()
    for item in os.getenv(
        "PRODUCT_MENU_CATALOG_BUSINESS_LOGINS",
        "wutao,demo_business_full,demo_role_project_manager,demo_role_finance,demo_role_executive",
    ).split(",")
    if item.strip()
}
INTERNAL_HISTORY_PATH_TOKENS = (
    "系统配置",
    "历史财务事实（内部）",
)
BUSINESS_CONFIG_PATH_PREFIX = "智慧施工管理平台 / 配置中心"
PRODUCT_ROOT_LABEL = "智慧施工管理平台"
CONFIG_ADMIN_GROUP_XMLIDS = (
    "smart_construction_core.group_sc_cap_business_config_admin",
    "smart_construction_core.group_sc_cap_config_admin",
    "smart_core.group_smart_core_business_config_admin",
    "smart_core.group_smart_core_admin",
)

SYSTEM_CONFIG_XMLIDS = set(LOWCODE_SYSTEM_CONFIG_MENU_XMLIDS) | {
    "smart_construction_core.menu_sc_business_config_center",
    "smart_construction_core.menu_sc_config_center",
    "smart_construction_core.menu_sc_dictionary",
    "smart_construction_core.menu_sc_dictionary_root",
    "smart_construction_core.menu_sc_approval_policy",
    "smart_construction_core.menu_sc_approval_scope",
    "smart_construction_core.menu_sc_project_stage_requirement_items",
    "smart_construction_core.menu_sc_project_cost_code",
    "smart_construction_core.menu_sc_legacy_user_context",
    "smart_construction_core.menu_sc_runtime_user_management",
    "smart_construction_core.menu_sc_legacy_user_priority_menu_plan",
}

LAYER_DEFINITIONS = {
    "formal_product": "正式产品办理入口，用于日常施工业务的新增、编辑、查询、分析和继续办理。",
    "system_config": "系统/产品配置入口，包括低代码恢复入口、字典、规则、定额、审批和管理配置。",
    "user_config": "租户或用户自主管理的偏好、个性化和运行时配置入口。",
    "history_acceptance": "历史数据承载、用户核对、历史来源事实、迁移连续性和验收过渡入口。",
    "dev_governance": "平台内核、场景治理、发布运维、诊断和开发治理入口。",
}

SCENE_ONLY_MENU_SCENE_KEYS = {
    "smart_construction_core.menu_sc_history_todo": "workspace.home",
}

DEV_TOKENS = (
    "平台内核",
    "scene governance",
    "场景治理",
    "场景与能力",
    "治理",
    "工作流",
    "项目管理（后台）",
    "release",
    "snapshot",
    "platform",
    "ops",
    "debug",
    "diagnostic",
    "订阅",
    "授权",
    "用量",
    "运营任务",
    "公司访问",
)
SYSTEM_TOKENS = (
    "系统权限",
    "配置中心",
    "系统配置",
    "菜单配置",
    "表单字段配置",
    "字段配置",
    "低代码",
    "数据字典",
    "业务字典",
    "字典",
    "定额",
    "审批配置",
    "审批范围",
    "阶段要求配置",
    "成本科目",
    "参数",
    "规则",
)
USER_CONFIG_TOKENS = (
    "用户配置",
    "个人配置",
    "个性化",
    "偏好",
    "preference",
    "personal",
    "tenant",
)
HISTORY_TOKENS = (
    "历史",
    "legacy",
    "用户确认",
    "user acceptance",
    "承载",
    "核对",
    "迁移",
    "历史来源",
)


Menu = env["ir.ui.menu"].sudo().with_context(active_test=False)  # noqa: F821
IMD = env["ir.model.data"].sudo()  # noqa: F821


def _text(value) -> str:
    return str(value or "").strip()


def _xmlid(record) -> str:
    if not record:
        return ""
    try:
        return record.get_external_id().get(record.id, "") or ""
    except Exception:
        row = IMD.search([("model", "=", record._name), ("res_id", "=", record.id)], limit=1)
        return row.complete_name if row else ""


def _menu_path(menu) -> str:
    names = []
    current = menu
    while current:
        names.append(_text(current.name))
        current = current.parent_id
    return " / ".join(reversed([name for name in names if name]))


def _read_action_raw(menu_ids: list[int]) -> dict[int, str]:
    if not menu_ids:
        return {}
    env.cr.execute("SELECT id, action FROM ir_ui_menu WHERE id = ANY(%s)", (menu_ids,))  # noqa: F821
    return {int(menu_id): _text(action) for menu_id, action in env.cr.fetchall()}  # noqa: F821


def _parse_action(raw: str) -> tuple[str, int | None]:
    value = _text(raw)
    if "," not in value:
        return "", None
    model, raw_id = value.split(",", 1)
    try:
        return _text(model), int(_text(raw_id))
    except Exception:
        return _text(model), None


def _action_xmlid(model: str, action_id: int | None) -> str:
    if not model or not action_id:
        return ""
    row = IMD.search([("model", "=", model), ("res_id", "=", action_id)], limit=1)
    return row.complete_name if row else ""


def _action_meta(model: str, action_id: int | None) -> dict[str, object]:
    if not model or not action_id or model not in env:  # noqa: F821
        return {}
    record = env[model].sudo().browse(action_id).exists()  # noqa: F821
    if not record:
        return {"exists": False}
    out = {"exists": True, "name": _text(getattr(record, "name", ""))}
    if model == "ir.actions.act_window":
        out.update(
            {
                "res_model": _text(record.res_model),
                "view_mode": _text(record.view_mode),
                "target": _text(record.target),
            }
        )
    elif model == "ir.actions.client":
        out["tag"] = _text(getattr(record, "tag", ""))
    elif model == "ir.actions.act_url":
        out["target"] = _text(getattr(record, "target", ""))
    return out


def _groups(menu) -> list[dict[str, object]]:
    rows = []
    for group in menu.groups_id:
        rows.append(
            {
                "id": int(group.id),
                "xmlid": _xmlid(group),
                "name": _text(group.display_name or group.name),
            }
        )
    return sorted(rows, key=lambda item: (item["xmlid"] or "", item["name"]))


def _user_meta(user) -> dict[str, object]:
    if not user:
        return {"id": None, "login": "", "name": ""}
    return {
        "id": int(user.id),
        "login": _text(getattr(user, "login", "")),
        "name": _text(getattr(user, "name", "")),
    }


def _visible_by_login(menu_ids: set[int]) -> dict[str, list[str]]:
    out = {str(menu_id): [] for menu_id in sorted(menu_ids)}
    for login in VISIBLE_LOGINS:
        user = env["res.users"].sudo().search([("login", "=", login)], limit=1)  # noqa: F821
        if not user:
            continue
        MenuForUser = env["ir.ui.menu"].with_user(user)  # noqa: F821
        try:
            visible = {int(menu_id) for menu_id in MenuForUser._visible_menu_ids(debug=False)}
        except TypeError:
            visible = {int(menu_id) for menu_id in MenuForUser._visible_menu_ids()}
        for menu_id in sorted(menu_ids & visible):
            out[str(menu_id)].append(login)
    return out


def _config_admin_logins() -> set[str]:
    group_ids = []
    for xmlid in CONFIG_ADMIN_GROUP_XMLIDS:
        group = env.ref(xmlid, raise_if_not_found=False)  # noqa: F821
        if group:
            group_ids.append(int(group.id))
    if not group_ids:
        return set()
    users = env["res.users"].sudo().search([("groups_id", "in", group_ids)])  # noqa: F821
    return {str(user.login or "").strip() for user in users if str(user.login or "").strip()}


def _classify(row: dict[str, object]) -> tuple[str, list[str], bool]:
    xmlid = _text(row.get("xmlid"))
    path = _text(row.get("path"))
    action_meta = row.get("action_meta") if isinstance(row.get("action_meta"), dict) else {}
    res_model = _text(action_meta.get("res_model"))
    text = " ".join(
        [
            xmlid,
            path,
            _text(row.get("action_xmlid")),
            _text(row.get("action_model")),
            res_model,
        ]
    ).lower()
    reasons = []
    create_user = row.get("create_user") if isinstance(row.get("create_user"), dict) else {}
    create_login = _text(create_user.get("login"))
    if not xmlid and create_login not in ("", "__system__"):
        return "user_config", ["runtime_user_menu_without_xmlid"], False
    if xmlid in SYSTEM_CONFIG_XMLIDS:
        return "system_config", ["explicit_system_config_xmlid"], False
    if xmlid in SCENE_ONLY_MENU_SCENE_KEYS:
        return "formal_product", ["scene_route_entry"], False
    if (
        "用户核对菜单" in path
        or "用户验收" in path
        or "menu_scbs55_user_acceptance" in xmlid
        or "menu_sc_user_acceptance" in xmlid
        or "legacy" in xmlid.lower()
        or res_model.startswith("sc.legacy.")
    ):
        return "history_acceptance", ["explicit_history_acceptance_surface"], False
    if any(token.lower() in text for token in DEV_TOKENS):
        reasons.append("dev_governance_token")
        return "dev_governance", reasons, False
    if any(token.lower() in text for token in SYSTEM_TOKENS):
        reasons.append("system_config_token")
        return "system_config", reasons, False
    if any(token.lower() in text for token in USER_CONFIG_TOKENS):
        reasons.append("user_config_token")
        return "user_config", reasons, False
    if any(token.lower() in text for token in HISTORY_TOKENS):
        reasons.append("history_acceptance_token")
        return "history_acceptance", reasons, False
    if _text(row.get("action_model")) or _text((row.get("action_meta") or {}).get("res_model") if isinstance(row.get("action_meta"), dict) else ""):
        return "formal_product", ["business_action_default"], False
    return "formal_product", ["container_default"], True


def _root_menus() -> list:
    roots = []
    for xmlid in ROOT_XMLIDS:
        menu = env.ref(xmlid, raise_if_not_found=False)  # noqa: F821
        if menu:
            roots.append(menu.sudo().with_context(active_test=False))
    seen = set()
    unique = []
    for root in roots:
        if int(root.id) in seen:
            continue
        seen.add(int(root.id))
        unique.append(root)
    return unique


def _export() -> dict[str, object]:
    roots = _root_menus()
    if not roots:
        raise AssertionError("no product menu catalog root resolved: %s" % (ROOT_XMLIDS,))

    root_ids = [int(root.id) for root in roots]
    seen_menu_ids = set()
    menus = Menu.browse()
    root_id_set = set(root_ids)
    env.cr.execute("SELECT id FROM ir_ui_menu ORDER BY sequence, id")  # noqa: F821
    all_menu_ids = [int(row[0]) for row in env.cr.fetchall()]  # noqa: F821
    for menu in Menu.browse(all_menu_ids).exists():
        current = menu
        belongs_to_root = False
        visited = set()
        while current:
            current_id = int(current.id)
            if current_id in visited:
                break
            visited.add(current_id)
            if current_id in root_id_set:
                belongs_to_root = True
                break
            current = current.parent_id
        if not belongs_to_root or int(menu.id) in seen_menu_ids:
            continue
        seen_menu_ids.add(int(menu.id))
        menus |= menu
    menus = menus.sorted(lambda item: (_menu_path(item), item.sequence or 0, item.id))
    menu_ids = [int(menu.id) for menu in menus]
    selected_ids = set(menu_ids)
    action_raw = _read_action_raw(menu_ids)
    visible_by_id = _visible_by_login(selected_ids)
    rows = []
    for menu in menus:
        menu_id = int(menu.id)
        raw = action_raw.get(menu_id, "")
        action_model, action_id = _parse_action(raw)
        row = {
            "id": menu_id,
            "xmlid": _xmlid(menu),
            "name": _text(menu.name),
            "path": _menu_path(menu),
            "parent_id": int(menu.parent_id.id) if menu.parent_id else None,
            "parent_xmlid": _xmlid(menu.parent_id) if menu.parent_id else "",
            "sequence": int(menu.sequence or 0),
            "active": bool(getattr(menu, "active", True)),
            "create_date": _text(getattr(menu, "create_date", "")),
            "write_date": _text(getattr(menu, "write_date", "")),
            "create_user": _user_meta(getattr(menu, "create_uid", None)),
            "write_user": _user_meta(getattr(menu, "write_uid", None)),
            "root_xmlid": _xmlid(menu if menu_id in root_ids else _root_for(menu, root_ids)),
            "action_raw": raw,
            "action_model": action_model,
            "action_id": action_id,
            "action_xmlid": _action_xmlid(action_model, action_id),
            "action_meta": _action_meta(action_model, action_id),
            "scene_key": SCENE_ONLY_MENU_SCENE_KEYS.get(_xmlid(menu), ""),
            "groups": _groups(menu),
            "child_ids": [int(child.id) for child in menu.child_id if int(child.id) in selected_ids],
            "visible_logins": visible_by_id.get(str(menu_id), []),
        }
        layer, reasons, needs_review = _classify(row)
        row["layer"] = layer
        row["classification_reasons"] = reasons
        row["needs_review"] = bool(needs_review)
        rows.append(row)

    # Container menus are normal product information architecture when they
    # group concrete child entries. Keep review focused on truly ambiguous
    # leaves or boundary labels.
    row_by_id = {int(row["id"]): row for row in rows}
    child_rows_by_parent: dict[int, list[dict[str, object]]] = {}
    for row in rows:
        parent_id = row.get("parent_id")
        if isinstance(parent_id, int):
            child_rows_by_parent.setdefault(parent_id, []).append(row)
    for row in rows:
        child_rows = child_rows_by_parent.get(int(row["id"]), [])
        if row["needs_review"] and child_rows:
            row["needs_review"] = False
            row["classification_reasons"] = ["container_with_child_entries"]
        if row["needs_review"] and not row["active"]:
            row["needs_review"] = False
            row["classification_reasons"] = ["inactive_container"]

    layer_counts: dict[str, int] = {key: 0 for key in LAYER_DEFINITIONS}
    for row in rows:
        layer_counts[row["layer"]] = layer_counts.get(row["layer"], 0) + 1

    formal_center_names = {
        _text(row.get("path")).split(" / ", 2)[1]
        for row in rows
        if row.get("active")
        and row.get("layer") == "formal_product"
        and _text(row.get("path")).startswith(PRODUCT_ROOT_LABEL + " / ")
        and len([part for part in _text(row.get("path")).split(" / ") if part]) == 2
    }

    internal_history_business_visible = []
    config_admin_logins = _config_admin_logins()
    ordinary_business_system_config_visible = []
    business_config_legacy = []
    business_config_legacy_active = []
    runtime_user_menus_without_xmlid = []
    formal_center_inactive_history = []
    for row in rows:
        visible_business_logins = sorted(BUSINESS_VISIBLE_LOGINS.intersection(row.get("visible_logins") or []))
        path = _text(row.get("path"))
        path_parts = [part for part in path.split(" / ") if part]
        xmlid = _text(row.get("xmlid")).lower()
        create_user = row.get("create_user") if isinstance(row.get("create_user"), dict) else {}
        create_login = _text(create_user.get("login"))
        if not xmlid and create_login and create_login != "__system__":
            runtime_user_menus_without_xmlid.append(
                {
                    "id": row.get("id"),
                    "path": path,
                    "active": row.get("active"),
                    "create_login": create_login,
                    "create_date": row.get("create_date"),
                }
            )
        if (
            not row.get("active")
            and row.get("layer") == "history_acceptance"
            and len(path_parts) >= 3
            and path_parts[0] == PRODUCT_ROOT_LABEL
            and path_parts[1] in formal_center_names
        ):
            formal_center_inactive_history.append(
                {
                    "xmlid": row.get("xmlid"),
                    "path": path,
                    "center": path_parts[1],
                    "action_res_model": (row.get("action_meta") or {}).get("res_model")
                    if isinstance(row.get("action_meta"), dict)
                    else "",
                }
            )
        if (
            row.get("active")
            and row.get("layer") == "history_acceptance"
            and visible_business_logins
            and any(token in path for token in INTERNAL_HISTORY_PATH_TOKENS)
        ):
            internal_history_business_visible.append(
                {
                    "xmlid": row.get("xmlid"),
                    "path": path,
                    "visible_logins": visible_business_logins,
                }
            )
        is_business_config_path = (
            path == BUSINESS_CONFIG_PATH_PREFIX or path.startswith(BUSINESS_CONFIG_PATH_PREFIX + " / ")
        )
        is_legacy_or_history = "legacy" in xmlid or "历史" in path
        if is_business_config_path and is_legacy_or_history:
            legacy_payload = {
                "xmlid": row.get("xmlid"),
                "path": path,
                "layer": row.get("layer"),
                "active": row.get("active"),
            }
            business_config_legacy.append(legacy_payload)
            if row.get("active"):
                business_config_legacy_active.append(legacy_payload)
        visible_ordinary_business_logins = [
            login for login in visible_business_logins if login not in config_admin_logins
        ]
        if row.get("active") and row.get("layer") == "system_config" and visible_ordinary_business_logins:
            ordinary_business_system_config_visible.append(
                {
                    "xmlid": row.get("xmlid"),
                    "path": path,
                    "visible_logins": visible_ordinary_business_logins,
                }
            )
    if internal_history_business_visible:
        raise AssertionError(
            "internal history menus must not be visible to business users: %s"
            % json.dumps(internal_history_business_visible[:20], ensure_ascii=False)
        )
    if ordinary_business_system_config_visible:
        raise AssertionError(
            "system config menus must not be visible to ordinary business users: %s"
            % json.dumps(ordinary_business_system_config_visible[:20], ensure_ascii=False)
        )
    if business_config_legacy:
        raise AssertionError(
            "business config must not contain legacy/history entries: %s"
            % json.dumps(business_config_legacy[:20], ensure_ascii=False)
        )

    top_level = [
        row
        for row in rows
        if row["id"] in root_ids or row["parent_id"] in root_ids
    ]
    return {
        "status": "PASS",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "db": env.cr.dbname,  # noqa: F821
        "root_xmlids": [_xmlid(root) for root in roots],
        "root_labels": [_text(root.name) for root in roots],
        "visible_logins_checked": [login for login in VISIBLE_LOGINS if env["res.users"].sudo().search([("login", "=", login)], limit=1)],  # noqa: F821
        "layer_definitions": LAYER_DEFINITIONS,
        "summary": {
            "menu_count": len(rows),
            "active_menu_count": sum(1 for row in rows if row["active"]),
            "inactive_menu_count": sum(1 for row in rows if not row["active"]),
            "action_menu_count": sum(1 for row in rows if row["action_raw"]),
            "needs_review_count": sum(1 for row in rows if row["needs_review"]),
            "internal_history_business_visible_count": len(internal_history_business_visible),
            "ordinary_business_system_config_visible_count": len(ordinary_business_system_config_visible),
            "business_config_legacy_count": len(business_config_legacy),
            "business_config_legacy_active_count": len(business_config_legacy_active),
            "runtime_user_menu_without_xmlid_count": len(runtime_user_menus_without_xmlid),
            "formal_center_inactive_history_count": len(formal_center_inactive_history),
            "layer_counts": layer_counts,
        },
        "top_level": [
            {
                "id": row["id"],
                "xmlid": row["xmlid"],
                "name": row["name"],
                "path": row["path"],
                "layer": row["layer"],
                "active": row["active"],
                "visible_logins": row["visible_logins"],
            }
            for row in sorted(top_level, key=lambda item: (item["path"], item["sequence"], item["id"]))
        ],
        "menus": sorted(rows, key=lambda item: (item["path"], item["sequence"], item["id"])),
    }


def _root_for(menu, root_ids: list[int]):
    current = menu
    while current:
        if int(current.id) in root_ids:
            return current
        current = current.parent_id
    return menu


payload = _export()
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
OUTPUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"status": payload["status"], "db": payload["db"], "summary": payload["summary"], "output": str(OUTPUT_PATH)}, ensure_ascii=False))
