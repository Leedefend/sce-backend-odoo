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


_load_module(
    "odoo.addons.smart_core.core.scene_merge_resolver",
    CORE_DIR / "scene_merge_resolver.py",
)
target = _load_module(
    "odoo.addons.smart_core.core.scene_dsl_compiler",
    CORE_DIR / "scene_dsl_compiler.py",
)


class TestSceneDslCompilerSurfaceProfile(unittest.TestCase):
    def test_surface_profile_counts_searchpanel(self):
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
                    "filters": [{"name": "mine"}],
                    "group_by": [{"field": "stage_id"}],
                    "searchpanel": [{"name": "stage_id"}],
                }
            },
        )

        profile = ((compiled.get("meta") or {}).get("surface_profile") or {})
        self.assertEqual(profile.get("search_filter_count"), 1)
        self.assertEqual(profile.get("search_group_by_count"), 1)
        self.assertEqual(profile.get("search_searchpanel_count"), 1)


if __name__ == "__main__":
    unittest.main()
