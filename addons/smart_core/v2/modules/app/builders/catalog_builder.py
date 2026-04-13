from __future__ import annotations

from typing import Any, Dict, List

from ..reason_codes import normalize_reason_code


def build_app_catalog_contract(result: Dict[str, Any]) -> Dict[str, Any]:
    apps = result.get("apps") or []
    if not isinstance(apps, list):
        apps = []
    normalized: List[Dict[str, Any]] = []
    for app in apps:
        if not isinstance(app, dict):
            continue
        normalized.append(
            {
                "app_key": str(app.get("app_key") or ""),
                "name": str(app.get("name") or ""),
                "active": bool(app.get("active")),
                "target_type": str(app.get("target_type") or "app"),
                "delivery_mode": str(app.get("delivery_mode") or "custom_app"),
                "is_clickable": bool(app.get("is_clickable", True)),
                "availability_status": str(app.get("availability_status") or "available"),
                "reason_code": normalize_reason_code(str(app.get("reason_code") or "")),
                "route": str(app.get("route") or ""),
                "active_match": app.get("active_match") if isinstance(app.get("active_match"), dict) else {},
            }
        )
    return {
        "apps": normalized,
        "count": int(result.get("count") or len(normalized)),
        "version": str(result.get("version") or "v2"),
        "source": str(result.get("source") or "v2-rebuild"),
    }


def build_app_nav_contract(result: Dict[str, Any]) -> Dict[str, Any]:
    nodes = result.get("nodes") or []
    if not isinstance(nodes, list):
        nodes = []
    normalized: List[Dict[str, Any]] = []
    for node in nodes:
        if not isinstance(node, dict):
            continue
        normalized.append(
            {
                "node_key": str(node.get("node_key") or ""),
                "name": str(node.get("name") or ""),
                "target_type": str(node.get("target_type") or "nav"),
                "delivery_mode": str(node.get("delivery_mode") or "custom_nav"),
                "is_clickable": bool(node.get("is_clickable", True)),
                "availability_status": str(node.get("availability_status") or "available"),
                "reason_code": normalize_reason_code(str(node.get("reason_code") or "")),
                "route": str(node.get("route") or ""),
                "active_match": node.get("active_match") if isinstance(node.get("active_match"), dict) else {},
            }
        )
    return {
        "app_key": str(result.get("app_key") or ""),
        "nodes": normalized,
        "count": int(result.get("count") or len(normalized)),
        "version": str(result.get("version") or "v2"),
        "source": str(result.get("source") or "v2-rebuild"),
    }


def build_app_open_contract(result: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "app_key": str(result.get("app_key") or ""),
        "open_url": str(result.get("open_url") or ""),
        "open_mode": str(result.get("open_mode") or "internal"),
        "target_type": str(result.get("target_type") or "open"),
        "delivery_mode": str(result.get("delivery_mode") or "custom_open"),
        "is_clickable": bool(result.get("is_clickable", True)),
        "availability_status": str(result.get("availability_status") or "available"),
        "reason_code": normalize_reason_code(str(result.get("reason_code") or "")),
        "active_match": result.get("active_match") if isinstance(result.get("active_match"), dict) else {},
        "version": str(result.get("version") or "v2"),
        "source": str(result.get("source") or "v2-rebuild"),
    }
