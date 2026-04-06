# -*- coding: utf-8 -*-
from __future__ import annotations

import logging

_logger = logging.getLogger(__name__)

TIER_RANK = {"community": 1, "pro": 2, "enterprise": 3}
PREFIX_MIN_TIER = {
    "governance.": "pro",
    "analytics.": "pro",
    "finance.": "pro",
    "owner.": "enterprise",
}


def get_intent_handler_contributions():
    return []


def _min_tier_for_key(cap_key: str) -> str:
    key = str(cap_key or "").strip().lower()
    for prefix, tier in PREFIX_MIN_TIER.items():
        if key.startswith(prefix):
            return tier
    return "community"


def _allow(cap_key: str, level: str) -> bool:
    current = TIER_RANK.get(level, TIER_RANK["community"])
    needed = TIER_RANK.get(_min_tier_for_key(cap_key), TIER_RANK["community"])
    return current >= needed


def _load_license_level(env) -> str:
    try:
        raw = env["ir.config_parameter"].sudo().get_param("sc.license.level") or "enterprise"
        val = str(raw).strip().lower()
        return val if val in TIER_RANK else "enterprise"
    except Exception:
        return "enterprise"


def smart_core_extend_system_init(data, env, user):
    try:
        level = _load_license_level(env)
        caps = data.get("capabilities") if isinstance(data.get("capabilities"), list) else []
        filtered = [cap for cap in caps if isinstance(cap, dict) and _allow(cap.get("key"), level)]
        if caps:
            data["capabilities"] = filtered
        groups = data.get("capability_groups") if isinstance(data.get("capability_groups"), list) else []
        if groups:
            for bucket in groups:
                if not isinstance(bucket, dict):
                    continue
                bucket_caps = bucket.get("capabilities") if isinstance(bucket.get("capabilities"), list) else []
                bucket_caps = [cap for cap in bucket_caps if isinstance(cap, dict) and _allow(cap.get("key"), level)]
                bucket["capabilities"] = bucket_caps
                bucket["capability_count"] = len(bucket_caps)
            data["capability_groups"] = groups

        ext_facts = data.get("ext_facts") if isinstance(data.get("ext_facts"), dict) else {}
        product = ext_facts.get("product") if isinstance(ext_facts.get("product"), dict) else {}
        product["license"] = {
            "level": level,
            "tiers": ["community", "pro", "enterprise"],
        }
        ext_facts["product"] = product
        data["ext_facts"] = ext_facts
    except Exception as exc:
        _logger.warning("[smart_license_core] extend system.init failed: %s", exc)
