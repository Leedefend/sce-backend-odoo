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

scene_bridge = _load_module(
    "odoo.addons.smart_core.core.scene_contract_parser_semantic_bridge",
    CORE_DIR / "scene_contract_parser_semantic_bridge.py",
)
core_pkg.scene_contract_parser_semantic_bridge = scene_bridge
released_bridge = _load_module(
    "odoo.addons.smart_core.core.released_scene_semantic_surface_bridge",
    CORE_DIR / "released_scene_semantic_surface_bridge.py",
)
core_pkg.released_scene_semantic_surface_bridge = released_bridge
target = _load_module(
    "odoo.addons.smart_core.core.scene_contract_builder",
    CORE_DIR / "scene_contract_builder.py",
)


class TestSceneContractAttachSemantics(unittest.TestCase):
    def test_attach_release_surface_scene_contract_backfills_runtime_semantics(self):
        payload = target.attach_release_surface_scene_contract(
            {
                "scene_key": "workspace.home",
                "title": "工作台",
                "parser_contract": {"view_type": "form"},
                "view_semantics": {"source_view": "form", "capability_flags": {"is_editable": True}},
                "native_view": {"views": {"form": {"layout": []}}},
                "semantic_page": {"title_node": {"text": "工作台"}},
            },
            product_key="my_work",
            capability="delivery.my_work.workspace",
            route="/my-work",
            diagnostics_ref="runtime.attach:test",
        )

        self.assertIn("scene_contract_standard_v1", payload)
        self.assertEqual((payload.get("semantic_runtime") or {}).get("view_type"), "form")
        self.assertIn("released_scene_semantic_surface", payload)


if __name__ == "__main__":
    unittest.main()
