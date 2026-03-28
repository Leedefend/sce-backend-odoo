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
lxml_module = types.ModuleType("lxml")
lxml_etree = types.ModuleType("lxml.etree")
lxml_etree._Element = type("_Element", (), {})
lxml_etree.fromstring = lambda value: type("FakeArch", (), {"tag": "form"})()
sys.modules["lxml"] = lxml_module
sys.modules["lxml.etree"] = lxml_etree
sys.modules.setdefault("odoo.addons", types.ModuleType("odoo.addons"))
sys.modules.setdefault("odoo.addons.smart_core", types.ModuleType("odoo.addons.smart_core"))
view_pkg = sys.modules.setdefault("odoo.addons.smart_core.view", types.ModuleType("odoo.addons.smart_core.view"))
view_pkg.__path__ = [str(VIEW_DIR)]

base_module = _load_module("odoo.addons.smart_core.view.base", VIEW_DIR / "base.py")
sys.modules["odoo.addons.smart_core.view.base"] = base_module
schema_module = _load_module("odoo.addons.smart_core.view.native_view_node_schema", VIEW_DIR / "native_view_node_schema.py")
sys.modules["odoo.addons.smart_core.view.native_view_node_schema"] = schema_module
form_module = _load_module("odoo.addons.smart_core.view.form_parser", VIEW_DIR / "form_parser.py")


class _FieldNode:
    def __init__(self, **attrs):
        self._attrs = attrs

    def get(self, key, default=None):
        return self._attrs.get(key, default)


class _GroupNode:
    def __init__(self):
        self._field = _FieldNode(name="name", string="Name")

    def xpath(self, expr):
        if expr == "./field":
            return [self._field]
        if expr == "./group":
            return []
        return []

    def get(self, key, default=None):
        return None


class _PageNode:
    def __init__(self):
        self._group = _GroupNode()

    def xpath(self, expr):
        if expr == "./group":
            return [self._group]
        return []

    def get(self, key, default=None):
        if key == "string":
            return "Details"
        return default


class _NotebookNode:
    def __init__(self):
        self._page = _PageNode()

    def xpath(self, expr):
        if expr == "./page":
            return [self._page]
        return []


class TestNativeViewFormParserSemantics(unittest.TestCase):
    def test_group_node_uses_stable_shape(self):
        parser = form_module.FormViewParser.__new__(form_module.FormViewParser)
        group = parser._parse_group_recursive(_GroupNode())
        self.assertEqual(group["kind"], "group")
        self.assertEqual(group["fields"][0]["name"], "name")
        self.assertIn("attributes", group)

    def test_notebook_page_nodes_use_stable_shape(self):
        parser = form_module.FormViewParser.__new__(form_module.FormViewParser)

        class _Arch:
            def xpath(self, expr):
                if expr == ".//notebook":
                    return [_NotebookNode()]
                return []

        notebooks = parser._parse_notebooks(_Arch())
        self.assertEqual(notebooks[0]["kind"], "notebook")
        self.assertEqual(notebooks[0]["pages"][0]["kind"], "page")
        self.assertEqual(notebooks[0]["pages"][0]["title"], "Details")


if __name__ == "__main__":
    unittest.main()
