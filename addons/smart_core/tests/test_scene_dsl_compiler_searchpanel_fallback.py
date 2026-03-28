# -*- coding: utf-8 -*-
import importlib.util
import sys
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


resolver_module = _load_module(
    "odoo.addons.smart_core.core.scene_merge_resolver",
    CORE_DIR / "scene_merge_resolver.py",
)
target = _load_module(
    "odoo.addons.smart_core.core.scene_dsl_compiler",
    CORE_DIR / "scene_dsl_compiler.py",
)


class TestSceneDslCompilerSearchpanelFallback(unittest.TestCase):
    def test_scene_compile_projects_searchpanel_from_ui_base_search(self):
        compiled = target.scene_compile(
            {
                "code": "projects.list",
                "name": "项目列表",
                "layout": {"kind": "list"},
                "target": {"route": "/s/projects.list"},
            },
            scene_key="projects.list",
            ui_base_contract={
                "search": {
                    "fields": [{"name": "name"}],
                    "filters": [{"name": "mine", "string": "我的"}],
                    "group_by": [{"field": "stage_id", "label": "按阶段"}],
                    "searchpanel": [{"name": "stage_id", "string": "阶段"}],
                }
            },
        )

        search_surface = compiled.get("search_surface") or {}
        self.assertEqual((search_surface.get("searchpanel") or [])[0]["name"], "stage_id")


if __name__ == "__main__":
    unittest.main()
