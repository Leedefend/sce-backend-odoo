# -*- coding: utf-8 -*-
from __future__ import annotations

import os

from odoo import api

from odoo.addons.smart_core.core.source_authority import build_source_authority_contract
from odoo.addons.smart_core.utils.contract_governance import is_truthy


class SceneChannelPolicy:
    SOURCE_KIND = "scene_channel_policy_projection"
    SOURCE_AUTHORITIES = ("request.params", "ir.config_parameter", "environment")
    NO_BUSINESS_FACT_AUTHORITY = True

    @classmethod
    def source_authority_contract(cls) -> dict:
        return build_source_authority_contract(
            kind=cls.SOURCE_KIND,
            authorities=cls.SOURCE_AUTHORITIES,
            no_business_fact_authority=cls.NO_BUSINESS_FACT_AUTHORITY,
            runtime_carrier="system.init.scene_channel_policy",
        )

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
