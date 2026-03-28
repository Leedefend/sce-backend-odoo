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
    "meta": {},
}
sys.modules["odoo.addons.smart_core.core.scene_dsl_compiler"] = scene_dsl_compiler
core_pkg.scene_dsl_compiler = scene_dsl_compiler

ui_base_contract_adapter = types.ModuleType("odoo.addons.smart_core.core.ui_base_contract_adapter")
ui_base_contract_adapter.adapt_ui_base_contract = lambda payload, **_kwargs: {
    "normalized_contract": dict(payload or {}),
    "orchestrator_input": {"view_fact": True},
}
sys.modules["odoo.addons.smart_core.core.ui_base_contract_adapter"] = ui_base_contract_adapter
core_pkg.ui_base_contract_adapter = ui_base_contract_adapter

parser_bridge = _load_module(
    "odoo.addons.smart_core.core.scene_ready_parser_semantic_bridge",
    CORE_DIR / "scene_ready_parser_semantic_bridge.py",
)
entry_bridge = _load_module(
    "odoo.addons.smart_core.core.scene_ready_entry_semantic_bridge",
    CORE_DIR / "scene_ready_entry_semantic_bridge.py",
)
orchestration_bridge = _load_module(
    "odoo.addons.smart_core.core.scene_ready_semantic_orchestration_bridge",
    CORE_DIR / "scene_ready_semantic_orchestration_bridge.py",
)
core_pkg.scene_ready_parser_semantic_bridge = parser_bridge
core_pkg.scene_ready_entry_semantic_bridge = entry_bridge
core_pkg.scene_ready_semantic_orchestration_bridge = orchestration_bridge

target = _load_module(
    "odoo.addons.smart_core.core.scene_ready_contract_builder",
    CORE_DIR / "scene_ready_contract_builder.py",
)


class TestSceneReadyContractBuilderSemanticConsumption(unittest.TestCase):
    def test_workspace_scene_ready_prefers_parser_semantic_view_mode(self):
        contract = target.build_scene_ready_contract_v1(
            scenes=[
                {
                    "code": "workspace.home",
                    "name": "工作台",
                    "layout": {"kind": "workspace"},
                    "target": {"route": "/my-work"},
                    "ui_base_contract": {
                        "parser_contract": {"view_type": "form"},
                        "view_semantics": {"source_view": "form", "capability_flags": {"is_editable": True}},
                        "native_view": {"views": {"form": {"layout": []}, "search": {"layout": []}}},
                        "semantic_page": {"title_node": {"text": "工作台"}},
                    },
                }
            ],
            role_surface={"landing_scene_key": "workspace.home"},
        )
        row = (contract.get("scenes") or [])[0]

        self.assertEqual(((row.get("view_modes") or [])[0] or {}).get("key"), "form")
        self.assertEqual(((row.get("action_surface") or {}).get("selection_mode")), "single")


if __name__ == "__main__":
    unittest.main()
