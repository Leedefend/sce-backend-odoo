# -*- coding: utf-8 -*-
from odoo import SUPERUSER_ID, api


def _rewrite_project_entry_payloads(env):
    canonical_payload = {
        "action_xmlid": "smart_construction_core.action_sc_project_list",
        "menu_xmlid": "smart_construction_core.menu_sc_project_project",
    }
    capabilities = env["sc.capability"].search([("key", "=", "project.board.open")])
    for capability in capabilities:
        capability.default_payload = dict(canonical_payload)
        capability.ui_hint = "项目台账与项目办理入口"


def _remove_legacy_project_lifecycle_action(env):
    canonical = env.ref("smart_construction_core.action_sc_project_list", raise_if_not_found=False)
    legacy = env.ref("smart_construction_core.action_sc_project_kanban_lifecycle", raise_if_not_found=False)
    if canonical and legacy:
        legacy_action_ref = "ir.actions.act_window,%s" % legacy.id
        env["ir.ui.menu"].search([("action", "=", legacy_action_ref)]).write(
            {"action": "ir.actions.act_window,%s" % canonical.id}
        )
        legacy.unlink()
    env["ir.model.data"].search(
        [
            ("module", "=", "smart_construction_core"),
            ("name", "=", "action_sc_project_kanban_lifecycle"),
        ]
    ).unlink()


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    _rewrite_project_entry_payloads(env)
    _remove_legacy_project_lifecycle_action(env)
