#!/usr/bin/env python3
"""Publish SCBS user-acceptance data menus for construction products.

Run with:
    odoo shell -c /path/to/odoo.conf -d sc_demo --no-http < scripts/ops/scbs_55_user_acceptance_menu_policy_apply.py
"""

from __future__ import annotations

import json
import os
import hashlib
from pathlib import Path


SOURCE_DOCUMENT = "/home/odoo/workspace/partner_import_source/5.6优化（老系统菜单，字段列表展示）1.docx"
PRODUCT_KEYS = ("construction.standard", "construction.preview")
MODULE = "smart_construction_core"
ROOT_XMLID = "smart_construction_core.menu_sc_root"
ACCEPTANCE_ROOT_XMLID = "smart_construction_core.menu_scbs55_user_acceptance_root"
DIRECT_ACCEPTANCE_ROOT_XMLID = "smart_construction_core.menu_scbsly_direct_project_acceptance_root"
OUTPUT_JSON_NAME = "scbs_55_user_acceptance_menu_policy_apply_result_v1.json"
ACCEPTANCE_ACTION_BY_MENU_NAME = {
    "施工合同": "smart_construction_core.action_scbsly_direct_acceptance_construction_contract",
    "供货合同分析": "smart_construction_core.action_scbsly_direct_acceptance_supplier_contract",
}


def artifact_root() -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.append(Path("/mnt/artifacts/migration"))
    candidates.append(Path(f"/tmp/scbs_55_menu_policy/{env.cr.dbname}"))  # noqa: F821
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return candidate
        except Exception:
            continue
    return Path(f"/tmp/scbs_55_menu_policy/{env.cr.dbname}")  # noqa: F821


def ensure_allowed_db() -> None:
    allowlist = {
        item.strip()
        for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", env.cr.dbname).split(",")  # noqa: F821
        if item.strip()
    }
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_replay": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def xml_name(*parts: object) -> str:
    value = "_".join(str(part or "").strip().lower() for part in parts if str(part or "").strip())
    out = []
    for char in value:
        out.append(char if char.isalnum() else "_")
    normalized = "".join(out).strip("_")
    while "__" in normalized:
        normalized = normalized.replace("__", "_")
    return normalized or "scbs55_menu"


def ref(xmlid: str):
    return env.ref(xmlid, raise_if_not_found=False)  # noqa: F821


def ensure_xmlid(record, name: str) -> None:
    existing = env["ir.model.data"].sudo().search(  # noqa: F821
        [("module", "=", MODULE), ("name", "=", name), ("model", "=", record._name)],
        limit=1,
    )
    if existing:
        if int(existing.res_id or 0) != int(record.id):
            existing.write({"res_id": int(record.id)})
        return
    env["ir.model.data"].sudo().create(  # noqa: F821
        {
            "module": MODULE,
            "name": name,
            "model": record._name,
            "res_id": int(record.id),
            "noupdate": True,
        }
    )


def collect_active_menu_ids(root_menu) -> set[int]:
    out = set()
    stack = [root_menu]
    while stack:
        menu = stack.pop()
        if not menu.exists() or not menu.active:
            continue
        out.add(int(menu.id))
        stack.extend(menu.child_id)
    return out


def xmlid_for(record) -> str:
    xid = env["ir.model.data"].sudo().search(  # noqa: F821
        [("model", "=", record._name), ("res_id", "=", int(record.id))],
        limit=1,
    )
    return f"{xid.module}.{xid.name}" if xid else ""


def direct_acceptance_policy_groups(root_menu) -> list[dict]:
    if not root_menu:
        return []
    groups = []
    for category in root_menu.child_id.sorted("sequence"):
        menus = []
        for menu in category.child_id.sorted("sequence"):
            if not menu.active or not menu.action:
                continue
            action = menu.action
            action_id = int(action.id)
            menus.append(
                {
                    "menu_xmlid": xmlid_for(menu),
                    "menu_id": int(menu.id),
                    "action_id": action_id,
                    "route": f"/a/{action_id}?menu_id={int(menu.id)}",
                    "label": str(menu.name or ""),
                    "model": str(getattr(action, "res_model", "") or ""),
                    "res_model": str(getattr(action, "res_model", "") or ""),
                    "enabled": True,
                    "release_state": "released",
                    "access_level": "public",
                    "sequence": int(menu.sequence or 0),
                    "visible_menu_path": f"系统菜单 / 用户验收 / 直营项目系统菜单 / {category.name} / {menu.name}",
                    "policy_note": "SCBSLY direct-project acceptance menu retained for customer verification.",
                }
            )
        if menus:
            groups.append(
                {
                    "group_key": f"construction.scbsly_direct.{xml_name(category.name)}",
                    "group_label": f"直营项目系统菜单 / {category.name}",
                    "category": "scbsly_direct_acceptance_menu",
                    "menus": menus,
                }
            )
    return groups


def menu_policy_payload(menu, *, group_label: str, note: str) -> dict:
    action = menu.action
    action_id = int(action.id) if action else 0
    menu_xmlid = xmlid_for(menu)
    model_name = str(getattr(action, "res_model", "") or "") if action else ""
    return {
        "menu_xmlid": menu_xmlid,
        "menu_id": int(menu.id),
        "action_id": action_id,
        "route": f"/a/{action_id}?menu_id={int(menu.id)}" if action_id else "",
        "label": str(menu.name or ""),
        "model": model_name,
        "res_model": model_name,
        "enabled": True,
        "release_state": "released",
        "access_level": "public",
        "sequence": int(menu.sequence or 0),
        "visible_menu_path": str(menu.complete_name or f"系统菜单 / {group_label} / {menu.name}"),
        "policy_note": note,
    }


def ensure_menu(*, xmlid_name: str, name: str, parent, sequence: int, action=None):
    menu = ref(f"{MODULE}.{xmlid_name}")
    values = {
        "name": name,
        "parent_id": parent.id if parent else False,
        "sequence": sequence,
        "active": True,
    }
    if action:
        values["action"] = f"{action._name},{action.id}"
    if menu:
        menu.sudo().write(values)
    else:
        menu = env["ir.ui.menu"].sudo().create(values)  # noqa: F821
        ensure_xmlid(menu, xmlid_name)
    return menu


def effective(menu: dict) -> bool:
    return bool(menu.get("enabled", True)) and str(menu.get("release_state") or "released").strip() in {
        "released",
        "preview",
        "stable",
        "public",
    }


def iter_policy_menus(policy):
    for group in policy.menu_groups if isinstance(policy.menu_groups, list) else []:
        if not isinstance(group, dict):
            continue
        for menu in group.get("menus") if isinstance(group.get("menus"), list) else []:
            if isinstance(menu, dict):
                yield menu


def collect_descendants(menu):
    Menu = env["ir.ui.menu"].sudo().with_context(active_test=False)  # noqa: F821
    env.cr.execute(  # noqa: F821
        """
        WITH RECURSIVE descendants AS (
            SELECT id
              FROM ir_ui_menu
             WHERE parent_id = %s
            UNION ALL
            SELECT child.id
              FROM ir_ui_menu child
              JOIN descendants parent ON child.parent_id = parent.id
        )
        SELECT id FROM descendants
        """,
        [int(menu.id)],
    )
    return Menu.browse([int(row[0]) for row in env.cr.fetchall()])  # noqa: F821


def collect_active_descendant_ids(menu) -> set[int]:
    env.cr.execute(  # noqa: F821
        """
        WITH RECURSIVE descendants AS (
            SELECT id, active
              FROM ir_ui_menu
             WHERE parent_id = %s
            UNION ALL
            SELECT child.id, child.active
              FROM ir_ui_menu child
              JOIN descendants parent ON child.parent_id = parent.id
        )
        SELECT id FROM descendants WHERE active
        """,
        [int(menu.id)],
    )
    return {int(row[0]) for row in env.cr.fetchall()}  # noqa: F821


def collect_active_descendant_rows(menu) -> list[tuple[int, int]]:
    env.cr.execute(  # noqa: F821
        """
        WITH RECURSIVE descendants AS (
            SELECT id, active, sequence
              FROM ir_ui_menu
             WHERE parent_id = %s
            UNION ALL
            SELECT child.id, child.active, child.sequence
              FROM ir_ui_menu child
              JOIN descendants parent ON child.parent_id = parent.id
        )
        SELECT id, COALESCE(sequence, 0)
          FROM descendants
         WHERE active
         ORDER BY sequence, id
        """,
        [int(menu.id)],
    )
    return [(int(row[0]), int(row[1] or 0)) for row in env.cr.fetchall()]  # noqa: F821


def action_domain(action) -> list:
    text = str(getattr(action, "domain", "") or "").strip()
    if not text:
        return []
    try:
        from odoo.tools.safe_eval import safe_eval  # noqa: E402

        value = safe_eval(text, {"context": {}, "uid": env.uid, "active_id": False, "active_ids": []})  # noqa: F821
        return value if isinstance(value, list) else []
    except Exception:
        return []


def action_record_count(action) -> int:
    model_name = str(getattr(action, "res_model", "") or "").strip()
    if not model_name or model_name not in env:  # noqa: F821
        return 0
    model = env[model_name].sudo().with_context(active_test=False)  # noqa: F821
    try:
        return int(model.search_count(action_domain(action)))
    except Exception:
        try:
            return int(model.search_count([]))
        except Exception:
            return 0


def legacy_data_signals(model_name: str) -> list[str]:
    if not model_name or model_name not in env:  # noqa: F821
        return []
    field_names = set(env[model_name]._fields)  # noqa: F821
    signals = []
    if model_name.startswith("sc.legacy."):
        signals.append("legacy_model")
    if any(field_name.startswith("legacy_") for field_name in field_names):
        signals.append("legacy_field")
    for field_name in (
        "raw_payload",
        "source_table",
        "legacy_source_table",
        "legacy_record_id",
        "legacy_fact_model",
        "legacy_contract_id",
        "legacy_project_id",
        "old_system_id",
    ):
        if field_name in field_names:
            signals.append(field_name)
    return sorted(set(signals))


def is_customer_acceptance_path(path: str) -> bool:
    return any(marker in path for marker in ("用户核对菜单", "用户验收", "直营项目系统菜单"))


def is_internal_only_path(path: str) -> bool:
    return any(
        marker in path
        for marker in (
            "基础设置/系统权限",
            "系统权限",
            "历史财务事实（内部）",
            "用户优先入口迭代计划",
            "旧库业务主体映射",
            "旧库往来单位映射",
            "旧库项目映射",
            "旧库报表承载清单",
            "用户信息与权限",
            "SCBS旧库事实暂存",
            "SCBS旧库材料映射",
        )
    )


def has_active_children(menu) -> bool:
    return any(child.active for child in menu.child_id)


def top_level_group_label(menu) -> str:
    current = menu
    while current.parent_id and int(current.parent_id.id) != int(root.id):  # noqa: F821
        current = current.parent_id
    return str(current.name or menu.parent_id.name or "旧业务数据核对")


def add_menu_and_active_ancestors(menu, *, source: str) -> None:
    current = menu
    while current and current.exists():
        allowed_menu_ids.add(int(current.id))  # noqa: F821
        allowed_group_by_menu_id.setdefault(int(current.id), top_level_group_label(current))  # noqa: F821
        allowed_sequence_by_menu_id.setdefault(int(current.id), int(current.sequence or 0))  # noqa: F821
        allowed_sources_by_menu_id.setdefault(int(current.id), set()).add(source)  # noqa: F821
        if int(current.id) == int(root.id):  # noqa: F821
            break
        current = current.parent_id


def discover_legacy_data_menus(root_menu) -> list[dict[str, object]]:
    discovered = []
    for menu in collect_descendants(root_menu):
        if not menu.active or not menu.action:
            continue
        action = menu.action
        model_name = str(getattr(action, "res_model", "") or "").strip()
        path = str(menu.complete_name or menu.name or "")
        signals = legacy_data_signals(model_name)
        count = action_record_count(action)
        acceptance_path = is_customer_acceptance_path(path)
        if not acceptance_path and is_internal_only_path(path):
            continue
        if not acceptance_path and (not signals or count <= 0):
            continue
        menu_xmlid = xmlid_for(menu)
        if menu_xmlid.startswith("smart_construction_demo.") or "演示" in path:
            continue
        discovered.append(
            {
                "menu_id": int(menu.id),
                "menu_xmlid": menu_xmlid,
                "label": str(menu.name or ""),
                "path": path,
                "action_id": int(action.id),
                "action_name": str(getattr(action, "name", "") or ""),
                "model": model_name,
                "record_count": count,
                "legacy_data_signals": signals,
                "acceptance_path": acceptance_path,
            }
        )
    best_by_identity = {}
    for item in discovered:
        key = (str(item["path"]), str(item["action_name"]), str(item["model"]))
        xmlid = str(item.get("menu_xmlid") or "")
        priority = (
            1 if "analysis_report" in xmlid else 0,
            1 if "scbs55_user_acceptance" in xmlid else 0,
            int(item["menu_id"]),
        )
        current = best_by_identity.get(key)
        if current is None or priority < current[0]:
            best_by_identity[key] = (priority, item)
    discovered = [item for _, item in best_by_identity.values()]
    discovered.sort(key=lambda item: (str(item["path"]), int(item["menu_id"])))
    return discovered


def upsert_runtime_policy(*, menu, visible: bool, note: str) -> int:
    return upsert_runtime_policy_by_id(
        menu_id=int(menu.id),
        sequence=int(menu.sequence or 0),
        visible=visible,
        note=note,
    )


def upsert_runtime_policy_by_id(*, menu_id: int, sequence: int, visible: bool, note: str) -> int:
    Policy = env["ui.menu.config.policy"].sudo().with_context(active_test=False)  # noqa: F821
    policies = Policy.search([("company_id", "=", env.company.id), ("menu_id", "=", menu_id)])  # noqa: F821
    values = {
        "active": True,
        "company_id": env.company.id,  # noqa: F821
        "menu_id": menu_id,
        "visible": visible,
        "custom_label": False,
        "target_parent_menu_id": False,
        "sequence_override": int(sequence or 0),
        "note": note,
    }
    if policies:
        policies.write(values)
        return len(policies)
    Policy.create(values)
    return 1


ensure_allowed_db()
artifact_dir = artifact_root()

Plan = env["sc.legacy.user.priority.menu.plan"].sudo()  # noqa: F821
rows = Plan.search([("source_document", "=", SOURCE_DOCUMENT), ("active", "=", True)], order="priority_sequence")
if not rows:
    raise RuntimeError({"missing_active_user_acceptance_plan_rows": SOURCE_DOCUMENT})

root = ref(ROOT_XMLID)
if not root:
    raise RuntimeError({"missing_root_menu_xmlid": ROOT_XMLID})

acceptance_root = ensure_menu(
    xmlid_name=ACCEPTANCE_ROOT_XMLID.split(".", 1)[1],
    name="用户核对菜单",
    parent=root,
    sequence=1,
)

groups_by_name = {}
allowed_xmlids = set()
allowed_menu_ids = {int(root.id), int(acceptance_root.id)}
allowed_group_by_xmlid = {}
allowed_group_by_menu_id = {int(acceptance_root.id): "用户核对菜单"}
allowed_sequence_by_xmlid = {}
allowed_sequence_by_menu_id = {int(acceptance_root.id): int(acceptance_root.sequence or 0)}
allowed_sources_by_menu_id = {int(root.id): {"root"}, int(acceptance_root.id): {"acceptance_root"}}
created_or_updated = []
for row in rows:
    action = row.target_action_id
    override_xmlid = ACCEPTANCE_ACTION_BY_MENU_NAME.get(str(row.legacy_menu_name or "").strip())
    if override_xmlid:
        action = ref(override_xmlid) or action
    if not action:
        raise RuntimeError({"missing_target_action": row.legacy_menu_name, "priority_sequence": row.priority_sequence})
    group_name = row.legacy_menu_group or "用户核对"
    group_menu = groups_by_name.get(group_name)
    if not group_menu:
        group_xmlid = xml_name("menu_scbs55_user_acceptance_group", group_name)
        group_sequence = int(row.priority_sequence or 0) // 10
        group_menu = ensure_menu(
            xmlid_name=group_xmlid,
            name=group_name,
            parent=acceptance_root,
            sequence=group_sequence,
        )
        groups_by_name[group_name] = group_menu
        allowed_menu_ids.add(int(group_menu.id))
        allowed_group_by_menu_id[int(group_menu.id)] = "用户核对菜单"
        allowed_sequence_by_menu_id[int(group_menu.id)] = int(group_menu.sequence or 0)
        allowed_sources_by_menu_id.setdefault(int(group_menu.id), set()).add("plan_group")

    menu_xmlid_name = xml_name("menu_scbs55_user_acceptance", f"{int(row.priority_sequence):03d}", row.legacy_menu_name)
    menu = ensure_menu(
        xmlid_name=menu_xmlid_name,
        name=row.legacy_menu_name,
        parent=group_menu,
        sequence=int(row.priority_sequence or 0),
        action=action,
    )
    allowed_xmlid = f"{MODULE}.{menu_xmlid_name}"
    allowed_xmlids.add(allowed_xmlid)
    allowed_menu_ids.add(int(menu.id))
    allowed_group_by_xmlid[allowed_xmlid] = row.legacy_menu_group or "用户核对"
    allowed_group_by_menu_id[int(menu.id)] = row.legacy_menu_group or "用户核对"
    allowed_sequence_by_xmlid[allowed_xmlid] = int(row.priority_sequence or 0)
    allowed_sequence_by_menu_id[int(menu.id)] = int(row.priority_sequence or 0)
    allowed_sources_by_menu_id.setdefault(int(menu.id), set()).add("priority_plan")
    created_or_updated.append(
        {
            "priority_sequence": int(row.priority_sequence or 0),
            "legacy_menu_group": row.legacy_menu_group,
            "legacy_menu_name": row.legacy_menu_name,
            "menu_id": int(menu.id),
            "menu_xmlid": allowed_xmlid,
            "action_id": int(action.id),
        }
    )

acceptance_descendant_ids = collect_active_descendant_ids(acceptance_root)
for menu in env["ir.ui.menu"].sudo().browse(sorted(acceptance_descendant_ids)).exists():  # noqa: F821
    allowed_menu_ids.add(int(menu.id))
    menu_xmlid = xmlid_for(menu)
    if menu.action and menu_xmlid:
        allowed_xmlids.add(menu_xmlid)
        allowed_group_by_xmlid.setdefault(menu_xmlid, menu.parent_id.name or "用户核对")
        allowed_sequence_by_xmlid.setdefault(menu_xmlid, int(menu.sequence or 0))
    allowed_group_by_menu_id.setdefault(int(menu.id), menu.parent_id.name or "用户核对")
    allowed_sequence_by_menu_id.setdefault(int(menu.id), int(menu.sequence or 0))
    allowed_sources_by_menu_id.setdefault(int(menu.id), set()).add("existing_acceptance_tree")

direct_acceptance_root = ref(DIRECT_ACCEPTANCE_ROOT_XMLID)
direct_acceptance_menu_ids = collect_active_menu_ids(direct_acceptance_root) if direct_acceptance_root else set()
allowed_menu_ids.update(direct_acceptance_menu_ids)
for menu_id in direct_acceptance_menu_ids:
    allowed_sources_by_menu_id.setdefault(int(menu_id), set()).add("direct_acceptance_tree")
direct_acceptance_groups = direct_acceptance_policy_groups(direct_acceptance_root)
direct_acceptance_leaf_count = sum(
    len(group.get("menus") if isinstance(group.get("menus"), list) else [])
    for group in direct_acceptance_groups
    if isinstance(group, dict)
)

legacy_data_discovered_menus = discover_legacy_data_menus(root)
for item in legacy_data_discovered_menus:
    menu = env["ir.ui.menu"].sudo().browse(int(item["menu_id"])).exists()  # noqa: F821
    if not menu:
        continue
    add_menu_and_active_ancestors(menu, source="legacy_data_discovery")
    menu_xmlid = str(item.get("menu_xmlid") or "").strip()
    group_label = top_level_group_label(menu)
    if menu_xmlid:
        if item.get("acceptance_path") or not has_active_children(menu):
            allowed_xmlids.add(menu_xmlid)
        allowed_group_by_xmlid.setdefault(menu_xmlid, group_label)
        allowed_sequence_by_xmlid.setdefault(menu_xmlid, int(menu.sequence or 0))
    allowed_group_by_menu_id.setdefault(int(menu.id), group_label)
    allowed_sequence_by_menu_id.setdefault(int(menu.id), int(menu.sequence or 0))

runtime_keep_policy_count = 0
runtime_hide_policy_count = 0
for menu in env["ir.ui.menu"].sudo().browse(sorted(allowed_menu_ids)).exists():  # noqa: F821
    runtime_keep_policy_count += upsert_runtime_policy(
        menu=menu,
        visible=True,
        note="User acceptance menu retained because it exposes legacy business data for customer verification.",
    )

active_descendant_rows = collect_active_descendant_rows(root)
hidden_menu_rows = [
    (menu_id, sequence)
    for menu_id, sequence in active_descendant_rows
    if menu_id not in allowed_menu_ids
]
for menu_id, sequence in hidden_menu_rows:
    runtime_hide_policy_count += upsert_runtime_policy_by_id(
        menu_id=menu_id,
        sequence=sequence,
        visible=False,
        note="Hidden while legacy business data customer-verification publishing strategy is active.",
    )

from odoo.addons.smart_core.delivery.product_policy_catalog_sync_service import ProductPolicyCatalogSyncService  # noqa: E402
from odoo import SUPERUSER_ID, api  # noqa: E402
from odoo.modules.registry import Registry  # noqa: E402


def policy_release_pages(groups: list[dict]) -> list[dict]:
    pages = []
    for group in groups:
        if not isinstance(group, dict) or group.get("category") == "hidden_original_menu":
            continue
        group_label = str(group.get("group_label") or "").strip()
        for menu in group.get("menus") if isinstance(group.get("menus"), list) else []:
            if not isinstance(menu, dict) or not effective(menu):
                continue
            menu_xmlid = str(menu.get("menu_xmlid") or "").strip()
            menu_id = int(menu.get("menu_id") or 0)
            action_id = int(menu.get("action_id") or 0)
            route = str(menu.get("route") or "").strip()
            if not route and action_id:
                route = f"/a/{action_id}" + (f"?menu_id={menu_id}" if menu_id else "")
            pages.append(
                {
                    "page_key": menu_xmlid or str(menu.get("menu_key") or "").strip(),
                    "menu_key": menu_xmlid or str(menu.get("menu_key") or "").strip(),
                    "menu_xmlid": menu_xmlid,
                    "label": str(menu.get("label") or "").strip(),
                    "route": route,
                    "menu_id": menu_id,
                    "action_id": action_id,
                    "res_model": str(menu.get("model") or menu.get("res_model") or "").strip(),
                    "enabled": True,
                    "release_state": "released",
                    "access_level": "public",
                    "visible_menu_path": str(menu.get("visible_menu_path") or "").strip()
                    or f"系统菜单 / 用户核对菜单 / {group_label} / {str(menu.get('label') or '').strip()}",
                }
            )
    return pages


def merge_release_pages(existing_pages: list, required_pages: list[dict]) -> tuple[list[dict], int]:
    merged = [dict(page) for page in existing_pages if isinstance(page, dict)]
    index = {}
    action_fallback_index = {}
    for pos, page in enumerate(merged):
        for key in ("menu_xmlid", "page_key", "menu_key"):
            value = str(page.get(key) or "").strip()
            if value:
                index.setdefault(value, pos)
        menu_id = int(page.get("menu_id") or 0)
        action_id = int(page.get("action_id") or 0)
        if menu_id:
            index.setdefault(f"menu_id:{menu_id}", pos)
        has_stable_page_key = bool(menu_id) or any(str(page.get(key) or "").strip() for key in ("menu_xmlid", "page_key", "menu_key"))
        if action_id and not has_stable_page_key:
            action_fallback_index.setdefault(f"action_id:{action_id}", pos)
    added = 0
    for page in required_pages:
        keys = [
            str(page.get("menu_xmlid") or "").strip(),
            str(page.get("page_key") or "").strip(),
            str(page.get("menu_key") or "").strip(),
        ]
        menu_id = int(page.get("menu_id") or 0)
        action_id = int(page.get("action_id") or 0)
        if menu_id:
            keys.append(f"menu_id:{menu_id}")
        hit = next((index[key] for key in keys if key and key in index), None)
        if hit is None and action_id and not any(keys):
            hit = action_fallback_index.get(f"action_id:{action_id}")
        if hit is None:
            next_pos = len(merged)
            for key in keys:
                if key:
                    index.setdefault(key, next_pos)
            if action_id and not any(keys):
                action_fallback_index.setdefault(f"action_id:{action_id}", next_pos)
            merged.append(dict(page))
            added += 1
            continue
        next_page = dict(merged[hit])
        next_page.update({key: value for key, value in page.items() if value not in ("", 0, None)})
        next_page["enabled"] = True
        next_page["release_state"] = "released"
        next_page["access_level"] = "public"
        merged[hit] = next_page
    return merged, added


def sync_platform_release_gate_pages(product_key: str, required_pages: list[dict]) -> dict[str, object]:
    platform_db = str(env["ir.config_parameter"].sudo().get_param("smart_core.platform_release_db", "") or "").strip()  # noqa: F821
    platform_db = platform_db or "sc_platform_core"
    current_db = str(env.cr.dbname)  # noqa: F821

    def update_in(read_env):
        Snapshot = read_env["sc.edition.release.snapshot"].sudo()
        snapshot = Snapshot.search(
            [
                ("product_key", "=", product_key),
                ("state", "=", "released"),
                ("is_active", "=", True),
                ("active", "=", True),
            ],
            order="released_at desc, activated_at desc, id desc",
            limit=1,
        )
        if not snapshot:
            return {"status": "SKIP", "reason": "active_release_snapshot_not_found", "platform_db": platform_db}
        meta = dict(snapshot.meta_json if isinstance(snapshot.meta_json, dict) else {})
        draft = dict(meta.get("release_draft") if isinstance(meta.get("release_draft"), dict) else {})
        existing_pages = draft.get("pages") if isinstance(draft.get("pages"), list) else []
        merged_pages, added = merge_release_pages(existing_pages, required_pages)
        draft["pages"] = merged_pages
        draft["page_count"] = sum(1 for page in merged_pages if isinstance(page, dict) and page.get("enabled", True) and str(page.get("release_state") or "released") in {"released", "preview"})
        draft["total_page_count"] = len(merged_pages)
        draft["fingerprint"] = hashlib.sha256(json.dumps(merged_pages, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
        meta["release_draft"] = draft
        snapshot.write({"meta_json": meta})
        return {
            "status": "PASS",
            "platform_db": platform_db,
            "snapshot_id": int(snapshot.id),
            "snapshot_version": str(snapshot.version or ""),
            "required_page_count": len(required_pages),
            "added_page_count": added,
            "release_draft_page_count": int(draft["page_count"]),
        }

    if platform_db == current_db:
        return update_in(env)  # noqa: F821
    try:
        registry = Registry(platform_db)
        with registry.cursor() as cr:
            read_env = api.Environment(cr, SUPERUSER_ID, dict(env.context or {}))  # noqa: F821
            result = update_in(read_env)
            cr.commit()
            return result
    except Exception as exc:
        return {
            "status": "SKIP",
            "reason": "platform_release_db_unavailable",
            "platform_db": platform_db,
            "error": str(exc),
        }

policy_results = {}
platform_release_gate_results = {}
for product_key in PRODUCT_KEYS:
    policy = ProductPolicyCatalogSyncService(env).sync_policy(product_key=product_key)
    menu_groups = policy.menu_groups if isinstance(policy.menu_groups, list) else []
    total = 0
    enabled = 0
    hidden = 0
    allowed_seen = set()
    grouped_allowed_menus = {}
    hidden_menus = []
    for group in menu_groups:
        if not isinstance(group, dict):
            continue
        for menu in group.get("menus") if isinstance(group.get("menus"), list) else []:
            if not isinstance(menu, dict):
                continue
            total += 1
            next_menu = dict(menu)
            menu_xmlid = str(next_menu.get("menu_xmlid") or "").strip()
            menu_id = int(next_menu.get("menu_id") or 0)
            if menu_xmlid in allowed_xmlids or menu_id in allowed_menu_ids:
                group_label = allowed_group_by_xmlid.get(menu_xmlid) or allowed_group_by_menu_id.get(menu_id) or "用户核对"
                next_menu["enabled"] = True
                next_menu["release_state"] = "released"
                next_menu["access_level"] = "public"
                next_menu["policy_note"] = "Retained because it exposes legacy business data for customer verification."
                next_menu["sequence"] = allowed_sequence_by_xmlid.get(menu_xmlid, allowed_sequence_by_menu_id.get(menu_id, int(next_menu.get("sequence") or 0)))
                enabled += 1
                if menu_xmlid:
                    allowed_seen.add(menu_xmlid)
                grouped_allowed_menus.setdefault(group_label, []).append(next_menu)
            else:
                next_menu["enabled"] = False
                next_menu["release_state"] = "hidden"
                next_menu["policy_note"] = "Hidden while legacy business data customer-verification publishing strategy is active."
                hidden += 1
                hidden_menus.append(next_menu)
    next_groups = []
    for group_index, (group_label, menus) in enumerate(grouped_allowed_menus.items(), start=1):
        next_groups.append(
            {
                "group_key": f"construction.scbs55.{xml_name(group_label)}",
                "group_label": group_label,
                "category": "scbs55_user_acceptance_menu",
                "menus": sorted(menus, key=lambda item: int(item.get("sequence") or 0)),
            }
        )
        _ = group_index
    next_groups.extend(direct_acceptance_groups)
    if hidden_menus:
        next_groups.append(
            {
                "group_key": "construction.scbs55.hidden_original_menus",
                "group_label": "隐藏原菜单",
                "category": "hidden_original_menu",
                "menus": hidden_menus,
            }
        )
    policy_visible_xmlids = {
        str(menu.get("menu_xmlid") or "").strip()
        for menus in grouped_allowed_menus.values()
        for menu in menus
        if str(menu.get("menu_xmlid") or "").strip()
    }
    supplemental_xmlids = sorted(allowed_xmlids - policy_visible_xmlids)
    if supplemental_xmlids:
        supplemental_menus = []
        for menu_xmlid in supplemental_xmlids:
            menu = ref(menu_xmlid)
            if not menu or not menu.active or not menu.action:
                continue
            supplemental_menus.append(
                menu_policy_payload(
                    menu,
                    group_label=allowed_group_by_xmlid.get(menu_xmlid) or allowed_group_by_menu_id.get(int(menu.id)) or "旧业务数据核对",
                    note="Supplemental legacy business data menu retained because the product catalog did not emit it.",
                )
            )
        if supplemental_menus:
            next_groups.append(
                {
                    "group_key": "construction.legacy_data.supplemental_customer_verification",
                    "group_label": "旧业务数据核对补充入口",
                    "category": "legacy_data_supplemental_customer_verification",
                    "menus": sorted(supplemental_menus, key=lambda item: (str(item.get("visible_menu_path") or ""), int(item.get("menu_id") or 0))),
                }
            )
            policy_visible_xmlids.update(
                str(menu.get("menu_xmlid") or "").strip()
                for menu in supplemental_menus
                if str(menu.get("menu_xmlid") or "").strip()
            )
    missing_allowed = sorted(allowed_xmlids - policy_visible_xmlids)
    policy.write(
        {
            "menu_groups": next_groups,
            "note": "Legacy business data customer-verification menu publishing strategy active.",
        }
    )
    platform_release_gate_results[product_key] = sync_platform_release_gate_pages(
        product_key,
        policy_release_pages(next_groups),
    )
    policy_results[product_key] = {
        "total_policy_menus": total,
        "enabled_policy_menus": enabled,
        "hidden_policy_menus": hidden,
        "direct_acceptance_enabled_menus": direct_acceptance_leaf_count,
        "missing_allowed_xmlids": missing_allowed,
    }

env.cr.commit()  # noqa: F821

payload = {
    "status": "PASS"
    if created_or_updated
    and not any(result["missing_allowed_xmlids"] for result in policy_results.values())
    and all(result["enabled_policy_menus"] >= len(created_or_updated) for result in policy_results.values())
    else "FAIL",
    "mode": "scbs_55_user_acceptance_menu_policy_apply",
    "database": env.cr.dbname,  # noqa: F821
    "source_document": SOURCE_DOCUMENT,
    "active_plan_menu_count": len(rows),
    "created_or_updated_menu_count": len(created_or_updated),
    "acceptance_tree_menu_count": len(acceptance_descendant_ids) + 1,
    "runtime_allowed_menu_count": len(allowed_menu_ids),
    "legacy_data_discovered_menu_count": len(legacy_data_discovered_menus),
    "direct_acceptance_menu_count": len(direct_acceptance_menu_ids),
    "direct_acceptance_leaf_count": direct_acceptance_leaf_count,
    "runtime_hidden_menu_count": len(hidden_menu_rows),
    "runtime_keep_policy_count": runtime_keep_policy_count,
    "runtime_hide_policy_count": runtime_hide_policy_count,
    "acceptance_root_xmlid": ACCEPTANCE_ROOT_XMLID,
    "allowed_menu_xmlids": sorted(allowed_xmlids),
    "allowed_menu_sources": {
        str(menu_id): sorted(sources)
        for menu_id, sources in sorted(allowed_sources_by_menu_id.items())
    },
    "legacy_data_discovered_menus": legacy_data_discovered_menus,
    "policy_results": policy_results,
    "platform_release_gate_results": platform_release_gate_results,
    "menus": created_or_updated,
}
write_json(artifact_dir / OUTPUT_JSON_NAME, payload)
print("SCBS_55_USER_ACCEPTANCE_MENU_POLICY_APPLY=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
if payload["status"] != "PASS":
    raise SystemExit(2)
