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


sys.modules.setdefault("odoo", types.ModuleType("odoo"))
sys.modules.setdefault("odoo.addons", types.ModuleType("odoo.addons"))
smart_core_pkg = sys.modules.setdefault("odoo.addons.smart_core", types.ModuleType("odoo.addons.smart_core"))
smart_core_pkg.__path__ = [str(CORE_DIR.parent)]
core_pkg = sys.modules.setdefault("odoo.addons.smart_core.core", types.ModuleType("odoo.addons.smart_core.core"))
core_pkg.__path__ = [str(CORE_DIR)]
smart_core_pkg.core = core_pkg

bridge_module = _load_module(
    "odoo.addons.smart_core.core.page_contract_parser_semantic_bridge",
    CORE_DIR / "page_contract_parser_semantic_bridge.py",
)
core_pkg.page_contract_parser_semantic_bridge = bridge_module
target = _load_module(
    "odoo.addons.smart_core.core.page_contracts_builder",
    CORE_DIR / "page_contracts_builder.py",
)


class TestPageContractsBuilderSemantics(unittest.TestCase):
    def test_build_page_contracts_projects_parser_surface(self):
        payload = target.build_page_contracts(
            {
                "role_surface": {"role_code": "owner"},
                "parser_contract": {"view_type": "tree"},
                "view_semantics": {"source_view": "tree", "capability_flags": {"is_editable": True}},
                "native_view": {"views": {"tree": {"layout": []}}},
                "semantic_page": {"list_semantics": {"columns": [{"name": "name"}]}},
            }
        )

        home = (((payload.get("pages") or {}).get("home") or {}).get("page_orchestration_v1") or {})
        self.assertEqual(((home.get("page") or {}).get("context") or {}).get("view_type"), "tree")
        self.assertEqual(((home.get("page") or {}).get("context") or {}).get("semantic_source_view"), "tree")
        self.assertTrue((((home.get("render_hints") or {}).get("semantic_view") or {}).get("capability_flags") or {}).get("is_editable"))
        self.assertIn("parser_semantic_surface", home.get("meta") or {})


if __name__ == "__main__":
    unittest.main()
