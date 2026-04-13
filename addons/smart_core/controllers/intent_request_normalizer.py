# smart_core/controllers/intent_request_normalizer.py
# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Any, Dict, Tuple


_CONTEXT_PARAM_KEYS = ("db", "database", "login", "username", "password", "lang", "tz", "company_id")


def normalize_dispatch_payload(body: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    params = body.get("params") if isinstance(body.get("params"), dict) else {}
    if not params and isinstance(body.get("payload"), dict):
        params = body.get("payload")

    context_in: Dict[str, Any] = body.get("context") if isinstance(body.get("context"), dict) else {}
    for key in _CONTEXT_PARAM_KEYS:
        if key in context_in and key not in params:
            params[key] = context_in[key]

    return {
        "params": params,
        "context": context_in,
    }


def _is_local_request(remote_addr: str | None, host: str | None) -> bool:
    remote = str(remote_addr or "")
    host_name = str(host or "")
    if remote in {"127.0.0.1", "::1"}:
        return True
    return "localhost" in host_name or "127.0.0.1" in host_name


def _is_dev_env(env_name: str | None, remote_addr: str | None, host: str | None) -> bool:
    env = str(env_name or "").strip().lower()
    if env in {"dev", "test", "local"}:
        return True
    if not env and _is_local_request(remote_addr, host):
        return True
    return False


def resolve_effective_db(
    *,
    params: Dict[str, Any],
    kwargs: Dict[str, Any],
    x_db_header: str | None,
    session_db: str | None,
    env_db: str | None,
    remote_addr: str | None,
    host: str | None,
    is_admin: bool,
    env_name: str | None,
) -> Tuple[str | None, str]:
    effective_db = None
    db_source = "unknown"

    if params.get("db"):
        effective_db = params.get("db")
        db_source = "params"
    elif kwargs.get("db"):
        effective_db = kwargs.get("db")
        db_source = "query"
    elif x_db_header:
        effective_db = x_db_header
        db_source = "header"
    elif session_db:
        effective_db = session_db
        db_source = "session"

    if effective_db and db_source in {"params", "query", "header"} and not _is_dev_env(env_name, remote_addr, host) and not is_admin:
        effective_db = env_db

    if not effective_db:
        effective_db = env_db

    return effective_db, db_source
