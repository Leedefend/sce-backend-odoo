# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
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
    _filter_nav_by_release_gate,
    _filter_nav_for_user_data_acceptance_only,
    _load_platform_release_gate,
    _remove_nav_groups_by_label,
)


BASELINE_FILE = "formal_business_product_menu_policy_v1.json"
PRODUCT_KEYS = ("construction.standard", "construction.preview")
CHECK_LOGIN = "wutao"
FORBIDDEN_USER_VISIBLE_GROUPS = {"用户数据验收", "用户核对菜单", "产品发布面", "正式业务菜单"}
EXPECTED_GROUP_COUNTS = {
    "基础资料": 2,
    "项目中心": 3,
    "合同中心": 6,
    "施工管理": 3,
    "物资与分包": 23,
    "财务中心": 42,
    "人事行政": 8,
    "资料证照": 3,
    "配置中心": 1,
    "税务中心": 6,
}
FINANCE_INTERFUND_ANALYSIS_PRODUCT_MENU_XMLIDS = {
    "smart_construction_core.menu_sc_finance_project_capital_position",
    "smart_construction_core.menu_sc_finance_counterparty_position_summary",
    "smart_construction_core.menu_sc_finance_project_counterparty_position",
    "smart_construction_core.menu_sc_company_contractor_responsibility_summary",
    "smart_construction_core.menu_sc_company_contractor_responsibility_fact",
}
REQUIRED_PRODUCTIZATION_META_KEYS = {
    "product_domain",
    "entry_intent",
    "disposition_policy",
    "integration_target",
    "business_entry_contract_version",
    "entry_target_policy",
}
MERGE_BY_CATEGORY_INTEGRATION_ACTION_XMLIDS_BY_MODEL = {
    "construction.contract.income": "smart_construction_core.action_construction_contract_income",
    "construction.contract.expense": "smart_construction_core.action_construction_contract_expense",
    "sc.settlement.order": "smart_construction_core.action_sc_settlement_order",
    "sc.labor.usage": "smart_construction_core.action_sc_labor_usage",
    "sc.material.outbound": "smart_construction_core.action_sc_material_outbound",
    "sc.receipt.income": "smart_construction_core.action_sc_receipt_income",
    "payment.request": "smart_construction_core.action_payment_request",
    "sc.payment.execution": "smart_construction_core.action_sc_payment_execution",
    "sc.expense.claim": "smart_construction_core.action_sc_expense_claim",
    "sc.financing.loan": "smart_construction_core.action_sc_financing_loan",
    "sc.invoice.registration": "smart_construction_core.action_sc_invoice_registration",
    "sc.self.funding.registration": "smart_construction_core.action_sc_self_funding_registration",
}
MERGE_BY_CATEGORY_ACTIONS_REQUIRING_EXPLICIT_VIEWS = {
    "smart_construction_core.action_construction_contract_income",
    "smart_construction_core.action_construction_contract_expense",
}


def artifact_root() -> Path:
    raw = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(raw)] if raw else []
    candidates.extend([Path("/mnt/artifacts/backend"), Path.cwd() / "artifacts"])
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return candidate
        except OSError:
            continue
    return Path("/tmp")


def _write_artifact(result: dict) -> None:
    target = artifact_root() / f"user_confirmed_menu_surface_guard.{env.cr.dbname}.json"  # noqa: F821
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True, default=str), encoding="utf-8")


def _text(value) -> str:
    return str(value or "").strip()


def _integration_entry_target_action_id(entry_target: dict) -> int:
    compatibility_refs = entry_target.get("compatibility_refs") if isinstance(entry_target.get("compatibility_refs"), dict) else {}
    return int(entry_target.get("action_id") or compatibility_refs.get("action_id") or 0)


def _action_has_explicit_views(action_xmlid: str) -> bool:
    action = env.ref(action_xmlid, raise_if_not_found=False)  # noqa: F821
    return bool(action and (action.view_id or action.view_ids))


def _baseline_candidates() -> list[Path]:
    return [
        Path("/mnt/scripts/verify/baselines") / BASELINE_FILE,
        Path.cwd() / "scripts" / "verify" / "baselines" / BASELINE_FILE,
        Path("/home/lidefend/workspace/sce-backend-odoo/scripts/verify/baselines") / BASELINE_FILE,
    ]


def _policy_row(group_label, menu_label, menu_key, menu_id, res_model) -> tuple[str, str, str, str]:
    # Database numeric IDs differ between local and daily dev databases; freeze stable product identity only.
    _ = menu_id
    return (
        _text(group_label),
        _text(menu_label),
        _text(menu_key),
        _text(res_model),
    )


def _load_baseline() -> dict[str, list[tuple[str, str, str, str]]]:
    path = next((candidate for candidate in _baseline_candidates() if candidate.is_file()), None)
    if not path:
        raise AssertionError("missing user confirmed menu baseline: %s" % BASELINE_FILE)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        payload = payload.get("products")
    if not isinstance(payload, list):
        raise AssertionError("baseline root must be list: %s" % path)

    out: dict[str, list[tuple[str, str, str, str]]] = {}
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


def _effective_policy_rows(product_key: str) -> list[tuple[str, str, str, str]]:
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


def _effective_policy_payload(product_key: str) -> dict:
    return ProductPolicyService(env).get_policy(  # noqa: F821
        product_key=product_key,
        enforce_release=True,
        enforce_access=False,
    )


def _assert_policy_productization_metadata(product_key: str) -> dict[str, int]:
    policy = _effective_policy_payload(product_key)
    groups = policy.get("menu_groups") if isinstance(policy.get("menu_groups"), list) else []
    checked = 0
    missing = []
    merge_by_category = 0
    integrated_merge_by_category = 0
    for group in groups:
        if not isinstance(group, dict):
            continue
        for menu in group.get("menus") or []:
            if not isinstance(menu, dict):
                continue
            menu_xmlid = _text(menu.get("menu_xmlid") or menu.get("page_key") or menu.get("menu_key"))
            if not menu_xmlid:
                continue
            checked += 1
            missing_keys = sorted(key for key in REQUIRED_PRODUCTIZATION_META_KEYS if not _text(menu.get(key)))
            if missing_keys:
                missing.append({"menu_xmlid": menu_xmlid, "label": _text(menu.get("label")), "missing": missing_keys})
            if _text(menu.get("disposition_policy")) == "merge_by_category":
                merge_by_category += 1
                if not _text(menu.get("default_business_category_code")):
                    missing.append({"menu_xmlid": menu_xmlid, "label": _text(menu.get("label")), "missing": ["default_business_category_code"]})
                model_name = _text(menu.get("res_model") or menu.get("model") or menu.get("fact_model"))
                expected_action_xmlid = MERGE_BY_CATEGORY_INTEGRATION_ACTION_XMLIDS_BY_MODEL.get(model_name)
                if expected_action_xmlid:
                    integrated_merge_by_category += 1
                    entry_target = menu.get("integration_entry_target") if isinstance(menu.get("integration_entry_target"), dict) else {}
                    integration_action_id = int(menu.get("integration_action_id") or 0)
                    missing_integration = []
                    if _text(menu.get("integration_action_xmlid")) != expected_action_xmlid:
                        missing_integration.append("integration_action_xmlid")
                    if integration_action_id <= 0:
                        missing_integration.append("integration_action_id")
                    if _text(entry_target.get("type")) != "compatibility":
                        missing_integration.append("integration_entry_target.type")
                    if _integration_entry_target_action_id(entry_target) != integration_action_id:
                        missing_integration.append("integration_entry_target.action_id")
                    if not _text(menu.get("integration_view_modes")):
                        missing_integration.append("integration_view_modes")
                    if (
                        expected_action_xmlid in MERGE_BY_CATEGORY_ACTIONS_REQUIRING_EXPLICIT_VIEWS
                        and not _action_has_explicit_views(expected_action_xmlid)
                    ):
                        missing_integration.append("integration_action_explicit_views")
                    if missing_integration:
                        missing.append(
                            {
                                "menu_xmlid": menu_xmlid,
                                "label": _text(menu.get("label")),
                                "model": model_name,
                                "missing": missing_integration,
                            }
                        )
    if missing:
        raise AssertionError("%s productization metadata missing: %s" % (product_key, missing[:20]))
    return {
        "policy_productized_menu_count": checked,
        "policy_merge_by_category_count": merge_by_category,
        "policy_integrated_merge_by_category_count": integrated_merge_by_category,
    }


def _assert_policy_matches_baseline() -> dict[str, int]:
    baseline = _load_baseline()
    counts = {}
    for product_key in PRODUCT_KEYS:
        expected = baseline.get(product_key)
        if expected is None:
            raise AssertionError("baseline missing product: %s" % product_key)
        actual = _effective_policy_rows(product_key)
        if actual != expected:
            expected_set = set(expected)
            actual_set = set(actual)
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
        _assert_policy_productization_metadata(product_key)
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
    if _acceptance_meta.get("applied"):
        delivery_nav = _remove_nav_groups_by_label(delivery_nav, {"用户核对菜单"})
    delivery_nav, _config_meta = _apply_user_menu_config_to_delivery_nav(user_env, delivery_nav)
    return delivery_nav


def _assert_runtime_nav_locked() -> dict[str, int]:
    nav = _runtime_delivery_nav_for_login(CHECK_LOGIN)
    _assert_no_duplicate_siblings(nav)
    labels = [_node_label(node) for _path, node in _walk(nav)]
    forbidden = sorted(label for label in labels if label in FORBIDDEN_USER_VISIBLE_GROUPS)
    if forbidden:
        raise AssertionError("forbidden user-visible groups leaked: %s" % forbidden)
    productized_nodes = 0
    merge_by_category_nodes = 0
    integrated_merge_by_category_nodes = 0
    runtime_merge_group_nodes = 0
    runtime_integrated_merge_group_nodes = 0
    missing_runtime_meta = []
    for path, node in _walk(nav):
        meta = node.get("meta") if isinstance(node.get("meta"), dict) else {}
        if meta.get("merge_by_category_group") is True:
            runtime_merge_group_nodes += 1
            children = node.get("children") if isinstance(node.get("children"), list) else []
            entry_target = meta.get("entry_target") if isinstance(meta.get("entry_target"), dict) else {}
            category_options = meta.get("business_category_options") if isinstance(meta.get("business_category_options"), list) else []
            action_id = int(meta.get("action_id") or 0)
            if action_id > 0:
                runtime_integrated_merge_group_nodes += 1
                missing_integration = []
                if _text(meta.get("default_business_category_code")):
                    missing_integration.append("default_business_category_code_must_be_empty")
                if _text(meta.get("current_business_category_code")):
                    missing_integration.append("current_business_category_code_must_be_empty")
                if _text(entry_target.get("type")) != "compatibility":
                    missing_integration.append("entry_target.type")
                if _integration_entry_target_action_id(entry_target) != action_id:
                    missing_integration.append("entry_target.action_id")
                if children:
                    missing_integration.append("legacy_child_menu_entries_must_be_empty")
                if len(category_options) <= 1:
                    missing_integration.append("business_category_options")
                category_codes = [
                    _text(option.get("code"))
                    for option in category_options
                    if isinstance(option, dict)
                ]
                if not category_codes or not all(category_codes):
                    missing_integration.append("business_category_options.code")
                if missing_integration:
                    missing_runtime_meta.append(
                        {
                            "path": " / ".join(path),
                            "label": _node_label(node),
                            "missing": missing_integration,
                        }
                    )
        menu_xmlid = _text(meta.get("menu_xmlid") or node.get("menu_xmlid"))
        if not menu_xmlid or not menu_xmlid.startswith("smart_construction_core."):
            continue
        if menu_xmlid in FINANCE_INTERFUND_ANALYSIS_PRODUCT_MENU_XMLIDS or _text(meta.get("business_entry_contract_version")):
            productized_nodes += 1
            missing_keys = sorted(key for key in REQUIRED_PRODUCTIZATION_META_KEYS if not _text(meta.get(key)))
            if missing_keys:
                missing_runtime_meta.append({"path": " / ".join(path), "menu_xmlid": menu_xmlid, "missing": missing_keys})
            if _text(meta.get("disposition_policy")) == "merge_by_category":
                merge_by_category_nodes += 1
                if not _text(meta.get("default_business_category_code")):
                    missing_runtime_meta.append({"path": " / ".join(path), "menu_xmlid": menu_xmlid, "missing": ["default_business_category_code"]})
                model_name = _text(meta.get("fact_model") or meta.get("res_model") or meta.get("model"))
                expected_action_xmlid = MERGE_BY_CATEGORY_INTEGRATION_ACTION_XMLIDS_BY_MODEL.get(model_name)
                if expected_action_xmlid:
                    integrated_merge_by_category_nodes += 1
                    entry_target = meta.get("integration_entry_target") if isinstance(meta.get("integration_entry_target"), dict) else {}
                    integration_action_id = int(meta.get("integration_action_id") or 0)
                    missing_integration = []
                    if _text(meta.get("integration_action_xmlid")) != expected_action_xmlid:
                        missing_integration.append("integration_action_xmlid")
                    if integration_action_id <= 0:
                        missing_integration.append("integration_action_id")
                    if _text(entry_target.get("type")) != "compatibility":
                        missing_integration.append("integration_entry_target.type")
                    if _integration_entry_target_action_id(entry_target) != integration_action_id:
                        missing_integration.append("integration_entry_target.action_id")
                    if not _text(meta.get("integration_view_modes")):
                        missing_integration.append("integration_view_modes")
                    if (
                        expected_action_xmlid in MERGE_BY_CATEGORY_ACTIONS_REQUIRING_EXPLICIT_VIEWS
                        and not _action_has_explicit_views(expected_action_xmlid)
                    ):
                        missing_integration.append("integration_action_explicit_views")
                    if missing_integration:
                        missing_runtime_meta.append(
                            {
                                "path": " / ".join(path),
                                "menu_xmlid": menu_xmlid,
                                "model": model_name,
                                "missing": missing_integration,
                            }
                        )
    if missing_runtime_meta:
        raise AssertionError("runtime productization metadata missing: %s" % missing_runtime_meta[:20])
    return {
        "runtime_node_count": sum(1 for _path, _node in _walk(nav)),
        "runtime_root_count": len(nav),
        "runtime_productized_node_count": productized_nodes,
        "runtime_merge_by_category_node_count": merge_by_category_nodes,
        "runtime_integrated_merge_by_category_node_count": integrated_merge_by_category_nodes,
        "runtime_merge_group_node_count": runtime_merge_group_nodes,
        "runtime_integrated_merge_group_node_count": runtime_integrated_merge_group_nodes,
    }


def main():
    try:
        policy_counts = _assert_policy_matches_baseline()
        runtime = _assert_runtime_nav_locked()
        result = {
            "status": "PASS",
            "db": env.cr.dbname,  # noqa: F821
            "guard": "user_confirmed_menu_surface_guard",
            "baseline": BASELINE_FILE,
            "policy_counts": policy_counts,
            "runtime": runtime,
            "check_login": CHECK_LOGIN,
            "errors": [],
        }
    except Exception as exc:
        result = {
            "status": "FAIL",
            "db": env.cr.dbname,  # noqa: F821
            "guard": "user_confirmed_menu_surface_guard",
            "baseline": BASELINE_FILE,
            "check_login": CHECK_LOGIN,
            "errors": [{"type": type(exc).__name__, "message": str(exc)}],
        }
        _write_artifact(result)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, default=str))
        raise SystemExit(1)
    _write_artifact(result)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, default=str))


raise SystemExit(main())
