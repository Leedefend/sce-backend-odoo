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
        base_entry = {"model": "res.users", "action_id": 88, "menu_id": 9, "can_create": True}
        entry = self.assembler._build_relation_entry_for_field("manager_id", descriptor, base_entry)
        self.assertEqual(entry.get("create_mode"), "page")
        self.assertEqual(entry.get("default_vals"), {})
        self.assertEqual(entry.get("reason_code"), "PAGE_ENTRY_READY")

    def test_build_relation_entry_page_mode_for_dictionary_keeps_type_default(self):
        descriptor = {"relation": "sc.dictionary", "domain": "[('type','=','project_type')]"}
        base_entry = {"model": "sc.dictionary", "action_id": 101, "menu_id": 11, "can_create": True}
        entry = self.assembler._build_relation_entry_for_field("project_type_id", descriptor, base_entry)
        self.assertEqual(entry.get("create_mode"), "page")
        self.assertEqual(entry.get("default_vals", {}).get("type"), "project_type")
        self.assertEqual(entry.get("reason_code"), "PAGE_ENTRY_READY")

    def test_build_relation_entry_page_mode_readonly_when_create_forbidden(self):
        descriptor = {"relation": "sc.dictionary", "domain": "[('type','=','project_type')]"}
        base_entry = {"model": "sc.dictionary", "action_id": 101, "menu_id": 11, "can_create": False}
        entry = self.assembler._build_relation_entry_for_field("project_type_id", descriptor, base_entry)
        self.assertEqual(entry.get("create_mode"), "page")
        self.assertEqual(entry.get("default_vals", {}).get("type"), "project_type")
        self.assertEqual(entry.get("reason_code"), "PAGE_ENTRY_READONLY")

    def test_build_relation_entry_quick_mode_for_dictionary(self):
        descriptor = {"relation": "sc.dictionary", "domain": "[('type','=','project_type')]"}
        base_entry = {"model": "sc.dictionary", "action_id": None, "menu_id": None, "can_create": True}
        entry = self.assembler._build_relation_entry_for_field("project_type_id", descriptor, base_entry)
        self.assertEqual(entry.get("create_mode"), "quick")
        self.assertEqual(entry.get("default_vals", {}).get("type"), "project_type")
        self.assertEqual(entry.get("reason_code"), "QUICK_CREATE_READY")

    def test_build_relation_entry_disabled_without_page_or_quick(self):
        descriptor = {"relation": "project.task", "domain": []}
        base_entry = {"model": "project.task", "action_id": None, "menu_id": None, "can_create": True}
        entry = self.assembler._build_relation_entry_for_field("task_id", descriptor, base_entry)
        self.assertEqual(entry.get("create_mode"), "disabled")
        self.assertEqual(entry.get("reason_code"), "NO_CREATE_ENTRY")

    def test_build_relation_entry_dictionary_domain_hint_from_model_field(self):
        class _Field:
            domain = [("type", "=", "project_type")]

        class _Model:
            _fields = {"project_type_id": _Field()}

        self.assembler.env = {"project.project": _Model()}
        descriptor = {"relation": "sc.dictionary", "domain": []}
        base_entry = {"model": "sc.dictionary", "action_id": None, "menu_id": None, "can_create": True}
        entry = self.assembler._build_relation_entry_for_field(
            "project_type_id",
            descriptor,
            base_entry,
            model_name="project.project",
        )
        self.assertEqual(entry.get("create_mode"), "quick")
        self.assertEqual(entry.get("default_vals", {}).get("type"), "project_type")


if __name__ == "__main__":
    unittest.main()
