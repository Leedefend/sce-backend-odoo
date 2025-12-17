# -*- coding: utf-8 -*-
"""
Quick inventory exporter for smart_construction_core.

Usage (from repo root):
    docker-compose run --rm -T odoo /bin/bash -lc "python3 /mnt/extra-addons/smart_construction_core/tools/audit/export_inventory.py -d sc_odoo"
"""
import argparse
import json
import sys

import odoo
from odoo import api, SUPERUSER_ID
from odoo.tools import config

# 保证输出为 UTF-8，避免中文乱码
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def _xmlid(record):
    return record.get_external_id().get(record.id)


def export_inventory(db_name: str):
    config.parse_config([])
    registry = odoo.registry(db_name)
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})

        # --- Menu inventory by ir.model.data (ground truth of what module defined) ---
        imd = env["ir.model.data"].sudo()
        menu_imd = imd.search([("module", "=", "smart_construction_core"), ("model", "=", "ir.ui.menu")])
        menu_by_xmlid = []
        Menu = env["ir.ui.menu"].sudo().with_context(active_test=False, **{"ir.ui.menu.full_list": True})
        for r in menu_imd:
            m = Menu.browse(r.res_id).exists()
            if not m:
                menu_by_xmlid.append(
                    {
                        "xml_id": f"{r.module}.{r.name}",
                        "res_id": r.res_id,
                        "missing_record": True,
                    }
                )
                continue
            menu_by_xmlid.append(
                {
                    "xml_id": f"{r.module}.{r.name}",
                    "id": m.id,
                    "name": m.name,
                    "parent_id": m.parent_id.id,
                    "parent_xml_id": _xmlid(m.parent_id),
                    "action": m.action and m.action.id,
                    "action_model": m.action and m.action._name,
                    "groups": list(filter(None, [_xmlid(g) for g in m.groups_id])),
                    "active": m.active,
                    "sequence": m.sequence,
                }
            )

        # Models belonging to module
        models = []
        model_rs = env["ir.model"].sudo().search([])
        for m in model_rs:
            mods = (m.modules or "").split(",")
            if "smart_construction_core" in mods:
                models.append({"id": m.id, "model": m.model, "name": m.name, "xml_id": _xmlid(m)})
        sc_models = {m["model"] for m in models}

        # Menus under module root
        try:
            root = env.ref("smart_construction_core.menu_sc_root")
        except Exception:
            root = None
        root_menus = []
        if root:
            menus_rs = (
                env["ir.ui.menu"]
                .sudo()
                .with_context(active_test=False, **{"ir.ui.menu.full_list": True})
                .search([("parent_id", "child_of", root.id)], order="parent_id,sequence,id")
            )
            for m in menus_rs:
                root_menus.append(
                    {
                        "id": m.id,
                        "xml_id": _xmlid(m),
                        "name": m.name,
                        "parent_id": m.parent_id.id,
                        "parent_xml_id": _xmlid(m.parent_id),
                        "action": m.action and m.action.id,
                        "action_model": m.action and m.action._name,
                        "groups": list(filter(None, [_xmlid(g) for g in m.groups_id])),
                        "active": m.active,
                        "sequence": m.sequence,
                    }
                )

        # Actions tied to smart_construction_core (by res_model or by xml_id module)
        actions = []
        act_rs = env["ir.actions.act_window"].sudo().search([])
        for act in act_rs:
            if act.res_model in sc_models or (act.xml_id or "").startswith("smart_construction_core."):
                actions.append(
                    {
                        "id": act.id,
                        "xml_id": act.xml_id or _xmlid(act),
                        "name": act.name,
                        "res_model": act.res_model,
                        "view_mode": act.view_mode,
                        "groups": list(filter(None, [_xmlid(g) for g in act.groups_id])),
                    }
                )

        # ACLs for module models
        acls = []
        acl_rs = env["ir.model.access"].sudo().search([])
        for acl in acl_rs:
            if acl.model_id.model in sc_models:
                acls.append(
                    {
                        "id": acl.id,
                        "name": acl.name,
                        "model": acl.model_id.model,
                        "group": _xmlid(acl.group_id),
                        "perm_read": acl.perm_read,
                        "perm_write": acl.perm_write,
                        "perm_create": acl.perm_create,
                        "perm_unlink": acl.perm_unlink,
                    }
                )

        payload = {
            "menus_defined_by_module": menu_by_xmlid,
            "menus_root_subtree": root_menus,
            "actions": actions,
            "models": models,
            "acls": acls,
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--database", required=True)
    args = parser.parse_args(argv)
    export_inventory(args.database)


if __name__ == "__main__":
    main(sys.argv[1:])
