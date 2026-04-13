from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class IntentExecutionResultV2:
    ok: bool = True
    data: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    code: int = 200
    effect: Optional[Dict[str, Any]] = None
    meta: Dict[str, Any] = field(default_factory=dict)

    def to_envelope_payload(self) -> Dict[str, Any]:
        return {
            "ok": bool(self.ok),
            "data": self.data,
            "error": self.error,
            "effect": self.effect,
            "code": int(self.code),
            "meta": dict(self.meta or {}),
        }
