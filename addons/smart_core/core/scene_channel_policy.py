# -*- coding: utf-8 -*-
from __future__ import annotations

import os

from odoo import api

from odoo.addons.smart_core.utils.contract_governance import is_truthy


class SceneChannelPolicy:
    def resolve(self, env: api.Environment, params: dict, scene_channel: str) -> tuple[str, bool]:
        pinned_param = params.get("scene_use_pinned") if isinstance(params, dict) else None
        rollback_param = params.get("scene_rollback") if isinstance(params, dict) else None
        rollback_active = is_truthy(pinned_param) or is_truthy(rollback_param)
        if pinned_param is not None and str(pinned_param).strip() not in {"", "0", "false", "no", "off"}:
            rollback_active = True
        try:
            config = env["ir.config_parameter"].sudo()
            rollback_active = rollback_active or is_truthy(config.get_param("sc.scene.use_pinned")) or \
                is_truthy(config.get_param("sc.scene.rollback"))
        except Exception:
            pass
        rollback_active = rollback_active or is_truthy(os.environ.get("SCENE_USE_PINNED")) or \
            is_truthy(os.environ.get("SCENE_ROLLBACK"))
        if rollback_active:
            scene_channel = "stable"
        return scene_channel, rollback_active
