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

form_module = _load_module("odoo.addons.smart_core.view.form_parser", VIEW_DIR / "form_parser.py")
sys.modules["odoo.addons.smart_core.view.form_parser"] = form_module

registry_module = _load_module("odoo.addons.smart_core.view.native_view_parser_registry", VIEW_DIR / "native_view_parser_registry.py")
source_loader_module = _load_module("odoo.addons.smart_core.view.native_view_source_loader", VIEW_DIR / "native_view_source_loader.py")


class _FakeModel:
    def get_view(self, *, view_id=None, view_type=None, context=None):
        return {
            "arch": "<form string='Demo'><sheet><group><field name='name'/></group></sheet></form>",
            "fields": {"name": {"string": "Name"}},
            "view_id": view_id or 1,
            "type": view_type,
        }


class _FakeEnv(dict):
    def __getitem__(self, key):
        return super().__getitem__(key)


class TestNativeViewParserSkeleton(unittest.TestCase):
    def test_registry_normalizes_aliases(self):
        self.assertEqual(registry_module.normalize_view_type("list"), "tree")
        self.assertIn("form", registry_module.list_registered_view_types())
        self.assertIsNotNone(registry_module.get_parser_class("form"))

    def test_source_loader_parses_arch_string(self):
        env = _FakeEnv({"x.demo": _FakeModel()})
        loader = source_loader_module.NativeViewSourceLoader(env, model="x.demo", view_type="form", view_id=7, context={"lang": "zh_CN"})
        payload = loader.load()
        self.assertEqual(payload["view_id"], 7)
        self.assertEqual(payload["arch"].tag, "form")


if __name__ == "__main__":
    unittest.main()
