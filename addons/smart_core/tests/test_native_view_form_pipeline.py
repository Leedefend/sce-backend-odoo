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


class _AccessError(Exception):
    pass


odoo_exceptions.UserError = _UserError
odoo_exceptions.AccessError = _AccessError
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
form_module = _load_module("odoo.addons.smart_core.view.form_parser", VIEW_DIR / "form_parser.py")
sys.modules["odoo.addons.smart_core.view.form_parser"] = form_module
pipeline_module = _load_module("odoo.addons.smart_core.view.native_view_pipeline", VIEW_DIR / "native_view_pipeline.py")
sys.modules["odoo.addons.smart_core.view.native_view_pipeline"] = pipeline_module
dispatcher_module = _load_module("odoo.addons.smart_core.view.view_dispatcher", VIEW_DIR / "view_dispatcher.py")
sys.modules["odoo.addons.smart_core.view.view_dispatcher"] = dispatcher_module
universal_module = _load_module("odoo.addons.smart_core.view.universal_parser", VIEW_DIR / "universal_parser.py")


class TestNativeViewFormPipeline(unittest.TestCase):
    def test_pipeline_payload_shape(self):
        payload = pipeline_module.build_native_view_pipeline_payload(
            raw_layout={"titleField": "name"},
            model="x.demo",
            view_type="form",
            view_id=7,
            permissions={"read": True},
            fields={"name": {"string": "Name"}},
            menus=[],
            actions=[],
        )
        self.assertEqual(payload["layout"]["titleField"], "name")
        self.assertEqual(payload["model"], "x.demo")
        self.assertEqual(payload["contract_version"], "native_view.v1")
        self.assertEqual(payload["parser_contract"]["view_type"], "form")
        self.assertEqual(payload["parser_contract"]["layout"]["kind"], "form")

    def test_universal_parser_uses_pipeline_payload_builder(self):
        parser = universal_module.UniversalViewSemanticParser.__new__(universal_module.UniversalViewSemanticParser)
        parser.env = {}
        parser.permission_env = {}
        parser.context = {}
        parser.model = "x.demo"
        parser.view_type = "form"
        parser.view_id = 9
        parser._parse_model_permissions = lambda: {"read": True}
        parser._parse_fields_with_permissions = lambda raw: {"name": {"string": "Name", "visible": True, "editable": True}}
        parser._merge_field_labels = lambda raw, fields: None
        parser._apply_permissions_to_layout = lambda raw, fields: None
        parser._parse_menus = lambda: []
        parser._parse_actions = lambda: []
        parser._apply_dynamic_overrides = lambda raw: raw

        original_dispatcher = universal_module.ViewDispatcher

        class _FakeDispatcher:
            def __init__(self, *args, **kwargs):
                pass

            def parse(self):
                return {"titleField": "name"}

        universal_module.ViewDispatcher = _FakeDispatcher
        try:
            payload = parser.parse()
        finally:
            universal_module.ViewDispatcher = original_dispatcher

        self.assertEqual(payload["layout"]["titleField"], "name")
        self.assertEqual(payload["model"], "x.demo")
        self.assertEqual(payload["view_id"], 9)
        self.assertEqual(payload["parser_contract"]["layout"]["kind"], "form")


if __name__ == "__main__":
    unittest.main()
