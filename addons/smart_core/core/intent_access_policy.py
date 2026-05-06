# -*- coding: utf-8 -*-


ANONYMOUS_INTENTS = frozenset({"login", "auth.login", "sys.intents", "session.bootstrap"})
PUBLIC_CONTEXT_INTENTS = ANONYMOUS_INTENTS | frozenset({"bootstrap", "permission.check"})


def normalize_intent_name(intent_name: str) -> str:
    return str(intent_name or "").strip()


def is_anonymous_allowed_intent(intent_name: str) -> bool:
    return normalize_intent_name(intent_name) in ANONYMOUS_INTENTS


def is_public_context_intent(intent_name: str) -> bool:
    return normalize_intent_name(intent_name) in PUBLIC_CONTEXT_INTENTS
