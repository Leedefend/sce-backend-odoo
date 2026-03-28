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
scene_dsl_compiler.scene_compile = lambda scene_payload, **_kwargs: scene_payload
sys.modules["odoo.addons.smart_core.core.scene_dsl_compiler"] = scene_dsl_compiler
core_pkg.scene_dsl_compiler = scene_dsl_compiler

ui_base_contract_adapter = types.ModuleType("odoo.addons.smart_core.core.ui_base_contract_adapter")
ui_base_contract_adapter.adapt_ui_base_contract = lambda payload, **_kwargs: {
    "normalized_contract": dict(payload or {}),
    "orchestrator_input": {"view_fact": True},
}
sys.modules["odoo.addons.smart_core.core.ui_base_contract_adapter"] = ui_base_contract_adapter
core_pkg.ui_base_contract_adapter = ui_base_contract_adapter

for name in (
    "scene_ready_parser_semantic_bridge",
    "scene_ready_entry_semantic_bridge",
    "scene_ready_semantic_orchestration_bridge",
    "scene_ready_search_semantic_bridge",
    "scene_ready_action_semantic_bridge",
):
    module = types.ModuleType(f"odoo.addons.smart_core.core.{name}")
    passthrough_name = f"apply_{name}"
    module.__dict__[passthrough_name] = lambda payload, **_kwargs: payload
    sys.modules[f"odoo.addons.smart_core.core.{name}"] = module
    setattr(core_pkg, name, module)

target = _load_module(
    "odoo.addons.smart_core.core.scene_ready_contract_builder",
    CORE_DIR / "scene_ready_contract_builder.py",
)


class TestSceneReadyConsumptionMetrics(unittest.TestCase):
    def test_metrics_count_searchpanel_only_surface_as_search(self):
        metrics = target._scene_type_consumption_metrics(
            [
                {
                    "scene": {"type": "workspace"},
                    "meta": {"base_facts": {"search": {"available": True}}},
                    "search_surface": {"searchpanel": [{"name": "stage_id"}]},
                }
            ]
        )

        scene_bucket = metrics["list"]
        self.assertEqual(scene_bucket["surface_nonempty_hits"]["search"], 1)
        self.assertEqual(scene_bucket["surface_nonempty_rate"]["search"], 1.0)


if __name__ == "__main__":
    unittest.main()
