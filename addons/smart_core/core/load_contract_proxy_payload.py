# -*- coding: utf-8 -*-
"""Helpers for legacy handlers that proxy onto the load_contract mainline."""

from __future__ import annotations

from typing import Any, Dict


LOAD_CONTRACT_PROXY_PARAM_KEYS = (
    "model",
    "model_code",
    "menu_id",
    "action_id",
    "view_type",
    "include",
    "force_refresh",
    "version",
    "if_none_match",
    "lang",
    "tz",
    "company_id",
)


def build_load_contract_proxy_payload(params: Dict[str, Any] | None) -> Dict[str, Dict[str, Any]]:
    source = params if isinstance(params, dict) else {}
    proxied_params: Dict[str, Any] = {}
    for key in LOAD_CONTRACT_PROXY_PARAM_KEYS:
        value = source.get(key)
        if key == "include" and value in (None, "", False):
            value = "all"
        if value not in (None, "", False):
            proxied_params[key] = value

    view_id = source.get("view_id")
    if view_id not in (None, "", False):
        context = source.get("context") if isinstance(source.get("context"), dict) else {}
        proxied_context = dict(context)
        proxied_context["requested_view_id"] = view_id
        proxied_params["context"] = proxied_context

    return {"params": proxied_params}
