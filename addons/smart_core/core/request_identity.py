# -*- coding: utf-8 -*-
from typing import Any


def identity_id(identity: Any, default: int | None = None) -> int | None:
    raw = getattr(identity, "id", identity)
    try:
        value = int(raw)
    except Exception:
        return default
    return value if value > 0 else default


def request_uid(request_obj: Any, default: int | None = None) -> int | None:
    uid = identity_id(getattr(request_obj, "uid", None), default=None)
    if uid:
        return uid
    env = getattr(request_obj, "env", None)
    return identity_id(getattr(env, "uid", None), default=default)
