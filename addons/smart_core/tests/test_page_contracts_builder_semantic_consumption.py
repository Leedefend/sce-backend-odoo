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

parser_bridge = _load_module(
    "odoo.addons.smart_core.core.page_contract_parser_semantic_bridge",
    CORE_DIR / "page_contract_parser_semantic_bridge.py",
)
semantic_bridge = _load_module(
    "odoo.addons.smart_core.core.page_contract_semantic_orchestration_bridge",
    CORE_DIR / "page_contract_semantic_orchestration_bridge.py",
)
core_pkg.page_contract_parser_semantic_bridge = parser_bridge
core_pkg.page_contract_semantic_orchestration_bridge = semantic_bridge

target = _load_module(
    "odoo.addons.smart_core.core.page_contracts_builder",
    CORE_DIR / "page_contracts_builder.py",
)


class TestPageContractsBuilderSemanticConsumption(unittest.TestCase):
    def test_build_page_contracts_prefers_form_semantics_for_home_page_type(self):
        payload = target.build_page_contracts(
            {
                "role_surface": {"role_code": "owner"},
                "parser_contract": {"view_type": "form"},
                "view_semantics": {"source_view": "form", "capability_flags": {"is_editable": True}},
                "native_view": {"views": {"form": {"layout": []}}},
                "semantic_page": {"title_node": {"text": "工作台"}},
            }
        )

        home = (((payload.get("pages") or {}).get("home") or {}).get("page_orchestration_v1") or {})
        page = home.get("page") or {}

        self.assertEqual(page.get("page_type"), "detail")
        self.assertEqual(page.get("layout_mode"), "detail_focus")
        self.assertEqual(page.get("priority_model"), "record_first")
        self.assertEqual((home.get("render_hints") or {}).get("semantic_page_type"), "detail")


if __name__ == "__main__":
    unittest.main()
