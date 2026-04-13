from __future__ import annotations

from typing import Any, Dict


def build_ping_contract(result: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "pong": bool(result.get("pong")),
        "server_time": str(result.get("server_time") or ""),
        "version": str(result.get("version") or "v2"),
    }


def build_registry_list_contract(result: Dict[str, Any]) -> Dict[str, Any]:
    intents = result.get("intents") or []
    if not isinstance(intents, list):
        intents = []
    return {
        "intents": [str(item) for item in intents],
        "count": int(result.get("count") or len(intents)),
        "version": str(result.get("version") or "v2"),
    }


def build_system_init_contract(result: Dict[str, Any]) -> Dict[str, Any]:
    identity = result.get("identity") if isinstance(result.get("identity"), dict) else {}
    catalog = result.get("catalog") if isinstance(result.get("catalog"), dict) else {}
    nav = result.get("nav") if isinstance(result.get("nav"), dict) else {}
    open_payload = result.get("open") if isinstance(result.get("open"), dict) else {}
    registry = result.get("registry") if isinstance(result.get("registry"), dict) else {}
    return {
        "identity": {
            "user_id": int(identity.get("user_id") or 0),
            "company_id": int(identity.get("company_id") or 0),
        },
        "catalog": catalog,
        "nav": nav,
        "open": open_payload,
        "registry": {
            "count": int(registry.get("count") or 0),
        },
        "version": str(result.get("version") or "v2"),
        "source": str(result.get("source") or "v2-rebuild"),
    }


def build_system_init_inspect_contract(result: Dict[str, Any]) -> Dict[str, Any]:
    bootstrap = result.get("bootstrap") if isinstance(result.get("bootstrap"), dict) else {}
    bootstrap_summary = result.get("bootstrap_summary") if isinstance(result.get("bootstrap_summary"), dict) else {}
    registry_summary = result.get("registry_summary") if isinstance(result.get("registry_summary"), dict) else {}
    return {
        "bootstrap": bootstrap,
        "bootstrap_summary": {
            "app_count": int(bootstrap_summary.get("app_count") or 0),
            "nav_count": int(bootstrap_summary.get("nav_count") or 0),
            "open_url": str(bootstrap_summary.get("open_url") or ""),
        },
        "registry_summary": {
            "intent_count": int(registry_summary.get("intent_count") or 0),
        },
        "health": str(result.get("health") or "degraded"),
        "version": str(result.get("version") or "v2"),
        "source": str(result.get("source") or "v2-rebuild"),
    }
