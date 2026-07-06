# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any

from odoo.addons.smart_core.core.source_authority import build_source_authority_contract

SOURCE_KIND = "delivery_product_identity_resolver"
SOURCE_AUTHORITIES = ("request.product_key", "request.base_product_key", "request.edition_key", "platform_default")
NO_BUSINESS_FACT_AUTHORITY = True
DEFAULT_BASE_PRODUCT_KEY = "platform"
LEGACY_DEFAULT_BASE_PRODUCT_KEY = DEFAULT_BASE_PRODUCT_KEY
LEGACY_DEFAULT_BASE_SOURCE_KIND = "platform_default_base_product_projection"
DEFAULT_EDITION_KEY = "standard"
DEFAULT_OPERATOR_EDITIONS = ("standard", "preview")


def _text(value: Any) -> str:
    return str(value or "").strip()


def source_authority_contract() -> dict[str, Any]:
    return build_source_authority_contract(
        kind=SOURCE_KIND,
        authorities=SOURCE_AUTHORITIES,
        rebuildable=None,
        no_business_fact_authority=NO_BUSINESS_FACT_AUTHORITY,
        fallback_base_product_key=DEFAULT_BASE_PRODUCT_KEY,
        default_base_source=LEGACY_DEFAULT_BASE_SOURCE_KIND,
    )


def legacy_default_base_source_authority_contract() -> dict[str, Any]:
    return build_source_authority_contract(
        kind=LEGACY_DEFAULT_BASE_SOURCE_KIND,
        authorities=("LEGACY_DEFAULT_BASE_PRODUCT_KEY",),
        rebuildable=None,
        no_business_fact_authority=True,
        platform_default=True,
    )


def resolve_product_identity(
    *,
    product_key: str | None = None,
    edition_key: str | None = None,
    base_product_key: str | None = None,
    default_base_product_key: str = DEFAULT_BASE_PRODUCT_KEY,
) -> dict[str, str]:
    product = _text(product_key)
    edition = _text(edition_key) or DEFAULT_EDITION_KEY
    base = _text(base_product_key)
    source = "product_key" if product else "base_and_edition" if base or _text(edition_key) else "platform_default"
    if product:
        parts = product.split(".", 1)
        if len(parts) == 2 and parts[0] and parts[1]:
            base = parts[0]
            edition = parts[1]
        else:
            base = base or _text(default_base_product_key) or DEFAULT_BASE_PRODUCT_KEY
    else:
        base = base or _text(default_base_product_key) or DEFAULT_BASE_PRODUCT_KEY
        product = f"{base}.{edition}"
    return {
        "product_key": product,
        "base_product_key": base or DEFAULT_BASE_PRODUCT_KEY,
        "edition_key": edition or DEFAULT_EDITION_KEY,
        "source": source,
        "default_base_source_authority": legacy_default_base_source_authority_contract() if source == "platform_default" else {},
    }


def default_operator_product_keys(*, base_product_key: str | None = None) -> tuple[str, ...]:
    base = _text(base_product_key) or DEFAULT_BASE_PRODUCT_KEY
    return tuple(f"{base}.{edition}" for edition in DEFAULT_OPERATOR_EDITIONS)
