# -*- coding: utf-8 -*-
from unittest.mock import patch

from odoo.tests.common import TransactionCase, tagged

from odoo.addons.smart_core.app_config_engine.services.dispatchers.action_dispatcher import ActionDispatcher
from odoo.addons.smart_core.app_config_engine.services.dispatchers.nav_dispatcher import NavDispatcher
from odoo.addons.smart_core.handlers.ui_contract import UiContractHandler


@tagged("post_install", "-at_install", "smart_core", "action_dispatcher")
class TestActionDispatcherServerMapping(TransactionCase):
    def test_server_action_prefers_mapping_before_materialize(self):
        dispatcher = ActionDispatcher(self.env, self.env)
        payload = {"subject": "action", "action_id": 462}
        server_info = {
            "type": "ir.actions.server",
            "_name": "ir.actions.server",
            "id": 462,
            "xml_id": "smart_construction_core.action_exec_structure_entry",
            "exists": True,
        }
        mapped = {
            "type": "ir.actions.act_window",
            "_name": "ir.actions.act_window",
            "id": 999,
            "res_model": "construction.work.breakdown",
            "view_mode": "tree,form",
            "exists": True,
        }
        expected = ({"subject": "mapped"}, {"v": 1})

        with (
            patch.object(dispatcher.resolver, "resolve_action", return_value=object()),
            patch.object(dispatcher.resolver, "as_action_info", return_value=server_info),
            patch.object(dispatcher.resolver, "map_server_to_window", return_value=mapped) as mocked_map,
            patch.object(
                dispatcher.resolver,
                "materialize_server_action",
                side_effect=AssertionError("materialize_server_action should not be called when mapping exists"),
            ),
            patch.object(dispatcher, "_dispatch_resolved", return_value=expected) as mocked_dispatch,
        ):
            result = dispatcher.dispatch(payload)

        self.assertEqual(result, expected)
        mocked_map.assert_called_once_with(462, "smart_construction_core.action_exec_structure_entry")
        mocked_dispatch.assert_called_once_with(mapped, payload)

    def test_server_action_falls_back_to_materialize_when_mapping_missing(self):
        dispatcher = ActionDispatcher(self.env, self.env)
        payload = {"subject": "action", "action_id": 777}
        server_info = {
            "type": "ir.actions.server",
            "_name": "ir.actions.server",
            "id": 777,
            "xml_id": "x.y.z",
            "exists": True,
        }
        materialized = {
            "type": "ir.actions.client",
            "_name": "ir.actions.client",
            "tag": "display_notification",
            "exists": True,
        }
        expected = ({"subject": "materialized"}, {"v": 1})

        with (
            patch.object(dispatcher.resolver, "resolve_action", return_value=object()),
            patch.object(dispatcher.resolver, "as_action_info", return_value=server_info),
            patch.object(dispatcher.resolver, "map_server_to_window", return_value=None) as mocked_map,
            patch.object(dispatcher.resolver, "materialize_server_action", return_value=materialized) as mocked_materialize,
            patch.object(dispatcher, "_dispatch_resolved", return_value=expected) as mocked_dispatch,
        ):
            result = dispatcher.dispatch(payload)

        self.assertEqual(result, expected)
        mocked_map.assert_called_once_with(777, "x.y.z")
        mocked_materialize.assert_called_once_with(server_info, payload)
        mocked_dispatch.assert_called_once_with(materialized, payload)

    def test_ui_contract_action_open_exec_structure_returns_page_contract(self):
        action = self.env.ref("smart_construction_core.action_exec_structure_entry", raise_if_not_found=False)
        if not action:
            self.skipTest("smart_construction_core.action_exec_structure_entry not installed")

        run_env = self.env
        pm_user = self.env["res.users"].sudo().search([("login", "=", "sc_fx_pm")], limit=1)
        if pm_user:
            run_env = self.env(user=pm_user)

        handler = UiContractHandler(run_env)
        result = handler.handle(payload={"params": {"op": "action_open", "action_id": int(action.id)}})

        self.assertTrue(result.get("ok"), result)
        data = result.get("data") or {}
        head = data.get("head") if isinstance(data.get("head"), dict) else {}
        model = str(data.get("model") or head.get("model") or "").strip()
        body = data.get("data") if isinstance(data.get("data"), dict) else {}
        contract_type = str(body.get("type") or "").strip().lower()
        self.assertTrue(model, f"ui.contract(action_open) returned empty model: {result}")
        self.assertNotEqual(contract_type, "diagnostic", f"unexpected diagnostic contract: {result}")

    def test_ui_contract_action_open_project_list_preserves_list_multi_actions(self):
        action = self.env.ref("smart_construction_core.action_sc_project_list", raise_if_not_found=False)
        if not action:
            self.skipTest("smart_construction_core.action_sc_project_list not installed")

        run_env = self.env
        demo_user = self.env["res.users"].sudo().search([("login", "=", "demo_full")], limit=1)
        if demo_user:
            run_env = self.env(user=demo_user)

        handler = UiContractHandler(run_env)
        result = handler.handle(payload={"params": {"op": "action_open", "action_id": int(action.id)}})

        self.assertTrue(result.get("ok"), result)
        data = result.get("data") or {}
        head = data.get("head") if isinstance(data.get("head"), dict) else {}
        self.assertEqual(str(head.get("view_type") or data.get("view_type") or "").strip().lower(), "tree")

        buttons = data.get("buttons") if isinstance(data.get("buttons"), list) else []
        toolbar = data.get("toolbar") if isinstance(data.get("toolbar"), dict) else {}
        header_rows = toolbar.get("header") if isinstance(toolbar.get("header"), list) else []
        multi_rows = [
            row
            for row in buttons + header_rows
            if isinstance(row, dict) and row.get("selection") == "multi"
        ]
        self.assertTrue(multi_rows, f"expected list multi actions in project list contract: {result}")
        list_profile = data.get("list_profile") if isinstance(data.get("list_profile"), dict) else {}
        self.assertEqual(
            list_profile.get("columns") or [],
            [
                "name",
                "user_id",
                "partner_id",
                "stage_id",
                "lifecycle_state",
                "date_start",
                "date",
            ],
        )
        self.assertEqual((list_profile.get("column_labels") or {}).get("name"), "名称")
        self.assertEqual((list_profile.get("column_labels") or {}).get("user_id"), "项目管理员")
        self.assertEqual((list_profile.get("column_labels") or {}).get("date"), "有效期")

    def test_ui_contract_action_open_payment_list_preserves_list_multi_actions(self):
        action = self.env.ref("smart_construction_core.action_sc_finance_dashboard", raise_if_not_found=False)
        if not action:
            self.skipTest("smart_construction_core.action_sc_finance_dashboard not installed")

        run_env = self.env
        demo_user = self.env["res.users"].sudo().search([("login", "=", "demo_full")], limit=1)
        if demo_user:
            run_env = self.env(user=demo_user)

        handler = UiContractHandler(run_env)
        result = handler.handle(payload={"params": {"op": "action_open", "action_id": int(action.id)}})

        self.assertTrue(result.get("ok"), result)
        data = result.get("data") or {}
        head = data.get("head") if isinstance(data.get("head"), dict) else {}
        self.assertEqual(str(head.get("view_type") or data.get("view_type") or "").strip().lower(), "tree")

        buttons = data.get("buttons") if isinstance(data.get("buttons"), list) else []
        toolbar = data.get("toolbar") if isinstance(data.get("toolbar"), dict) else {}
        header_rows = toolbar.get("header") if isinstance(toolbar.get("header"), list) else []
        multi_rows = [
            row
            for row in buttons + header_rows
            if isinstance(row, dict) and row.get("selection") == "multi"
        ]
        self.assertTrue(multi_rows, f"expected list multi actions in payment list contract: {result}")
        list_profile = data.get("list_profile") if isinstance(data.get("list_profile"), dict) else {}
        self.assertEqual(
            list_profile.get("columns") or [],
            [
                "name",
                "type",
                "project_id",
                "contract_id",
                "settlement_id",
                "settlement_amount_payable",
                "partner_id",
                "amount",
                "state",
                "date_request",
            ],
        )
        self.assertEqual((list_profile.get("column_labels") or {}).get("name"), "申请单号")
        self.assertEqual((list_profile.get("column_labels") or {}).get("date_request"), "申请日期")

    def test_ui_contract_action_open_material_plan_list_preserves_list_multi_actions(self):
        action = self.env.ref("smart_construction_core.action_project_material_plan", raise_if_not_found=False)
        if not action:
            self.skipTest("smart_construction_core.action_project_material_plan not installed")

        run_env = self.env
        demo_user = self.env["res.users"].sudo().search([("login", "=", "demo_full")], limit=1)
        if demo_user:
            run_env = self.env(user=demo_user)

        handler = UiContractHandler(run_env)
        result = handler.handle(payload={"params": {"op": "action_open", "action_id": int(action.id)}})

        self.assertTrue(result.get("ok"), result)
        data = result.get("data") or {}
        head = data.get("head") if isinstance(data.get("head"), dict) else {}
        self.assertEqual(str(head.get("view_type") or data.get("view_type") or "").strip().lower(), "tree")

        buttons = data.get("buttons") if isinstance(data.get("buttons"), list) else []
        toolbar = data.get("toolbar") if isinstance(data.get("toolbar"), dict) else {}
        header_rows = toolbar.get("header") if isinstance(toolbar.get("header"), list) else []
        multi_rows = [
            row
            for row in buttons + header_rows
            if isinstance(row, dict) and row.get("selection") == "multi"
        ]
        self.assertTrue(multi_rows, f"expected list multi actions in material plan contract: {result}")
        list_profile = data.get("list_profile") if isinstance(data.get("list_profile"), dict) else {}
        self.assertEqual(
            list_profile.get("columns") or [],
            ["name", "project_id", "date_plan", "state"],
        )
        self.assertEqual((list_profile.get("column_labels") or {}).get("name"), "单号")
        self.assertEqual((list_profile.get("column_labels") or {}).get("date_plan"), "需用日期")

    def test_ui_contract_action_open_payment_form_excludes_list_toolbar_actions(self):
        action = self.env.ref("smart_construction_core.action_sc_finance_dashboard", raise_if_not_found=False)
        if not action:
            self.skipTest("smart_construction_core.action_sc_finance_dashboard not installed")

        payment = self.env["payment.request"].sudo().search([], limit=1)
        if not payment:
            self.skipTest("payment.request demo data not installed")

        run_env = self.env
        demo_user = self.env["res.users"].sudo().search([("login", "=", "demo_full")], limit=1)
        if demo_user:
            run_env = self.env(user=demo_user)

        handler = UiContractHandler(run_env)
        result = handler.handle(payload={"params": {
            "op": "action_open",
            "action_id": int(action.id),
            "record_id": int(payment.id),
            "render_profile": "edit",
        }})

        self.assertTrue(result.get("ok"), result)
        data = result.get("data") or {}
        head = data.get("head") if isinstance(data.get("head"), dict) else {}
        self.assertEqual(str(head.get("view_type") or data.get("view_type") or "").strip().lower(), "form")

        buttons = data.get("buttons") if isinstance(data.get("buttons"), list) else []
        toolbar = data.get("toolbar") if isinstance(data.get("toolbar"), dict) else {}
        header_rows = toolbar.get("header") if isinstance(toolbar.get("header"), list) else []
        self.assertFalse(header_rows, f"form contract should not expose toolbar header rows: {result}")

        for row in buttons:
            if not isinstance(row, dict):
                continue
            self.assertEqual(str(row.get("selection") or "none").strip().lower(), "none", result)
            self.assertIn(str(row.get("level") or "").strip().lower(), {"header", "smart", "sidebar", "footer"}, result)

    def test_ui_contract_action_open_tier_review_payment_list_hides_nav_loop_actions(self):
        action = self.env.ref("smart_construction_core.action_sc_tier_review_my_payment_request", raise_if_not_found=False)
        if not action:
            self.skipTest("smart_construction_core.action_sc_tier_review_my_payment_request not installed")

        run_env = self.env
        demo_user = self.env["res.users"].sudo().search([("login", "=", "demo_full")], limit=1)
        if demo_user:
            run_env = self.env(user=demo_user)

        handler = UiContractHandler(run_env)
        result = handler.handle(payload={"params": {"op": "action_open", "action_id": int(action.id)}})

        self.assertTrue(result.get("ok"), result)
        data = result.get("data") or {}
        head = data.get("head") if isinstance(data.get("head"), dict) else {}
        self.assertEqual(str(head.get("model") or "").strip(), "tier.review")
        self.assertEqual(str(head.get("view_type") or data.get("view_type") or "").strip().lower(), "tree")

        def has_nav_loop(rows):
            return any(
                isinstance(row, dict)
                and str(row.get("key") or "").startswith("smart_construction_core.action_sc_tier_review_my_")
                for row in rows
            )

        buttons = data.get("buttons") if isinstance(data.get("buttons"), list) else []
        toolbar = data.get("toolbar") if isinstance(data.get("toolbar"), dict) else {}
        header_rows = toolbar.get("header") if isinstance(toolbar.get("header"), list) else []
        self.assertFalse(has_nav_loop(buttons), result)
        self.assertFalse(has_nav_loop(header_rows), result)

    def test_nav_enrich_server_action_infers_mapped_model(self):
        menu = self.env.ref("smart_construction_core.menu_sc_project_wbs", raise_if_not_found=False)
        if not menu:
            self.skipTest("smart_construction_core.menu_sc_project_wbs not installed")

        dispatcher = NavDispatcher(self.env, self.env)
        tree = [{"menu_id": int(menu.id), "children": []}]
        dispatcher._enrich_nav_models(tree)
        model = str(tree[0].get("model") or "").strip()
        self.assertEqual(model, "construction.work.breakdown")
