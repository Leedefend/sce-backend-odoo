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
        from odoo.addons.smart_construction_core.handlers.capability_describe import (
            CapabilityDescribeHandler,
        )
        from odoo.addons.smart_construction_core.handlers.my_work_summary import (
            MyWorkSummaryHandler,
        )
        from odoo.addons.smart_construction_core.handlers.my_work_complete import (
            MyWorkCompleteHandler,
            MyWorkCompleteBatchHandler,
        )
        from odoo.addons.smart_construction_core.handlers.usage_track import (
            UsageTrackHandler,
        )
        from odoo.addons.smart_construction_core.handlers.usage_report import (
            UsageReportHandler,
        )
        from odoo.addons.smart_construction_core.handlers.capability_visibility_report import (
            CapabilityVisibilityReportHandler,
        )
    except Exception as e:
        _logger.warning("[smart_core_register] import handler failed: %s", e)
        return

    registry["system.ping.construction"] = SystemPingConstructionHandler
    registry["capability.describe"] = CapabilityDescribeHandler
    registry["my.work.summary"] = MyWorkSummaryHandler
    registry["my.work.complete"] = MyWorkCompleteHandler
    registry["my.work.complete_batch"] = MyWorkCompleteBatchHandler
    registry["usage.track"] = UsageTrackHandler
    registry["usage.report"] = UsageReportHandler
    registry["capability.visibility.report"] = CapabilityVisibilityReportHandler
    _logger.info("[smart_core_register] registered system.ping.construction")
    _logger.info("[smart_core_register] registered capability.describe")
    _logger.info("[smart_core_register] registered my.work.summary")
    _logger.info("[smart_core_register] registered my.work.complete")
    _logger.info("[smart_core_register] registered my.work.complete_batch")
    _logger.info("[smart_core_register] registered usage.track")
    _logger.info("[smart_core_register] registered usage.report")
    _logger.info("[smart_core_register] registered capability.visibility.report")


def smart_core_extend_system_init(data, env, user):
    """
    Enrich smart_core system.init response with construction scenes/capabilities.
    """
    try:
        Cap = env["sc.capability"].sudo()
        Scene = env["sc.scene"].sudo()
        Entitlement = env.get("sc.entitlement")
        Usage = env.get("sc.usage.counter")
        caps = Cap.search([("active", "=", True)], order="sequence, id")
        scenes = Scene.search([
            ("active", "=", True),
            ("state", "=", "published"),
            ("is_test", "=", False),
        ], order="sequence, id")
        data["capabilities"] = [
            rec.to_public_dict(user) for rec in caps if rec._user_visible(user)
        ]
        if not data.get("scenes"):
            data["scenes"] = [
                scene.to_public_dict(user) for scene in scenes if scene._user_allowed(user)
            ]
        if Entitlement:
            data["entitlements"] = Entitlement.get_payload(user)
        if Usage:
            data["usage"] = Usage.get_usage_map(user.company_id)
    except Exception as exc:
        _logger.warning("[smart_core_extend_system_init] failed: %s", exc)
