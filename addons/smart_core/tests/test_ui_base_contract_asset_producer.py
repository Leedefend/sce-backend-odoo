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
odoo_mod = sys.modules["odoo"]
odoo_mod.api = types.SimpleNamespace(Environment=lambda *args, **kwargs: None)

sys.modules.setdefault("odoo.addons", types.ModuleType("odoo.addons"))
smart_core_pkg = sys.modules.setdefault("odoo.addons.smart_core", types.ModuleType("odoo.addons.smart_core"))
smart_core_pkg.__path__ = [str(CORE_DIR.parent)]
core_pkg = sys.modules.setdefault("odoo.addons.smart_core.core", types.ModuleType("odoo.addons.smart_core.core"))
core_pkg.__path__ = [str(CORE_DIR)]
smart_core_pkg.core = core_pkg

canonicalizer = types.ModuleType("odoo.addons.smart_core.core.ui_base_contract_canonicalizer")
canonicalizer.canonicalize_ui_base_contract = lambda payload: payload if isinstance(payload, dict) else {}
sys.modules["odoo.addons.smart_core.core.ui_base_contract_canonicalizer"] = canonicalizer
core_pkg.ui_base_contract_canonicalizer = canonicalizer

contract_service = types.ModuleType("odoo.addons.smart_core.app_config_engine.services.contract_service")
contract_service.ContractService = object
sys.modules["odoo.addons.smart_core.app_config_engine.services.contract_service"] = contract_service

action_dispatcher = types.ModuleType(
    "odoo.addons.smart_core.app_config_engine.services.dispatchers.action_dispatcher"
)
action_dispatcher.ActionDispatcher = object
sys.modules[
    "odoo.addons.smart_core.app_config_engine.services.dispatchers.action_dispatcher"
] = action_dispatcher

scene_registry_provider = types.ModuleType("odoo.addons.smart_core.core.scene_registry_provider")
scene_registry_provider.has_db_scenes = lambda env: False
scene_registry_provider.load_scene_configs = lambda env, drift=None: []
sys.modules["odoo.addons.smart_core.core.scene_registry_provider"] = scene_registry_provider
core_pkg.scene_registry_provider = scene_registry_provider

captured_upserts = []


def _upsert_asset(_env, **vals):
    captured_upserts.append(vals)
    return {"id": len(captured_upserts), **vals}


repo_module = types.ModuleType("odoo.addons.smart_core.core.ui_base_contract_asset_repository")
repo_module.upsert_asset = _upsert_asset
sys.modules["odoo.addons.smart_core.core.ui_base_contract_asset_repository"] = repo_module
core_pkg.ui_base_contract_asset_repository = repo_module

target = _load_module(
    "odoo.addons.smart_core.core.ui_base_contract_asset_producer",
    CORE_DIR / "ui_base_contract_asset_producer.py",
)


class TestUiBaseContractAssetProducer(unittest.TestCase):
    def setUp(self):
        captured_upserts.clear()

    def test_refresh_uses_runtime_rows_when_registry_empty(self):
        result = target.refresh_ui_base_contract_assets(
            env=object(),
            scene_keys=["projects.list"],
            scene_rows=[
                {
                    "code": "projects.list",
                    "target": {
                        "route": "/s/projects.list",
                        "model": "project.project",
                    },
                }
            ],
            role_code="owner",
            company_id=1,
            source_type="runtime_intent",
            code_version="unit-test",
        )

        self.assertEqual(result["scene_source"], "runtime_rows")
        self.assertEqual(result["produced_count"], 1)
        self.assertEqual(result["failed_count"], 0)
        self.assertEqual(len(captured_upserts), 1)
        self.assertEqual(captured_upserts[0]["scene_key"], "projects.list")
        self.assertEqual(captured_upserts[0]["role_code"], "owner")
        self.assertEqual(captured_upserts[0]["company_id"], 1)


if __name__ == "__main__":
    unittest.main()
