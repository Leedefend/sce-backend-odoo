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
    "action_surface": {},
    "search_surface": {},
    "permission_surface": {},
    "workflow_surface": {},
    "validation_surface": {},
    "meta": {},
}
sys.modules["odoo.addons.smart_core.core.scene_dsl_compiler"] = scene_dsl_compiler
core_pkg.scene_dsl_compiler = scene_dsl_compiler

ui_base_contract_adapter = types.ModuleType("odoo.addons.smart_core.core.ui_base_contract_adapter")
ui_base_contract_adapter.adapt_ui_base_contract = lambda payload, **_kwargs: {
    "normalized_contract": dict(payload or {}),
    "orchestrator_input": {"seed_fact": True},
}
sys.modules["odoo.addons.smart_core.core.ui_base_contract_adapter"] = ui_base_contract_adapter
core_pkg.ui_base_contract_adapter = ui_base_contract_adapter

for name in (
    "scene_ready_parser_semantic_bridge",
    "scene_ready_entry_semantic_bridge",
    "scene_ready_search_semantic_bridge",
    "scene_ready_semantic_orchestration_bridge",
    "scene_ready_action_semantic_bridge",
):
    module = _load_module(f"odoo.addons.smart_core.core.{name}", CORE_DIR / f"{name}.py")
    setattr(core_pkg, name, module)

target = _load_module(
    "odoo.addons.smart_core.core.scene_ready_contract_builder",
    CORE_DIR / "scene_ready_contract_builder.py",
)


class TestSceneReadySurfaceSeedFallback(unittest.TestCase):
    def test_builder_seeds_canonical_semantic_surfaces_from_scene_payload(self):
        contract = target.build_scene_ready_contract_v1(
            scenes=[
                {
                    "code": "projects.detail",
                    "name": "项目详情",
                    "layout": {"kind": "form"},
                    "target": {"route": "/s/projects.detail", "model": "project.project"},
                    "search_surface": {
                        "default_sort": "priority desc",
                        "filters": [{"name": "mine"}],
                        "mode": "filter_bar",
                    },
                    "permission_surface": {
                        "visible": True,
                        "allowed": False,
                        "reason_code": "missing_capability",
                        "required_capabilities": ["project.write"],
                    },
                    "workflow_surface": {
                        "state_field": "state",
                        "states": [{"key": "draft"}],
                    },
                    "validation_surface": {
                        "required_fields": ["name"],
                        "field_rules": [{"field": "name", "rule": "required"}],
                    },
                    "ui_base_contract": {
                        "parser_contract": {"view_type": "form"},
                        "view_semantics": {"source_view": "form"},
                        "native_view": {"views": {"form": {"layout": []}}},
                    },
                }
            ],
            role_surface={"landing_scene_key": "projects.detail"},
        )

        row = (contract.get("scenes") or [])[0]
        self.assertEqual((row.get("search_surface") or {}).get("default_sort"), "priority desc")
        self.assertEqual((row.get("search_surface") or {}).get("mode"), "filter_bar")
        self.assertEqual(((row.get("permission_surface") or {}).get("required_capabilities") or [])[0], "project.write")
        self.assertEqual((row.get("workflow_surface") or {}).get("state_field"), "state")
        self.assertEqual(((row.get("validation_surface") or {}).get("required_fields") or [])[0], "name")


if __name__ == "__main__":
    unittest.main()
