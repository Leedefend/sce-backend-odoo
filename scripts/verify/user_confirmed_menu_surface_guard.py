# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from odoo import SUPERUSER_ID, api
from odoo.addons.smart_core.adapters.nav_tree_cleaner import NavTreeCleaner
from odoo.addons.smart_core.adapters.odoo_nav_adapter import OdooNavAdapter
from odoo.addons.smart_core.app_config_engine.services.dispatchers.nav_dispatcher import NavDispatcher
from odoo.addons.smart_core.delivery.delivery_engine import DeliveryEngine
from odoo.addons.smart_core.delivery.product_policy_service import ProductPolicyService
from odoo.addons.smart_core.handlers.system_init import (
    _apply_user_menu_config_to_delivery_nav,
    _dedupe_nav_siblings_by_identity,
    _filter_nav_by_release_gate,
    _filter_nav_for_user_data_acceptance_only,
    _load_platform_release_gate,
    _remove_nav_groups_by_label,
    _rehome_business_master_data_nav_groups,
    _sort_business_nav_groups,
    _unwrap_internal_nav_groups,
)


BASELINE_FILE = "user_confirmed_formal_menu_policy_62.json"
PRODUCT_KEYS = ("construction.standard", "construction.preview")
CHECK_LOGIN = "wutao"
FORBIDDEN_USER_VISIBLE_GROUPS = {"用户数据验收", "用户核对菜单", "产品发布面", "正式业务菜单"}
EXPECTED_GROUP_COUNTS = {
    "基础资料": 2,
    "项目中心": 3,
    "合同中心": 6,
    "施工管理": 1,
    "物资与分包": 10,
    "财务中心": 34,
    "人事行政": 7,
    "资料证照": 1,
    "基础设置": 1,
}
FINANCE_INTERFUND_ANALYSIS_PRODUCT_MENU_XMLIDS = {
    "smart_construction_core.menu_sc_finance_project_capital_position",
    "smart_construction_core.menu_sc_finance_counterparty_position_summary",
    "smart_construction_core.menu_sc_finance_project_counterparty_position",
}


def _text(value) -> str:
    return str(value or "").strip()


def _baseline_candidates() -> list[Path]:
    return [
        Path("/mnt/scripts/verify/baselines") / BASELINE_FILE,
        Path.cwd() / "scripts" / "verify" / "baselines" / BASELINE_FILE,
        Path("/home/lidefend/workspace/sce-backend-odoo/scripts/verify/baselines") / BASELINE_FILE,
    ]


def _policy_row(group_label, menu_label, menu_key, menu_id, res_model) -> tuple[str, str, str, int, str]:
    return (
        _text(group_label),
        _text(menu_label),
        _text(menu_key),
        int(menu_id or 0),
        _text(res_model),
    )


def _load_baseline() -> dict[str, list[tuple[str, str, str, int, str]]]:
    path = next((candidate for candidate in _baseline_candidates() if candidate.is_file()), None)
    if not path:
        raise AssertionError("missing user confirmed menu baseline: %s" % BASELINE_FILE)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        payload = payload.get("products")
    if not isinstance(payload, list):
        raise AssertionError("baseline root must be list: %s" % path)

    out: dict[str, list[tuple[str, str, str, int, int, str]]] = {}
    for policy in payload:
        if not isinstance(policy, dict):
            continue
        product_key = _text(policy.get("product_key"))
        rows = []
        for group in policy.get("menu_groups") or []:
            if not isinstance(group, dict):
                continue
            group_label = _text(group.get("group_label") or group.get("label"))
            for menu in group.get("menus") or []:
                if not isinstance(menu, dict):
                    continue
                rows.append(
                    _policy_row(
                        group_label,
                        menu.get("label") or menu.get("name"),
                        menu.get("menu_xmlid") or menu.get("page_key") or menu.get("menu_key"),
                        menu.get("menu_id"),
                        menu.get("res_model") or menu.get("model"),
                    )
                )
        out[product_key] = rows
    return out


def _effective_policy_rows(product_key: str) -> list[tuple[str, str, str, int, str]]:
    policy = ProductPolicyService(env).get_policy(  # noqa: F821
        product_key=product_key,
        enforce_release=True,
        enforce_access=False,
    )
    groups = policy.get("menu_groups") if isinstance(policy.get("menu_groups"), list) else []
    rows = []
    group_counts = {}
    for group in groups:
        if not isinstance(group, dict):
            continue
        group_label = _text(group.get("group_label") or group.get("label"))
        menus = group.get("menus") if isinstance(group.get("menus"), list) else []
        group_counts[group_label] = len(menus)
        for menu in menus:
            if not isinstance(menu, dict):
                continue
            rows.append(
                _policy_row(
                    group_label,
                    menu.get("label") or menu.get("name"),
                    menu.get("menu_xmlid") or menu.get("page_key") or menu.get("menu_key"),
                    menu.get("menu_id"),
                    menu.get("res_model") or menu.get("model"),
                )
            )
    if group_counts != EXPECTED_GROUP_COUNTS:
        raise AssertionError("%s group counts drift: %s" % (product_key, group_counts))
    return rows


def _assert_policy_matches_baseline() -> dict[str, int]:
    baseline = _load_baseline()
    counts = {}
    for product_key in PRODUCT_KEYS:
        expected = baseline.get(product_key)
        if expected is None:
            raise AssertionError("baseline missing product: %s" % product_key)
        actual = _effective_policy_rows(product_key)
        actual_without_finance_interfund = [
            row for row in actual if row[2] not in FINANCE_INTERFUND_ANALYSIS_PRODUCT_MENU_XMLIDS
        ]
        if actual_without_finance_interfund != expected:
            expected_set = set(expected)
            actual_set = set(actual_without_finance_interfund)
            raise AssertionError(
                "%s confirmed menu policy drift: only_expected=%s only_actual=%s"
                % (product_key, sorted(expected_set - actual_set)[:20], sorted(actual_set - expected_set)[:20])
            )
        missing_finance_interfund = sorted(
            FINANCE_INTERFUND_ANALYSIS_PRODUCT_MENU_XMLIDS
            - {row[2] for row in actual}
        )
        if missing_finance_interfund:
            raise AssertionError("%s missing finance interfund product menus: %s" % (product_key, missing_finance_interfund))
        counts[product_key] = len(actual)
    return counts


def _node_label(node: dict) -> str:
    return _text(node.get("label") or node.get("title") or node.get("name"))


def _node_identity(node: dict) -> str:
    meta = node.get("meta") if isinstance(node.get("meta"), dict) else {}
    target = node.get("target") if isinstance(node.get("target"), dict) else {}
    return _text(
        node.get("menu_id")
        or meta.get("menu_id")
        or target.get("menu_id")
        or node.get("menu_xmlid")
        or meta.get("menu_xmlid")
        or meta.get("menu_key")
        or target.get("menu_xmlid")
        or node.get("action_id")
        or meta.get("action_id")
        or target.get("action_id")
        or _node_label(node)
    )


def _walk(nodes, path=()):
    for node in nodes or []:
        if not isinstance(node, dict):
            continue
        current = path + (_node_label(node),)
        yield current, node
        children = node.get("children") if isinstance(node.get("children"), list) else []
        yield from _walk(children, current)


def _assert_no_duplicate_siblings(nodes) -> None:
    def visit(children, path):
        rows = [node for node in (children or []) if isinstance(node, dict)]
        counts = Counter(_node_identity(node) for node in rows)
        duplicates = [key for key, count in counts.items() if key and count > 1]
        if duplicates:
            raise AssertionError("duplicate visible menu siblings at %s: %s" % (" / ".join(path), duplicates[:20]))
        for node in rows:
            visit(node.get("children") if isinstance(node.get("children"), list) else [], path + [_node_label(node)])

    visit(nodes, [])


def _runtime_delivery_nav_for_login(login: str) -> list[dict]:
    user = env["res.users"].sudo().search([("login", "=", login)], limit=1)  # noqa: F821
    if not user:
        raise AssertionError("missing verification user: %s" % login)
    user_env = env(user=user.id)  # noqa: F821
    su_env = api.Environment(env.cr, SUPERUSER_ID, dict(user_env.context or {}))  # noqa: F821
    nav_data, _versions = NavDispatcher(user_env, su_env).build_nav(
        {"subject": "nav", "scene": "web", "root_xmlid": "smart_construction_core.menu_sc_root"}
    )
    native_nav = NavTreeCleaner().clean(nav_data.get("nav") or [])
    OdooNavAdapter().enrich(user_env, native_nav)
    payload = DeliveryEngine(user_env).build(
        data={},
        product_key="",
        edition_key="standard",
        base_product_key="",
        native_nav=native_nav,
    )
    delivery_nav = payload.get("nav") if isinstance(payload.get("nav"), list) else []
    release_gate = _load_platform_release_gate(
        user_env,
        product_key=_text(payload.get("product_key")) or "construction.standard",
    )
    delivery_nav, _gate_meta = _filter_nav_by_release_gate(delivery_nav, release_gate)
    delivery_nav, _acceptance_meta = _filter_nav_for_user_data_acceptance_only(user_env, delivery_nav)
    delivery_nav = _remove_nav_groups_by_label(delivery_nav, {"用户核对菜单"})
    delivery_nav, _config_meta = _apply_user_menu_config_to_delivery_nav(user_env, delivery_nav)
    delivery_nav = _unwrap_internal_nav_groups(delivery_nav, {"产品发布面", "正式业务菜单"})
    delivery_nav = _rehome_business_master_data_nav_groups(delivery_nav)
    delivery_nav = _dedupe_nav_siblings_by_identity(delivery_nav)
    return _sort_business_nav_groups(delivery_nav)


def _assert_runtime_nav_locked() -> dict[str, int]:
    nav = _runtime_delivery_nav_for_login(CHECK_LOGIN)
    _assert_no_duplicate_siblings(nav)
    labels = [_node_label(node) for _path, node in _walk(nav)]
    forbidden = sorted(label for label in labels if label in FORBIDDEN_USER_VISIBLE_GROUPS)
    if forbidden:
        raise AssertionError("forbidden user-visible groups leaked: %s" % forbidden)
    return {
        "runtime_node_count": sum(1 for _path, _node in _walk(nav)),
        "runtime_root_count": len(nav),
    }


def main():
    policy_counts = _assert_policy_matches_baseline()
    runtime = _assert_runtime_nav_locked()
    print(
        json.dumps(
            {
                "status": "PASS",
                "db": env.cr.dbname,  # noqa: F821
                "guard": "user_confirmed_menu_surface_guard",
                "baseline": BASELINE_FILE,
                "policy_counts": policy_counts,
                "runtime": runtime,
                "check_login": CHECK_LOGIN,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


main()
