# -*- coding: utf-8 -*-
import importlib.util
import sys
import types
import unittest
from pathlib import Path


CORE_DIR = Path(__file__).resolve().parents[1] / "core"


def _load_module(module_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


odoo_module = sys.modules.setdefault("odoo", types.ModuleType("odoo"))
addons_module = sys.modules.setdefault("odoo.addons", types.ModuleType("odoo.addons"))
smart_core_pkg = sys.modules.setdefault("odoo.addons.smart_core", types.ModuleType("odoo.addons.smart_core"))
smart_core_pkg.__path__ = [str(CORE_DIR.parent)]
core_pkg = sys.modules.setdefault("odoo.addons.smart_core.core", types.ModuleType("odoo.addons.smart_core.core"))
core_pkg.__path__ = [str(CORE_DIR)]
smart_core_pkg.core = core_pkg
addons_module.smart_core = smart_core_pkg
odoo_module.addons = addons_module


class _Datetime:
    @staticmethod
    def now():
        class _Now:
            def strftime(self, fmt):
                return "09:30"

        return _Now()


odoo_module.fields = types.SimpleNamespace(Datetime=_Datetime)

bridge_module = _load_module(
    "odoo.addons.smart_core.core.workspace_home_parser_semantic_bridge",
    CORE_DIR / "workspace_home_parser_semantic_bridge.py",
)
core_pkg.workspace_home_parser_semantic_bridge = bridge_module

target = _load_module(
    "odoo.addons.smart_core.core.workspace_home_contract_builder",
    CORE_DIR / "workspace_home_contract_builder.py",
)


class TestWorkspaceHomeContractBuilderSemantics(unittest.TestCase):
    def test_builder_projects_parser_semantics_into_workspace_contract(self):
        payload = target.build_workspace_home_contract(
            {
                "parser_contract": {"view_type": "form"},
                "view_semantics": {
                    "source_view": "form",
                    "capability_flags": {"is_editable": True},
                    "semantic_meta": {"field_count": 2},
                },
                "native_view": {"views": {"form": {"layout": []}}},
                "semantic_page": {"title_node": {"text": "工作台"}},
            }
        )

        self.assertEqual((payload.get("layout") or {}).get("view_type"), "form")
        page = (payload.get("page_orchestration_v1") or {}).get("page") or {}
        page_context = page.get("context") or {}
        view_type = page_context.get("view_type")
        self.assertEqual(view_type, "form")
        self.assertIn("parser_semantic_surface", payload.get("diagnostics") or {})


if __name__ == "__main__":
    unittest.main()
