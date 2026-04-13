from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

from ..modules.app.services.catalog_service import AppCatalogServiceV2


class SystemService:
    def __init__(self) -> None:
        self._app_service = AppCatalogServiceV2()

    def ping(self, payload: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        _ = payload
        _ = context
        return {
            "pong": True,
            "server_time": datetime.now(timezone.utc).isoformat(),
            "version": "v2",
        }

    def list_registered_intents(self, registry_snapshot: tuple[str, ...]) -> Dict[str, Any]:
        intents = list(registry_snapshot)
        return {
            "intents": intents,
            "count": len(intents),
            "version": "v2",
        }

    def build_system_init(self, payload: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        app_key = str((payload or {}).get("app_key") or "platform").strip() or "platform"
        catalog = self._app_service.list_apps()
        nav = self._app_service.build_app_nav(app_key)
        open_payload = self._app_service.build_app_open(app_key)
        return {
            "identity": {
                "user_id": int((context or {}).get("user_id") or 0),
                "company_id": int((context or {}).get("company_id") or 0),
            },
            "catalog": catalog,
            "nav": nav,
            "open": open_payload,
            "registry": {
                "count": len((context or {}).get("registry_snapshot") or ()),
            },
            "version": "v2",
            "source": "v2-rebuild",
        }

    def build_system_init_inspect(self, payload: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        system_init_payload = self.build_system_init(payload, context)
        catalog = system_init_payload.get("catalog") if isinstance(system_init_payload.get("catalog"), dict) else {}
        nav = system_init_payload.get("nav") if isinstance(system_init_payload.get("nav"), dict) else {}
        open_payload = system_init_payload.get("open") if isinstance(system_init_payload.get("open"), dict) else {}
        registry = system_init_payload.get("registry") if isinstance(system_init_payload.get("registry"), dict) else {}

        app_count = int(catalog.get("count") or 0)
        nav_count = int(nav.get("count") or 0)
        open_url = str(open_payload.get("open_url") or "")
        registry_count = int(registry.get("count") or 0)

        health = "ok"
        if app_count <= 0 or nav_count <= 0 or not open_url:
            health = "degraded"

        return {
            "bootstrap": system_init_payload,
            "bootstrap_summary": {
                "app_count": app_count,
                "nav_count": nav_count,
                "open_url": open_url,
            },
            "registry_summary": {
                "intent_count": registry_count,
            },
            "health": health,
            "version": "v2",
            "source": "v2-rebuild",
        }
