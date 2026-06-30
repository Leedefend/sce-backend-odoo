# -*- coding: utf-8 -*-
import importlib.util
import json
import re
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

target = _load_module(
    "odoo.addons.smart_core.core.ui_base_contract_asset_event_queue",
    CORE_DIR / "ui_base_contract_asset_event_queue.py",
)


class _Config:
    def __init__(self):
        self.values = {}

    def sudo(self):
        return self

    def get_param(self, key):
        return self.values.get(key, "")

    def set_param(self, key, value):
        self.values[key] = value


class _Env:
    def __init__(self):
        self.config = _Config()

    def __getitem__(self, item):
        if item != "ir.config_parameter":
            raise KeyError(item)
        return self.config


class TestUiBaseContractAssetEventQueue(unittest.TestCase):
    def setUp(self):
        self.env = _Env()

    def _meta(self):
        return json.loads(self.env.config.values[target.QUEUE_META_KEY])

    def assert_utc_z(self, value):
        self.assertRegex(value, r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
        self.assertNotRegex(value, re.escape("+00:00"))

    def test_enqueue_pop_and_compact_meta_timestamps_use_utc_z_contract(self):
        target.enqueue_scene_keys(self.env, scene_keys=["Project.List"], reason="unit")
        self.assert_utc_z(self._meta()["updated_at"])

        target.pop_scene_keys(self.env, limit=1)
        self.assert_utc_z(self._meta()["consumed_at"])

        self.env.config.values[target.QUEUE_KEY] = '["A__pkg1", "a", 42, ""]'
        target.get_queue_metrics(self.env)
        meta = self._meta()
        self.assertEqual(meta["last_operation"], "compact")
        self.assert_utc_z(meta["updated_at"])


if __name__ == "__main__":
    unittest.main()
