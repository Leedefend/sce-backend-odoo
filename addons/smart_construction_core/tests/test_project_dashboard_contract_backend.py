# -*- coding: utf-8 -*-

from unittest.mock import patch

from odoo.tests.common import TransactionCase, tagged

from odoo.addons.smart_construction_core.handlers.project_dashboard import ProjectDashboardHandler
from odoo.addons.smart_core.orchestration.project_dashboard_contract_orchestrator import (
    ProjectDashboardContractOrchestrator,
)


@tagged("sc_smoke", "project_dashboard_contract_backend")
class TestProjectDashboardContractBackend(TransactionCase):
    def _run_handler(self, payload=None, context=None):
        handler = ProjectDashboardHandler(self.env, payload=payload or {})
        return handler.handle(payload=payload or {}, ctx=context or {})

    def test_project_id_prefers_params_over_context(self):
        context = {"project_id": 202, "model": "project.project", "record_id": 303}
        with patch(
            "odoo.addons.smart_construction_core.handlers.project_dashboard.ProjectDashboardContractOrchestrator.build_contract",
            return_value={"scene": {"key": "project.management", "page": "project.management.dashboard"}, "project": {}, "zones": {}},
        ) as mocked_build_contract:
            result = self._run_handler(
                payload={"project_id": 101},
                context=context,
            )
        self.assertTrue(result.get("ok"))
        mocked_build_contract.assert_called_once_with(project_id=101, context=context)

    def test_project_id_uses_context_record_for_project_model(self):
        context = {"model": "project.project", "record_id": 606}
        with patch(
            "odoo.addons.smart_construction_core.handlers.project_dashboard.ProjectDashboardContractOrchestrator.build_contract",
            return_value={"scene": {"key": "project.management", "page": "project.management.dashboard"}, "project": {}, "zones": {}},
        ) as mocked_build_contract:
            result = self._run_handler(
                payload={},
                context=context,
            )
        self.assertTrue(result.get("ok"))
        mocked_build_contract.assert_called_once_with(project_id=606, context=context)

    def test_contract_envelope_contains_scene_and_meta(self):
        fake_data = {
            "scene": {"key": "project.management", "page": "project.management.dashboard"},
            "page": {"key": "project.management.dashboard", "route": "/s/project.management"},
            "route_context": {
                "primary_protocol": "/s/project.management?project_id=<id>",
                "query_key": "project_id",
            },
            "project": {"id": 1, "name": "Demo"},
            "zones": {
                "header": {},
                "metrics": {},
                "progress": {},
                "contract": {},
                "cost": {},
                "finance": {},
                "risk": {},
            },
        }
        with patch(
            "odoo.addons.smart_construction_core.handlers.project_dashboard.ProjectDashboardContractOrchestrator.build_contract",
            return_value=fake_data,
        ):
            result = self._run_handler(payload={"project_id": 1}, context={})
        self.assertTrue(result.get("ok"))
        data = result.get("data") or {}
        self.assertEqual((data.get("scene") or {}).get("key"), "project.management")
        self.assertEqual((data.get("scene") or {}).get("page"), "project.management.dashboard")
        self.assertEqual((data.get("page") or {}).get("key"), "project.management.dashboard")
        self.assertEqual((data.get("route_context") or {}).get("query_key"), "project_id")
        zones = data.get("zones") or {}
        for key in ("header", "metrics", "progress", "contract", "cost", "finance", "risk"):
            self.assertIn(key, zones)
        meta = result.get("meta") or {}
        self.assertEqual(meta.get("intent"), "project.dashboard")
        self.assertEqual(meta.get("contract_version"), "v1")

    def test_contract_orchestrator_v1_placeholder_shape(self):
        orchestrator = ProjectDashboardContractOrchestrator(self.env)
        contract = orchestrator.build_dashboard_contract_v1({"zones": {}}, project_id=9)
        self.assertEqual(contract.get("scene_key"), "project.dashboard")
        self.assertEqual(((contract.get("project_context") or {}).get("project_id")), 9)
        self.assertEqual(len(contract.get("blocks") or []), 3)
