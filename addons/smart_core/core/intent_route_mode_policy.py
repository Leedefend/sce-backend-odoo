from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


_POLICY_PATH = Path(__file__).resolve().parents[3] / "artifacts" / "v2" / "v2_intent_route_policy_v1.json"
_ALLOWED_MODES = {"legacy_only", "v2_shadow", "v2_primary"}


def _load_policy() -> Dict[str, Any]:
    if not _POLICY_PATH.exists():
        return {
            "snapshot_id": "v2_intent_route_policy_v1",
            "schema_version": "v1",
            "default_mode": "legacy_only",
            "allowed_modes": ["legacy_only", "v2_shadow", "v2_primary"],
            "intents": {},
        }
    data = json.loads(_POLICY_PATH.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def resolve_intent_route_mode(intent: str) -> Dict[str, str]:
    policy = _load_policy()
    default_mode = str(policy.get("default_mode") or "legacy_only")
    intents = policy.get("intents") if isinstance(policy.get("intents"), dict) else {}
    configured = str(intents.get(str(intent or "").strip()) or default_mode)

    mode = configured if configured in _ALLOWED_MODES else "legacy_only"
    reason = "intent_policy_match" if str(intent or "").strip() in intents else "default_mode"

    return {
        "mode": mode,
        "reason": reason,
        "policy_version": str(policy.get("schema_version") or "v1"),
        "snapshot_id": str(policy.get("snapshot_id") or "v2_intent_route_policy_v1"),
    }
