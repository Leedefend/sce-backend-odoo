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
odoo_safe_eval.safe_eval = lambda expr: expr
sys.modules["odoo.tools"] = odoo_tools
sys.modules["odoo.tools.safe_eval"] = odoo_safe_eval


class _FakeNode:
    def __init__(self, name=None, string=None, widget=None, optional=None):
        self._attrs = {"name": name, "string": string, "widget": widget, "optional": optional}

    def get(self, key):
        return self._attrs.get(key)


class _FakeArch:
    def __init__(self):
        self.attrib = {"editable": "bottom", "create": "1", "delete": "0", "decoration-danger": "state == 'late'"}

    def xpath(self, expr):
        if expr == ".//field[@name]":
            return [
                _FakeNode(name="name", string="Name"),
                _FakeNode(name="stage_id", string="Stage", widget="badge"),
            ]
        return []

    def get(self, key):
        return self.attrib.get(key)


lxml_module = types.ModuleType("lxml")
lxml_etree = types.ModuleType("lxml.etree")
lxml_etree._Element = type("_Element", (), {})
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
registry_module = _load_module("odoo.addons.smart_core.view.native_view_parser_registry", VIEW_DIR / "native_view_parser_registry.py")


class _FakeModel:
    def get_view(self, *, view_id=None, view_type=None, context=None):
        return {
            "arch": "<tree><field name='name'/></tree>",
            "fields": {"name": {"string": "Name"}},
            "view_id": view_id or 1,
            "type": view_type,
        }


class _FakeEnv(dict):
    def __getitem__(self, key):
        return super().__getitem__(key)


class TestNativeViewTreeParser(unittest.TestCase):
    def test_registry_resolves_tree_parser(self):
        parser_cls = registry_module.get_parser_class("tree")
        self.assertEqual(parser_cls.__name__, "TreeViewParser")

    def test_tree_parser_outputs_structured_columns(self):
        env = _FakeEnv({"x.demo": _FakeModel()})
        parser = tree_module.TreeViewParser(env, "x.demo", "tree", 3, {})
        payload = parser.parse()
        self.assertEqual(payload["columns"][0]["name"], "name")
        self.assertEqual(payload["columns"][0]["kind"], "field")
        self.assertEqual(payload["columns"][0]["semantic_role"], "tree_column")
        self.assertEqual(payload["columns"][1]["semantic_meta"]["has_widget"], True)
        self.assertEqual(payload["editable"], "bottom")
        self.assertIn("decoration-danger", payload["decorations"])
        self.assertEqual(payload["view_semantics"]["capability_flags"]["is_editable"], True)
        self.assertEqual(payload["view_semantics"]["semantic_meta"]["editable_mode"], "bottom")


if __name__ == "__main__":
    unittest.main()
