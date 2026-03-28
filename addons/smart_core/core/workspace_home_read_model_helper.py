# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, List
from urllib.parse import parse_qs, urlparse


IGNORED_WORKSPACE_TOP_KEYS = {
    "capabilities",
    "scenes",
    "nav",
    "nav_legacy",
    "nav_meta",
    "nav_contract",
    "default_route",
    "intents",
    "intents_meta",
    "feature_flags",
    "capability_groups",
    "capability_surface_summary",
    "preload",
    "page_contracts",
    "workspace_home",
    "role_surface",
    "role_surface_map",
    "surface_mapping",
    "surface_policies",
    "ext_facts",
    "user",
}


def _to_text(value: Any) -> str:
    return str(value or "").strip()


def scene_from_route(route: Any) -> str:
    route_text = _to_text(route)
    if not route_text:
        return ""
    parsed = urlparse(route_text)
    if parsed.path == "/s" and parsed.query:
        return _to_text(parsed.query)
    if parsed.path.startswith("/s/"):
        return _to_text(parsed.path.split("/s/", 1)[1])
    query = parse_qs(parsed.query or "")
    value = query.get("scene")
    if value and value[0]:
        return _to_text(value[0])
    return ""


def as_record_list(payload: Any) -> List[Dict[str, Any]]:
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if isinstance(payload, dict):
        for key in ("items", "records", "rows", "data", "actions", "tasks"):
            value = payload.get(key)
            if isinstance(value, list):
                return [row for row in value if isinstance(row, dict)]
    return []


def extract_business_collections(data: Dict[str, Any] | None) -> Dict[str, List[Dict[str, Any]]]:
    if not isinstance(data, dict):
        return {}
    collections: Dict[str, List[Dict[str, Any]]] = {}
    for key, value in data.items():
        if key in IGNORED_WORKSPACE_TOP_KEYS:
            continue
        rows = as_record_list(value)
        if rows:
            collections[str(key)] = rows
    return collections
