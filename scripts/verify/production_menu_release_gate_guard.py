# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path

from odoo.addons.smart_core.delivery.delivery_engine import DeliveryEngine
from odoo.addons.smart_core.handlers.menu_configuration import (
    MenuConfigurationAuditHandler,
    MenuConfigurationLoadHandler,
)
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
FORBIDDEN_POLICY_PATH_TOKENS = ("用户核对菜单", "旧业务数据核对", "直营项目数据核对")
BASELINE_FILE = "formal_business_product_menu_policy_v1.json"
EXPECTED_FORMAL_TOP_GROUPS = (
    "基础资料",
    "项目中心",
    "合同中心",
    "施工管理",
    "物资与分包",
    "财务中心",
    "人事行政",
    "资料证照",
    "基础设置",
    "税务中心",
)
REQUIRED_FORMAL_MENU_XMLIDS = (
    "smart_construction_core.menu_sc_customer_partner",
    "smart_construction_core.menu_sc_supplier_partner",
)
FORMAL_MENU_CONFIG_MAX_EXTRA_MENU_COUNT = 80


def _baseline_candidates() -> list[Path]:
    return [
        Path("/mnt/scripts/verify/baselines") / BASELINE_FILE,
        Path.cwd() / "scripts" / "verify" / "baselines" / BASELINE_FILE,
        Path("/home/lidefend/workspace/sce-backend-odoo/scripts/verify/baselines") / BASELINE_FILE,
    ]


def _text(value):
    return str(value or "").strip()


def _node_label(node: dict) -> str:
    return _text(node.get("label") or node.get("name") or node.get("title"))


def _node_menu_xmlid(node: dict) -> str:
    direct = _text(
        node.get("menu_xmlid")
        or node.get("xmlid")
        or node.get("menu_key")
        or node.get("page_key")
    )
    if direct:
        return direct
    meta = node.get("meta") if isinstance(node.get("meta"), dict) else {}
    return _text(
        meta.get("menu_xmlid")
        or meta.get("xmlid")
        or meta.get("menu_key")
        or meta.get("page_key")
    )


def _walk(nodes, path=()):
    for node in nodes if isinstance(nodes, list) else []:
        if not isinstance(node, dict):
            continue
        current = path + (_node_label(node),)
        yield current, node
        yield from _walk(node.get("children"), current)


def _formal_group_nodes(nav: list[dict]) -> list[dict]:
    if len(nav) == 1 and isinstance(nav[0], dict) and _node_label(nav[0]) in {"系统菜单", "智慧施工管理平台"}:
        children = nav[0].get("children")
        return children if isinstance(children, list) else []
    return nav


def _released_policy_menu_count(product_key: str) -> int:
    return len(_released_policy_menus(product_key))


def _policy_row(group_label: str, menu: dict) -> tuple[str, str, str]:
    return (
        _text(group_label),
        _text(menu.get("label") or menu.get("name")),
        _text(menu.get("menu_xmlid") or menu.get("page_key") or menu.get("menu_key")),
    )


def _load_formal_baseline() -> dict[str, list[tuple[str, str, str]]]:
    path = next((candidate for candidate in _baseline_candidates() if candidate.is_file()), None)
    if not path:
        raise AssertionError(f"missing formal product menu baseline: {BASELINE_FILE}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    products = payload.get("products") if isinstance(payload, dict) else payload
    if not isinstance(products, list):
        raise AssertionError(f"{BASELINE_FILE} products must be a list")
    out: dict[str, list[tuple[str, str, str, str]]] = {}
    for product in products:
        if not isinstance(product, dict):
            continue
        product_key = _text(product.get("product_key"))
        rows = []
        for group in product.get("menu_groups") or []:
            if not isinstance(group, dict):
                continue
            group_label = _text(group.get("group_label") or group.get("label"))
            for menu in group.get("menus") or []:
                if isinstance(menu, dict):
                    rows.append(_policy_row(group_label, menu))
        out[product_key] = rows
    return out


def _released_policy_menus(product_key: str) -> list[dict]:
    policy = env["sc.product.policy"].sudo().search([("product_key", "=", product_key)], limit=1)  # noqa: F821
    if not policy:
        raise AssertionError(f"missing product policy: {product_key}")
    if not policy.active or policy.access_level != "public":
        raise AssertionError(f"{product_key} policy must be active public")
    rows = []
    for group in policy.menu_groups or []:
        if not isinstance(group, dict):
            continue
        group_label = _text(group.get("group_label") or group.get("label") or group.get("group_key"))
        for menu in group.get("menus") or []:
            if not isinstance(menu, dict):
                continue
            if menu.get("enabled") and _text(menu.get("release_state")) == "released":
                visible_path = _text(menu.get("visible_menu_path"))
                label = _text(menu.get("label") or menu.get("name"))
                if any(token in visible_path or token in group_label or token in label for token in FORBIDDEN_POLICY_PATH_TOKENS):
                    raise AssertionError(
                        f"{product_key} product policy contains acceptance menu: {group_label} / {label} / {visible_path}"
                    )
                row = dict(menu)
                row["_group_label"] = group_label
                rows.append(row)
    if len(rows) < MIN_RELEASED_POLICY_MENU_COUNT:
        raise AssertionError(f"{product_key} has no released product menus")
    return rows


def _assert_policy_matches_formal_baseline(product_key: str, baseline: dict[str, list[tuple[str, str, str, str]]]) -> dict:
    expected = baseline.get(product_key)
    if expected is None:
        raise AssertionError(f"formal baseline missing product: {product_key}")
    rows = _released_policy_menus(product_key)
    actual = [_policy_row(_text(row.get("_group_label")), row) for row in rows]
    if actual != expected:
        expected_set = set(expected)
        actual_set = set(actual)
        raise AssertionError(
            "%s formal product menu policy drift: only_expected=%s only_actual=%s"
            % (product_key, sorted(expected_set - actual_set)[:20], sorted(actual_set - expected_set)[:20])
        )
    return {
        "baseline_menu_count": len(expected),
        "policy_released_menu_count": len(actual),
    }


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
    top_groups = [_node_label(node) for node in _formal_group_nodes(gated_nav) if isinstance(node, dict)]
    missing_groups = [label for label in EXPECTED_FORMAL_TOP_GROUPS if label not in top_groups]
    if missing_groups:
        raise AssertionError(f"{product_key} missing formal top groups: {missing_groups}; actual={top_groups}")
    leaf_xmlids = {
        _node_menu_xmlid(node)
        for _path, node in _walk(gated_nav)
        if isinstance(node, dict) and not node.get("children")
    }
    missing_xmlids = [xmlid for xmlid in REQUIRED_FORMAL_MENU_XMLIDS if xmlid not in leaf_xmlids]
    if missing_xmlids:
        raise AssertionError(f"{product_key} missing required formal menu xmlids: {missing_xmlids}")
    return {
        "product_key": product_key,
        "snapshot_id": int(snapshot.id),
        "snapshot_version": _text(snapshot.version),
        "policy_released_menu_count": released_policy_count,
        "gate_page_count": int(gate.get("page_count") or 0),
        "raw_nav_node_count": sum(1 for _path, _node in _walk(raw_nav)),
        "gated_nav_node_count": sum(1 for _path, _node in _walk(gated_nav)),
        "top_groups": top_groups,
        "gate_meta": gate_meta,
    }


def _assert_menu_config_scope(released_policy_count: int) -> dict:
    root = env.ref("smart_construction_core.menu_sc_root", raise_if_not_found=False)  # noqa: F821
    if not root:
        raise AssertionError("formal business root menu not found: smart_construction_core.menu_sc_root")
    params = {"root_menu_id": int(root.id)}
    panel = MenuConfigurationLoadHandler(env=env, payload={"params": params}).handle({"params": params})  # noqa: F821
    data = panel.get("data") if isinstance(panel, dict) else {}
    menus = data.get("menus") if isinstance(data, dict) and isinstance(data.get("menus"), list) else []
    max_menu_count = released_policy_count + FORMAL_MENU_CONFIG_MAX_EXTRA_MENU_COUNT
    if len(menus) > max_menu_count:
        raise AssertionError(
            "menu config candidate scope drift: menu_count=%s max=%s" % (len(menus), max_menu_count)
        )
    forbidden_menus = [
        _text(row.get("complete_name") or row.get("name"))
        for row in menus
        if any(token in _text(row.get("complete_name") or row.get("name")) for token in FORBIDDEN_POLICY_PATH_TOKENS)
    ]
    if forbidden_menus:
        raise AssertionError(f"menu config exposes forbidden menus: {forbidden_menus[:20]}")

    audit = MenuConfigurationAuditHandler(env=env, payload={"params": params}).handle({"params": params})  # noqa: F821
    audit_data = audit.get("data") if isinstance(audit, dict) else {}
    summary = audit_data.get("summary") if isinstance(audit_data, dict) and isinstance(audit_data.get("summary"), dict) else {}
    policies = audit_data.get("policies") if isinstance(audit_data, dict) and isinstance(audit_data.get("policies"), list) else []
    if int(summary.get("configured_policy_count") or 0) > max_menu_count:
        raise AssertionError(
            "menu config audit scope drift: configured_policy_count=%s max=%s"
            % (int(summary.get("configured_policy_count") or 0), max_menu_count)
        )
    forbidden_policies = [
        _text(row.get("menu_complete_name") or row.get("menu_label"))
        for row in policies
        if any(token in _text(row.get("menu_complete_name") or row.get("menu_label")) for token in FORBIDDEN_POLICY_PATH_TOKENS)
    ]
    if forbidden_policies:
        raise AssertionError(f"menu config audit exposes forbidden policies: {forbidden_policies[:20]}")
    return {
        "scope_root_menu_id": int(root.id),
        "panel_menu_count": len(menus),
        "audit_configured_policy_count": int(summary.get("configured_policy_count") or 0),
        "audit_applicable_policy_count": int(summary.get("applicable_policy_count") or 0),
        "max_menu_count": max_menu_count,
    }


def main():
    identity = _assert_startup_identity()
    platform_release_db = _assert_platform_release_db()
    baseline = _load_formal_baseline()
    products = []
    for product_key in PRODUCT_KEYS:
        policy_meta = _assert_policy_matches_formal_baseline(product_key, baseline)
        runtime_meta = _assert_runtime_gate(product_key, int(policy_meta["policy_released_menu_count"]))
        runtime_meta.update(policy_meta)
        products.append(runtime_meta)
    menu_config_scope = _assert_menu_config_scope(
        int(products[0]["policy_released_menu_count"]) if products else MIN_RELEASED_POLICY_MENU_COUNT
    )
    print(
        json.dumps(
            {
                "status": "PASS",
                "db": env.cr.dbname,  # noqa: F821
                "startup_identity": identity,
                "smart_core.platform_release_db": platform_release_db,
                "products": products,
                "menu_config_scope": menu_config_scope,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


main()
