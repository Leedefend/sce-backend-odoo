# -*- coding: utf-8 -*-
import importlib.util
import sys
import types
import unittest
from pathlib import Path


VIEW_DIR = Path(__file__).resolve().parents[1] / "view"


def _load_module(module_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


sys.modules.setdefault("odoo", types.ModuleType("odoo"))
odoo_module = sys.modules["odoo"]
odoo_module.api = types.SimpleNamespace(Environment=object)
odoo_module.models = types.SimpleNamespace()
odoo_exceptions = types.ModuleType("odoo.exceptions")


class _UserError(Exception):
    pass


odoo_exceptions.UserError = _UserError
sys.modules["odoo.exceptions"] = odoo_exceptions
odoo_http = types.ModuleType("odoo.http")
odoo_http.request = None
sys.modules["odoo.http"] = odoo_http
odoo_tools = types.ModuleType("odoo.tools")
odoo_safe_eval = types.ModuleType("odoo.tools.safe_eval")
odoo_safe_eval.safe_eval = lambda expr: eval(expr, {}, {})
sys.modules["odoo.tools"] = odoo_tools
sys.modules["odoo.tools.safe_eval"] = odoo_safe_eval


class _FakeNode:
    def __init__(self, **attrs):
        self._attrs = attrs

    def get(self, key, default=None):
        return self._attrs.get(key, default)


lxml_module = types.ModuleType("lxml")
lxml_etree = types.ModuleType("lxml.etree")
lxml_etree._Element = type("_Element", (), {})


class _FakeArch(lxml_etree._Element):
    tag = "search"

    def xpath(self, expr):
        if expr == ".//field[@name]":
            return [
                _FakeNode(name="name", string="Name"),
                _FakeNode(name="stage_id", string="Stage", operator="="),
            ]
        if expr == ".//filter[@name]":
            return [
                _FakeNode(name="late", string="Late", domain="[('state', '=', 'late')]"),
                _FakeNode(name="group_stage", string="By Stage", context="{'group_by': 'stage_id'}"),
            ]
        if expr == ".//filter[@context]":
            return [
                _FakeNode(name="group_stage", string="By Stage", context="{'group_by': 'stage_id'}"),
            ]
        if expr == ".//searchpanel/field[@name]":
            return [
                _FakeNode(name="stage_id", string="Stage", select="multi"),
            ]
        return []


lxml_etree.fromstring = lambda value: _FakeArch()
sys.modules["lxml"] = lxml_module
sys.modules["lxml.etree"] = lxml_etree
sys.modules.setdefault("odoo.addons", types.ModuleType("odoo.addons"))
sys.modules.setdefault("odoo.addons.smart_core", types.ModuleType("odoo.addons.smart_core"))
view_pkg = sys.modules.setdefault("odoo.addons.smart_core.view", types.ModuleType("odoo.addons.smart_core.view"))
view_pkg.__path__ = [str(VIEW_DIR)]

base_module = _load_module("odoo.addons.smart_core.view.base", VIEW_DIR / "base.py")
sys.modules["odoo.addons.smart_core.view.base"] = base_module
form_module = _load_module("odoo.addons.smart_core.view.form_parser", VIEW_DIR / "form_parser.py")
sys.modules["odoo.addons.smart_core.view.form_parser"] = form_module
tree_module = _load_module("odoo.addons.smart_core.view.tree_parser", VIEW_DIR / "tree_parser.py")
sys.modules["odoo.addons.smart_core.view.tree_parser"] = tree_module
kanban_module = _load_module("odoo.addons.smart_core.view.kanban_parser", VIEW_DIR / "kanban_parser.py")
sys.modules["odoo.addons.smart_core.view.kanban_parser"] = kanban_module
search_module = _load_module("odoo.addons.smart_core.view.search_parser", VIEW_DIR / "search_parser.py")
sys.modules["odoo.addons.smart_core.view.search_parser"] = search_module
registry_module = _load_module("odoo.addons.smart_core.view.native_view_parser_registry", VIEW_DIR / "native_view_parser_registry.py")


class _FakeModel:
    def get_view(self, *, view_id=None, view_type=None, context=None):
        return {
            "arch": "<search><field name='name'/><filter name='late'/></search>",
            "fields": {"name": {"string": "Name"}},
            "view_id": view_id or 1,
            "type": view_type,
        }


class _FakeEnv(dict):
    def __getitem__(self, key):
        return super().__getitem__(key)


class TestNativeViewSearchParser(unittest.TestCase):
    def test_registry_resolves_search_parser(self):
        parser_cls = registry_module.get_parser_class("search")
        self.assertEqual(parser_cls.__name__, "SearchViewParser")

    def test_search_parser_outputs_structured_search_payload(self):
        env = _FakeEnv({"x.demo": _FakeModel()})
        parser = search_module.SearchViewParser(env, "x.demo", "search", 7, {})
        payload = parser.parse()
        self.assertEqual(payload["fields"][0]["name"], "name")
        self.assertEqual(payload["fields"][0]["semantic_role"], "search_field")
        self.assertEqual(payload["fields"][1]["semantic_meta"]["has_operator"], True)
        self.assertEqual(payload["filters"][0]["name"], "late")
        self.assertEqual(payload["filters"][0]["semantic_role"], "search_filter")
        self.assertEqual(payload["filters"][1]["semantic_meta"]["has_context"], True)
        self.assertEqual(payload["group_bys"][0]["group_by"], "stage_id")
        self.assertEqual(payload["group_bys"][0]["semantic_role"], "search_group_by")
        self.assertEqual(payload["group_bys"][0]["semantic_meta"]["context_keys"], ["group_by"])
        self.assertEqual(payload["searchpanel"][0]["name"], "stage_id")
        self.assertEqual(payload["searchpanel"][0]["semantic_role"], "searchpanel_field")
        self.assertEqual(payload["searchpanel"][0]["semantic_meta"]["is_multi"], True)


if __name__ == "__main__":
    unittest.main()
