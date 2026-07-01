# -*- coding: utf-8 -*-
from __future__ import annotations

import json

from odoo import SUPERUSER_ID, api
from odoo.addons.smart_core.utils.backend_contract_boundaries import ensure_lowcode_contract_source_status


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    Contract = env["ui.business.config.contract"].sudo()
    updated = 0
    for rec in Contract.search([], order="id"):
        payload = rec.contract_json if isinstance(rec.contract_json, dict) else {}
        next_payload = ensure_lowcode_contract_source_status(payload)
        if next_payload == payload:
            continue
        cr.execute(
            """
            UPDATE ui_business_config_contract
               SET contract_json = %s::jsonb,
                   write_date = NOW()
             WHERE id = %s
            """,
            (json.dumps(next_payload, ensure_ascii=False), rec.id),
        )
        updated += 1
    print("[17.0.0.59] ui_business_config_contract source_status backfilled: %s" % updated)
