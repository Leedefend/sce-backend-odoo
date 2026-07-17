#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import importlib.util
import sys
import types
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = ROOT / "addons/smart_core/model/ui_business_config_contract.py"


def _install_odoo_stubs() -> None:
    class _Api:
        @staticmethod
        def constrains(*_args, **_kwargs):
            return lambda func: func

        @staticmethod
        def model(func):
            return func

        @staticmethod
        def model_create_multi(func):
            return func

    class _Fields:
        @staticmethod
        def Char(*_args, **_kwargs):
            return None

        @staticmethod
        def Selection(*_args, **_kwargs):
            return None

        @staticmethod
        def Many2one(*_args, **_kwargs):
            return None

        @staticmethod
        def Integer(*_args, **_kwargs):
            return None

        @staticmethod
        def Boolean(*_args, **_kwargs):
            return None

        @staticmethod
        def Json(*_args, **_kwargs):
            return None

        class Datetime:
            def __new__(cls, *_args, **_kwargs):
                return None

            @staticmethod
            def now():
                return "2026-01-01 00:00:00"

    odoo_mod = types.ModuleType("odoo")
    odoo_mod.api = _Api()
    odoo_mod.fields = _Fields()
    odoo_mod.models = types.SimpleNamespace(Model=object)
    odoo_mod.__path__ = []
    addons_mod = types.ModuleType("odoo.addons")
    addons_mod.__path__ = [str(ROOT / "addons")]
    smart_core_mod = types.ModuleType("odoo.addons.smart_core")
    smart_core_mod.__path__ = [str(ROOT / "addons/smart_core")]
    smart_core_model_mod = types.ModuleType("odoo.addons.smart_core.model")
    smart_core_model_mod.__path__ = [str(ROOT / "addons/smart_core/model")]
    utils_mod = types.ModuleType("odoo.addons.smart_core.utils")
    utils_mod.__path__ = [str(ROOT / "addons/smart_core/utils")]
    exceptions_mod = types.ModuleType("odoo.exceptions")
    exceptions_mod.ValidationError = type("ValidationError", (Exception,), {})
    sys.modules["odoo"] = odoo_mod
    sys.modules["odoo.addons"] = addons_mod
    sys.modules["odoo.addons.smart_core"] = smart_core_mod
    sys.modules["odoo.addons.smart_core.model"] = smart_core_model_mod
    sys.modules["odoo.addons.smart_core.utils"] = utils_mod
    sys.modules["odoo.exceptions"] = exceptions_mod


def _load_module():
    _install_odoo_stubs()
    module_name = "odoo.addons.smart_core.model.ui_business_config_contract"
    spec = importlib.util.spec_from_file_location(module_name, MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class BusinessConfigContractSchemaTests(unittest.TestCase):
    def setUp(self):
        self.module = _load_module()
        self.contract = self.module.UIBusinessConfigContract

    def test_unknown_view_orchestration_fields_are_reported(self):
        payload = {
            "view_orchestration": {
                "views": {
                    "tree": {
                        "columns": [{"name": "name"}, {"name": "missing_column"}],
                        "default_group_by": "missing_group",
                    },
                    "kanban": {
                        "slots": {"primary": ["name", "missing_slot"]},
                    },
                    "calendar": {
                        "date_slots": {"start": "date_start", "stop": "missing_stop"},
                    },
                    "pivot": {
                        "measures": ["amount_total", "missing_measure"],
                        "dimensions": [{"field": "partner_id"}, {"field": "missing_dimension"}],
                    },
                }
            }
        }

        unknown = self.contract._unknown_view_orchestration_fields(
            payload,
            {"name", "date_start", "amount_total", "partner_id"},
        )

        self.assertEqual(
            unknown,
            [
                "calendar.date_slots.stop:missing_stop",
                "kanban.slots.primary:missing_slot",
                "pivot.dimensions:missing_dimension",
                "pivot.measures:missing_measure",
                "tree.columns:missing_column",
                "tree.default_group_by:missing_group",
            ],
        )

    def test_business_semantic_ids_are_not_treated_as_model_fields(self):
        payload = {
            "view_orchestration": {
                "views": {
                    "kanban": {
                        "cards": [{"name": "delivery_status_card"}],
                        "kpis": [{"name": "gross_margin"}],
                        "actions": [{"name": "open_settlement"}],
                        "navigation_slots": {"primary": "project_dashboard"},
                    }
                }
            }
        }

        self.assertEqual(
            self.contract._unknown_view_orchestration_fields(payload, {"name"}),
            [],
        )

    def test_source_authority_declares_boundary_classifier(self):
        source = self.contract.source_authority_contract(self.contract)

        self.assertEqual(source.get("kind"), "ui_business_config_contract_orchestration_config")
        self.assertEqual(source.get("boundary_classifier"), "smart_core.utils.backend_contract_boundaries")

    def test_form_layout_unknown_fields_are_reported(self):
        payload = {
            "view_orchestration": {
                "views": {
                    "form": {
                        "layout": [
                            {
                                "type": "sheet",
                                "children": [
                                    {
                                        "type": "group",
                                        "children": [
                                            {"type": "field", "name": "name"},
                                            {"type": "field", "name": "missing_layout_field"},
                                        ],
                                    }
                                ],
                            }
                        ]
                    }
                }
            }
        }

        self.assertEqual(
            self.contract._unknown_view_orchestration_fields(payload, {"name"}),
            ["form.layout[0].children[0].children[1]:missing_layout_field"],
        )

    def test_form_columns_accepts_layout_column_count(self):
        payload = {
            "view_orchestration": {
                "views": {
                    "form": {
                        "columns": 2,
                        "fields": [{"name": "name"}],
                        "layout": [{"type": "field", "name": "name"}],
                    }
                }
            }
        }

        self.contract._check_view_orchestration_payload(self.contract, payload)

    def test_list_columns_still_requires_array(self):
        payload = {
            "view_orchestration": {
                "views": {
                    "tree": {
                        "columns": 2,
                    }
                }
            }
        }

        with self.assertRaises(self.module.ValidationError):
            self.contract._check_view_orchestration_payload(self.contract, payload)


if __name__ == "__main__":
    unittest.main()
