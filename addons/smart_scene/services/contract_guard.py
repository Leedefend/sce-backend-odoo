# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict

from odoo.addons.smart_scene.schemas.scene_contract_schema import check_top_level_shape


def guard_scene_contract(payload: Dict[str, Any]) -> Dict[str, Any]:
    ok, detail = check_top_level_shape(payload)
    return {
        "ok": bool(ok),
        "detail": detail,
    }

