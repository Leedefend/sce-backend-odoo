# -*- coding: utf-8 -*-
import importlib.util
import sys
import unittest
from pathlib import Path


SMART_CORE_DIR = Path(__file__).resolve().parents[1]


def _load_contract_governance():
    sys.modules.pop("smart_core_contract_governance_kanban_under_test", None)
    spec = importlib.util.spec_from_file_location(
        "smart_core_contract_governance_kanban_under_test",
        SMART_CORE_DIR / "utils" / "contract_governance.py",
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _kanban_contract():
    return {
        "head": {"model": "project.project", "view_type": "kanban"},
        "fields": {
            "name": {"string": "Name", "type": "char"},
            "project_code": {"string": "Code", "type": "char"},
            "manager_id": {"string": "Manager", "type": "many2one"},
            "stage_id": {"string": "Stage", "type": "many2one"},
            "lifecycle_state": {"string": "State", "type": "selection"},
            "message_ids": {"string": "Messages", "type": "one2many"},
        },
        "views": {"kanban": {"fields": []}},
    }


class TestContractGovernanceKanbanProfileRegistry(unittest.TestCase):
    def test_registered_kanban_model_without_profile_uses_generic_fallback(self):
        module = _load_contract_governance()
        module.register_legacy_project_kanban_governance_model("project.project")

        data = _kanban_contract()
        module.apply_project_form_domain_override(data, "user")

        profile = data.get("kanban_profile") or {}
        self.assertEqual(profile.get("title_field"), "name")
        self.assertIn("name", profile.get("primary_fields") or [])
        self.assertNotIn("message_ids", ((data.get("views") or {}).get("kanban") or {}).get("fields") or [])

    def test_kanban_profile_is_extension_registered(self):
        module = _load_contract_governance()
        module.register_legacy_project_kanban_governance_model("project.project")
        module.register_legacy_project_kanban_profile(
            "project.project",
            {
                "title_field": "project_code",
                "primary_fields": ["project_code", "manager_id"],
                "secondary_fields": ["stage_id"],
                "status_fields": ["lifecycle_state"],
                "max_meta": 2,
            },
        )

        data = _kanban_contract()
        module.apply_project_form_domain_override(data, "user")

        profile = data.get("kanban_profile") or {}
        self.assertEqual(profile.get("title_field"), "project_code")
        self.assertEqual(profile.get("primary_fields"), ["project_code", "manager_id", "name"])
        self.assertEqual(profile.get("secondary_fields"), ["stage_id", "lifecycle_state"])
        self.assertEqual(profile.get("status_fields"), ["lifecycle_state"])
        self.assertEqual(profile.get("max_meta"), 2)


if __name__ == "__main__":
    unittest.main()
