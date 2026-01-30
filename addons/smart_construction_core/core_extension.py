# -*- coding: utf-8 -*-
import logging

_logger = logging.getLogger(__name__)


def smart_core_register(registry):
    """
    Register construction demo intent into smart_core registry.
    """
    try:
        from odoo.addons.smart_construction_core.handlers.system_ping_construction import (
            SystemPingConstructionHandler,
        )
    except Exception as e:
        _logger.warning("[smart_core_register] import handler failed: %s", e)
        return

    registry["system.ping.construction"] = SystemPingConstructionHandler
    _logger.info("[smart_core_register] registered system.ping.construction")


def smart_core_extend_system_init(data, env, user):
    """
    Enrich smart_core system.init response with construction scenes/capabilities.
    """
    try:
        Cap = env["sc.capability"].sudo()
        Scene = env["sc.scene"].sudo()
        caps = Cap.search([("active", "=", True)], order="sequence, id")
        scenes = Scene.search([("active", "=", True), ("state", "=", "published")], order="sequence, id")
        data["capabilities"] = [
            rec.to_public_dict(user) for rec in caps if rec._user_allowed(user)
        ]
        data["scenes"] = [
            scene.to_public_dict(user) for scene in scenes if scene._user_allowed(user)
        ]
    except Exception as exc:
        _logger.warning("[smart_core_extend_system_init] failed: %s", exc)
