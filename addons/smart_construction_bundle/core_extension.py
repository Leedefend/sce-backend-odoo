# -*- coding: utf-8 -*-
from __future__ import annotations

import logging

from .services.bundle_registry import (
    default_dashboard,
    list_bundle_capabilities,
    list_bundle_scenes,
    recommended_roles,
)

_logger = logging.getLogger(__name__)


def get_intent_handler_contributions():
    return []


def smart_core_extend_system_init(data, env, user):
    try:
        bundle = str((env.context or {}).get("sc.bundle") or "").strip().lower()
        if bundle not in {"", "construction"}:
            return
        ext_facts = data.get("ext_facts") if isinstance(data.get("ext_facts"), dict) else {}
        product = ext_facts.get("product") if isinstance(ext_facts.get("product"), dict) else {}
        product["bundle"] = {
            "name": "smart_construction_bundle",
            "scenes": list_bundle_scenes(),
            "capabilities": list_bundle_capabilities(),
            "recommended_roles": recommended_roles(),
            "default_dashboard": default_dashboard(),
        }
        ext_facts["product"] = product
        data["ext_facts"] = ext_facts
    except Exception as exc:
        _logger.warning("[smart_construction_bundle] extend system.init failed: %s", exc)
