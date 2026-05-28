#!/usr/bin/env python3
"""Publish only the SCBS 55 user-acceptance menus for construction products.

Run with:
    odoo shell -c /path/to/odoo.conf -d sc_demo --no-http < scripts/ops/scbs_55_user_acceptance_menu_policy_apply.py
"""

from __future__ import annotations

import json
import os
from pathlib import Path


SOURCE_DOCUMENT = "/home/odoo/workspace/partner_import_source/5.6优化（老系统菜单，字段列表展示）1.docx"
PRODUCT_KEYS = ("construction.standard", "construction.preview")
MODULE = "smart_construction_core"
ROOT_XMLID = "smart_construction_core.menu_sc_root"
ACCEPTANCE_ROOT_XMLID = "smart_construction_core.menu_scbs55_user_acceptance_root"
OUTPUT_JSON_NAME = "scbs_55_user_acceptance_menu_policy_apply_result_v1.json"


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


ensure_allowed_db()
artifact_dir = artifact_root()

Plan = env["sc.legacy.user.priority.menu.plan"].sudo()  # noqa: F821
rows = Plan.search([("source_document", "=", SOURCE_DOCUMENT), ("active", "=", True)], order="priority_sequence")
if len(rows) != 55:
    raise RuntimeError({"expected_55_plan_rows": 55, "actual": len(rows)})

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
created_or_updated = []
for row in rows:
    action = row.target_action_id
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

from odoo.addons.smart_core.delivery.product_policy_catalog_sync_service import ProductPolicyCatalogSyncService  # noqa: E402

policy_results = {}
for product_key in PRODUCT_KEYS:
    policy = ProductPolicyCatalogSyncService(env).sync_policy(product_key=product_key)
    menu_groups = policy.menu_groups if isinstance(policy.menu_groups, list) else []
    total = 0
    enabled = 0
    hidden = 0
    allowed_seen = set()
    next_groups = []
    for group in menu_groups:
        if not isinstance(group, dict):
            continue
        next_group = dict(group)
        next_menus = []
        for menu in group.get("menus") if isinstance(group.get("menus"), list) else []:
            if not isinstance(menu, dict):
                continue
            total += 1
            next_menu = dict(menu)
            menu_xmlid = str(next_menu.get("menu_xmlid") or "").strip()
            if menu_xmlid in allowed_xmlids:
                next_menu["enabled"] = True
                next_menu["release_state"] = "released"
                next_menu["access_level"] = "public"
                next_menu["policy_note"] = "SCBS 55 user acceptance menu retained for customer verification."
                enabled += 1
                allowed_seen.add(menu_xmlid)
            else:
                next_menu["enabled"] = False
                next_menu["release_state"] = "hidden"
                next_menu["policy_note"] = "Hidden while SCBS 55 user acceptance menu-only publishing strategy is active."
                hidden += 1
            next_menus.append(next_menu)
        next_group["menus"] = next_menus
        next_groups.append(next_group)
    missing_allowed = sorted(allowed_xmlids - allowed_seen)
    policy.write(
        {
            "menu_groups": next_groups,
            "note": "SCBS 55 user acceptance menu-only publishing strategy active.",
        }
    )
    policy_results[product_key] = {
        "total_policy_menus": total,
        "enabled_policy_menus": enabled,
        "hidden_policy_menus": hidden,
        "missing_allowed_xmlids": missing_allowed,
    }

env.cr.commit()  # noqa: F821

payload = {
    "status": "PASS"
    if len(created_or_updated) == 55
    and all(not result["missing_allowed_xmlids"] and result["enabled_policy_menus"] == 55 for result in policy_results.values())
    else "FAIL",
    "mode": "scbs_55_user_acceptance_menu_policy_apply",
    "database": env.cr.dbname,  # noqa: F821
    "source_document": SOURCE_DOCUMENT,
    "created_or_updated_menu_count": len(created_or_updated),
    "acceptance_root_xmlid": ACCEPTANCE_ROOT_XMLID,
    "allowed_menu_xmlids": sorted(allowed_xmlids),
    "policy_results": policy_results,
    "menus": created_or_updated,
}
write_json(artifact_dir / OUTPUT_JSON_NAME, payload)
print("SCBS_55_USER_ACCEPTANCE_MENU_POLICY_APPLY=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
if payload["status"] != "PASS":
    raise SystemExit(2)
