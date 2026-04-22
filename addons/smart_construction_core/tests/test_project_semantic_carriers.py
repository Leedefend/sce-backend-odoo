# -*- coding: utf-8 -*-
import importlib.util
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[3]


def _load_module(module_name: str, relative_path: str):
    target = ROOT / relative_path
    spec = importlib.util.spec_from_file_location(module_name, target)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


STATE_EXPLAIN_MODULE = _load_module(
    "odoo.addons.smart_construction_core.services.project_state_explain_service",
    "addons/smart_construction_core/services/project_state_explain_service.py",
)
PROJECT_CONTEXT_MODULE = _load_module(
    "odoo.addons.smart_construction_core.services.project_context_contract",
    "addons/smart_construction_core/services/project_context_contract.py",
)
CONTRACT_GOVERNANCE_MODULE = _load_module(
    "smart_core_contract_governance_test_module",
    "addons/smart_core/utils/contract_governance.py",
)

build_project_context = PROJECT_CONTEXT_MODULE.build_project_context
ProjectStateExplainService = STATE_EXPLAIN_MODULE.ProjectStateExplainService
apply_project_form_domain_override = CONTRACT_GOVERNANCE_MODULE.apply_project_form_domain_override


class TestProjectSemanticCarriers(unittest.TestCase):
    def test_build_project_context_adds_explicit_execution_stage_and_condition_aliases(self):
        project = SimpleNamespace(
            id=7,
            display_name="项目-A",
            name="项目-A",
            lifecycle_state="in_progress",
            sc_execution_state="ready",
            sc_execution_state_label="准备完成",
            health_state="attention",
            state="legacy",
        )

        result = build_project_context(project)

        self.assertEqual(result.get("execution_stage"), "in_progress")
        self.assertEqual(result.get("execution_stage_label"), "在建")
        self.assertEqual(result.get("stage"), "in_progress")
        self.assertEqual(result.get("stage_label"), "在建")
        self.assertEqual(result.get("project_condition"), "attention")
        self.assertEqual(result.get("status"), "attention")

    def test_state_explain_adds_execution_stage_and_project_condition_aliases(self):
        project = SimpleNamespace(
            lifecycle_state="closing",
            health_state="risk",
            state="legacy",
        )

        result = ProjectStateExplainService(env=None).build(project)

        self.assertEqual(result.get("execution_stage_label"), "收口")
        self.assertEqual(result.get("stage_label"), "收口")
        self.assertIn("收口阶段", result.get("execution_stage_explain") or "")
        self.assertEqual(result.get("execution_stage_explain"), result.get("stage_explain"))
        self.assertEqual(result.get("project_condition_explain"), "risk")
        self.assertEqual(result.get("status_explain"), "risk")

    def test_state_explain_empty_case_keeps_compat_and_new_fields(self):
        result = ProjectStateExplainService(env=None).build(None)

        self.assertEqual(result.get("execution_stage_label"), "未选择项目")
        self.assertEqual(result.get("stage_label"), "未选择项目")
        self.assertEqual(result.get("project_condition_explain"), "请先选择项目或创建项目。")
        self.assertEqual(result.get("status_explain"), "请先选择项目或创建项目。")

    def test_project_list_label_uses_project_execution_stage(self):
        self.assertEqual(
            CONTRACT_GOVERNANCE_MODULE._PROJECT_LIST_COLUMN_LABELS.get("lifecycle_state"),
            "项目执行阶段",
        )


if __name__ == "__main__":
    unittest.main()
