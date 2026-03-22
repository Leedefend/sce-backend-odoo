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
from odoo.addons.smart_core.orchestration.project_plan_bootstrap_scene_orchestrator import (
    ProjectPlanBootstrapSceneOrchestrator,
)
from odoo.addons.smart_construction_core.services.project_execution_service import (
    ProjectExecutionService,
)
from odoo.addons.smart_construction_core.services.project_plan_bootstrap_service import (
    ProjectPlanBootstrapService,
)
from odoo.addons.smart_core.orchestration.project_execution_scene_orchestrator import (
    ProjectExecutionSceneOrchestrator,
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
            "scene_key": "project.plan_bootstrap",
            "scene_label": "计划准备",
            "state_fallback_text": "当前状态：正在核对计划准备度。",
            "title": "计划编排：Demo",
            "summary": {"project_code": "P-21"},
            "blocks": [{"key": "plan_summary_detail"}, {"key": "plan_tasks"}, {"key": "next_actions"}],
            "suggested_action": {"intent": "project.plan_bootstrap.block.fetch"},
            "runtime_fetch_hints": {"blocks": {"plan_summary_detail": {"intent": "project.plan_bootstrap.block.fetch"}}},
        }
        handler = ProjectPlanBootstrapEnterHandler(self.env, payload={"project_id": 21})
        with patch(
            "odoo.addons.smart_construction_core.handlers.project_plan_bootstrap_enter.ProjectPlanBootstrapSceneOrchestrator.build_entry",
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
            "odoo.addons.smart_construction_core.handlers.project_plan_bootstrap_block_fetch.ProjectPlanBootstrapSceneOrchestrator.build_runtime_block",
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

    def test_plan_enter_uses_orchestration_carrier_shape(self):
        fake_entry = {
            "project_id": 21,
            "scene_key": "project.plan_bootstrap",
            "scene_label": "计划准备",
            "state_fallback_text": "当前状态：正在核对计划准备度。",
            "title": "计划准备：Demo",
            "summary": {"project_code": "P-21"},
            "blocks": [{"key": "plan_summary_detail"}, {"key": "plan_tasks"}, {"key": "next_actions"}],
            "suggested_action": {"intent": "project.plan_bootstrap.block.fetch"},
            "runtime_fetch_hints": {"blocks": {"next_actions": {"intent": "project.plan_bootstrap.block.fetch"}}},
        }
        handler = ProjectPlanBootstrapEnterHandler(self.env, payload={"project_id": 21})
        with patch(
            "odoo.addons.smart_construction_core.handlers.project_plan_bootstrap_enter.ProjectPlanBootstrapSceneOrchestrator.build_entry",
            return_value=fake_entry,
        ):
            result = handler.handle(payload={"project_id": 21}, ctx={})
        self.assertTrue(result.get("ok"))
        self.assertEqual(((result.get("data") or {}).get("scene_key")), "project.plan_bootstrap")

    def test_plan_orchestrator_runtime_block_shape(self):
        project = self.env["project.project"].create(
            {
                "name": "Plan Orchestrator Test",
                "manager_id": self.env.user.id,
                "user_id": self.env.user.id,
                "date_start": "2026-03-23",
            }
        )
        orchestrator = ProjectPlanBootstrapSceneOrchestrator(self.env)
        result = orchestrator.build_runtime_block("next_actions", project_id=project.id, context={})
        block = result.get("block") if isinstance(result.get("block"), dict) else {}
        self.assertEqual(result.get("block_key"), "next_actions")
        self.assertTrue(isinstance(block, dict))

    def test_plan_service_build_block_returns_block_payload(self):
        project = self.env["project.project"].create(
            {
                "name": "Plan Build Block Test",
                "manager_id": self.env.user.id,
                "user_id": self.env.user.id,
                "date_start": "2026-03-23",
            }
        )
        service = ProjectPlanBootstrapService(self.env)
        block = service.build_block("plan_summary_detail", project=project, context={})
        self.assertTrue(isinstance(block, dict))
        self.assertTrue(str(block.get("block_type") or "").strip())

    def test_execution_enter_returns_scheduling_placeholder(self):
        fake_entry = {
            "project_id": 21,
            "scene_key": "project.execution",
            "title": "项目执行：Demo",
            "summary": {"project_code": "P-21"},
            "blocks": [{"key": "execution_tasks"}],
            "suggested_action": {"intent": "project.execution.block.fetch"},
            "runtime_fetch_hints": {"blocks": {"execution_tasks": {"intent": "project.execution.block.fetch"}}},
        }
        handler = ProjectExecutionEnterHandler(self.env, payload={"project_id": 21})
        with patch(
            "odoo.addons.smart_construction_core.handlers.project_execution_enter.ProjectExecutionSceneOrchestrator.build_entry",
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
        activity_count = self.env["mail.activity"].sudo().search_count(
            [
                ("res_model", "=", "project.project"),
                ("res_id", "=", project.id),
                ("summary", "=", "执行推进跟进"),
            ]
        )
        self.assertEqual(activity_count, 1)

        result_done = handler.handle(payload={"project_id": project.id, "target_state": "done"}, ctx={})
        self.assertTrue(result_done.get("ok"))
        self.assertEqual(((result_done.get("data") or {}).get("result")), "success")

        task.invalidate_recordset(["sc_state", "kanban_state"])
        self.assertEqual(task.sc_state, "done")
        self.assertEqual(task.kanban_state, "done")
        activity_count = self.env["mail.activity"].sudo().search_count(
            [
                ("res_model", "=", "project.project"),
                ("res_id", "=", project.id),
                ("summary", "=", "执行推进跟进"),
            ]
        )
        self.assertEqual(activity_count, 0)

    def test_execution_advance_blocks_when_multiple_open_tasks_exist(self):
        project = self.env["project.project"].create(
            {
                "name": "Execution Scope Guard Test",
                "manager_id": self.env.user.id,
                "user_id": self.env.user.id,
            }
        )
        self.env["project.task"].create(
            {
                "name": "Root Task A",
                "project_id": project.id,
                "user_ids": [(6, 0, [self.env.user.id])],
                "user_id": self.env.user.id,
            }
        )
        self.env["project.task"].create(
            {
                "name": "Root Task B",
                "project_id": project.id,
                "user_ids": [(6, 0, [self.env.user.id])],
                "user_id": self.env.user.id,
            }
        )

        handler = ProjectExecutionAdvanceHandler(self.env, payload={"project_id": project.id})
        result = handler.handle(payload={"project_id": project.id}, ctx={})
        self.assertTrue(result.get("ok"))
        self.assertEqual(((result.get("data") or {}).get("result")), "blocked")
        self.assertEqual(
            ((result.get("data") or {}).get("reason_code")),
            "EXECUTION_SCOPE_MULTI_OPEN_TASKS_UNSUPPORTED",
        )

    def test_execution_pilot_precheck_block_reports_ready_project(self):
        project = self.env["project.project"].create(
            {
                "name": "Pilot Precheck Ready Test",
                "manager_id": self.env.user.id,
                "user_id": self.env.user.id,
                "date_start": "2026-03-23",
            }
        )
        self.env["project.task"].create(
            {
                "name": "Project Root Task",
                "project_id": project.id,
                "user_ids": [(6, 0, [self.env.user.id])],
                "user_id": self.env.user.id,
            }
        )

        service = ProjectExecutionService(self.env)
        block = service.build_block("pilot_precheck", project=project, context={})
        data = block.get("data") if isinstance(block.get("data"), dict) else {}
        summary = data.get("summary") if isinstance(data.get("summary"), dict) else {}
        checks = data.get("checks") if isinstance(data.get("checks"), list) else []

        self.assertEqual(block.get("block_type"), "checklist")
        self.assertEqual(summary.get("overall_state"), "ready")
        self.assertEqual(summary.get("failed_count"), 0)
        self.assertTrue(checks)

    def test_execution_pilot_precheck_detects_multi_open_task_violation(self):
        project = self.env["project.project"].create(
            {
                "name": "Pilot Precheck Blocked Test",
                "manager_id": self.env.user.id,
                "user_id": self.env.user.id,
                "date_start": "2026-03-23",
            }
        )
        self.env["project.task"].create(
            {
                "name": "Project Root Task A",
                "project_id": project.id,
                "user_ids": [(6, 0, [self.env.user.id])],
                "user_id": self.env.user.id,
            }
        )
        self.env["project.task"].create(
            {
                "name": "Project Root Task B",
                "project_id": project.id,
                "user_ids": [(6, 0, [self.env.user.id])],
                "user_id": self.env.user.id,
            }
        )

        service = ProjectExecutionService(self.env)
        block = service.build_block("pilot_precheck", project=project, context={})
        data = block.get("data") if isinstance(block.get("data"), dict) else {}
        summary = data.get("summary") if isinstance(data.get("summary"), dict) else {}

        self.assertEqual(summary.get("overall_state"), "blocked")
        self.assertEqual(summary.get("primary_reason_code"), "PILOT_SINGLE_OPEN_TASK_REQUIRED")

    def test_execution_enter_uses_orchestration_carrier_shape(self):
        fake_entry = {
            "project_id": 21,
            "scene_key": "project.execution",
            "scene_label": "执行推进",
            "state_fallback_text": "当前状态：正在查看执行推进状态。",
            "title": "执行推进：Demo",
            "summary": {"project_code": "P-21"},
            "blocks": [{"key": "execution_tasks"}, {"key": "pilot_precheck"}, {"key": "next_actions"}],
            "suggested_action": {"intent": "project.execution.block.fetch"},
            "runtime_fetch_hints": {"blocks": {"next_actions": {"intent": "project.execution.block.fetch"}}},
        }
        handler = ProjectExecutionEnterHandler(self.env, payload={"project_id": 21})
        with patch(
            "odoo.addons.smart_construction_core.handlers.project_execution_enter.ProjectExecutionSceneOrchestrator.build_entry",
            return_value=fake_entry,
        ):
            result = handler.handle(payload={"project_id": 21}, ctx={})
        self.assertTrue(result.get("ok"))
        self.assertEqual(((result.get("data") or {}).get("scene_key")), "project.execution")

    def test_execution_orchestrator_runtime_block_shape(self):
        project = self.env["project.project"].create(
            {
                "name": "Execution Orchestrator Test",
                "manager_id": self.env.user.id,
                "user_id": self.env.user.id,
                "date_start": "2026-03-23",
            }
        )
        self.env["project.task"].create(
            {
                "name": "Project Root Task",
                "project_id": project.id,
                "user_ids": [(6, 0, [self.env.user.id])],
                "user_id": self.env.user.id,
            }
        )
        orchestrator = ProjectExecutionSceneOrchestrator(self.env)
        result = orchestrator.build_runtime_block("next_actions", project_id=project.id, context={})
        block = result.get("block") if isinstance(result.get("block"), dict) else {}
        data = block.get("data") if isinstance(block.get("data"), dict) else {}
        actions = data.get("actions") if isinstance(data.get("actions"), list) else []

        self.assertEqual(result.get("block_key"), "next_actions")
        self.assertTrue(actions)
