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

canonicalizer = types.ModuleType("odoo.addons.smart_core.core.ui_base_contract_canonicalizer")
canonicalizer.canonicalize_ui_base_contract = lambda payload: payload if isinstance(payload, dict) else {}
sys.modules["odoo.addons.smart_core.core.ui_base_contract_canonicalizer"] = canonicalizer
core_pkg.ui_base_contract_canonicalizer = canonicalizer

target = _load_module(
    "odoo.addons.smart_core.core.ui_base_contract_asset_repository",
    CORE_DIR / "ui_base_contract_asset_repository.py",
)


class TestUiBaseContractAssetRepository(unittest.TestCase):
    def test_rejects_action_asset_for_canonical_scene_root(self):
        scene = {
            "code": "contract.center",
            "target": {
                "route": "/s/contract.center",
                "menu_xmlid": "smart_construction_core.menu_sc_contract_center",
            },
        }
        asset = {
            "id": 31,
            "source_ref": "action:522",
            "payload": {"model": "construction.contract"},
        }

        self.assertTrue(target._is_canonical_scene_root(scene))
        self.assertTrue(target._asset_is_stale_for_scene(asset, scene))

    def test_keeps_scene_asset_for_canonical_scene_root(self):
        scene = {
            "code": "contract.center",
            "target": {
                "route": "/s/contract.center",
            },
        }
        asset = {
            "id": 32,
            "source_ref": "scene:contract.center:minimal",
            "payload": {"model": "res.partner"},
        }

        self.assertFalse(target._asset_is_stale_for_scene(asset, scene))

    def test_keeps_action_asset_for_action_backed_scene(self):
        scene = {
            "code": "contracts.workspace",
            "target": {
                "route": "/s/contracts.workspace",
                "action_xmlid": "smart_construction_core.action_construction_contract_my",
            },
        }
        asset = {
            "id": 33,
            "source_ref": "action:522",
            "payload": {"model": "construction.contract"},
        }

        self.assertFalse(target._is_canonical_scene_root(scene))
        self.assertFalse(target._asset_is_stale_for_scene(asset, scene))


if __name__ == "__main__":
    unittest.main()
