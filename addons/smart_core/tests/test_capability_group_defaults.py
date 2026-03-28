# -*- coding: utf-8 -*-
import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "core" / "capability_group_defaults.py"


def _load_target_module():
    spec = importlib.util.spec_from_file_location("capability_group_defaults_under_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


TARGET = _load_target_module()
default_group_meta = TARGET.default_group_meta
default_group_order_map = TARGET.default_group_order_map
infer_group_key = TARGET.infer_group_key


class TestCapabilityGroupDefaults(unittest.TestCase):
    def test_default_group_meta(self):
        self.assertEqual(default_group_meta("workspace")["label"], "工作台")
        self.assertEqual(default_group_meta("custom")["key"], "custom")

    def test_infer_group_key(self):
        self.assertEqual(infer_group_key("workspace.home"), "workspace")
        self.assertEqual(infer_group_key("analytics.sales"), "analytics")
        self.assertEqual(infer_group_key("permission.user"), "governance")

    def test_default_group_order_map(self):
        order_map = default_group_order_map()
        self.assertEqual(order_map["workspace"], 1)


if __name__ == "__main__":
    unittest.main()
