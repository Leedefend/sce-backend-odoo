# -*- coding: utf-8 -*-
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "utils" / "contract_governance.py"


def _load_contract_governance():
    spec = importlib.util.spec_from_file_location("contract_governance_record_context_registry", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class ContractGovernanceRecordContextRegistryTests(unittest.TestCase):
    def setUp(self):
        self.contract_governance = _load_contract_governance()

    def test_core_has_no_default_business_record_context_clear_models(self):
        self.assertEqual(self.contract_governance.LEGACY_RECORD_CONTEXT_CLEAR_MODELS, set())

    def test_core_has_no_default_business_delete_only_models(self):
        self.assertNotIn("project.task", self.contract_governance.LEGACY_DELETE_ONLY_MODELS)

    def test_record_context_clear_models_must_be_registered_explicitly(self):
        self.contract_governance.register_legacy_record_context_clear_model("project.project")

        self.assertEqual(self.contract_governance.LEGACY_RECORD_CONTEXT_CLEAR_MODELS, {"project.project"})

    def test_business_delete_only_models_must_be_registered_explicitly(self):
        self.contract_governance.register_legacy_delete_only_model("project.task")

        self.assertIn("project.task", self.contract_governance.LEGACY_DELETE_ONLY_MODELS)

    def test_core_has_no_default_business_field_presentations(self):
        self.assertEqual(self.contract_governance._LEGACY_FIELD_PRESENTATION_REGISTRY, {})

    def test_core_has_no_default_business_standard_list_profiles(self):
        self.assertEqual(self.contract_governance._LEGACY_STANDARD_LIST_PROFILE_REGISTRY, [])

    def test_core_has_no_default_business_kanban_row_actions(self):
        self.assertEqual(self.contract_governance._LEGACY_KANBAN_ROW_ACTION_REGISTRY, {})

    def test_core_has_no_default_business_kanban_profiles(self):
        self.assertEqual(self.contract_governance._LEGACY_PROJECT_KANBAN_PROFILE_REGISTRY, {})

    def test_core_has_no_default_business_form_profiles(self):
        self.assertEqual(self.contract_governance._LEGACY_PROJECT_FORM_PROFILE_REGISTRY, {})

    def test_core_has_no_default_business_form_governance_models(self):
        self.assertEqual(self.contract_governance._LEGACY_PROJECT_FORM_GOVERNANCE_MODELS, set())
        self.assertEqual(self.contract_governance._LEGACY_PROJECT_TASK_FORM_GOVERNANCE_MODELS, set())
        self.assertEqual(self.contract_governance._LEGACY_PROJECT_KANBAN_GOVERNANCE_MODELS, set())

    def test_core_has_no_default_business_capability_groups(self):
        self.assertEqual(self.contract_governance._CAPABILITY_GROUP_PROFILE_REGISTRY, {})

        capabilities = self.contract_governance.normalize_capabilities([{"key": "project.read", "name": "Project read"}])

        self.assertEqual(capabilities[0]["group_key"], "others")
        self.assertEqual(capabilities[0]["group_label"], "Other")

    def test_business_capability_groups_must_be_registered_explicitly(self):
        self.contract_governance.register_capability_group_profile(
            "project_management",
            {
                "label": "项目管理",
                "icon": "briefcase",
                "key_prefixes": ["project.", "scene.project"],
            },
        )

        capabilities = self.contract_governance.normalize_capabilities([{"key": "project.read", "name": "项目读取"}])

        self.assertEqual(capabilities[0]["group_key"], "project_management")
        self.assertEqual(capabilities[0]["group_label"], "项目管理")
        self.assertEqual(capabilities[0]["group_icon"], "briefcase")

    def test_core_has_no_default_business_scene_semantic_profiles(self):
        self.assertEqual(self.contract_governance._SCENE_SEMANTIC_PROFILE_REGISTRY, [])

        scenes = self.contract_governance.normalize_scenes([{"code": "projects.ledger", "name": "Project ledger"}])

        self.assertEqual((scenes[0]["scene_meta"] or {}).get("purpose"), "Business work")

    def test_business_scene_semantics_must_be_registered_explicitly(self):
        self.contract_governance.register_scene_semantic_profile(
            {
                "purpose": "项目推进",
                "code_prefixes": ["projects."],
                "code_contains": ["project"],
            }
        )

        scenes = self.contract_governance.normalize_scenes([{"code": "projects.ledger", "name": "项目台账"}])

        self.assertEqual((scenes[0]["scene_meta"] or {}).get("purpose"), "项目推进")

    def test_business_form_governance_models_must_be_registered_explicitly(self):
        self.contract_governance.register_legacy_project_form_governance_model("project.project")
        self.contract_governance.register_legacy_project_kanban_governance_model("project.project")
        self.contract_governance.register_legacy_project_task_form_governance_model("project.task")

        self.assertEqual(self.contract_governance._LEGACY_PROJECT_FORM_GOVERNANCE_MODELS, {"project.project"})
        self.assertEqual(self.contract_governance._LEGACY_PROJECT_KANBAN_GOVERNANCE_MODELS, {"project.project"})
        self.assertEqual(self.contract_governance._LEGACY_PROJECT_TASK_FORM_GOVERNANCE_MODELS, {"project.task"})

    def test_business_form_profiles_must_be_registered_explicitly(self):
        self.contract_governance.register_legacy_project_form_profile(
            "project.project",
            {
                "primary_fields": ["name", "project_type_id"],
                "create_hidden_fields": ["project_code", "stage_id"],
                "action_priorities": ["提交", "保存"],
                "action_noise_markers": ["评分"],
                "search_noise_markers": ["活动"],
                "action_group_labels": {"basic": "基础操作"},
                "max_fields": 12,
            },
        )

        self.assertEqual(
            self.contract_governance._LEGACY_PROJECT_FORM_PROFILE_REGISTRY,
            {
                "project.project": {
                    "primary_fields": ["name", "project_type_id"],
                    "create_hidden_fields": ["project_code", "stage_id"],
                    "action_priorities": ["提交", "保存"],
                    "action_noise_markers": ["评分"],
                    "search_noise_markers": ["活动"],
                    "action_group_labels": {"basic": "基础操作"},
                    "max_fields": 12,
                }
            },
        )

    def test_business_field_presentations_must_be_registered_explicitly(self):
        self.contract_governance.register_legacy_field_presentation(
            "project.project",
            "is_favorite",
            {
                "label": "我的收藏",
                "widget": "boolean_favorite",
                "cell_role": "favorite",
                "mutation": {
                    "type": "field_toggle",
                    "operation": "record_write",
                    "field": "is_favorite",
                    "value_type": "boolean",
                },
            },
        )

        self.assertEqual(
            self.contract_governance._LEGACY_FIELD_PRESENTATION_REGISTRY[("project.project", "is_favorite")],
            {
                "label": "我的收藏",
                "widget": "boolean_favorite",
                "cell_role": "favorite",
                "mutation": {
                    "type": "field_toggle",
                    "operation": "record_write",
                    "field": "is_favorite",
                    "value_type": "boolean",
                },
            },
        )

    def test_business_standard_list_profiles_must_be_registered_explicitly(self):
        self.contract_governance.register_legacy_standard_list_profile(
            {
                "profile_key": "project.project.list",
                "model_name": "project.project",
                "columns_order": ["name", "project_code"],
                "column_labels": {"name": "名称", "project_code": "项目编号"},
                "row_primary": "name",
                "status_field": "lifecycle_state",
                "strict_columns": True,
            }
        )

        self.assertEqual(
            self.contract_governance._LEGACY_STANDARD_LIST_PROFILE_REGISTRY,
            [
                {
                    "profile_key": "project.project.list",
                    "model_name": "project.project",
                    "columns_order": ["name", "project_code"],
                    "column_labels": {"name": "名称", "project_code": "项目编号"},
                    "row_primary": "name",
                    "row_secondary": "",
                    "status_field": "lifecycle_state",
                    "strict_columns": True,
                    "signature_any": [],
                }
            ],
        )

    def test_business_kanban_row_actions_must_be_registered_explicitly(self):
        self.contract_governance.register_legacy_kanban_row_action(
            "project.project",
            {
                "key": "open_project_dashboard",
                "label": "进入项目驾驶舱",
                "intent": "open_scene",
                "target": {"scene_key": "project.management"},
            },
        )

        self.assertEqual(
            self.contract_governance._LEGACY_KANBAN_ROW_ACTION_REGISTRY,
            {
                "project.project": [
                    {
                        "key": "open_project_dashboard",
                        "name": "open_project_dashboard",
                        "label": "进入项目驾驶舱",
                        "intent": "open_scene",
                        "target": {"scene_key": "project.management"},
                    }
                ]
            },
        )

    def test_business_kanban_profiles_must_be_registered_explicitly(self):
        self.contract_governance.register_legacy_project_kanban_profile(
            "project.project",
            {
                "title_field": "name",
                "primary_fields": ["name", "project_code"],
                "secondary_fields": ["manager_id"],
                "status_fields": ["lifecycle_state"],
                "max_meta": 3,
            },
        )

        self.assertEqual(
            self.contract_governance._LEGACY_PROJECT_KANBAN_PROFILE_REGISTRY,
            {
                "project.project": {
                    "title_field": "name",
                    "primary_fields": ["name", "project_code"],
                    "secondary_fields": ["manager_id"],
                    "status_fields": ["lifecycle_state"],
                    "max_meta": 3,
                }
            },
        )


if __name__ == "__main__":
    unittest.main()
