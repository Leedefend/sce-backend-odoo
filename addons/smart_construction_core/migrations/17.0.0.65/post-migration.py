# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    action = env.ref("smart_construction_core.action_sc_business_config_workbench", raise_if_not_found=False)
    tree_view = env.ref("smart_construction_core.view_sc_business_config_workbench_tree", raise_if_not_found=False)
    if action and tree_view:
        action.write(
            {
                "view_id": tree_view.id,
                "view_ids": [
                    (5, 0, 0),
                    (0, 0, {"view_mode": "tree", "view_id": tree_view.id}),
                ],
            }
        )
        pinned = 1
    else:
        pinned = 0
    print("[17.0.0.65] business config workbench list pinned: actions=%s" % pinned)
