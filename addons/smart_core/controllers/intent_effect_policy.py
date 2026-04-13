# smart_core/controllers/intent_effect_policy.py
# -*- coding: utf-8 -*-

from __future__ import annotations

import re
from typing import Any, Dict


_WRITE_INTENT_RE = re.compile(
    r"(create|write|unlink|delete|batch|execute|upload|cancel|approve|reject|submit|done|import|rollback|pin|set)",
    re.IGNORECASE,
)


def is_write_intent(intent_name: str, params: Dict[str, Any]) -> bool:
    intent = str(intent_name or "").strip().lower()
    if not intent:
        return False
    if _WRITE_INTENT_RE.search(intent):
        return True
    if intent == "api.data":
        op = str((params or {}).get("op") or "").strip().lower()
        return op in {"create", "write", "unlink", "delete", "batch"}
    return False


def should_commit_write_effect(
    *,
    normalized: Any,
    status: int,
    intent_name: str,
    params: Dict[str, Any],
) -> bool:
    return (
        isinstance(normalized, dict)
        and status < 400
        and bool(normalized.get("ok", True))
        and is_write_intent(intent_name, params)
    )
