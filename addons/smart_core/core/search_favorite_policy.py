# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any


def client_requested_shared_favorite(params: dict[str, Any]) -> bool:
    if not isinstance(params, dict):
        return False
    return params.get("is_shared") is True


def resolve_search_favorite_shared(params: dict[str, Any]) -> bool:
    """User favorite intent must not create global ir.filters from client input."""
    return False
