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


smart_scene_pkg = sys.modules.setdefault("addons.smart_scene", types.ModuleType("addons.smart_scene"))
smart_scene_pkg.__path__ = [str(CORE_DIR.parent)]
core_pkg = sys.modules.setdefault("addons.smart_scene.core", types.ModuleType("addons.smart_scene.core"))
core_pkg.__path__ = [str(CORE_DIR)]
smart_scene_pkg.core = core_pkg

for name in ("layout_orchestrator", "scene_resolver", "structure_mapper", "scene_parser_semantic_bridge", "scene_contract_builder"):
    module = _load_module(f"addons.smart_scene.core.{name}", CORE_DIR / f"{name}.py")
    setattr(core_pkg, name, module)

target = _load_module("addons.smart_scene.core.scene_engine", CORE_DIR / "scene_engine.py")


class TestSceneEngineSemantics(unittest.TestCase):
    def test_build_scene_contract_from_specs_projects_parser_surface(self):
        payload = target.build_scene_contract_from_specs(
            scene_hint={"key": "workspace.home"},
            page_hint={"key": "workspace.home", "title": "工作台"},
            zone_specs=[],
            built_zones={},
            diagnostics={"source": "test"},
            semantic_surface={
                "parser_contract": {"view_type": "kanban"},
                "view_semantics": {"source_view": "kanban", "capability_flags": {"has_menu": True}},
                "native_view": {"views": {"kanban": {"layout": []}}},
                "semantic_page": {"kanban_semantics": {"lane_count": 3}},
            },
        )

        self.assertEqual((((payload.get("page") or {}).get("surface") or {}).get("view_type")), "kanban")
        self.assertIn("parser_semantic_surface", payload.get("diagnostics") or {})


if __name__ == "__main__":
    unittest.main()
