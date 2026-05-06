# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo.http import request


def rollback_request_env(logger=None, *, reason: str = "", trace_id: str | None = None, request_obj=None) -> bool:
    req = request_obj or request
    try:
        req.env.cr.rollback()
        return True
    except Exception:
        if logger is not None:
            logger.exception("request env rollback failed: reason=%s trace=%s", reason, trace_id)
        return False
