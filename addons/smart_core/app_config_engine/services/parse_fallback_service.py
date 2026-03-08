# -*- coding: utf-8 -*-
"""Fallback parse service.

This service handles parser/fallback switch only and keeps compatibility by
delegating concrete fallback parsing to AppViewConfig.
"""

from __future__ import annotations

import logging
from typing import Any


_logger = logging.getLogger(__name__)


class ParseFallbackService:
    """Parser fallback coordinator."""

    def __init__(self, owner):
        self.owner = owner

    def resolve_parsed_contract(
        self,
        *,
        model_name: str,
        view_type: str,
        view_data: dict,
        parsed_json: Any,
        force_fallback: bool = False,
    ) -> dict:
        """Choose parser-native result or fallback parse result."""
        parsed_ok = self.owner._parsed_ok(view_type, parsed_json)
        _logger.info("VIEW_PARSE_DEBUG: force_fallback=%s, parsed_ok=%s", force_fallback, parsed_ok)
        if force_fallback or not parsed_ok:
            _logger.info("VIEW_PARSE_DEBUG: 使用 Fallback 解析 → %s.%s", model_name, view_type)
            return self.owner._fallback_parse(model_name, view_type, view_data)
        _logger.info("VIEW_PARSE_DEBUG: using app.view.parser for %s.%s", model_name, view_type)
        return parsed_json if isinstance(parsed_json, dict) else {}

