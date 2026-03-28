# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Callable


def normalize_allowlist_values(raw: Any) -> set[str]:
    values = raw if isinstance(raw, (list, tuple, set)) else []
    return {str(item or "").strip() for item in values if str(item or "").strip()}


def load_surface_policy_map_from_payload(
    payload: dict,
    *,
    normalize_surface: Callable[[Any], str],
) -> dict[str, dict[str, set[str]]]:
    surfaces = payload.get("surfaces") if isinstance(payload.get("surfaces"), dict) else {}
    out: dict[str, dict[str, set[str]]] = {}
    for surface_key, policy in surfaces.items():
        key = normalize_surface(surface_key)
        if not key or not isinstance(policy, dict):
            continue
        nav_allowlist = normalize_allowlist_values(policy.get("nav_allowlist"))
        deep_link_allowlist = normalize_allowlist_values(policy.get("deep_link_allowlist"))
        if nav_allowlist or deep_link_allowlist:
            out[key] = {
                "nav_allowlist": nav_allowlist,
                "deep_link_allowlist": deep_link_allowlist,
            }
    return out


def resolve_builtin_surface_policy(
    surface_key: str,
    *,
    nav_allowlist_map: dict,
    deep_link_allowlist_map: dict,
) -> dict:
    nav_allowlist = normalize_allowlist_values(nav_allowlist_map.get(surface_key) or set())
    deep_link_allowlist = normalize_allowlist_values(deep_link_allowlist_map.get(surface_key) or ())
    if not nav_allowlist and not deep_link_allowlist:
        return {"name": "", "enabled": False, "source": "none", "nav_allowlist": set(), "deep_link_allowlist": set()}
    return {
        "name": surface_key,
        "enabled": True,
        "source": "builtin",
        "nav_allowlist": nav_allowlist,
        "deep_link_allowlist": deep_link_allowlist,
    }
