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

bridge_module = _load_module("addons.smart_scene.core.scene_parser_semantic_bridge", CORE_DIR / "scene_parser_semantic_bridge.py")
setattr(core_pkg, "scene_parser_semantic_bridge", bridge_module)
target = _load_module("addons.smart_scene.core.scene_contract_builder", CORE_DIR / "scene_contract_builder.py")


class TestSceneContractBuilder(unittest.TestCase):
    def test_build_scene_contract_projects_semantic_runtime_assertions(self):
        payload = target.build_scene_contract(
            scene={"key": "workspace.record", "scene_key": "workspace.record"},
            page={"key": "workspace.record", "page_status": "ready"},
            zones={},
            permissions={
                "record_state_summary": {
                    "page_status": "ready",
                    "current_state": "draft",
                }
            },
            diagnostics={
                "semantic_runtime_state": {
                    "page_status": "ready",
                    "current_state": "draft",
                }
            },
        )

        assertions = ((payload.get("diagnostics") or {}).get("semantic_runtime_assertions")) or {}
        self.assertTrue(assertions.get("runtime_state_present"))
        self.assertTrue(assertions.get("page_status_aligned"))
        self.assertTrue(assertions.get("record_state_summary_aligned"))
        self.assertTrue(assertions.get("current_state_projected"))
        self.assertEqual(
            (((payload.get("scene_contract_v1") or {}).get("diagnostics") or {}).get("semantic_runtime_assertions") or {}).get("page_status_aligned"),
            True,
        )
        runtime_view = ((((payload.get("diagnostics") or {}).get("consumer_semantics")) or {}).get("runtime")) or {}
        self.assertEqual(runtime_view.get("page_status"), "ready")
        self.assertEqual(runtime_view.get("runtime_page_status"), "ready")
        self.assertEqual(runtime_view.get("current_state"), "draft")
        self.assertEqual((runtime_view.get("alignment") or {}).get("page_status_aligned"), True)

    def test_build_scene_contract_flags_misaligned_runtime_assertions(self):
        payload = target.build_scene_contract(
            scene={"key": "workspace.record", "scene_key": "workspace.record"},
            page={"key": "workspace.record", "page_status": "readonly"},
            zones={},
            permissions={
                "record_state_summary": {
                    "page_status": "ready",
                    "current_state": "draft",
                }
            },
            diagnostics={
                "semantic_runtime_state": {
                    "page_status": "ready",
                    "current_state": "approved",
                }
            },
        )

        assertions = ((payload.get("diagnostics") or {}).get("semantic_runtime_assertions")) or {}
        self.assertFalse(assertions.get("page_status_aligned"))
        self.assertFalse(assertions.get("record_state_summary_aligned"))
        self.assertFalse(assertions.get("current_state_projected"))
        runtime_view = ((((payload.get("diagnostics") or {}).get("consumer_semantics")) or {}).get("runtime")) or {}
        self.assertEqual(runtime_view.get("page_status"), "readonly")
        self.assertEqual(runtime_view.get("runtime_page_status"), "ready")
        self.assertEqual((runtime_view.get("alignment") or {}).get("record_state_summary_aligned"), False)


if __name__ == "__main__":
    unittest.main()
