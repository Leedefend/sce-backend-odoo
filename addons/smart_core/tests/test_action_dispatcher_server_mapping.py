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

    def test_action_open_missing_model_returns_diagnostic_contract(self):
        dispatcher = ActionDispatcher(self.env, self.env)
        payload = {"subject": "action", "action_id": 999}
        missing_model_info = {
            "type": "ir.actions.act_window",
            "_name": "ir.actions.act_window",
            "id": 999,
            "name": "Missing demo model",
            "xml_id": "x_missing.action_missing_demo_model",
            "res_model": "project.project",
            "view_mode": "tree,kanban,form",
            "exists": True,
        }

        with (
            patch.object(dispatcher.resolver, "resolve_action", return_value=object()),
            patch.object(dispatcher.resolver, "as_action_info", return_value=missing_model_info),
        ):
            data, versions = dispatcher.dispatch(payload)

        body = data.get("data") if isinstance(data, dict) else {}
        info = body.get("info") if isinstance(body, dict) else {}
        self.assertEqual(body.get("type"), "diagnostic", data)
        self.assertIn("模型不可用", str(info.get("issue") or ""))
        self.assertEqual(info.get("action_id"), 999)
        self.assertTrue(versions.get("diagnostic"))

    def test_ui_contract_action_open_missing_model_does_not_raise_500(self):
        handler = UiContractHandler(self.env)
        dispatcher = ActionDispatcher(self.env, self.env)
        missing_model_info = {
            "type": "ir.actions.act_window",
            "_name": "ir.actions.act_window",
            "id": 999,
            "name": "Missing demo model",
            "xml_id": "x_missing.action_missing_demo_model",
            "res_model": "project.project",
            "view_mode": "tree,kanban,form",
            "exists": True,
        }

        with (
            patch.object(handler, "_build_dispatcher", return_value=dispatcher),
            patch.object(dispatcher.resolver, "resolve_action", return_value=object()),
            patch.object(dispatcher.resolver, "as_action_info", return_value=missing_model_info),
        ):
            result = handler.handle(payload={"params": {"op": "action_open", "action_id": 999}})

        self.assertTrue(result.get("ok"), result)
        data = result.get("data") if isinstance(result, dict) else {}
        body = data.get("data") if isinstance(data, dict) else {}
        self.assertEqual(body.get("type"), "diagnostic", result)
        self.assertIn("模型不可用", str(body.get("info", {}).get("issue") or ""))

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

    def test_nav_enrich_server_action_infers_mapped_model(self):
        menu = self.env.ref("smart_construction_core.menu_sc_project_wbs", raise_if_not_found=False)
        if not menu:
            self.skipTest("smart_construction_core.menu_sc_project_wbs not installed")

        dispatcher = NavDispatcher(self.env, self.env)
        tree = [{"menu_id": int(menu.id), "children": []}]
        dispatcher._enrich_nav_models(tree)
        model = str(tree[0].get("model") or "").strip()
        self.assertEqual(model, "construction.work.breakdown")
