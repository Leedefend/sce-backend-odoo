from __future__ import annotations

from typing import Any, Dict, List

from ..policies.navigation_policy import AppNavigationPolicyV2
from ..policies.availability_policy import AppAvailabilityPolicyV2


class AppCatalogServiceV2:
    def __init__(self) -> None:
        self._policy = AppNavigationPolicyV2()
        self._availability_policy = AppAvailabilityPolicyV2()

    def _status(self, *, app_key: str, target: str) -> Dict[str, str]:
        availability_status, reason_code = self._availability_policy.classify(app_key=app_key, target=target)
        return {
            "availability_status": availability_status,
            "reason_code": reason_code,
            "is_clickable": availability_status != "unavailable",
        }

    def list_apps(self) -> Dict[str, Any]:
        apps: List[Dict[str, Any]] = [
            {
                "app_key": "platform",
                "name": "Platform",
                "active": True,
                "target_type": "app",
                "delivery_mode": "custom_app",
                **self._status(app_key="platform", target="home"),
                "route": self._policy.build_route(app_key="platform", target="home"),
                "active_match": self._policy.build_active_match(app_key="platform", target="home"),
            },
            {
                "app_key": "workspace",
                "name": "Workspace",
                "active": True,
                "target_type": "app",
                "delivery_mode": "custom_app",
                **self._status(app_key="workspace", target="home"),
                "route": self._policy.build_route(app_key="workspace", target="home"),
                "active_match": self._policy.build_active_match(app_key="workspace", target="home"),
            },
        ]
        return {
            "apps": apps,
            "count": len(apps),
            "version": "v2",
            "source": "v2-rebuild",
        }

    def build_app_nav(self, app_key: str) -> Dict[str, Any]:
        key = str(app_key or "platform").strip() or "platform"
        nodes = [
            {
                "node_key": f"{key}.home",
                "name": "Home",
                "target_type": "nav",
                "delivery_mode": "custom_nav",
                **self._status(app_key=key, target="home"),
                "route": self._policy.build_route(app_key=key, target="home"),
                "active_match": self._policy.build_active_match(app_key=key, target="home"),
            },
            {
                "node_key": f"{key}.work",
                "name": "Work",
                "target_type": "nav",
                "delivery_mode": "custom_nav",
                **self._status(app_key=key, target="work"),
                "route": self._policy.build_route(app_key=key, target="work"),
                "active_match": self._policy.build_active_match(app_key=key, target="work"),
            },
        ]
        return {
            "app_key": key,
            "nodes": nodes,
            "count": len(nodes),
            "version": "v2",
            "source": "v2-rebuild",
        }

    def build_app_open(self, app_key: str) -> Dict[str, Any]:
        key = str(app_key or "platform").strip() or "platform"
        return {
            "app_key": key,
            "open_url": self._policy.build_route(app_key=key, target="home"),
            "open_mode": "internal",
            "target_type": "open",
            "delivery_mode": "custom_open",
            **self._status(app_key=key, target="home"),
            "active_match": self._policy.build_active_match(app_key=key, target="home"),
            "version": "v2",
            "source": "v2-rebuild",
        }
