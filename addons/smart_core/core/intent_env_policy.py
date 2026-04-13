# -*- coding: utf-8 -*-
# smart_core/core/intent_env_policy.py

from __future__ import annotations

import logging
from typing import Any, Dict, Tuple

import odoo
from odoo import SUPERUSER_ID, api
from odoo.http import request

_logger = logging.getLogger(__name__)


def build_dispatch_envs(params: Dict[str, Any], add_ctx: Dict[str, Any]) -> Tuple[api.Environment, api.Environment, Any]:
    """
    返回 (env, su_env, extra_cursor)
    - 切库时打开 extra cursor，调用方负责 finalize。
    - 不切库时 extra_cursor 为 None。
    """
    target_db = (params or {}).get("db") or request.env.cr.dbname
    cur_db = request.env.cr.dbname

    _logger.info("[intent_router][debug] _build_envs target_db: %s", target_db)
    _logger.info("[intent_router][debug] _build_envs cur_db: %s", cur_db)
    _logger.info("[intent_router][debug] _build_envs request.env.cr.dbname: %s", request.env.cr.dbname)

    base_ctx = dict(request.env.context or {})
    if add_ctx:
        base_ctx.update(add_ctx)

    if target_db == cur_db:
        env = request.env(context=base_ctx)
        su_env = api.Environment(env.cr, SUPERUSER_ID, dict(env.context))
        return env, su_env, None

    registry = odoo.registry(target_db)
    try:
        registry.check_signaling()
    except Exception:
        pass

    cursor = registry.cursor()
    try:
        env = api.Environment(cursor, request.uid, base_ctx)
        su_env = api.Environment(cursor, SUPERUSER_ID, dict(env.context))
        return env, su_env, cursor
    except Exception:
        cursor.close()
        raise


def finalize_dispatch_cursor(*, extra_cursor: Any, dispatch_succeeded: bool, intent: str, dbname: str) -> None:
    if extra_cursor is None:
        return

    try:
        if dispatch_succeeded:
            _logger.info("[intent_router] commit extra cursor intent=%s db=%s", intent, dbname)
            extra_cursor.commit()
        extra_cursor.close()
    except Exception:
        _logger.exception("[intent] close cursor failed (db=%s)", dbname)
