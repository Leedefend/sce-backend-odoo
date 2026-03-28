# -*- coding: utf-8 -*-
import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "core" / "delivery_capability_entry_defaults.py"


def _load_target_module():
    spec = importlib.util.spec_from_file_location("delivery_capability_entry_defaults_under_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


TARGET = _load_target_module()
build_delivery_capability_entry = TARGET.build_delivery_capability_entry


class TestDeliveryCapabilityEntryDefaults(unittest.TestCase):
    def test_build_delivery_capability_entry_uses_row_and_runtime_defaults(self):
        payload = build_delivery_capability_entry(
            {"capability_key": "delivery.workspace", "product_key": "prod_a"},
            {"ui_label": "工作台能力", "group_key": "workspace", "state": "READY"},
        )

        self.assertEqual(payload["key"], "delivery.workspace")
        self.assertEqual(payload["label"], "工作台能力")
        self.assertEqual(payload["group_key"], "workspace")
        self.assertEqual(payload["runtime_state"], "READY")


if __name__ == "__main__":
    unittest.main()
