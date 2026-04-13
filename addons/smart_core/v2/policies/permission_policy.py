from __future__ import annotations

from typing import Any, Dict, Tuple


class PermissionPolicyV2:
    def authorize(self, *, intent: str, permission_mode: str, context: Dict[str, Any]) -> Tuple[bool, str]:
        _ = intent
        mode = str(permission_mode or "public").strip().lower()
        if mode == "public":
            return True, ""
        if mode == "authenticated":
            user_id = int(context.get("user_id") or 0)
            if user_id > 0:
                return True, ""
            return False, "AUTHENTICATION_REQUIRED"
        return False, "PERMISSION_MODE_UNSUPPORTED"
