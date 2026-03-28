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

scene_dsl_compiler = types.ModuleType("odoo.addons.smart_core.core.scene_dsl_compiler")
scene_dsl_compiler.scene_compile = lambda scene_payload, **_kwargs: {
    "scene": {"key": scene_payload.get("code") or scene_payload.get("key"), "title": scene_payload.get("name")},
    "page": {"mode": "", "route": ((scene_payload.get("target") or {}).get("route") or "")},
    "surface": {},
    "actions": list(scene_payload.get("actions") or []),
    "workflow_surface": {},
    "validation_surface": {},
    "search_surface": {"default_sort": "write_date desc"},
    "meta": {},
}
sys.modules["odoo.addons.smart_core.core.scene_dsl_compiler"] = scene_dsl_compiler
core_pkg.scene_dsl_compiler = scene_dsl_compiler

ui_base_contract_adapter = types.ModuleType("odoo.addons.smart_core.core.ui_base_contract_adapter")
ui_base_contract_adapter.adapt_ui_base_contract = lambda payload, **_kwargs: {
    "normalized_contract": dict(payload or {}),
    "orchestrator_input": {"search_fact": True},
}
sys.modules["odoo.addons.smart_core.core.ui_base_contract_adapter"] = ui_base_contract_adapter
core_pkg.ui_base_contract_adapter = ui_base_contract_adapter

for name in (
    "scene_ready_parser_semantic_bridge",
    "scene_ready_entry_semantic_bridge",
    "scene_ready_search_semantic_bridge",
    "scene_ready_semantic_orchestration_bridge",
):
    module = _load_module(f"odoo.addons.smart_core.core.{name}", CORE_DIR / f"{name}.py")
    setattr(core_pkg, name, module)

target = _load_module(
    "odoo.addons.smart_core.core.scene_ready_contract_builder",
    CORE_DIR / "scene_ready_contract_builder.py",
)


class TestSceneReadySearchSurfaceSemanticConsumption(unittest.TestCase):
    def test_builder_backfills_search_surface_from_parser_semantics(self):
        contract = target.build_scene_ready_contract_v1(
            scenes=[
                {
                    "code": "projects.list",
                    "name": "项目列表",
                    "layout": {"kind": "list"},
                    "target": {"route": "/s/projects.list", "model": "project.project"},
                    "ui_base_contract": {
                        "parser_contract": {"view_type": "tree"},
                        "view_semantics": {"source_view": "tree", "capability_flags": {"is_editable": True}},
                        "native_view": {
                            "views": {
                                "tree": {"layout": []},
                                "search": {
                                    "fields": [{"name": "name"}],
                                    "filters": [{"name": "mine", "string": "我的"}],
                                    "group_bys": [{"name": "by_stage", "string": "按阶段", "group_by": "stage_id"}],
                                    "searchpanel": [{"name": "stage_id", "string": "阶段"}],
                                },
                            }
                        },
                        "semantic_page": {"list_semantics": {"columns": [{"name": "name"}]}},
                    },
                }
            ],
            role_surface={"landing_scene_key": "projects.list"},
        )
        row = (contract.get("scenes") or [])[0]
        search_surface = row.get("search_surface") or {}

        self.assertEqual((search_surface.get("fields") or [])[0]["name"], "name")
        self.assertEqual((search_surface.get("filters") or [])[0]["name"], "mine")
        self.assertEqual((search_surface.get("group_by") or [])[0]["field"], "stage_id")
        self.assertEqual((search_surface.get("searchpanel") or [])[0]["name"], "stage_id")
        self.assertEqual(search_surface.get("mode"), "faceted")


if __name__ == "__main__":
    unittest.main()
