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
core_pkg.page_contract_parser_semantic_bridge = parser_bridge
semantic_bridge = _load_module(
    "odoo.addons.smart_core.core.page_contract_semantic_orchestration_bridge",
    CORE_DIR / "page_contract_semantic_orchestration_bridge.py",
)
core_pkg.page_contract_semantic_orchestration_bridge = semantic_bridge

target = _load_module(
    "odoo.addons.smart_core.core.page_contracts_builder",
    CORE_DIR / "page_contracts_builder.py",
)


class TestPageContractsBuilderBoundaries(unittest.TestCase):
    def test_page_contract_builder_declares_projection_source(self):
        source = target.source_authority_contract()

        self.assertEqual(source.get("kind"), "page_contract_projection")
        self.assertTrue(source.get("projection_only"))
        self.assertTrue(source.get("no_business_fact_authority"))
        self.assertEqual(source.get("legacy_page_copy_source"), "legacy_industry_page_copy_projection")

    def test_builtin_industry_copy_is_marked_as_legacy_projection(self):
        payload = target.build_page_contracts({})
        diagnostics = payload.get("diagnostics") or {}

        self.assertEqual((payload.get("source_authority") or {}).get("kind"), "page_contract_projection")
        self.assertEqual(
            ((diagnostics.get("legacy_page_copy_source_authority") or {}).get("kind")),
            "legacy_industry_page_copy_projection",
        )
        self.assertTrue(((diagnostics.get("legacy_page_copy_source_authority") or {}).get("no_business_fact_authority")))


if __name__ == "__main__":
    unittest.main()
