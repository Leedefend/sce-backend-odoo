# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged

from odoo.addons.smart_core.core.scene_ready_contract_builder import build_scene_ready_contract_v1
from odoo.addons.smart_core.core.ui_base_contract_adapter import adapt_ui_base_contract


def _sample_ui_base_contract(model: str = "project.project") -> dict:
    return {
        "model": model,
        "views": {
            "tree": {
                "columns": ["name", "state", "manager_id"],
                "fields": ["name", "state", "manager_id"],
            },
            "form": {
                "fields": ["name", "manager_id", "start_date"],
            },
        },
        "fields": {
            "name": {"type": "char", "string": "项目名称"},
            "manager_id": {"type": "many2one", "string": "项目经理"},
            "state": {"type": "selection", "string": "状态"},
            "start_date": {"type": "date", "string": "开始日期"},
        },
        "search": {
            "default_sort": "write_date desc",
            "filters": [{"key": "my", "label": "我的项目", "domain": [["manager_id", "=", "uid"]]}],
            "group_by": [{"field": "state", "label": "按状态"}],
            "fields": ["name", "manager_id"],
        },
        "permissions": {
            "visible": True,
            "allowed": True,
            "required_capabilities": ["projects.list"],
        },
        "workflow": {
            "state_field": "state",
            "states": ["draft", "active"],
            "transitions": [{"key": "confirm", "from": "draft", "to": "active"}],
        },
        "validator": {
            "required_fields": ["name", "manager_id"],
        },
        "actions": {
            "items": [
                {"key": "create_project", "label": "创建项目", "intent": "record.create"},
                {"key": "export_list", "label": "导出", "intent": "record.export"},
            ]
        },
    }


@tagged("post_install", "-at_install", "smart_core", "scene_runtime_chain")
class TestSceneRuntimeContractChain(TransactionCase):
    def test_ui_base_adapter_emits_seven_fact_buckets(self):
        payload = adapt_ui_base_contract(_sample_ui_base_contract(), scene_key="projects.list")
        orchestrator_input = payload.get("orchestrator_input") or {}
        self.assertEqual(orchestrator_input.get("scene_key"), "projects.list")
        for key in (
            "view_fact",
            "field_fact",
            "search_fact",
            "action_fact",
            "permission_fact",
            "workflow_fact",
            "validation_fact",
        ):
            self.assertIn(key, orchestrator_input)

    def test_scene_ready_list_runtime_chain(self):
        contract = build_scene_ready_contract_v1(
            scenes=[
                {
                    "code": "projects.list",
                    "name": "项目列表",
                    "layout": {"kind": "list"},
                    "target": {"route": "/s/projects.list", "model": "project.project"},
                    "ui_base_contract": _sample_ui_base_contract(),
                }
            ],
            role_surface={"landing_scene_key": "projects.list"},
        )
        entries = contract.get("scenes") or []
        self.assertEqual(len(entries), 1)
        row = entries[0]
        self.assertTrue((row.get("search_surface") or {}).get("filters"))
        self.assertTrue((row.get("permission_surface") or {}).get("allowed"))
        self.assertTrue((row.get("action_surface") or {}).get("counts"))
        self.assertTrue(((row.get("meta") or {}).get("ui_base_orchestrator_input") or {}).get("view_fact"))

    def test_scene_ready_form_runtime_chain(self):
        contract = build_scene_ready_contract_v1(
            scenes=[
                {
                    "code": "projects.intake",
                    "name": "项目立项",
                    "layout": {"kind": "form"},
                    "target": {"route": "/s/projects.intake", "model": "project.project", "view_mode": "form"},
                    "blocks": [{"type": "form_block", "zone": "main", "source": "ui_base_contract.views.form"}],
                    "next_scene": "project.management",
                    "ui_base_contract": _sample_ui_base_contract(),
                }
            ],
            role_surface={"landing_scene_key": "projects.intake"},
        )
        row = (contract.get("scenes") or [])[0]
        validation_surface = row.get("validation_surface") or {}
        workflow_surface = row.get("workflow_surface") or {}
        self.assertIn("name", validation_surface.get("required_fields") or [])
        self.assertEqual(workflow_surface.get("state_field"), "state")
        self.assertEqual(row.get("next_scene"), "project.management")
        self.assertEqual(row.get("next_scene_route"), "/s/project.management")

    def test_scene_ready_form_next_scene_from_provider(self):
        def _provider(scene_key: str = "", runtime: dict | None = None, context: dict | None = None):
            _ = runtime or {}
            _ = context or {}
            return {
                "scene_key": scene_key,
                "next_scene": "contracts.workspace",
                "next_scene_route": "/s/contracts.workspace",
            }

        contract = build_scene_ready_contract_v1(
            scenes=[
                {
                    "code": "projects.intake",
                    "name": "项目立项",
                    "layout": {"kind": "form"},
                    "target": {"route": "/s/projects.intake", "model": "project.project", "view_mode": "form"},
                    "blocks": [{"type": "form_block", "zone": "main", "source": "ui_base_contract.views.form"}],
                    "providers": [{"key": "test.intake.provider"}],
                    "provider_registry": {
                        "test.intake.provider": _provider,
                    },
                    "ui_base_contract": _sample_ui_base_contract(),
                }
            ],
            role_surface={"landing_scene_key": "projects.intake"},
        )
        row = (contract.get("scenes") or [])[0]
        self.assertEqual(row.get("next_scene"), "contracts.workspace")
        self.assertEqual(row.get("next_scene_route"), "/s/contracts.workspace")

    def test_scene_ready_workspace_runtime_chain(self):
        contract = build_scene_ready_contract_v1(
            scenes=[
                {
                    "code": "workspace.home",
                    "name": "工作台",
                    "layout": {"kind": "workspace"},
                    "target": {"route": "/s/workspace.home"},
                    "ui_base_contract": _sample_ui_base_contract(),
                }
            ],
            role_surface={"landing_scene_key": "workspace.home"},
        )
        row = (contract.get("scenes") or [])[0]
        search_surface = row.get("search_surface") or {}
        self.assertEqual(search_surface.get("fields"), [])
        self.assertEqual(search_surface.get("group_by"), [])

    def test_scene_ready_finance_actions_include_mutation_and_refresh_policy(self):
        contract = build_scene_ready_contract_v1(
            scenes=[
                {
                    "code": "finance.payment_requests",
                    "name": "付款申请审批",
                    "layout": {"kind": "list"},
                    "target": {"route": "/s/finance.payment_requests", "model": "finance.payment.request"},
                    "ui_base_contract": _sample_ui_base_contract(model="finance.payment.request"),
                }
            ],
            role_surface={"landing_scene_key": "finance.payment_requests"},
        )
        row = (contract.get("scenes") or [])[0]
        actions = row.get("actions") or []
        self.assertGreaterEqual(len(actions), 3)
        first_target = (actions[0] or {}).get("target") or {}
        self.assertEqual(((first_target.get("mutation") or {}).get("model") or ""), "finance.payment.request")
        self.assertTrue(((first_target.get("refresh_policy") or {}).get("on_success") or []))

    def test_scene_ready_risk_actions_include_mutation_and_refresh_policy(self):
        contract = build_scene_ready_contract_v1(
            scenes=[
                {
                    "code": "risk.center",
                    "name": "风险中心",
                    "layout": {"kind": "workspace"},
                    "target": {"route": "/s/risk.center", "model": "project.risk.action"},
                    "ui_base_contract": _sample_ui_base_contract(model="project.risk.action"),
                }
            ],
            role_surface={"landing_scene_key": "risk.center"},
        )
        row = (contract.get("scenes") or [])[0]
        actions = row.get("actions") or []
        self.assertGreaterEqual(len(actions), 3)
        first_target = (actions[0] or {}).get("target") or {}
        self.assertEqual(((first_target.get("mutation") or {}).get("model") or ""), "project.risk.action")
        self.assertTrue(((first_target.get("refresh_policy") or {}).get("on_success") or []))

    def test_pilot_core_scenes_materialize_strict_contract_fields(self):
        scenes = [
            {
                "code": "workspace.home",
                "name": "工作台",
                "layout": {"kind": "workspace"},
                "target": {"route": "/my-work"},
                "ui_base_contract": _sample_ui_base_contract(model="project.risk.action"),
            },
            {
                "code": "finance.payment_requests",
                "name": "付款申请审批",
                "layout": {"kind": "list"},
                "target": {"route": "/s/finance.payment_requests", "model": "finance.payment.request"},
                "ui_base_contract": _sample_ui_base_contract(model="finance.payment.request"),
            },
            {
                "code": "risk.center",
                "name": "风险中心",
                "layout": {"kind": "workspace"},
                "target": {"route": "/s/risk.center", "model": "project.risk.action"},
                "ui_base_contract": _sample_ui_base_contract(model="project.risk.action"),
            },
            {
                "code": "project.management",
                "name": "项目驾驶舱",
                "layout": {"kind": "workspace"},
                "target": {"route": "/s/project.management", "model": "project.project"},
                "ui_base_contract": _sample_ui_base_contract(model="project.project"),
            },
        ]

        contract = build_scene_ready_contract_v1(
            scenes=scenes,
            role_surface={"landing_scene_key": "workspace.home"},
        )
        rows = contract.get("scenes") or []
        self.assertEqual(len(rows), 4)
        rows_by_key = {
            ((row.get("scene") or {}).get("key") or ""): row
            for row in rows
            if isinstance(row, dict)
        }
        for key in ("workspace.home", "finance.payment_requests", "risk.center", "project.management"):
            row = rows_by_key.get(key) or {}
            self.assertEqual(row.get("scene_tier"), "core")
            runtime_policy = row.get("runtime_policy") or {}
            self.assertTrue(bool(runtime_policy.get("strict_contract_mode")))
            surface = row.get("surface") or {}
            self.assertTrue(bool(surface.get("kind")))
            self.assertTrue(bool((surface.get("intent") or {}).get("title")))
            self.assertTrue(isinstance(row.get("projection"), dict))
            self.assertTrue(isinstance(row.get("action_surface"), dict))
