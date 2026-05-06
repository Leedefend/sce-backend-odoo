# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict

from .source_authority import build_source_authority_contract

SOURCE_KIND = "delivery_capability_entry_default_projection"
SOURCE_AUTHORITIES = ("delivery_engine_v1", "runtime_capability_payload")
NO_BUSINESS_FACT_AUTHORITY = True


def source_authority_contract() -> dict:
    return build_source_authority_contract(
        kind=SOURCE_KIND,
        authorities=SOURCE_AUTHORITIES,
        no_business_fact_authority=NO_BUSINESS_FACT_AUTHORITY,
        capability_entry_default_only=True,
    )


def to_text(value: Any) -> str:
    return str(value or "").strip()


def build_delivery_capability_entry(row: Dict[str, Any], runtime: Dict[str, Any]) -> Dict[str, Any]:
    key = to_text(row.get("capability_key") or row.get("key"))
    payload = {
        "key": key,
        "label": to_text(row.get("label") or runtime.get("ui_label") or runtime.get("name") or key),
        "group_key": to_text(row.get("group_key") or runtime.get("group_key") or "delivery"),
        "group_label": to_text(row.get("group_label") or runtime.get("group_label") or "产品交付"),
        "product_key": to_text(row.get("product_key")),
        "target_scene_key": to_text(row.get("target_scene_key") or runtime.get("target_scene_key")),
        "delivery_level": to_text(row.get("delivery_level") or "exclusive"),
        "entry_kind": to_text(row.get("entry_kind") or "exclusive"),
        "runtime_capability_key": to_text(runtime.get("key")),
        "runtime_state": to_text(runtime.get("state")) or "POLICY_READY",
        "runtime_reason_code": to_text(runtime.get("reason_code")),
        "source": "delivery_engine_v1",
        "default_source_authority": source_authority_contract(),
    }
    source_authority = row.get("source_authority")
    if isinstance(source_authority, dict) and source_authority:
        payload["source_authority"] = source_authority
    runtime_source_authority = runtime.get("source_authority")
    if isinstance(runtime_source_authority, dict) and runtime_source_authority:
        payload["runtime_source_authority"] = runtime_source_authority
    return payload
