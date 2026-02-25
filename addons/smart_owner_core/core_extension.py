# -*- coding: utf-8 -*-
from __future__ import annotations

import logging

from .services.capability_registry_owner import list_owner_capabilities
from .services.scene_registry_owner import list_owner_scenes

_logger = logging.getLogger(__name__)


def smart_core_register(registry):
    """Register owner-domain intents into Smart Core registry."""
    try:
        from odoo.addons.smart_owner_core.handlers.owner_payment_request import (
            OwnerPaymentRequestApproveHandler,
            OwnerPaymentRequestSubmitHandler,
        )
    except Exception as exc:
        _logger.warning("[smart_owner_core] intent import failed: %s", exc)
        return

    registry["owner.payment.request.submit"] = OwnerPaymentRequestSubmitHandler
    registry["owner.payment.request.approve"] = OwnerPaymentRequestApproveHandler


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

