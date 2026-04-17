# -*- coding: utf-8 -*-
"""Native parse orchestration service.

This service only decides how to obtain parser-native structure and does not
apply runtime governance filtering.
"""

from __future__ import annotations

import logging
from typing import Any


_logger = logging.getLogger(__name__)


class NativeParseService:
    """Parse path coordinator for parser-native output."""

    def __init__(self, owner):
        self.owner = owner

    def parse_with_primary_parser(self, model_name: str, view_type: str, *, force_fallback: bool = False) -> Any:
        """Try parser-native extraction and return raw parsed payload."""
        parsed_json = None
        model_exists = self.owner._model_exists("app.view.parser")
        _logger.info("VIEW_PARSE_DEBUG: app.view.parser model_exists=%s", model_exists)
        if force_fallback or not model_exists:
            return None
        try:
            parsed_json = self.owner.env["app.view.parser"].sudo().parse_odoo_view(model_name, view_type)
            if self.owner._looks_like_parser_wrapper(parsed_json):
                _logger.info("VIEW_PARSE_DEBUG: unwrap parser wrapper → %s.%s", model_name, view_type)
                parsed_json = self.owner._unwrap_contract_shape(view_type, parsed_json)
            _logger.info(
                "VIEW_PARSE_DEBUG: parser_success=%s keys=%s",
                bool(parsed_json),
                list((parsed_json or {}).keys()),
            )
        except Exception as exc:
            _logger.exception("app.view.parser 解析失败，进入降级：%s.%s, error=%s", model_name, view_type, exc)
        return parsed_json

    def parse_view_data_with_primary_parser(self, model_name: str, view_type: str, view_data: dict, *, force_fallback: bool = False) -> Any:
        """Parse an already-selected Odoo view payload with the native parser."""
        if force_fallback or not isinstance(view_data, dict):
            return None
        model_exists = self.owner._model_exists("app.view.parser")
        _logger.info("VIEW_PARSE_DEBUG: app.view.parser model_exists=%s selected_view_data=True", model_exists)
        if not model_exists:
            return None
        try:
            parser = self.owner.env["app.view.parser"].sudo()
            arch = view_data.get("arch") or ""
            fields_info = view_data.get("fields") or {}
            toolbar_raw = view_data.get("toolbar") or {}
            base = {
                "modifiers": parser._collect_modifiers(arch),
                "search": {
                    "filters": [],
                    "group_by": [],
                    "facets": {"enabled": True},
                },
                "toolbar": parser._normalize_toolbar(toolbar_raw),
                "order": getattr(self.owner.env[model_name], "_order", "id desc") or "id desc",
            }
            if view_type == "form":
                base.update(parser._parse_form_view(arch, fields_info, model_name))
                return base
            if view_type == "tree":
                tree_block = parser._parse_tree_view(arch, fields_info)
                if tree_block.get("default_order"):
                    base["order"] = tree_block["default_order"]
                base.update(tree_block)
                return base
        except Exception as exc:
            _logger.exception(
                "selected view parser failed, fallback may be used: %s.%s, error=%s",
                model_name,
                view_type,
                exc,
            )
        return None
