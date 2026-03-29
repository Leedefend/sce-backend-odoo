# -*- coding: utf-8 -*-
import importlib.util
import sys
import types
import unittest
from pathlib import Path


SMART_CORE_DIR = Path(__file__).resolve().parents[1]
MIXIN_PATH = SMART_CORE_DIR / "app_config_engine" / "models" / "contract_mixin.py"


def _load_module(module_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


sys.modules.setdefault("odoo", types.ModuleType("odoo"))
odoo_module = sys.modules["odoo"]
odoo_module.models = types.SimpleNamespace(AbstractModel=object)


def _identity_decorator(fn):
    return fn


odoo_module.api = types.SimpleNamespace(model=_identity_decorator)

module = _load_module("smart_core_contract_mixin_form_structure", MIXIN_PATH)
ContractSchemaMixin = module.ContractSchemaMixin


class _DummyMixin(ContractSchemaMixin):
    pass


class TestAppViewConfigFormStructure(unittest.TestCase):
    def test_governed_form_keeps_header_and_button_box_actions(self):
        mixin = _DummyMixin()
        payload = {
            "layout": [{"type": "sheet", "children": []}],
            "statusbar": {"field": "lifecycle_state"},
            "header_buttons": [
                {"string": "提交立项", "name": "action_sc_submit", "type": "object", "groups_xmlids": ["base.group_user"]}
            ],
            "button_box": [
                {"string": "任务", "name": "action_view_tasks", "type": "object"}
            ],
            "stat_buttons": [
                {"string": "任务", "name": "action_view_tasks", "type": "object"}
            ],
            "field_modifiers": {"user_id": {"readonly": "not active"}},
            "toolbar": {"header": [], "sidebar": [], "footer": []},
            "search": {"filters": [], "group_by": [], "facets": {"enabled": True}},
        }

        result = mixin.sanitize_governed_contract("form", payload)

        self.assertEqual(result["statusbar"]["field"], "lifecycle_state")
        self.assertEqual(result["header_buttons"][0]["name"], "action_sc_submit")
        self.assertEqual(result["header_buttons"][0]["groups_xmlids"], ["base.group_user"])
        self.assertEqual(result["button_box"][0]["name"], "action_view_tasks")
        self.assertEqual(result["stat_buttons"][0]["name"], "action_view_tasks")
        self.assertEqual(result["field_modifiers"]["user_id"]["readonly"], "not active")


if __name__ == "__main__":
    unittest.main()
