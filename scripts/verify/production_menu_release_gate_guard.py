# -*- coding: utf-8 -*-
from __future__ import annotations

import json

from odoo.addons.smart_core.delivery.delivery_engine import DeliveryEngine
from odoo.addons.smart_core.handlers.system_init import (
    _filter_nav_by_release_gate,
    _load_platform_release_gate,
)
from odoo.addons.smart_core.utils.extension_hooks import call_extension_hook_first


PRODUCT_KEYS = ("construction.standard", "construction.preview")
EXPECTED_BASE_PRODUCT_KEY = "construction"
EXPECTED_PLATFORM_RELEASE_DB_MATCH_CURRENT = True
MIN_RELEASED_POLICY_MENU_COUNT = 1
FORBIDDEN_RUNTIME_LABEL_TOKENS = ("用户核对菜单",)


def _text(value):
    return str(value or "").strip()


def _node_label(node: dict) -> str:
    return _text(node.get("label") or node.get("name") or node.get("title"))


def _walk(nodes, path=()):
    for node in nodes if isinstance(nodes, list) else []:
        if not isinstance(node, dict):
            continue
        current = path + (_node_label(node),)
        yield current, node
        yield from _walk(node.get("children"), current)


def _released_policy_menu_count(product_key: str) -> int:
    policy = env["sc.product.policy"].sudo().search([("product_key", "=", product_key)], limit=1)  # noqa: F821
    if not policy:
        raise AssertionError(f"missing product policy: {product_key}")
    if not policy.active or policy.access_level != "public":
        raise AssertionError(f"{product_key} policy must be active public")
    count = 0
    for group in policy.menu_groups or []:
        if not isinstance(group, dict):
            continue
        for menu in group.get("menus") or []:
            if not isinstance(menu, dict):
                continue
            if menu.get("enabled") and _text(menu.get("release_state")) == "released":
                count += 1
    if count < MIN_RELEASED_POLICY_MENU_COUNT:
        raise AssertionError(f"{product_key} has no released product menus")
    return count


def _active_snapshot(product_key: str):
    return env["sc.edition.release.snapshot"].sudo().search(  # noqa: F821
        [
            ("product_key", "=", product_key),
            ("state", "=", "released"),
            ("is_active", "=", True),
            ("active", "=", True),
        ],
        order="released_at desc, activated_at desc, id desc",
        limit=1,
    )


def _snapshot_page_count(snapshot) -> int:
    meta = snapshot.meta_json if snapshot and isinstance(snapshot.meta_json, dict) else {}
    draft = meta.get("release_draft") if isinstance(meta.get("release_draft"), dict) else {}
    return int(draft.get("page_count") or 0)


def _assert_startup_identity() -> dict:
    identity = call_extension_hook_first(env, "smart_core_resolve_startup_delivery_identity", env, {})  # noqa: F821
    if not isinstance(identity, dict):
        raise AssertionError("startup delivery identity hook did not return a dict")
    if _text(identity.get("product_key")) != "construction.standard":
        raise AssertionError(f"startup product_key drift: {identity!r}")
    if _text(identity.get("base_product_key")) != EXPECTED_BASE_PRODUCT_KEY:
        raise AssertionError(f"startup base_product_key drift: {identity!r}")
    if _text(identity.get("edition_key")) != "standard":
        raise AssertionError(f"startup edition_key drift: {identity!r}")
    return identity


def _assert_platform_release_db() -> str:
    configured = _text(env["ir.config_parameter"].sudo().get_param("smart_core.platform_release_db", ""))  # noqa: F821
    current_db = _text(env.cr.dbname)  # noqa: F821
    if not configured:
        raise AssertionError("smart_core.platform_release_db is empty")
    if EXPECTED_PLATFORM_RELEASE_DB_MATCH_CURRENT and configured != current_db:
        raise AssertionError(f"smart_core.platform_release_db must be {current_db}, got {configured}")
    return configured


def _assert_runtime_gate(product_key: str, released_policy_count: int) -> dict:
    snapshot = _active_snapshot(product_key)
    if not snapshot:
        raise AssertionError(f"{product_key} active released snapshot not found")
    snapshot_page_count = _snapshot_page_count(snapshot)
    if snapshot_page_count != released_policy_count:
        raise AssertionError(
            f"{product_key} snapshot page_count drift: snapshot={snapshot_page_count} policy={released_policy_count}"
        )
    gate = _load_platform_release_gate(env, product_key=product_key)  # noqa: F821
    if not gate.get("applied"):
        raise AssertionError(f"{product_key} release gate not applied: {gate!r}")
    if int(gate.get("snapshot_id") or 0) != int(snapshot.id):
        raise AssertionError(f"{product_key} release gate snapshot drift: {gate!r} active={snapshot.id}")
    if int(gate.get("page_count") or 0) != released_policy_count:
        raise AssertionError(f"{product_key} release gate page_count drift: {gate!r}")
    delivery = DeliveryEngine(env).build(  # noqa: F821
        data={"role_surface": {"role_code": "business_config_admin"}, "scenes": [], "capabilities": []},
        product_key=product_key,
        edition_key="standard" if product_key.endswith(".standard") else "preview",
        base_product_key=EXPECTED_BASE_PRODUCT_KEY,
    )
    raw_nav = delivery.get("nav") if isinstance(delivery.get("nav"), list) else []
    gated_nav, gate_meta = _filter_nav_by_release_gate(raw_nav, gate, env=env)  # noqa: F821
    paths = [" / ".join(part for part in path if part) for path, _node in _walk(gated_nav)]
    forbidden_paths = [
        path for path in paths
        if any(token in path for token in FORBIDDEN_RUNTIME_LABEL_TOKENS)
    ]
    if forbidden_paths:
        raise AssertionError(f"{product_key} forbidden runtime menu paths: {forbidden_paths[:20]}")
    if not gated_nav:
        raise AssertionError(f"{product_key} gated runtime nav is empty")
    return {
        "product_key": product_key,
        "snapshot_id": int(snapshot.id),
        "snapshot_version": _text(snapshot.version),
        "policy_released_menu_count": released_policy_count,
        "gate_page_count": int(gate.get("page_count") or 0),
        "raw_nav_node_count": sum(1 for _path, _node in _walk(raw_nav)),
        "gated_nav_node_count": sum(1 for _path, _node in _walk(gated_nav)),
        "gate_meta": gate_meta,
    }


def main():
    identity = _assert_startup_identity()
    platform_release_db = _assert_platform_release_db()
    products = []
    for product_key in PRODUCT_KEYS:
        products.append(_assert_runtime_gate(product_key, _released_policy_menu_count(product_key)))
    print(
        json.dumps(
            {
                "status": "PASS",
                "db": env.cr.dbname,  # noqa: F821
                "startup_identity": identity,
                "smart_core.platform_release_db": platform_release_db,
                "products": products,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


main()
