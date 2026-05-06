# -*- coding: utf-8 -*-
"""Lite preview envelope helpers.

This module is intentionally side-effect free so opt-in behavior can be
verified without importing Odoo handlers or touching runtime delivery.
"""

from __future__ import annotations

from typing import Any, Dict

from .source_authority import build_source_authority_contract
from .unified_page_contract_lite_adapter import build_lite_contract, build_lite_patch
from .unified_page_contract_lite_patch_normalizer import normalize_lite_patch_source
from .unified_page_contract_lite_source_normalizer import normalize_lite_contract_source


SUPPORTED_LITE_PREVIEW_CLIENT_TYPES = ("web_pc", "wx_mini", "harmony_h5")
SOURCE_KIND = "unified_page_contract_lite_preview_projection"
SOURCE_AUTHORITIES = ("legacy_response", "lite_contract_projection", "lite_patch_projection")
NO_BUSINESS_FACT_AUTHORITY = True


def source_authority_contract() -> Dict[str, Any]:
    return build_source_authority_contract(
        kind=SOURCE_KIND,
        authorities=SOURCE_AUTHORITIES,
        no_business_fact_authority=NO_BUSINESS_FACT_AUTHORITY,
        runtime_carrier="unified_page_contract_lite_preview",
    )

LITE_PREVIEW_CONTRACT_MODE = "lite_preview"
LITE_PREVIEW_CONTRACT_VERSION = "2.0.0"
LITE_PREVIEW_FALLBACK_MODE = "legacy_default"


def is_lite_preview_request(params: Dict[str, Any], entry_point: str) -> bool:
    return (
        params.get("contractMode") == LITE_PREVIEW_CONTRACT_MODE
        and params.get("contractVersion") == LITE_PREVIEW_CONTRACT_VERSION
        and params.get("entryPoint") == entry_point
        and params.get("clientType") in SUPPORTED_LITE_PREVIEW_CLIENT_TYPES
        and params.get("fallbackMode", LITE_PREVIEW_FALLBACK_MODE) == LITE_PREVIEW_FALLBACK_MODE
    )


def build_lite_preview_envelope(
    legacy_data: Dict[str, Any],
    params: Dict[str, Any],
    entry_point: str,
    *,
    payload_type: str = "lite_patch",
) -> Dict[str, Any]:
    if payload_type == "lite_contract":
        normalized_contract_source = normalize_lite_contract_source(legacy_data)
        payload = build_lite_contract(
            normalized_contract_source,
            client_type=str(params.get("clientType") or "web_pc"),
            trace_id=str(params.get("traceId") or ""),
        )
    else:
        payload_type = "lite_patch"
        normalized_patch_source = normalize_lite_patch_source(legacy_data)
        payload = build_lite_patch(normalized_patch_source)
    return {
        "contractMode": LITE_PREVIEW_CONTRACT_MODE,
        "contractVersion": LITE_PREVIEW_CONTRACT_VERSION,
        "entryPoint": entry_point,
        "payloadType": payload_type,
        "fallbackMode": LITE_PREVIEW_FALLBACK_MODE,
        "payload": payload,
        "meta": {
            "previewOnly": True,
            "defaultUnchanged": True,
            "traceId": str(params.get("traceId") or ""),
        },
    }


def with_lite_preview_if_requested(
    response: Dict[str, Any],
    params: Dict[str, Any],
    entry_point: str,
    *,
    payload_type: str = "lite_patch",
) -> Dict[str, Any]:
    if not is_lite_preview_request(params, entry_point):
        return response
    if not isinstance(response.get("data"), dict):
        return response
    out = dict(response)
    out["lite_preview"] = build_lite_preview_envelope(
        response.get("data") or {},
        params,
        entry_point,
        payload_type=payload_type,
    )
    return out
