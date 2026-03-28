# -*- coding: utf-8 -*-
import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "core" / "delivery_menu_defaults.py"


def _load_target_module():
    spec = importlib.util.spec_from_file_location("delivery_menu_defaults_under_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


TARGET = _load_target_module()
build_delivery_menu_child = TARGET.build_delivery_menu_child
build_delivery_menu_group = TARGET.build_delivery_menu_group
build_delivery_menu_root = TARGET.build_delivery_menu_root
synthetic_menu_id = TARGET.synthetic_menu_id


class TestDeliveryMenuDefaults(unittest.TestCase):
    def test_synthetic_menu_id_stable(self):
        self.assertEqual(synthetic_menu_id("abc"), synthetic_menu_id("abc"))

    def test_build_delivery_menu_child(self):
        payload = build_delivery_menu_child({"menu_key": "k1", "label": "L1", "route": "/x"})
        self.assertEqual(payload["key"], "k1")
        self.assertEqual(payload["meta"]["route"], "/x")

    def test_build_delivery_menu_group_and_root(self):
        group = build_delivery_menu_group("released_products", "已发布产品", [])
        root = build_delivery_menu_root([group], "pm")
        self.assertEqual(group["key"], "group:released_products")
        self.assertEqual(root["meta"]["role_code"], "pm")


if __name__ == "__main__":
    unittest.main()
