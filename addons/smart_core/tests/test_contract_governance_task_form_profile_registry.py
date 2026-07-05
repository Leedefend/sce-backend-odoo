# -*- coding: utf-8 -*-
import importlib.util
import sys
import unittest
from pathlib import Path


SMART_CORE_DIR = Path(__file__).resolve().parents[1]


def _load_contract_governance():
    sys.modules.pop("smart_core_contract_governance_under_test", None)
    spec = importlib.util.spec_from_file_location(
        "smart_core_contract_governance_under_test",
        SMART_CORE_DIR / "utils" / "contract_governance.py",
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _task_form_contract():
    return {
        "head": {"model": "project.task", "view_type": "form"},
        "fields": {
            "name": {"string": "Name", "type": "char"},
            "project_id": {"string": "Project", "type": "many2one"},
            "description": {"string": "Description", "type": "text"},
        },
        "views": {"form": {"layout": []}},
    }


class TestContractGovernanceTaskFormProfileRegistry(unittest.TestCase):
    def test_registered_task_model_without_profile_does_not_inject_layout(self):
        module = _load_contract_governance()
        module.register_legacy_project_task_form_governance_model("project.task")

        data = _task_form_contract()
        module.apply_project_form_domain_override(data, "user")

        self.assertNotIn("visible_fields", data)
        self.assertEqual(data["views"]["form"]["layout"], [])

    def test_task_form_profile_is_extension_registered(self):
        module = _load_contract_governance()
        module.register_legacy_project_task_form_governance_model("project.task")
        module.register_legacy_project_task_form_profile(
            "project.task",
            {
                "fields": ["name", "project_id", "description"],
                "field_labels": {
                    "name": "任务名称",
                    "project_id": "所属项目",
                    "description": "执行说明",
                },
                "core_group_label": "任务基础信息",
                "description_group_label": "任务说明",
                "description_fields": ["description"],
            },
        )

        data = _task_form_contract()
        module.apply_project_form_domain_override(data, "user")

        self.assertEqual(data["visible_fields"], ["name", "project_id", "description"])
        self.assertEqual([row["label"] for row in data["field_groups"]], ["任务基础信息", "任务说明"])
        groups = data["views"]["form"]["layout"][0]["children"]
        self.assertEqual(groups[0]["string"], "任务基础信息")
        self.assertEqual(groups[1]["string"], "任务说明")
        self.assertEqual([node["fieldInfo"]["label"] for node in groups[0]["children"]], ["任务名称", "所属项目"])
        self.assertEqual([node["fieldInfo"]["label"] for node in groups[1]["children"]], ["执行说明"])


if __name__ == "__main__":
    unittest.main()
