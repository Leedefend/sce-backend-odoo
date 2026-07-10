# -*- coding: utf-8 -*-
"""Converge construction product menu release to user-confirmed formal entries."""
from __future__ import annotations

import json


ACCEPTANCE_PATH_TOKENS = ("用户核对菜单", "用户数据验收")
PRODUCT_KEYS = ("construction.standard", "construction.preview")

# Acceptance actions that are intentionally represented by a different formal action.
FORMAL_EQUIVALENT_ACTIONS = {
    506: 506,  # 项目台账
    866: 565,  # 投标报名管理
    895: 566,  # 投标报名费申请
    893: 761,  # 抵扣登记
}

FORMAL_EQUIVALENT_MENU_XMLIDS = (
    "smart_construction_core.menu_sc_project_project",
    "smart_construction_core.menu_sc_tender_registration",
    "smart_construction_core.menu_sc_tender_registration_fee",
    "smart_construction_core.menu_sc_tax_deduction_registration_user",
    "smart_construction_core.menu_sc_company_user_roster_formal",
    "smart_construction_core.menu_sc_salary_registration_scbs55_formal",
    "smart_construction_core.menu_sc_payment_deposit_return_refund_formal",
)

GROUP_DISPLAY_ORDER = {
    "基础资料": 5,
    "项目中心": 10,
    "投标管理类单据": 20,
    "合同中心": 30,
    "施工管理": 40,
    "物资与分包": 50,
    "财务中心": 60,
    "人事行政": 70,
    "资料证照": 80,
    "配置中心": 990,
    "配置": 990,
    "系统配置": 990,
}

MENU_GROUP_OVERRIDES = {
    "smart_construction_core.menu_sc_customer_partner": ("construction.基础资料", "基础资料"),
    "smart_construction_core.menu_sc_supplier_partner": ("construction.基础资料", "基础资料"),
}

CONFIRMED_LABEL_MARKERS = ("（已确认）", "(已确认)", "已确认")


def is_acceptance_path(path: str) -> bool:
    return any(token in str(path or "") for token in ACCEPTANCE_PATH_TOKENS)


def clean_confirmed_label(value) -> str:
    label = str(value or "").strip()
    for marker in CONFIRMED_LABEL_MARKERS:
        label = label.replace(marker, "")
    return label.strip()


def menu_xmlid(menu) -> str:
    try:
        return str(menu.get_external_id().get(menu.id) or "")
    except Exception:
        return ""


def menu_action_id(menu) -> int:
    action = getattr(menu, "action", False)
    try:
        return int(getattr(action, "id", 0) or 0)
    except Exception:
        return 0


def action_count(action) -> int:
    model = str(getattr(action, "res_model", "") or "")
    if not model or model not in env:  # noqa: F821
        return 0
    try:
        return env[model].sudo().with_context(active_test=False).search_count(eval(action.domain or "[]"))  # noqa: F821
    except Exception:
        return 0


def find_formal_menus_for_action(action_id: int):
    if action_id <= 0:
        return env["ir.ui.menu"].sudo().browse()  # noqa: F821
    menus = env["ir.ui.menu"].sudo().with_context(active_test=False).search(  # noqa: F821
        [("action", "=", "ir.actions.act_window,%s" % action_id)]
    )
    return menus.filtered(lambda menu: not is_acceptance_path(menu.complete_name))


def build_menu_payload(menu) -> dict:
    action = menu.action
    action_id = int(getattr(action, "id", 0) or 0)
    model = str(getattr(action, "res_model", "") or "")
    view_modes = [
        item.strip()
        for item in str(getattr(action, "view_mode", "") or "").split(",")
        if item.strip()
    ]
    xmlid = menu_xmlid(menu)
    return {
        "label": str(menu.name or ""),
        "route": "/a/%s?menu_id=%s" % (action_id, int(menu.id)),
        "enabled": True,
        "menu_id": int(menu.id),
        "menu_key": xmlid or "menu.%s" % int(menu.id),
        "page_key": xmlid or "menu.%s" % int(menu.id),
        "sequence": int(menu.sequence or 0),
        "action_id": action_id,
        "res_model": model,
        "scene_key": "",
        "menu_xmlid": xmlid,
        "page_label": str(menu.name or ""),
        "view_modes": view_modes,
        "policy_note": "released_as_user_confirmed_formal_product_menu",
        "product_key": str(menu.parent_id.name or ""),
        "source_kind": "ir.ui.menu",
        "access_level": "public",
        "action_model": "ir.actions.act_window",
        "release_state": "released",
        "capability_key": "construction.menu.%s" % (xmlid.replace(".", "_") if xmlid else int(menu.id)),
        "control_object": "用户可见菜单页面",
        "release_domain": "construction",
        "target_scene_key": "",
        "visible_menu_path": str(menu.complete_name or "").replace("/", " / "),
        "control_granularity": "user_visible_menu_page",
    }


def group_for_menu(menu) -> tuple[str, str]:
    xmlid = menu_xmlid(menu)
    if xmlid in MENU_GROUP_OVERRIDES:
        return MENU_GROUP_OVERRIDES[xmlid]
    path = [item.strip() for item in str(menu.complete_name or "").split("/") if item.strip()]
    label = path[1] if len(path) > 1 else (menu.parent_id.name or "业务菜单")
    return "construction.%s" % label, label


def group_display_sort_key(group: dict) -> tuple[int, str]:
    label = str(group.get("group_label") or group.get("label") or "")
    return GROUP_DISPLAY_ORDER.get(label, 900), label


def policy_menu_index(policy) -> dict[int, dict]:
    indexed = {}
    for group in policy.menu_groups or []:
        if not isinstance(group, dict):
            continue
        for row in group.get("menus") or []:
            if not isinstance(row, dict):
                continue
            try:
                menu_id = int(row.get("menu_id") or 0)
            except Exception:
                menu_id = 0
            if menu_id > 0:
                indexed[menu_id] = dict(row)
    return indexed


def add_current_product_policy_menus_to_allowlist() -> int:
    added = 0
    policies = ProductPolicy.search([("product_key", "in", list(PRODUCT_KEYS)), ("active", "=", True)])
    for policy in policies:
        for group in policy.menu_groups or []:
            if not isinstance(group, dict):
                continue
            for row in group.get("menus") or []:
                if not isinstance(row, dict):
                    continue
                try:
                    menu_id = int(row.get("menu_id") or 0)
                except Exception:
                    menu_id = 0
                if menu_id > 0 and menu_id not in allow_menu_ids:
                    allow_menu_ids.add(menu_id)
                    sources_by_menu.setdefault(menu_id, set()).add("current_product_policy")
                    added += 1
    return added


def upsert_policy(menu, *, visible: bool, note: str) -> None:
    Policy = env["ui.menu.config.policy"].sudo().with_context(active_test=False)  # noqa: F821
    policies = Policy.search([("company_id", "=", env.company.id), ("menu_id", "=", int(menu.id))])  # noqa: F821
    values = {
        "active": True,
        "company_id": env.company.id,  # noqa: F821
        "menu_id": int(menu.id),
        "visible": bool(visible),
        "target_parent_menu_id": False,
        "sequence_override": int(menu.sequence or 0),
        "note": note,
    }
    if not visible:
        values["custom_label"] = False
    if policies:
        policies.write(values)
    else:
        Policy.create(values)


Menu = env["ir.ui.menu"].sudo().with_context(active_test=False)  # noqa: F821
Policy = env["ui.menu.config.policy"].sudo().with_context(active_test=False)  # noqa: F821
ProductPolicy = env["sc.product.policy"].sudo()  # noqa: F821

confirmed_policies = Policy.search(
    [("active", "=", True), ("custom_label", "ilike", "已确认"), ("menu_id", "!=", False)],
    order="id",
)

allow_menu_ids: set[int] = set()
sources_by_menu: dict[int, set[str]] = {}
for policy in confirmed_policies:
    menu = policy.menu_id
    action_id = menu_action_id(menu)
    target_menus = Menu.browse()
    if is_acceptance_path(menu.complete_name):
        equivalent_action_id = FORMAL_EQUIVALENT_ACTIONS.get(action_id, action_id)
        target_menus = find_formal_menus_for_action(equivalent_action_id)
    else:
        target_menus = menu
    for target in target_menus:
        allow_menu_ids.add(int(target.id))
        sources_by_menu.setdefault(int(target.id), set()).add(str(policy.custom_label or menu.name or ""))

for xmlid in FORMAL_EQUIVALENT_MENU_XMLIDS:
    menu = env.ref(xmlid, raise_if_not_found=False)  # noqa: F821
    if menu:
        allow_menu_ids.add(int(menu.id))
        sources_by_menu.setdefault(int(menu.id), set()).add("verified_formal_equivalent")

current_product_policy_seed_count = add_current_product_policy_menus_to_allowlist()

if not allow_menu_ids:
    raise RuntimeError("confirmed formal menu allowlist is empty")

policy_updates = {}
for product_key in PRODUCT_KEYS:
    policy = ProductPolicy.search([("product_key", "=", product_key), ("active", "=", True)], limit=1)
    if not policy:
        raise RuntimeError("missing product policy %s" % product_key)
    existing_rows = policy_menu_index(policy)
    groups: dict[str, dict] = {}
    for menu in Menu.browse(sorted(allow_menu_ids)).exists():
        group_key, group_label = group_for_menu(menu)
        group = groups.setdefault(
            group_key,
            {
                "group_key": group_key,
                "key": group_key,
                "group_label": group_label,
                "label": group_label,
                "title": group_label,
                "category": "user_confirmed_formal_product_menu",
                "menus": [],
            },
        )
        row = existing_rows.get(int(menu.id)) or build_menu_payload(menu)
        row = dict(row)
        clean_label = clean_confirmed_label(row.get("label") or menu.name)
        row["enabled"] = True
        row["release_state"] = "released"
        row["policy_note"] = "released_as_user_confirmed_formal_product_menu"
        row["label"] = clean_label
        row["title"] = clean_label
        row["name"] = clean_label
        row["page_label"] = clean_confirmed_label(row.get("page_label") or clean_label)
        row["product_key"] = group_label
        row["visible_menu_path"] = "智慧施工管理平台 / %s / %s" % (group_label, clean_label)
        group["menus"].append(row)
    next_groups = []
    for group in sorted(groups.values(), key=group_display_sort_key):
        group["menus"].sort(key=lambda row: (int(row.get("sequence") or 0), int(row.get("menu_id") or 0)))
        next_groups.append(group)
    policy.write(
        {
            "menu_groups": next_groups,
            "state": "stable" if product_key.endswith(".standard") else "preview",
            "active": True,
        }
    )
    policy_updates[product_key] = {
        "group_count": len(next_groups),
        "menu_count": sum(len(group.get("menus") or []) for group in next_groups),
    }

root = env.ref("smart_construction_core.menu_sc_root", raise_if_not_found=False)  # noqa: F821
all_leaf_menus = Menu.search([("action", "!=", False), ("active", "=", True)])
if root:
    root_path = str(root.complete_name or root.name or "")
    all_leaf_menus = all_leaf_menus.filtered(lambda menu: str(menu.complete_name or "").startswith(root_path))

hidden_count = 0
shown_count = 0
for menu in all_leaf_menus:
    if int(menu.id) in allow_menu_ids:
        upsert_policy(menu, visible=True, note="User-confirmed formal product menu retained.")
        shown_count += 1
    else:
        upsert_policy(menu, visible=False, note="Hidden by user-confirmed formal product menu convergence.")
        hidden_count += 1

cleaned_custom_label_count = 0
for policy in Policy.search([("active", "=", True), ("custom_label", "ilike", "已确认")]):
    cleaned = clean_confirmed_label(policy.custom_label)
    policy.write({"custom_label": cleaned or False})
    cleaned_custom_label_count += 1

env.cr.commit()  # noqa: F821

payload = {
    "status": "PASS",
    "mode": "confirmed_formal_menu_release_converge",
    "database": env.cr.dbname,  # noqa: F821
    "confirmed_policy_count": len(confirmed_policies),
    "current_product_policy_seed_count": current_product_policy_seed_count,
    "allow_menu_count": len(allow_menu_ids),
    "allow_menu_ids": sorted(allow_menu_ids),
    "allow_menu_xmlids": sorted(menu_xmlid(menu) for menu in Menu.browse(sorted(allow_menu_ids)).exists()),
    "policy_updates": policy_updates,
    "runtime_show_policy_count": shown_count,
    "runtime_hide_policy_count": hidden_count,
    "cleaned_custom_label_count": cleaned_custom_label_count,
}
print("CONFIRMED_FORMAL_MENU_RELEASE_CONVERGE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
