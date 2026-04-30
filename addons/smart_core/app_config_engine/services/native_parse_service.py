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
            # Keep the parser in the request user's environment. Odoo applies
            # group-based view pruning while composing inherited views; using
            # sudo here can produce a different form from the native client.
            parsed_json = self.owner.env["app.view.parser"].parse_odoo_view(model_name, view_type)
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
