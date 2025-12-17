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


def export_inventory(db_name: str):
    config.parse_config([])
    registry = odoo.registry(db_name)
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})

        # Menus under module root
        try:
            root = env.ref("smart_construction_core.menu_sc_root")
        except Exception:
            root = None
        menus = []
        if root:
            menus_rs = env["ir.ui.menu"].sudo().with_context(active_test=False).search(
                [("parent_id", "child_of", root.id)], order="parent_id,sequence,id"
            )
            for m in menus_rs:
                menus.append(
                    {
                        "id": m.id,
                        "xml_id": m.xml_id,
                        "name": m.name,
                        "parent_id": m.parent_id.id,
                        "parent_xml_id": m.parent_id.xml_id,
                        "action": m.action and m.action.id,
                        "action_model": m.action and m.action._name,
                        "groups": m.groups_id.mapped("xml_id"),
                        "active": m.active,
                        "sequence": m.sequence,
                    }
                )

        # Actions tied to smart_construction_core
        actions = []
        act_rs = env["ir.actions.act_window"].sudo().search(
            [("binding_model_id.modules", "ilike", "smart_construction_core")], order="id"
        )
        for act in act_rs:
            actions.append(
                {
                    "id": act.id,
                    "xml_id": act.xml_id,
                    "name": act.name,
                    "res_model": act.res_model,
                    "view_mode": act.view_mode,
                    "groups": act.groups_id.mapped("xml_id"),
                }
            )

        # Models belonging to module
        models = []
        model_rs = env["ir.model"].sudo().search([])
        for m in model_rs:
            mods = (m.modules or "").split(",")
            if "smart_construction_core" in mods:
                models.append({"id": m.id, "model": m.model, "name": m.name})

        # ACLs for module models
        acls = []
        acl_rs = env["ir.model.access"].sudo().search([])
        sc_models = {m["model"] for m in models}
        for acl in acl_rs:
            if acl.model_id.model in sc_models:
                acls.append(
                    {
                        "id": acl.id,
                        "name": acl.name,
                        "model": acl.model_id.model,
                        "group": acl.group_id.xml_id,
                        "perm_read": acl.perm_read,
                        "perm_write": acl.perm_write,
                        "perm_create": acl.perm_create,
                        "perm_unlink": acl.perm_unlink,
                    }
                )

        payload = {
            "menus": menus,
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
