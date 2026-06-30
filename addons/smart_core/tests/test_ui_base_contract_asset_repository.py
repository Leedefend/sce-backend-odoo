# -*- coding: utf-8 -*-
import importlib.util
import json
import os
import sys
import types
import unittest
from datetime import date
from decimal import Decimal
from unittest.mock import patch
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
    def test_upsert_asset_serializes_projection_scalars(self):
        class _Savepoint:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

        class _Cursor:
            def savepoint(self):
                return _Savepoint()

        class _Record:
            def __init__(self, vals):
                self.id = 1
                self.vals = vals
                self.payload_json = vals.get("payload_json")

            def write(self, vals):
                self.vals.update(vals)
                self.payload_json = vals.get("payload_json", self.payload_json)

        class _Model:
            def __init__(self):
                self.created = None

            def sudo(self):
                return self

            def search(self, _domain, limit=None):
                return None if limit else []

            def create(self, vals):
                self.created = _Record(vals)
                return self.created

        class _Env:
            def __init__(self, model):
                self.model = model
                self.cr = _Cursor()

            def __contains__(self, item):
                return item == target.ASSET_MODEL

            def __getitem__(self, item):
                if item != target.ASSET_MODEL:
                    raise KeyError(item)
                return self.model

        model = _Model()
        env = _Env(model)
        original_table_available = target._asset_table_available
        original_get_latest = target.get_latest_asset
        target._asset_table_available = lambda _env: True
        target.get_latest_asset = lambda *_args, **_kwargs: {"ok": True}
        try:
            result = target.upsert_asset(
                env,
                scene_key="project.list",
                payload={"day": date(2026, 6, 30), "amount": Decimal("12.30")},
            )
        finally:
            target._asset_table_available = original_table_available
            target.get_latest_asset = original_get_latest

        self.assertEqual(result, {"ok": True})
        self.assertEqual(json.loads(model.created.payload_json), {"amount": "12.30", "day": "2026-06-30"})

    def test_auto_refresh_missing_assets_defaults_on_for_dev_and_off_for_prod(self):
        class _Config:
            def sudo(self):
                return self

            def get_param(self, key):
                return ""

        class _Env:
            def __getitem__(self, item):
                if item != "ir.config_parameter":
                    raise KeyError(item)
                return _Config()

        env = _Env()
        with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
            self.assertTrue(target._should_auto_refresh_missing_assets(env))
        with patch.dict(os.environ, {"ENV": "test"}, clear=True):
            self.assertTrue(target._should_auto_refresh_missing_assets(env))
        with patch.dict(os.environ, {"ENV": "prod"}, clear=True):
            self.assertFalse(target._should_auto_refresh_missing_assets(env))

    def test_auto_refresh_missing_assets_explicit_override_wins(self):
        with patch.dict(os.environ, {"ENV": "prod", "SC_UI_BASE_ASSET_AUTO_REFRESH_MISSING": "1"}, clear=True):
            self.assertTrue(target._should_auto_refresh_missing_assets(None))
        with patch.dict(os.environ, {"ENV": "dev", "SC_UI_BASE_ASSET_AUTO_REFRESH_MISSING": "0"}, clear=True):
            self.assertFalse(target._should_auto_refresh_missing_assets(None))

    def test_build_scene_asset_map_batches_lookup_and_preserves_scope_priority(self):
        class _Company:
            def __init__(self, record_id):
                self.id = record_id

        class _Record:
            def __init__(self, *, record_id, scene_key, role_code=False, company_id=None, payload=None):
                self.id = record_id
                self.contract_kind = "ui_base"
                self.scene_key = scene_key
                self.role_code = role_code
                self.company_id = _Company(company_id) if company_id else None
                self.scope_hash = ""
                self.source_type = "precompile"
                self.asset_version = "v1"
                self.asset_hash = f"h{record_id}"
                self.source_ref = f"scene:{scene_key}"
                self.code_version = ""
                self.generated_at = ""
                self.payload_json = "{}"
                self.write_date = str(record_id)

        class _Model:
            def __init__(self, records):
                self.records = records
                self.search_calls = []

            def sudo(self):
                return self

            def search(self, domain):
                self.search_calls.append(domain)
                return self.records

        class _Env:
            def __init__(self, model):
                self.model = model
                self.cr = object()

            def __contains__(self, item):
                return item == target.ASSET_MODEL

            def __getitem__(self, item):
                if item != target.ASSET_MODEL:
                    raise KeyError(item)
                return self.model

        model = _Model(
            [
                _Record(record_id=4, scene_key="projects.list", role_code="pm", company_id=7),
                _Record(record_id=3, scene_key="projects.list", company_id=7),
                _Record(record_id=2, scene_key="finance.center", company_id=7),
                _Record(record_id=1, scene_key="finance.center"),
            ]
        )
        env = _Env(model)
        original_table_available = target._asset_table_available
        target._asset_table_available = lambda _env: True
        try:
            result = target.build_scene_asset_map(
                env,
                scene_keys=["projects.list", "finance.center", "projects.list"],
                role_code="pm",
                company_id=7,
            )
        finally:
            target._asset_table_available = original_table_available

        self.assertEqual(len(model.search_calls), 1)
        self.assertEqual(result["projects.list"]["id"], 4)
        self.assertEqual(result["finance.center"]["id"], 2)

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

    def test_rejects_action_asset_when_action_backed_scene_identity_drifted(self):
        scene = {
            "code": "projects.list",
            "target": {
                "route": "/s/projects.list",
                "action_id": 452,
            },
        }
        asset = {
            "id": 34,
            "source_ref": "action:519",
            "payload": {"model": "project.project"},
        }

        self.assertFalse(target._is_canonical_scene_root(scene))
        self.assertTrue(target._asset_is_stale_for_scene(asset, scene))


if __name__ == "__main__":
    unittest.main()
