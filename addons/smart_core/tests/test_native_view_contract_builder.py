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
form_module = _load_module("odoo.addons.smart_core.view.form_parser", VIEW_DIR / "form_parser.py")
sys.modules["odoo.addons.smart_core.view.form_parser"] = form_module
tree_module = _load_module("odoo.addons.smart_core.view.tree_parser", VIEW_DIR / "tree_parser.py")
sys.modules["odoo.addons.smart_core.view.tree_parser"] = tree_module
kanban_module = _load_module("odoo.addons.smart_core.view.kanban_parser", VIEW_DIR / "kanban_parser.py")
sys.modules["odoo.addons.smart_core.view.kanban_parser"] = kanban_module
search_module = _load_module("odoo.addons.smart_core.view.search_parser", VIEW_DIR / "search_parser.py")
sys.modules["odoo.addons.smart_core.view.search_parser"] = search_module
registry_module = _load_module("odoo.addons.smart_core.view.native_view_parser_registry", VIEW_DIR / "native_view_parser_registry.py")
sys.modules["odoo.addons.smart_core.view.native_view_parser_registry"] = registry_module
builder_module = _load_module("odoo.addons.smart_core.view.native_view_contract_builder", VIEW_DIR / "native_view_contract_builder.py")


class TestNativeViewContractBuilder(unittest.TestCase):
    def test_contract_builder_adds_stable_parser_contract(self):
        payload = builder_module.build_native_view_contract(
            raw_layout={"columns": [{"name": "name"}]},
            model="x.demo",
            view_type="list",
            view_id=11,
            permissions={"read": True},
            fields={"name": {"string": "Name"}},
            menus=[],
            actions=[],
        )
        self.assertEqual(payload["contract_version"], "native_view.v1")
        self.assertEqual(payload["parser_contract"]["view_type"], "tree")
        self.assertEqual(payload["parser_contract"]["layout"]["kind"], "tree")
        self.assertEqual(payload["parser_contract"]["layout"]["body"]["columns"][0]["name"], "name")


if __name__ == "__main__":
    unittest.main()
