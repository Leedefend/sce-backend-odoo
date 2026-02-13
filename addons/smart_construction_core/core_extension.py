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
        from odoo.addons.smart_construction_core.handlers.usage_export_csv import (
            UsageExportCsvHandler,
        )
        from odoo.addons.smart_construction_core.handlers.capability_visibility_report import (
            CapabilityVisibilityReportHandler,
        )
        from odoo.addons.smart_construction_core.handlers.payment_request_approval import (
            PaymentRequestApproveHandler,
            PaymentRequestDoneHandler,
            PaymentRequestRejectHandler,
            PaymentRequestSubmitHandler,
        )
        from odoo.addons.smart_construction_core.handlers.payment_request_available_actions import (
            PaymentRequestAvailableActionsHandler,
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
    registry["usage.export.csv"] = UsageExportCsvHandler
    registry["capability.visibility.report"] = CapabilityVisibilityReportHandler
    registry["payment.request.submit"] = PaymentRequestSubmitHandler
    registry["payment.request.approve"] = PaymentRequestApproveHandler
    registry["payment.request.reject"] = PaymentRequestRejectHandler
    registry["payment.request.done"] = PaymentRequestDoneHandler
    registry["payment.request.available_actions"] = PaymentRequestAvailableActionsHandler
    _logger.info("[smart_core_register] registered system.ping.construction")
    _logger.info("[smart_core_register] registered capability.describe")
    _logger.info("[smart_core_register] registered my.work.summary")
    _logger.info("[smart_core_register] registered my.work.complete")
    _logger.info("[smart_core_register] registered my.work.complete_batch")
    _logger.info("[smart_core_register] registered usage.track")
    _logger.info("[smart_core_register] registered usage.report")
    _logger.info("[smart_core_register] registered usage.export.csv")
    _logger.info("[smart_core_register] registered capability.visibility.report")
    _logger.info("[smart_core_register] registered payment.request.submit")
    _logger.info("[smart_core_register] registered payment.request.approve")
    _logger.info("[smart_core_register] registered payment.request.reject")
    _logger.info("[smart_core_register] registered payment.request.done")
    _logger.info("[smart_core_register] registered payment.request.available_actions")


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
