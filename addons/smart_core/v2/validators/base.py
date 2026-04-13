from __future__ import annotations

from typing import Any, Dict


class BaseIntentValidatorV2:
    def validate(self, intent: str, payload: Dict[str, Any], context: Dict[str, Any]) -> None:
        _ = intent
        _ = payload
        _ = context


class DefaultIntentValidatorV2(BaseIntentValidatorV2):
    def validate(self, intent: str, payload: Dict[str, Any], context: Dict[str, Any]) -> None:
        if not str(intent or "").strip():
            raise ValueError("intent is required")
        if payload is not None and not isinstance(payload, dict):
            raise ValueError("payload must be a dict")
        if context is not None and not isinstance(context, dict):
            raise ValueError("context must be a dict")
