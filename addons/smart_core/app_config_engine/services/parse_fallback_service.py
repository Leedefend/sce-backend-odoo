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
    SOURCE_KIND = "odoo_view_parse_fallback_coordinator"
    SOURCE_AUTHORITIES = ("app.view.config", "ir.ui.view", "odoo.get_view")
    NO_BUSINESS_FACT_AUTHORITY = True

    @classmethod
    def source_authority_contract(cls) -> dict:
        return {
            "kind": cls.SOURCE_KIND,
            "authorities": list(cls.SOURCE_AUTHORITIES),
            "projection_only": True,
            "rebuildable": True,
            "no_business_fact_authority": cls.NO_BUSINESS_FACT_AUTHORITY,
            "runtime_carrier": "app_config_engine.parse_fallback_service",
        }

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
        _logger.debug("VIEW_PARSE_DEBUG: force_fallback=%s, parsed_ok=%s", force_fallback, parsed_ok)
        if force_fallback or not parsed_ok:
            _logger.debug("VIEW_PARSE_DEBUG: 使用 Fallback 解析 → %s.%s", model_name, view_type)
            return self.owner._fallback_parse(model_name, view_type, view_data)
        _logger.debug("VIEW_PARSE_DEBUG: using app.view.parser for %s.%s", model_name, view_type)
        return parsed_json if isinstance(parsed_json, dict) else {}
