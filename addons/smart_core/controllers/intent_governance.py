# smart_core/controllers/intent_governance.py
# -*- coding: utf-8 -*-

from __future__ import annotations

INTENT_ALIASES = {
    "bootstrap": "session.bootstrap",
    "app.init": "system.init",
    "system.init": "system.init",
    "auth.login": "login",
}

INTENT_REQUEST_SCHEMA_MAP = {
    "login": "auth.login.v1",
    "session.bootstrap": "session.bootstrap.v1",
    "system.init": "system.init.v1",
    "ui.contract": "ui.contract.v1",
}


def canon_intent(name: str) -> str:
    return INTENT_ALIASES.get(name or "", name or "")


def resolve_request_schema_key(intent_name: str) -> str:
    key = str(intent_name or "").strip()
    if not key:
        return "unknown.intent.v1"
    return INTENT_REQUEST_SCHEMA_MAP.get(key, f"{key}.v1")
