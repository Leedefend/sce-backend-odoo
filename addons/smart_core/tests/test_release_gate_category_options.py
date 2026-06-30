# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged

from odoo.addons.smart_core.handlers.system_init import (
    _apply_user_menu_config_to_delivery_nav,
    _node_release_gate_keys,
)


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
