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

for name in (
    "page_contract_parser_semantic_bridge",
    "page_contract_semantic_orchestration_bridge",
    "runtime_page_parser_semantic_bridge",
    "runtime_page_semantic_orchestration_bridge",
    "scene_contract_parser_semantic_bridge",
    "scene_contract_semantic_orchestration_bridge",
    "released_scene_semantic_surface_bridge",
    "page_contracts_builder",
    "scene_contract_builder",
):
    module = _load_module(f"odoo.addons.smart_core.core.{name}", CORE_DIR / f"{name}.py")
    setattr(core_pkg, name, module)

target = _load_module(
    "odoo.addons.smart_core.core.runtime_page_contract_builder",
    CORE_DIR / "runtime_page_contract_builder.py",
)


class TestRuntimePageContractBuilderBoundaries(unittest.TestCase):
    def test_runtime_page_builder_declares_projection_source(self):
        source = target.source_authority_contract()
        payload = target.build_runtime_page_contracts({})

        self.assertEqual(source.get("kind"), "runtime_page_contract_projection")
        self.assertTrue(source.get("projection_only"))
        self.assertTrue(source.get("no_business_fact_authority"))
        self.assertEqual((payload.get("runtime_source_authority") or {}).get("kind"), source.get("kind"))
        home_meta = ((((payload.get("pages") or {}).get("home") or {}).get("page_orchestration_v1") or {}).get("meta") or {})
        self.assertEqual((home_meta.get("runtime_source_authority") or {}).get("kind"), source.get("kind"))


if __name__ == "__main__":
    unittest.main()
