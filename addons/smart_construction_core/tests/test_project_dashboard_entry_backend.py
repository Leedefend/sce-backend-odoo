# -*- coding: utf-8 -*-

from unittest.mock import patch

from odoo.tests.common import TransactionCase, tagged

from odoo.addons.smart_construction_core.handlers.project_dashboard_block_fetch import (
    ProjectDashboardBlockFetchHandler,
)
from odoo.addons.smart_construction_core.handlers.project_dashboard_enter import (
    ProjectDashboardEnterHandler,
)
from odoo.addons.smart_construction_core.handlers.project_dashboard_open import (
    ProjectDashboardOpenHandler,
)
from odoo.addons.smart_core.orchestration.project_dashboard_scene_orchestrator import (
    ProjectDashboardSceneOrchestrator,
)
from odoo.addons.smart_construction_core.services.project_dashboard_service import (
    ProjectDashboardService,
)


@tagged("sc_smoke", "project_dashboard_entry_backend")
class TestProjectDashboardEntryBackend(TransactionCase):
    def test_entry_requires_project_id(self):
        handler = ProjectDashboardEnterHandler(self.env, payload={})
        result = handler.handle(payload={}, ctx={})
        self.assertFalse(result.get("ok"))
        self.assertEqual(((result.get("error") or {}).get("code")), "PROJECT_CONTEXT_MISSING")

    def test_entry_returns_minimal_shape(self):
        fake_entry = {
            "project_id": 11,
            "scene_key": "project.management",
            "scene_label": "项目驾驶舱",
            "state_fallback_text": "当前状态：已完成立项，正在查看项目驾驶舱。",
            "title": "Demo",
            "summary": {"project_code": "P-11"},
            "blocks": [{"key": "progress"}, {"key": "risks"}, {"key": "next_actions"}],
            "suggested_action": {"intent": "project.dashboard.block.fetch"},
            "runtime_fetch_hints": {"blocks": {"progress": {"intent": "project.dashboard.block.fetch"}}},
        }
        handler = ProjectDashboardEnterHandler(self.env, payload={"project_id": 11})
        with patch(
            "odoo.addons.smart_construction_core.handlers.project_dashboard_enter.ProjectDashboardSceneOrchestrator.build_entry",
            return_value=fake_entry,
        ):
            result = handler.handle(payload={"project_id": 11}, ctx={})
        self.assertTrue(result.get("ok"))
        self.assertEqual(set((result.get("data") or {}).keys()), set(fake_entry.keys()))

    def test_runtime_block_fetch_keeps_block_level_payload(self):
        fake_block = {
            "project_id": 11,
            "block_key": "progress",
            "block": {"block_type": "progress_summary", "state": "ready", "data": {}},
            "degraded": False,
        }
        handler = ProjectDashboardBlockFetchHandler(self.env, payload={"project_id": 11, "block_key": "progress"})
        with patch(
            "odoo.addons.smart_construction_core.handlers.project_dashboard_block_fetch.ProjectDashboardSceneOrchestrator.build_runtime_block",
            return_value=fake_block,
        ):
            result = handler.handle(payload={"project_id": 11, "block_key": "progress"}, ctx={})
        self.assertTrue(result.get("ok"))
        self.assertEqual((((result.get("data") or {}).get("block") or {}).get("block_type")), "progress_summary")

    def test_open_is_deprecated_alias_wrapper(self):
        fake_entry = {
            "project_id": 11,
            "title": "Demo",
            "summary": {"project_code": "P-11"},
            "blocks": [{"key": "progress"}, {"key": "risks"}, {"key": "next_actions"}],
            "suggested_action": {"intent": "project.dashboard.block.fetch"},
            "runtime_fetch_hints": {"blocks": {"progress": {"intent": "project.dashboard.block.fetch"}}},
        }
        handler = ProjectDashboardOpenHandler(self.env, payload={"project_id": 11})
        with patch(
            "odoo.addons.smart_construction_core.handlers.project_dashboard_open.ProjectDashboardEnterHandler.handle",
            return_value={"ok": True, "data": fake_entry, "meta": {"intent": "project.dashboard.enter"}},
        ):
            result = handler.handle(payload={"project_id": 11}, ctx={})
        self.assertTrue(result.get("ok"))
        self.assertTrue(((result.get("meta") or {}).get("deprecated")))
        self.assertEqual((((result.get("data") or {}).get("entry") or {}).get("project_id")), 11)

    def test_dashboard_enter_uses_orchestration_carrier_shape(self):
        fake_entry = {
            "project_id": 11,
            "scene_key": "project.management",
            "scene_label": "项目驾驶舱",
            "state_fallback_text": "当前状态：已完成立项，正在查看项目驾驶舱。",
            "title": "项目驾驶舱：Demo",
            "summary": {"project_code": "P-11"},
            "blocks": [{"key": "progress"}, {"key": "risks"}, {"key": "next_actions"}],
            "suggested_action": {"intent": "project.dashboard.block.fetch"},
            "runtime_fetch_hints": {"blocks": {"progress": {"intent": "project.dashboard.block.fetch"}}},
        }
        handler = ProjectDashboardEnterHandler(self.env, payload={"project_id": 11})
        with patch(
            "odoo.addons.smart_construction_core.handlers.project_dashboard_enter.ProjectDashboardSceneOrchestrator.build_entry",
            return_value=fake_entry,
        ):
            result = handler.handle(payload={"project_id": 11}, ctx={})
        self.assertTrue(result.get("ok"))
        self.assertEqual(((result.get("data") or {}).get("scene_key")), "project.management")

    def test_dashboard_orchestrator_runtime_block_shape(self):
        project = self.env["project.project"].create(
            {
                "name": "Dashboard Orchestrator Test",
                "manager_id": self.env.user.id,
                "user_id": self.env.user.id,
            }
        )
        orchestrator = ProjectDashboardSceneOrchestrator(self.env)
        result = orchestrator.build_runtime_block("progress", project_id=project.id, context={})
        block = result.get("block") if isinstance(result.get("block"), dict) else {}

        self.assertEqual(result.get("block_key"), "progress")
        self.assertTrue(isinstance(block, dict))

    def test_dashboard_service_build_block_returns_block_payload(self):
        project = self.env["project.project"].create(
            {
                "name": "Dashboard Build Block Test",
                "manager_id": self.env.user.id,
                "user_id": self.env.user.id,
            }
        )
        service = ProjectDashboardService(self.env)
        block = service.build_block("progress", project=project, context={})
        self.assertTrue(isinstance(block, dict))
        self.assertTrue(str(block.get("block_type") or "").strip())
