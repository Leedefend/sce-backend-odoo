# -*- coding: utf-8 -*-
from __future__ import annotations

import logging

from .services.bundle_registry import (
    default_dashboard,
    list_bundle_capabilities,
    list_bundle_scenes,
    product_profile,
    recommended_roles,
)

_logger = logging.getLogger(__name__)


def get_intent_handler_contributions():
    return []


def _build_bundle_product_fact() -> dict:
    return {
        "profile": product_profile(),
        "name": "smart_construction_bundle",
        "scenes": list_bundle_scenes(),
        "capabilities": list_bundle_capabilities(),
        "recommended_roles": recommended_roles(),
        "default_dashboard": default_dashboard(),
    }


def smart_core_resolve_startup_delivery_identity(env, params=None):
    params = params if isinstance(params, dict) else {}
    bundle = str((params.get("sc.bundle") or (env.context or {}).get("sc.bundle") or "")).strip().lower()
    if bundle not in {"", "construction"}:
        return None
    profile = product_profile()
    product_key = str(profile.get("product_key") or "construction.standard").strip() or "construction.standard"
    if "." in product_key:
        base_product_key, edition_key = product_key.split(".", 1)
    else:
        base_product_key, edition_key = "construction", "standard"
    return {
        "product_key": product_key,
        "base_product_key": base_product_key or "construction",
        "edition_key": edition_key or "standard",
        "source": "smart_construction_bundle",
        "projection_only": True,
        "no_business_fact_authority": True,
    }


def get_system_init_fact_contributions(env, user, context=None):
    context = context if isinstance(context, dict) else {}
    bundle = str((context.get("sc.bundle") or (env.context or {}).get("sc.bundle") or "")).strip().lower()
    if bundle not in {"", "construction"}:
        return None
    return {
        "module": "product",
        "facts": {
            "bundle": _build_bundle_product_fact(),
        },
    }


def smart_core_extend_system_init(data, env, user):
    try:
        bundle = str((env.context or {}).get("sc.bundle") or "").strip().lower()
        if bundle not in {"", "construction"}:
            return
        ext_facts = data.get("ext_facts") if isinstance(data.get("ext_facts"), dict) else {}
        product = ext_facts.get("product") if isinstance(ext_facts.get("product"), dict) else {}
        product["bundle"] = _build_bundle_product_fact()
        ext_facts["product"] = product
        data["ext_facts"] = ext_facts
    except Exception as exc:
        _logger.warning("[smart_construction_bundle] extend system.init failed: %s", exc)
