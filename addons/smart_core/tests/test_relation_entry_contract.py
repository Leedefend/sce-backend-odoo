# -*- coding: utf-8 -*-
import unittest

from odoo.addons.smart_core.app_config_engine.services.assemblers.page_assembler import PageAssembler


class TestRelationEntryContract(unittest.TestCase):
    def setUp(self):
        self.assembler = PageAssembler.__new__(PageAssembler)
        self.assembler.env = {}

    def test_extract_dictionary_type_from_domain_list(self):
        result = self.assembler._extract_dictionary_type_from_domain([("type", "=", "project_type")])
        self.assertEqual(result, "project_type")

    def test_extract_dictionary_type_from_domain_string(self):
        result = self.assembler._extract_dictionary_type_from_domain("[('type','=','project_category')]")
        self.assertEqual(result, "project_category")

    def test_build_relation_entry_page_mode(self):
        descriptor = {"relation": "res.users", "domain": []}
        base_entry = {"model": "res.users", "action_id": 88, "menu_id": 9, "can_read": True, "can_create": True}
        entry = self.assembler._build_relation_entry_for_field("manager_id", descriptor, base_entry)
        self.assertEqual(entry.get("create_mode"), "page")
        self.assertEqual(entry.get("default_vals"), {})
        self.assertTrue(entry.get("can_read"))
        self.assertEqual(entry.get("reason_code"), "PAGE_ENTRY_READY")

    def test_build_relation_entry_page_mode_for_dictionary_keeps_type_default(self):
        descriptor = {"relation": "sc.dictionary", "domain": "[('type','=','project_type')]"}
        base_entry = {"model": "sc.dictionary", "action_id": 101, "menu_id": 11, "can_read": True, "can_create": True}
        entry = self.assembler._build_relation_entry_for_field("project_type_id", descriptor, base_entry)
        self.assertEqual(entry.get("create_mode"), "page")
        self.assertEqual(entry.get("default_vals", {}).get("type"), "project_type")
        self.assertTrue(entry.get("can_read"))
        self.assertEqual(entry.get("reason_code"), "PAGE_ENTRY_READY")

    def test_build_relation_entry_page_mode_readonly_when_create_forbidden(self):
        descriptor = {"relation": "sc.dictionary", "domain": "[('type','=','project_type')]"}
        base_entry = {"model": "sc.dictionary", "action_id": 101, "menu_id": 11, "can_read": True, "can_create": False}
        entry = self.assembler._build_relation_entry_for_field("project_type_id", descriptor, base_entry)
        self.assertEqual(entry.get("create_mode"), "page")
        self.assertEqual(entry.get("default_vals", {}).get("type"), "project_type")
        self.assertTrue(entry.get("can_read"))
        self.assertEqual(entry.get("reason_code"), "PAGE_ENTRY_READONLY")

    def test_build_relation_entry_quick_mode_for_dictionary(self):
        descriptor = {"relation": "sc.dictionary", "domain": "[('type','=','project_type')]"}
        base_entry = {"model": "sc.dictionary", "action_id": None, "menu_id": None, "can_read": True, "can_create": True}
        entry = self.assembler._build_relation_entry_for_field("project_type_id", descriptor, base_entry)
        self.assertEqual(entry.get("create_mode"), "quick")
        self.assertEqual(entry.get("default_vals", {}).get("type"), "project_type")
        self.assertTrue(entry.get("can_read"))
        self.assertEqual(entry.get("reason_code"), "QUICK_CREATE_READY")

    def test_build_relation_entry_disabled_without_page_or_quick(self):
        descriptor = {"relation": "project.task", "domain": []}
        base_entry = {"model": "project.task", "action_id": None, "menu_id": None, "can_read": True, "can_create": True}
        entry = self.assembler._build_relation_entry_for_field("task_id", descriptor, base_entry)
        self.assertEqual(entry.get("create_mode"), "disabled")
        self.assertTrue(entry.get("can_read"))
        self.assertEqual(entry.get("reason_code"), "NO_CREATE_ENTRY")

    def test_build_relation_entry_dictionary_domain_hint_from_model_field(self):
        class _Field:
            domain = [("type", "=", "project_type")]

        class _Model:
            _fields = {"project_type_id": _Field()}

        self.assembler.env = {"project.project": _Model()}
        descriptor = {"relation": "sc.dictionary", "domain": []}
        base_entry = {"model": "sc.dictionary", "action_id": None, "menu_id": None, "can_read": True, "can_create": True}
        entry = self.assembler._build_relation_entry_for_field(
            "project_type_id",
            descriptor,
            base_entry,
            model_name="project.project",
        )
        self.assertEqual(entry.get("create_mode"), "quick")
        self.assertEqual(entry.get("default_vals", {}).get("type"), "project_type")

    def test_build_relation_entry_disabled_when_relation_read_forbidden(self):
        descriptor = {"relation": "sc.dictionary", "domain": "[('type','=','project_type')]"}
        base_entry = {"model": "sc.dictionary", "action_id": 101, "menu_id": 11, "can_read": False, "can_create": True}
        entry = self.assembler._build_relation_entry_for_field("project_type_id", descriptor, base_entry)
        self.assertEqual(entry.get("create_mode"), "disabled")
        self.assertFalse(entry.get("can_read"))
        self.assertEqual(entry.get("reason_code"), "RELATION_READ_FORBIDDEN")

    def test_apply_access_policy_blocks_when_core_relation_unreadable(self):
        data = {
            "fields": {
                "name": {"type": "char"},
                "project_type_id": {
                    "type": "many2one",
                    "relation": "sc.dictionary",
                    "relation_entry": {"can_read": False, "reason_code": "RELATION_READ_FORBIDDEN"},
                },
            },
            "field_groups": [
                {"name": "core", "fields": ["name", "project_type_id"]},
            ],
            "warnings": [],
            "degraded": False,
        }
        self.assembler._apply_access_policy(data, model_name="project.project")
        policy = data.get("access_policy") or {}
        self.assertEqual(policy.get("mode"), "block")
        self.assertEqual(policy.get("reason_code"), "RELATION_READ_FORBIDDEN_CORE")
        self.assertEqual(len(policy.get("blocked_fields") or []), 1)

    def test_apply_access_policy_degrades_when_non_core_relation_unreadable(self):
        data = {
            "fields": {
                "name": {"type": "char"},
                "project_type_id": {
                    "type": "many2one",
                    "relation": "sc.dictionary",
                    "relation_entry": {"can_read": False, "reason_code": "RELATION_READ_FORBIDDEN"},
                },
            },
            "field_groups": [
                {"name": "core", "fields": ["name"]},
            ],
            "warnings": [],
            "degraded": False,
        }
        self.assembler._apply_access_policy(data, model_name="project.project")
        policy = data.get("access_policy") or {}
        self.assertEqual(policy.get("mode"), "degrade")
        self.assertEqual(policy.get("reason_code"), "RELATION_READ_FORBIDDEN")
        self.assertEqual(len(policy.get("degraded_fields") or []), 1)

    def test_apply_access_policy_degrades_when_core_relation_targets_system_model(self):
        data = {
            "fields": {
                "name": {"type": "char"},
                "alias_model_id": {
                    "type": "many2one",
                    "relation": "ir.model",
                    "relation_entry": {"can_read": False, "reason_code": "RELATION_READ_FORBIDDEN"},
                },
            },
            "field_groups": [
                {"name": "core", "fields": ["name", "alias_model_id"]},
            ],
            "warnings": [],
            "degraded": False,
        }
        self.assembler._apply_access_policy(data, model_name="project.project")
        policy = data.get("access_policy") or {}
        self.assertEqual(policy.get("mode"), "degrade")
        self.assertEqual(policy.get("reason_code"), "RELATION_READ_FORBIDDEN")
        self.assertEqual(len(policy.get("blocked_fields") or []), 0)
        self.assertEqual(len(policy.get("degraded_fields") or []), 1)


if __name__ == "__main__":
    unittest.main()
