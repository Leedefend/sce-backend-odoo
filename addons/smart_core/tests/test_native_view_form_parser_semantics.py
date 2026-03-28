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


class _ButtonNode(_FieldNode):
    pass


class _WidgetNode(_FieldNode):
    pass


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
    def test_title_and_field_nodes_use_semantic_metadata(self):
        parser = form_module.FormViewParser.__new__(form_module.FormViewParser)

        class _Arch:
            def xpath(self, expr):
                if expr == ".//div[contains(@class, 'oe_title')]//field":
                    return [_FieldNode(name="name", string="Name")]
                return []

        title_node = parser._parse_title_node(_Arch())
        self.assertEqual(title_node["semantic_role"], "form_title_field")
        self.assertEqual(title_node["semantic_meta"]["is_title"], True)

    def test_group_node_uses_stable_shape(self):
        parser = form_module.FormViewParser.__new__(form_module.FormViewParser)
        group = parser._parse_group_recursive(_GroupNode())
        self.assertEqual(group["kind"], "group")
        self.assertEqual(group["fields"][0]["name"], "name")
        self.assertIn("attributes", group)
        self.assertEqual(group["semantic_role"], "form_group")

    def test_notebook_page_nodes_use_stable_shape(self):
        parser = form_module.FormViewParser.__new__(form_module.FormViewParser)

        class _Arch:
            def xpath(self, expr):
                if expr == ".//notebook":
                    return [_NotebookNode()]
                return []

        notebooks = parser._parse_notebooks(_Arch())
        self.assertEqual(notebooks[0]["kind"], "notebook")
        self.assertEqual(notebooks[0]["semantic_role"], "form_notebook")
        self.assertEqual(notebooks[0]["pages"][0]["kind"], "page")
        self.assertEqual(notebooks[0]["pages"][0]["semantic_role"], "form_page")
        self.assertEqual(notebooks[0]["pages"][0]["title"], "Details")

    def test_button_ribbon_and_chatter_nodes_use_semantic_metadata(self):
        parser = form_module.FormViewParser.__new__(form_module.FormViewParser)
        button = parser._parse_button(_ButtonNode(name="action_confirm", type="object", context="{}", **{"data-hotkey": "c"}))
        self.assertEqual(button["semantic_role"], "form_button")
        self.assertEqual(button["semantic_meta"]["has_hotkey"], True)

        class _RibbonArch:
            def xpath(self, expr):
                if expr == ".//widget[@name='web_ribbon']":
                    return [_WidgetNode(title="Archived", bg_color="bg-danger")]
                return []

        ribbon = parser._parse_ribbon(_RibbonArch())
        self.assertEqual(ribbon["kind"], "ribbon")
        self.assertEqual(ribbon["semantic_role"], "form_ribbon")

        class _ChatterArch:
            def xpath(self, expr):
                if expr == ".//div[contains(@class,'oe_chatter')]//field":
                    return [
                        _FieldNode(name="message_follower_ids"),
                        _FieldNode(name="activity_ids"),
                        _FieldNode(name="message_ids"),
                    ]
                return []

        chatter = parser._parse_chatter(_ChatterArch())
        self.assertEqual(chatter["kind"], "chatter")
        self.assertEqual(chatter["semantic_role"], "form_chatter")
        self.assertEqual(chatter["semantic_meta"]["has_messages"], True)

    def test_form_parser_outputs_view_level_semantics(self):
        parser = form_module.FormViewParser.__new__(form_module.FormViewParser)
        parser._parse_title_field = lambda arch: "name"
        parser._parse_title_node = lambda arch: {"kind": "field", "name": "name"}
        parser._parse_header_buttons = lambda arch: [{"kind": "action", "name": "action_confirm"}]
        parser._parse_stat_buttons = lambda arch: [{"kind": "action", "name": "action_stats"}]
        parser._parse_ribbon = lambda arch: {"kind": "ribbon", "title": "Archived"}
        parser._parse_groups = lambda nodes: [{"kind": "group"}]
        parser._parse_notebooks = lambda arch: [{"kind": "notebook"}]
        parser._parse_chatter = lambda arch: {"kind": "chatter", "messages": "message_ids"}

        class _Arch:
            def xpath(self, expr):
                return []

        parser.get_view_info = lambda fallback_view_type="form": {"arch": _Arch()}
        payload = parser.parse()
        self.assertEqual(payload["view_semantics"]["kind"], "view_semantics")
        self.assertEqual(payload["view_semantics"]["source_view"], "form")
        self.assertEqual(payload["view_semantics"]["capability_flags"]["has_title"], True)
        self.assertEqual(payload["view_semantics"]["semantic_meta"]["header_button_count"], 1)


if __name__ == "__main__":
    unittest.main()
