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
            "title": "Demo",
            "summary": {"project_code": "P-11"},
            "blocks": [{"key": "progress"}, {"key": "risks"}, {"key": "next_actions"}],
            "suggested_action": {"intent": "project.dashboard.block.fetch"},
            "runtime_fetch_hints": {"blocks": {"progress": {"intent": "project.dashboard.block.fetch"}}},
        }
        handler = ProjectDashboardEnterHandler(self.env, payload={"project_id": 11})
        with patch(
            "odoo.addons.smart_construction_core.handlers.project_dashboard_enter.ProjectDashboardService.build_entry",
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
            "odoo.addons.smart_construction_core.handlers.project_dashboard_block_fetch.ProjectDashboardService.build_runtime_block",
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
