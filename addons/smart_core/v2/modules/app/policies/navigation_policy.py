from __future__ import annotations

from typing import Dict


class AppNavigationPolicyV2:
    def build_route(self, *, app_key: str, target: str) -> str:
        key = str(app_key or "platform").strip() or "platform"
        slug = str(target or "home").strip() or "home"
        return f"/apps/{key}/{slug}"

    def build_active_match(self, *, app_key: str, target: str) -> Dict[str, str]:
        key = str(app_key or "platform").strip() or "platform"
        slug = str(target or "home").strip() or "home"
        return {
            "app_key": key,
            "target": slug,
            "route_prefix": f"/apps/{key}",
        }
