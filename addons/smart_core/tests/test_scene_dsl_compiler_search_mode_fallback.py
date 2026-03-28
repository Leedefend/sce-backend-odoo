# -*- coding: utf-8 -*-
import importlib.util
import sys
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "core" / "scene_dsl_compiler.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("scene_dsl_compiler_search_mode_under_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


compiler_module = _load_module()


class TestSceneDslCompilerSearchModeFallback(unittest.TestCase):
    def test_generate_surfaces_preserves_base_search_mode(self):
        ctx = compiler_module.CompileContext(
            scene_key="projects.list",
            ui_base_contract={
                "search": {
                    "fields": [{"name": "name"}],
                    "searchpanel": [{"name": "stage_id", "string": "阶段"}],
                    "mode": "faceted",
                }
            },
            provider_registry={},
            profile={},
            policies={},
            providers=[],
            runtime={"role_code": "pm"},
        )

        out = compiler_module.generate_surfaces(
            {
                "blocks": [],
                "search_surface": {},
                "meta": {},
            },
            ctx,
        )

        self.assertEqual(((out.get("search_surface") or {}).get("mode")), "faceted")
        self.assertEqual(((out.get("search_surface") or {}).get("searchpanel") or [])[0]["name"], "stage_id")


if __name__ == "__main__":
    unittest.main()
