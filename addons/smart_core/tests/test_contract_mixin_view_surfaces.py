#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import importlib.util
import sys
import types
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = ROOT / "addons/smart_core/app_config_engine/models/contract_mixin.py"


def _load_mixin():
    class _Api:
        @staticmethod
        def model(func):
            return func

    sys.modules["odoo"] = types.SimpleNamespace(models=types.SimpleNamespace(AbstractModel=object), api=_Api())
    spec = importlib.util.spec_from_file_location("smart_core_test_contract_mixin", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module.ContractSchemaMixin


class ContractMixinViewSurfaceTests(unittest.TestCase):
    def setUp(self):
        self.mixin = _load_mixin().__new__(_load_mixin())

    def test_native_sanitize_serializes_non_json_scalars(self):
        result = self.mixin.sanitize_native_contract(
            "form",
            {
                "layout": {
                    "updated_on": date(2026, 6, 30),
                    "amount": Decimal("12.30"),
                }
            },
        )

        self.assertEqual(result["layout"]["updated_on"], "2026-06-30")
        self.assertEqual(result["layout"]["amount"], "12.30")

    def test_governed_form_passthrough_serializes_non_json_scalars(self):
        result = self.mixin.sanitize_governed_contract(
            "form",
            {
                "layout": {
                    "sections": [
                        {
                            "name": "base",
                            "updated_on": date(2026, 6, 30),
                            "amount": Decimal("12.30"),
                        }
                    ]
                }
            },
        )

        section = result["layout"]["sections"][0]
        self.assertEqual(section["updated_on"], "2026-06-30")
        self.assertEqual(section["amount"], "12.30")

    def test_governed_sanitize_keeps_non_form_view_surface_blocks(self):
        for view_type, surface_key in (
            ("search", "search"),
            ("activity", "activity"),
            ("dashboard", "dashboard"),
        ):
            with self.subTest(view_type=view_type):
                result = self.mixin.sanitize_governed_contract(
                    view_type,
                    {
                        surface_key: {"fields": [{"name": "name"}], "cards": [{"name": "kpi"}]},
                        "unsafe_nested": {"should": "drop"},
                    },
                )

                self.assertIn(surface_key, result)
                self.assertNotIn("unsafe_nested", result)


if __name__ == "__main__":
    unittest.main()
