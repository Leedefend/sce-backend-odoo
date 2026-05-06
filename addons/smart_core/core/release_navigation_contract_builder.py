# -*- coding: utf-8 -*-
from __future__ import annotations

import zlib

SOURCE_KIND = "release_navigation_projection"
SOURCE_AUTHORITIES = ("delivery_engine_v1", "legacy_release_navigation_fallback")
NO_BUSINESS_FACT_AUTHORITY = True
LEGACY_FALLBACK_SOURCE_KIND = "legacy_release_navigation_fallback"


def source_authority_contract() -> dict:
    return {
        "kind": SOURCE_KIND,
        "authorities": list(SOURCE_AUTHORITIES),
        "projection_only": True,
        "no_business_fact_authority": NO_BUSINESS_FACT_AUTHORITY,
        "legacy_fallback": LEGACY_FALLBACK_SOURCE_KIND,
    }


def legacy_fallback_source_authority_contract() -> dict:
    return {
        "kind": LEGACY_FALLBACK_SOURCE_KIND,
        "authorities": ["compatibility_release_navigation_defaults"],
        "projection_only": True,
        "no_business_fact_authority": True,
        "legacy_compatibility": True,
    }


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

    product_children = [
        _leaf(
            key="release.fr1.project_intake",
            label="FR-1 项目立项",
            route="/s/projects.intake",
            scene_key="projects.intake",
            product_key="fr1",
            legacy_fallback=True,
        ),
        _leaf(
            key="release.fr2.project_flow",
            label="FR-2 项目推进",
            route="/release/fr2",
            product_key="fr2",
            legacy_fallback=True,
        ),
        _leaf(
            key="release.fr3.cost_tracking",
            label="FR-3 成本记录",
            route="/release/fr3",
            product_key="fr3",
            legacy_fallback=True,
        ),
        _leaf(
            key="release.fr4.payment_tracking",
            label="FR-4 付款记录",
            route="/release/fr4",
            product_key="fr4",
            legacy_fallback=True,
        ),
        _leaf(
            key="release.fr5.settlement_summary",
            label="FR-5 结算结果",
            route="/release/fr5",
            product_key="fr5",
            legacy_fallback=True,
        ),
    ]

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

    if role_code not in {"pm", "owner", "executive"}:
        product_children = product_children[:1]

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
            "product_keys": ["fr1", "fr2", "fr3", "fr4", "fr5"],
            "group_count": 2,
            "leaf_count": len(product_children) + len(utility_children),
            "source": "legacy_release_navigation_v1",
            "fallback_used": True,
            "fallback_source_authority": legacy_fallback_source_authority_contract(),
        },
    }
