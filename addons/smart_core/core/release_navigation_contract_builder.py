# -*- coding: utf-8 -*-
from __future__ import annotations

import zlib

from .source_authority import build_source_authority_contract

SOURCE_KIND = "release_navigation_projection"
SOURCE_AUTHORITIES = ("delivery_engine_v1", "legacy_release_navigation_fallback")
NO_BUSINESS_FACT_AUTHORITY = True
LEGACY_FALLBACK_SOURCE_KIND = "legacy_release_navigation_fallback"
_LEGACY_RELEASE_NAVIGATION_LEAVES: list[dict] = []


def source_authority_contract() -> dict:
    return build_source_authority_contract(
        kind=SOURCE_KIND,
        authorities=SOURCE_AUTHORITIES,
        rebuildable=None,
        no_business_fact_authority=NO_BUSINESS_FACT_AUTHORITY,
        legacy_fallback=LEGACY_FALLBACK_SOURCE_KIND,
    )


def legacy_fallback_source_authority_contract() -> dict:
    return build_source_authority_contract(
        kind=LEGACY_FALLBACK_SOURCE_KIND,
        authorities=("compatibility_release_navigation_defaults",),
        rebuildable=None,
        no_business_fact_authority=True,
        legacy_compatibility=True,
    )


def _synthetic_menu_id(key: str, base: int = 900_000_000, span: int = 50_000_000) -> int:
    raw = zlib.crc32(str(key or "").encode("utf-8")) & 0xFFFFFFFF
    return int(base + (raw % span))


def _leaf(
    *,
    key: str,
    label: str,
    route: str,
    scene_key: str | None = None,
    product_key: str | None = None,
    legacy_fallback: bool = False,
) -> dict:
    menu_id = _synthetic_menu_id(key)
    meta = {
        "route": route,
        "action_type": "release.navigation",
        "menu_xmlid": f"release.navigation.{key.replace('.', '_')}",
    }
    if scene_key:
        meta["scene_key"] = scene_key
    if product_key:
        meta["product_key"] = product_key
    if legacy_fallback:
        meta["source_authority"] = legacy_fallback_source_authority_contract()
        meta["legacy_compatibility"] = True
    return {
        "key": key,
        "label": label,
        "title": label,
        "menu_id": menu_id,
        "children": [],
        "meta": meta,
    }


def register_legacy_release_navigation_leaf(
    *,
    key: str,
    label: str,
    route: str,
    scene_key: str | None = None,
    product_key: str | None = None,
    visible_roles: tuple[str, ...] | list[str] | None = None,
) -> None:
    leaf_key = str(key or "").strip()
    leaf_label = str(label or "").strip()
    leaf_route = str(route or "").strip()
    if not leaf_key or not leaf_label or not leaf_route:
        return
    roles = tuple(str(role or "").strip().lower() for role in (visible_roles or ()) if str(role or "").strip())
    row = {
        "key": leaf_key,
        "label": leaf_label,
        "route": leaf_route,
        "scene_key": str(scene_key or "").strip(),
        "product_key": str(product_key or "").strip(),
        "visible_roles": roles,
    }
    for index, item in enumerate(_LEGACY_RELEASE_NAVIGATION_LEAVES):
        if item.get("key") == leaf_key:
            _LEGACY_RELEASE_NAVIGATION_LEAVES[index] = row
            return
    _LEGACY_RELEASE_NAVIGATION_LEAVES.append(row)


def _registered_product_children(role_code: str) -> list[dict]:
    role = str(role_code or "").strip().lower()
    rows: list[dict] = []
    for item in _LEGACY_RELEASE_NAVIGATION_LEAVES:
        roles = item.get("visible_roles") or ()
        if roles and role not in roles:
            continue
        rows.append(
            _leaf(
                key=item.get("key") or "",
                label=item.get("label") or "",
                route=item.get("route") or "",
                scene_key=item.get("scene_key") or None,
                product_key=item.get("product_key") or None,
                legacy_fallback=True,
            )
        )
    return rows


def build_release_navigation_contract(data: dict) -> dict:
    payload = data if isinstance(data, dict) else {}
    delivery_payload = payload.get("delivery_engine_v1") if isinstance(payload.get("delivery_engine_v1"), dict) else {}
    if isinstance(delivery_payload.get("nav"), list):
        return {
            "contract_version": str(delivery_payload.get("contract_version") or "v1"),
            "source": "delivery_engine_v1",
            "source_authority": source_authority_contract(),
            "role_code": str(delivery_payload.get("role_code") or ""),
            "nav": delivery_payload.get("nav") or [],
            "meta": {
                "product_key": str(delivery_payload.get("product_key") or ""),
                "edition_key": str(delivery_payload.get("edition_key") or ""),
                "source": "delivery_engine_v1",
                "fallback_used": False,
            },
        }
    role_surface = data.get("role_surface") if isinstance(data.get("role_surface"), dict) else {}
    role_code = str(role_surface.get("role_code") or "").strip().lower()

    product_children = _registered_product_children(role_code)

    utility_children = [
        _leaf(
            key="release.my_work",
            label="我的工作",
            route="/my-work",
            scene_key="my_work.workspace",
            product_key="my_work",
            legacy_fallback=True,
        ),
    ]

    nav = [
        {
            "key": "root:release_navigation",
            "label": "产品发布面",
            "title": "产品发布面",
            "menu_id": _synthetic_menu_id("root:release_navigation", base=880_000_000, span=10_000_000),
            "children": [
                {
                    "key": "group:released_products",
                    "label": "已发布产品",
                    "title": "已发布产品",
                    "menu_id": _synthetic_menu_id("group:released_products", base=881_000_000, span=10_000_000),
                    "children": product_children,
                    "meta": {"group_key": "released_products", "source": "release_navigation_v1"},
                },
                {
                    "key": "group:released_utilities",
                    "label": "工作辅助",
                    "title": "工作辅助",
                    "menu_id": _synthetic_menu_id("group:released_utilities", base=882_000_000, span=10_000_000),
                    "children": utility_children,
                    "meta": {"group_key": "released_utilities", "source": "release_navigation_v1"},
                },
            ],
            "meta": {
                "source": "release_navigation_v1",
                "role_code": role_code,
            },
        }
    ]

    return {
        "contract_version": "v1",
        "source": "legacy_release_navigation_v1",
        "source_authority": source_authority_contract(),
        "role_code": role_code,
        "nav": nav,
        "meta": {
            "product_keys": [str((leaf.get("meta") or {}).get("product_key") or "") for leaf in product_children if (leaf.get("meta") or {}).get("product_key")],
            "group_count": 2,
            "leaf_count": len(product_children) + len(utility_children),
            "source": "legacy_release_navigation_v1",
            "fallback_used": True,
            "fallback_source_authority": legacy_fallback_source_authority_contract(),
        },
    }
