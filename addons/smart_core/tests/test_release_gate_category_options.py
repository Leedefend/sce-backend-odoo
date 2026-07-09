# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged

from odoo.addons.smart_core.handlers.system_init import (
    _apply_constrained_user_menu_config_to_released_nav,
    _apply_user_menu_config_to_delivery_nav,
    _filter_nav_by_release_gate,
    _node_release_gate_keys,
)
from odoo.addons.smart_core.delivery.edition_release_snapshot_service import EditionReleaseSnapshotService


class _ConfigParam:
    def __init__(self, values):
        self.values = values

    def sudo(self):
        return self

    def get_param(self, key, default=""):
        return self.values.get(key, default)


class _MenuConfigUnavailableEnv:
    user = object()

    def __init__(self, *, config_only="1"):
        self.config_only = config_only

    def __getitem__(self, model):
        if model == "ir.config_parameter":
            return _ConfigParam({
                "smart_core.nav.user_menu_config.config_only.enabled": self.config_only,
            })
        raise KeyError(model)


class _OverlayModel:
    def __init__(self, nav):
        self.nav = nav

    def apply_runtime_overlay(self, nav_fact, user=None):
        return {
            "tree": self.nav,
            "flat": [],
        }, {
            "applied": True,
            "applied_count": 2,
            "hidden_count": 0,
            "renamed_count": 0,
            "reordered_count": 0,
            "moved_count": 2,
        }


class _MenuConfigOverlayEnv:
    user = object()

    def __init__(self, overlay_nav):
        self.overlay_nav = overlay_nav

    def __getitem__(self, model):
        if model == "ir.config_parameter":
            return _ConfigParam({})
        if model == "ui.menu.config.policy":
            return _OverlayModel(self.overlay_nav)
        raise KeyError(model)


class _ModelDataRows(list):
    def sudo(self):
        return self

    def search(self, domain):
        model = next((value for field, op, value in domain if field == "model" and op == "="), "")
        modules = set(next((value for field, op, value in domain if field == "module" and op == "in"), []) or [])
        names = set(next((value for field, op, value in domain if field == "name" and op == "in"), []) or [])
        rows = list(self)
        if model:
            rows = [row for row in rows if getattr(row, "model", "") == model]
        if modules:
            rows = [row for row in rows if getattr(row, "module", "") in modules]
        if names:
            rows = [row for row in rows if getattr(row, "name", "") in names]
        return rows


class _ProtectedMenuReleaseGateEnv:
    user = object()

    def __init__(self):
        self.model_data = _ModelDataRows([
            type("ModelDataRow", (), {
                "model": "ir.ui.menu",
                "module": "smart_construction_core",
                "name": "menu_sc_business_config_workbench",
                "res_id": 827,
            })(),
            type("ModelDataRow", (), {
                "model": "ir.ui.menu",
                "module": "smart_construction_core",
                "name": "menu_ui_form_field_policy_business_config",
                "res_id": 644,
            })(),
        ])

    def __getitem__(self, model):
        if model == "ir.model.data":
            return self.model_data
        if model == "ir.config_parameter":
            return _ConfigParam({
                "smart_core.lowcode.system_config_menu_xmlids": (
                    "smart_construction_core.menu_sc_business_config_workbench,"
                    "smart_construction_core.menu_ui_form_field_policy_business_config"
                ),
            })
        raise KeyError(model)


@tagged("post_install", "-at_install", "release_gate_category_options")
class TestReleaseGateCategoryOptions(TransactionCase):
    def test_category_option_menu_refs_are_release_gate_keys(self):
        node = {
            "label": "结算办理",
            "meta": {
                "action_id": 675,
                "business_category_options": [
                    {
                        "label": "收入合同结算",
                        "menu_id": 486,
                        "menu_xmlid": "smart_construction_core.menu_sc_income_contract_settlement",
                    },
                    {
                        "label": "支出合同结算",
                        "menu_id": 491,
                        "menu_xmlid": "smart_construction_core.menu_sc_expense_contract_settlement",
                    },
                ],
            },
        }

        keys = _node_release_gate_keys(node)

        self.assertIn("/a/675", keys)
        self.assertIn("system.menu_486", keys)
        self.assertIn("system.menu_491", keys)
        self.assertIn("smart_construction_core.menu_sc_income_contract_settlement", keys)
        self.assertIn("smart_construction_core.menu_sc_expense_contract_settlement", keys)

    def test_user_menu_config_overlay_fails_closed_when_policy_model_unavailable(self):
        nav = [{"menu_id": 1, "name": "智慧施工管理平台", "children": [{"menu_id": 2, "name": "系统菜单"}]}]

        next_nav, meta = _apply_user_menu_config_to_delivery_nav(
            _MenuConfigUnavailableEnv(config_only="1"),
            nav,
        )

        self.assertEqual(next_nav, [])
        self.assertEqual(meta.get("reason"), "policy_model_unavailable")
        self.assertTrue(meta.get("config_only"))
        self.assertEqual(meta.get("unconfigured_hidden_count"), 2)

    def test_user_menu_config_overlay_can_fail_open_when_config_only_disabled(self):
        nav = [{"menu_id": 1, "name": "智慧施工管理平台", "children": []}]

        next_nav, meta = _apply_user_menu_config_to_delivery_nav(
            _MenuConfigUnavailableEnv(config_only="0"),
            nav,
        )

        self.assertEqual(next_nav, nav)
        self.assertEqual(meta.get("reason"), "policy_model_unavailable")
        self.assertFalse(meta.get("config_only"))

    def test_release_gate_reapplied_after_overlay_removes_resurrected_unreleased_menu(self):
        nav = [
            {
                "menu_id": 291,
                "name": "智慧施工管理平台",
                "children": [
                    {"menu_id": 500, "name": "项目台账", "route": "/a/100?menu_id=500", "children": []},
                    {
                        "menu_id": 430,
                        "name": "历史物资库存事实",
                        "route": "/a/717?menu_id=430",
                        "model": "sc.legacy.material.stock.fact",
                        "meta": {"source": "ui.menu.config.policy", "menu_id": 430, "action_id": 717},
                        "children": [],
                    },
                    {
                        "menu_id": 646,
                        "name": "菜单配置",
                        "model": "ui.menu.config.policy",
                        "meta": {"delivery_bucket": "delivery_business_config"},
                        "children": [],
                    },
                ],
            }
        ]
        gate = {
            "applied": True,
            "product_key": "construction.standard",
            "allowed": {
                "menu_ids": ["291", "500"],
                "action_ids": ["100"],
                "routes": ["/a/100?menu_id=500"],
            },
        }

        filtered, meta = _filter_nav_by_release_gate(nav, gate)

        root = filtered[0]
        labels = [child["name"] for child in root["children"]]
        self.assertIn("项目台账", labels)
        self.assertIn("菜单配置", labels)
        self.assertNotIn("历史物资库存事实", labels)
        self.assertEqual(meta["removed_leaf_count"], 1)
        self.assertEqual(meta["runtime_business_config_passthrough_count"], 1)

    def test_release_gate_keeps_protected_runtime_config_menus(self):
        nav = [
            {
                "menu_id": 291,
                "name": "智慧施工管理平台",
                "children": [
                    {"menu_id": 500, "name": "项目台账", "route": "/a/100?menu_id=500", "children": []},
                    {
                        "menu_id": 297,
                        "name": "配置中心",
                        "children": [
                            {
                                "menu_id": 853,
                                "name": "低代码系统配置",
                                "children": [
                                    {
                                        "menu_id": 827,
                                        "name": "配置工作台",
                                        "route": "/a/1009?menu_id=827",
                                        "model": "ui.business.config.contract",
                                        "children": [],
                                    },
                                    {
                                        "menu_id": 644,
                                        "name": "表单字段配置",
                                        "route": "/a/1017?menu_id=644",
                                        "model": "ui.form.field.policy",
                                        "children": [],
                                    },
                                ],
                            }
                        ],
                    },
                ],
            }
        ]
        gate = {
            "applied": True,
            "product_key": "construction.standard",
            "allowed": {
                "menu_ids": ["291", "500"],
                "action_ids": ["100"],
                "routes": ["/a/100?menu_id=500"],
            },
        }

        filtered, meta = _filter_nav_by_release_gate(nav, gate, env=_ProtectedMenuReleaseGateEnv())

        root = filtered[0]
        config_center = next(child for child in root["children"] if child["name"] == "配置中心")
        lowcode_group = config_center["children"][0]
        self.assertEqual([child["name"] for child in lowcode_group["children"]], ["配置工作台", "表单字段配置"])
        self.assertEqual(meta["removed_leaf_count"], 0)
        self.assertEqual(meta["runtime_business_config_passthrough_count"], 2)

    def test_release_target_integrity_allows_action_only_formal_entry(self):
        service = EditionReleaseSnapshotService(self.env)
        check = service._target_integrity_check(
            [
                {
                    "page_key": "smart_construction_core.menu_sc_tax_certificate_registration_user",
                    "label": "外经证登记",
                    "route": "/a/762",
                    "menu_id": 0,
                    "action_id": 762,
                    "menu_xmlid": "smart_construction_core.menu_sc_tax_certificate_registration_user",
                    "res_model": "sc.legacy.payment.residual.fact",
                }
            ]
        )

        self.assertEqual(check.get("status"), "pass")
        self.assertFalse(check.get("blocking"))

    def test_released_nav_overlay_is_blocked_when_product_centers_are_changed(self):
        released_nav = [
            {
                "label": "系统菜单",
                "children": [
                    {"label": "基础资料", "children": [{"label": "客户", "menu_id": 598, "children": []}]},
                    {"label": "合同中心", "children": [{"label": "一般合同（公司）", "menu_id": 529, "children": []}]},
                ],
            }
        ]
        flattened_overlay_nav = [
            {
                "label": "系统菜单",
                "children": [
                    {"label": "客户", "menu_id": 598, "children": []},
                    {"label": "一般合同（公司）", "menu_id": 529, "children": []},
                ],
            }
        ]

        next_nav, meta = _apply_constrained_user_menu_config_to_released_nav(
            _MenuConfigOverlayEnv(flattened_overlay_nav),
            released_nav,
        )

        self.assertEqual(next_nav, released_nav)
        self.assertFalse(meta.get("applied"))
        self.assertTrue(meta.get("blocked"))
        self.assertEqual(meta.get("reason"), "blocked_product_center_signature_change")
        self.assertEqual(meta.get("before_center_signature"), ["基础资料", "合同中心"])
        self.assertEqual(meta.get("after_center_signature"), ["客户", "一般合同（公司）"])
