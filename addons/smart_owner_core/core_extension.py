# -*- coding: utf-8 -*-
from __future__ import annotations

import logging

from .services.capability_registry_owner import list_owner_capabilities
from .services.scene_registry_owner import list_owner_scenes

_logger = logging.getLogger(__name__)


def get_intent_handler_contributions():
    try:
        from odoo.addons.smart_owner_core.handlers.owner_payment_request import (
            OwnerApprovalCenterHandler,
            OwnerDashboardOpenHandler,
            OwnerPaymentRequestApproveHandler,
            OwnerPaymentRequestSubmitHandler,
            OwnerProjectsDetailHandler,
            OwnerProjectsListHandler,
            OwnerReportOverviewHandler,
            OwnerRiskListHandler,
        )
    except Exception as exc:
        _logger.warning("[smart_owner_core] intent import failed: %s", exc)
        return []

    return [
        {
            "intent": "owner.payment.request.submit",
            "handler": OwnerPaymentRequestSubmitHandler,
            "source_module": "smart_owner_core",
            "domain": "owner",
            "status": "active",
        },
        {
            "intent": "owner.payment.request.approve",
            "handler": OwnerPaymentRequestApproveHandler,
            "source_module": "smart_owner_core",
            "domain": "owner",
            "status": "active",
        },
        {
            "intent": "owner.dashboard.open",
            "handler": OwnerDashboardOpenHandler,
            "source_module": "smart_owner_core",
            "domain": "owner",
            "status": "active",
        },
        {
            "intent": "owner.projects.list",
            "handler": OwnerProjectsListHandler,
            "source_module": "smart_owner_core",
            "domain": "owner",
            "status": "active",
        },
        {
            "intent": "owner.projects.detail",
            "handler": OwnerProjectsDetailHandler,
            "source_module": "smart_owner_core",
            "domain": "owner",
            "status": "active",
        },
        {
            "intent": "owner.risk.list",
            "handler": OwnerRiskListHandler,
            "source_module": "smart_owner_core",
            "domain": "owner",
            "status": "active",
        },
        {
            "intent": "owner.report.overview",
            "handler": OwnerReportOverviewHandler,
            "source_module": "smart_owner_core",
            "domain": "owner",
            "status": "active",
        },
        {
            "intent": "owner.approval.center",
            "handler": OwnerApprovalCenterHandler,
            "source_module": "smart_owner_core",
            "domain": "owner",
            "status": "active",
        },
    ]


def smart_core_extend_system_init(data, env, user):
    """
    Optional owner-domain overlay.

    Activation condition:
    - request context contains sc.industry=owner
    - smart_owner_core is enabled in sc.core.extension_modules

    This keeps L0 untouched and applies owner-domain payload through extension hook only.
    """
    try:
        industry = str((env.context or {}).get("sc.industry") or "").strip().lower()
        if industry != "owner":
            return

        owner_scenes = list_owner_scenes()
        owner_caps = list_owner_capabilities()

        # Scene-independent deployment simulation: replace domain payload by owner-only package.
        data["scenes"] = owner_scenes
        data["capabilities"] = owner_caps
        data["scene_count"] = len(owner_scenes)
        data["capability_count"] = len(owner_caps)
    except Exception as exc:
        _logger.warning("[smart_owner_core] system_init extension failed: %s", exc)
