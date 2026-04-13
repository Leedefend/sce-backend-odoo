from __future__ import annotations

from typing import Dict, Tuple

from ..reason_codes import (
    APP_REASON_APP_KEY_MISSING,
    APP_REASON_OK,
    APP_REASON_WORKSPACE_WORK_PARTIAL,
)


class AppAvailabilityPolicyV2:
    def classify(self, *, app_key: str, target: str) -> Tuple[str, str]:
        key = str(app_key or "").strip().lower()
        tgt = str(target or "").strip().lower()
        if not key:
            return "unavailable", APP_REASON_APP_KEY_MISSING
        if key == "workspace" and tgt == "work":
            return "degraded", APP_REASON_WORKSPACE_WORK_PARTIAL
        return "available", APP_REASON_OK
