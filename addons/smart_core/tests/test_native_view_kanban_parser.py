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
    def __init__(self, tag="field", **attrs):
        self.tag = tag
        self._attrs = attrs

    def get(self, key, default=None):
        return self._attrs.get(key, default)


class _FakeTemplate:
    def xpath(self, expr):
        if expr == ".//field[@name]":
            return [
                _FakeNode(name="name", widget=None),
                _FakeNode(name="stage_id", widget="badge"),
            ]
        return []


lxml_module = types.ModuleType("lxml")
lxml_etree = types.ModuleType("lxml.etree")
lxml_etree._Element = type("_Element", (), {})


class _FakeArch(lxml_etree._Element):
    tag = "kanban"

    def __init__(self):
        self.attrib = {
            "default_group_by": "stage_id",
            "on_create": "quick_create",
            "quick_create_view": "x_demo.quick_create_view",
            "create": "1",
            "delete": "0",
        }

    def xpath(self, expr):
        if expr == ".//t[@t-name='kanban-box']":
            return [_FakeTemplate()]
        if expr == ".//field[@name='color']":
            return [_FakeNode(name="color")]
        if expr == ".//a[@name]":
            return [_FakeNode(tag="a", name="open_record", type="object")]
        if expr == ".//t[@t-name='kanban-menu']":
            return []
        if expr == "//field[@name]":
            return [
                _FakeNode(name="name"),
                _FakeNode(name="stage_id"),
                _FakeNode(name="color"),
            ]
        return []

    def find(self, expr):
        if expr == "kanban":
            return self
        return None

    def get(self, key, default=None):
        return self.attrib.get(key, default)


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
registry_module = _load_module("odoo.addons.smart_core.view.native_view_parser_registry", VIEW_DIR / "native_view_parser_registry.py")


class _FakeModel:
    def get_view(self, *, view_id=None, view_type=None, context=None):
        return {
            "arch": "<kanban><templates><t t-name='kanban-box'><field name='name'/></t></templates></kanban>",
            "fields": {
                "name": {"string": "Name"},
                "stage_id": {"string": "Stage"},
                "color": {"string": "Color"},
            },
            "view_id": view_id or 1,
            "type": view_type,
        }


class _FakeEnv(dict):
    def __getitem__(self, key):
        return super().__getitem__(key)


class TestNativeViewKanbanParser(unittest.TestCase):
    def test_registry_resolves_kanban_parser(self):
        parser_cls = registry_module.get_parser_class("kanban")
        self.assertEqual(parser_cls.__name__, "KanbanViewParser")

    def test_kanban_parser_outputs_structured_layout(self):
        env = _FakeEnv({"x.demo": _FakeModel()})
        parser = kanban_module.KanbanViewParser(env, "x.demo", "kanban", 5, {})
        payload = parser.parse()
        self.assertEqual(payload["group_by"], "stage_id")
        self.assertEqual(payload["cards"][0]["name"], "name")
        self.assertEqual(payload["cards"][0]["semantic_role"], "kanban_card_field")
        self.assertEqual(payload["cards"][1]["semantic_meta"]["has_widget"], True)
        self.assertEqual(payload["actions"][0]["name"], "open_record")
        self.assertEqual(payload["actions"][0]["semantic_role"], "kanban_card_action")
        self.assertEqual(payload["actions"][0]["semantic_meta"]["target_scope"], "card")
        self.assertEqual(payload["color_field"], "color")


if __name__ == "__main__":
    unittest.main()
