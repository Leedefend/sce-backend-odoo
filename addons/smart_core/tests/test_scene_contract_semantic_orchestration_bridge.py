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

target = _load_module(
    "odoo.addons.smart_core.core.scene_contract_semantic_orchestration_bridge",
    CORE_DIR / "scene_contract_semantic_orchestration_bridge.py",
)


class TestSceneContractSemanticOrchestrationBridge(unittest.TestCase):
    def test_bridge_projects_form_semantics_into_detail_layout(self):
        bridged = target.apply_scene_contract_semantic_orchestration_bridge(
            {
                "page": {"layout": "workspace", "zones": [{"key": "primary", "layout": "workspace"}]},
                "governance": {
                    "parser_semantic_surface": {
                        "parser_contract": {"view_type": "form"},
                        "view_semantics": {"source_view": "form"},
                        "semantic_page": {"title_node": {"text": "工作台"}},
                    }
                },
            }
        )

        self.assertEqual((bridged.get("page") or {}).get("layout"), "detail")
        self.assertEqual((((bridged.get("page") or {}).get("zones") or [])[0].get("layout")), "detail")

    def test_bridge_projects_tree_semantics_into_list_layout(self):
        bridged = target.apply_scene_contract_semantic_orchestration_bridge(
            {
                "page": {"layout": "workspace", "zones": [{"key": "primary", "layout": "workspace"}]},
                "governance": {
                    "parser_semantic_surface": {
                        "parser_contract": {"view_type": "tree"},
                        "view_semantics": {"source_view": "tree"},
                        "semantic_page": {"list_semantics": {"columns": [{"name": "name"}]}},
                    }
                },
            }
        )

        self.assertEqual((bridged.get("page") or {}).get("layout"), "list")
        self.assertEqual((((bridged.get("page") or {}).get("zones") or [])[0].get("layout")), "list")


if __name__ == "__main__":
    unittest.main()
