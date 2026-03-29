# -*- coding: utf-8 -*-
import importlib.util
import sys
import types
import unittest
from pathlib import Path


CORE_DIR = Path(__file__).resolve().parents[1] / "core"
SCHEMA_DIR = Path(__file__).resolve().parents[1] / "schemas"
SCHEMA_PATH = Path(__file__).resolve().parents[1] / "schemas" / "scene_contract_schema.py"
BUILDER_PATH = Path(__file__).resolve().parents[1] / "core" / "scene_contract_builder.py"


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


smart_scene_pkg = sys.modules.setdefault("addons.smart_scene", types.ModuleType("addons.smart_scene"))
smart_scene_pkg.__path__ = [str(CORE_DIR.parent)]
core_pkg = sys.modules.setdefault("addons.smart_scene.core", types.ModuleType("addons.smart_scene.core"))
core_pkg.__path__ = [str(CORE_DIR)]
schema_pkg = sys.modules.setdefault("addons.smart_scene.schemas", types.ModuleType("addons.smart_scene.schemas"))
schema_pkg.__path__ = [str(SCHEMA_DIR)]
smart_scene_pkg.core = core_pkg
smart_scene_pkg.schemas = schema_pkg

bridge_module = _load_module(CORE_DIR / "scene_parser_semantic_bridge.py", "addons.smart_scene.core.scene_parser_semantic_bridge")
setattr(core_pkg, "scene_parser_semantic_bridge", bridge_module)

schema_module = _load_module(SCHEMA_PATH, "addons.smart_scene.schemas.scene_contract_schema")
builder_module = _load_module(BUILDER_PATH, "addons.smart_scene.core.scene_contract_builder")


def _base_contract():
    return {
        "contract_version": "v1",
        "scene": {},
        "page": {},
        "nav_ref": {},
        "zones": {},
        "blocks": {},
        "record": {},
        "permissions": {},
        "actions": {
            "primary_actions": [],
            "secondary_actions": [],
            "contextual_actions": [],
            "danger_actions": [],
            "recommended_actions": [],
        },
        "extensions": {},
        "diagnostics": {},
    }


class TestSceneContractSchema(unittest.TestCase):
    def test_schema_accepts_diagnostics_semantic_runtime_state_object(self):
        payload = _base_contract()
        payload["diagnostics"] = {"semantic_runtime_state": {"page_status": "ready"}}

        ok, detail = schema_module.check_top_level_shape(payload)

        self.assertTrue(ok)
        self.assertEqual(detail.get("code"), "ok")

    def test_schema_rejects_non_object_semantic_runtime_state(self):
        payload = _base_contract()
        payload["diagnostics"] = {"semantic_runtime_state": "ready"}

        ok, detail = schema_module.check_top_level_shape(payload)

        self.assertFalse(ok)
        self.assertEqual(detail.get("code"), "invalid_diagnostics_semantic_runtime_state")

    def test_builder_shape_validator_rejects_non_object_semantic_runtime_state(self):
        payload = _base_contract()
        payload["diagnostics"] = {"semantic_runtime_state": "ready"}

        verdict = builder_module.validate_scene_contract_shape(payload)

        self.assertFalse(verdict.get("ok"))
        self.assertIn(
            {"code": "invalid_diagnostics_semantic_runtime_state"},
            verdict.get("issues") or [],
        )


if __name__ == "__main__":
    unittest.main()
