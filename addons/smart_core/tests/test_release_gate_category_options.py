# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged

from odoo.addons.smart_core.handlers.system_init import _node_release_gate_keys


@tagged("post_install", "-at_install")
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
