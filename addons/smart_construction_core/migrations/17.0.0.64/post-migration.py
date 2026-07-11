# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo import SUPERUSER_ID, api


SETTLEMENT_ACTION_XMLIDS = (
    "smart_construction_core.action_sc_settlement_order_income",
    "smart_construction_core.action_sc_settlement_order_expense",
)


def _pin_settlement_action(env, action_xmlid):
    action = env.ref(action_xmlid, raise_if_not_found=False)
    tree_view = env.ref(
        "smart_construction_core.view_sc_settlement_order_user_confirmed_tree",
        raise_if_not_found=False,
    )
    form_view = env.ref("smart_construction_core.view_sc_settlement_order_form", raise_if_not_found=False)
    if not action or not tree_view:
        return False

    action.write(
        {
            "view_id": tree_view.id,
            "view_ids": [
                (5, 0, 0),
                (0, 0, {"view_mode": "tree", "view_id": tree_view.id}),
                (0, 0, {"view_mode": "form", "view_id": form_view.id if form_view else False}),
            ],
        }
    )
    return True


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    pinned = sum(1 for action_xmlid in SETTLEMENT_ACTION_XMLIDS if _pin_settlement_action(env, action_xmlid))

    synced = 0
    Contract = env["ui.business.config.contract"].sudo()
    if hasattr(Contract, "sc_sync_settlement_formal_list_contracts"):
        synced = Contract.sc_sync_settlement_formal_list_contracts()

    print(
        "[17.0.0.64] settlement formal list actions pinned: actions=%s contracts=%s"
        % (pinned, synced)
    )
