# -*- coding: utf-8 -*-

from unittest.mock import patch

from odoo.tests.common import TransactionCase, tagged

from odoo.addons.smart_construction_core.handlers.project_plan_bootstrap_block_fetch import (
    ProjectPlanBootstrapBlockFetchHandler,
)
from odoo.addons.smart_construction_core.handlers.project_plan_bootstrap_enter import (
    ProjectPlanBootstrapEnterHandler,
)
from odoo.addons.smart_construction_core.handlers.project_execution_enter import (
    ProjectExecutionEnterHandler,
)
from odoo.addons.smart_construction_core.handlers.project_execution_advance import (
    ProjectExecutionAdvanceHandler,
)


@tagged("sc_smoke", "project_plan_bootstrap_backend")
class TestProjectPlanBootstrapBackend(TransactionCase):
    def test_entry_requires_project_id(self):
        handler = ProjectPlanBootstrapEnterHandler(self.env, payload={})
        result = handler.handle(payload={}, ctx={})
        self.assertFalse(result.get("ok"))
        self.assertEqual(((result.get("error") or {}).get("code")), "PROJECT_CONTEXT_MISSING")

    def test_entry_returns_minimal_shape(self):
        fake_entry = {
            "project_id": 21,
            "title": "计划编排：Demo",
            "summary": {"project_code": "P-21"},
            "blocks": [{"key": "plan_summary_detail"}, {"key": "plan_tasks"}, {"key": "next_actions"}],
            "suggested_action": {"intent": "project.plan_bootstrap.block.fetch"},
            "runtime_fetch_hints": {"blocks": {"plan_summary_detail": {"intent": "project.plan_bootstrap.block.fetch"}}},
        }
        handler = ProjectPlanBootstrapEnterHandler(self.env, payload={"project_id": 21})
        with patch(
            "odoo.addons.smart_construction_core.handlers.project_plan_bootstrap_enter.ProjectPlanBootstrapService.build_entry",
            return_value=fake_entry,
        ):
            result = handler.handle(payload={"project_id": 21}, ctx={})
        self.assertTrue(result.get("ok"))
        self.assertEqual(set((result.get("data") or {}).keys()), set(fake_entry.keys()))

    def test_runtime_block_fetch_keeps_block_level_payload(self):
        fake_block = {
            "project_id": 21,
            "block_key": "plan_summary_detail",
            "block": {"block_type": "plan_summary_detail", "state": "ready", "data": {}},
            "degraded": False,
        }
        handler = ProjectPlanBootstrapBlockFetchHandler(self.env, payload={"project_id": 21, "block_key": "plan_summary_detail"})
        with patch(
            "odoo.addons.smart_construction_core.handlers.project_plan_bootstrap_block_fetch.ProjectPlanBootstrapService.build_runtime_block",
            return_value=fake_block,
        ):
            result = handler.handle(payload={"project_id": 21, "block_key": "plan_summary_detail"}, ctx={})
        self.assertTrue(result.get("ok"))
        self.assertEqual((((result.get("data") or {}).get("block") or {}).get("block_type")), "plan_summary_detail")

    def test_execution_enter_requires_project_id(self):
        handler = ProjectExecutionEnterHandler(self.env, payload={})
        result = handler.handle(payload={}, ctx={})
        self.assertFalse(result.get("ok"))
        self.assertEqual(((result.get("error") or {}).get("code")), "PROJECT_CONTEXT_MISSING")

    def test_execution_enter_returns_scheduling_placeholder(self):
        fake_entry = {
            "project_id": 21,
            "title": "项目执行：Demo",
            "summary": {"project_code": "P-21"},
            "blocks": [{"key": "execution_tasks"}],
            "suggested_action": {"intent": "project.execution.block.fetch"},
            "runtime_fetch_hints": {"blocks": {"execution_tasks": {"intent": "project.execution.block.fetch"}}},
        }
        handler = ProjectExecutionEnterHandler(self.env, payload={"project_id": 21})
        with patch(
            "odoo.addons.smart_construction_core.handlers.project_execution_enter.ProjectExecutionService.build_entry",
            return_value=fake_entry,
        ):
            result = handler.handle(payload={"project_id": 21}, ctx={})
        self.assertTrue(result.get("ok"))
        self.assertEqual(set((result.get("data") or {}).keys()), set(fake_entry.keys()))

    def test_execution_advance_requires_project_id(self):
        handler = ProjectExecutionAdvanceHandler(self.env, payload={})
        result = handler.handle(payload={}, ctx={})
        self.assertFalse(result.get("ok"))
        self.assertEqual(((result.get("error") or {}).get("code")), "PROJECT_CONTEXT_MISSING")

    def test_execution_advance_updates_real_project_task(self):
        project = self.env["project.project"].create(
            {
                "name": "Execution Real Usage Test",
                "manager_id": self.env.user.id,
                "user_id": self.env.user.id,
            }
        )
        task = self.env["project.task"].create(
            {
                "name": "Root Task",
                "project_id": project.id,
                "user_ids": [(6, 0, [self.env.user.id])],
                "user_id": self.env.user.id,
            }
        )
        self.assertEqual(task.sc_state, "draft")

        handler = ProjectExecutionAdvanceHandler(self.env, payload={"project_id": project.id})
        result = handler.handle(payload={"project_id": project.id}, ctx={})
        self.assertTrue(result.get("ok"))
        self.assertEqual(((result.get("data") or {}).get("result")), "success")

        task.invalidate_recordset(["sc_state", "kanban_state"])
        self.assertEqual(task.sc_state, "in_progress")
        self.assertEqual(task.kanban_state, "normal")
