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
SERVICE_PATH = ROOT / "addons/smart_core/app_config_engine/services/contract_governance_filter.py"
SEARCH_PATH = ROOT / "addons/smart_core/app_config_engine/models/app_search_config.py"
WORKFLOW_PATH = ROOT / "addons/smart_core/app_config_engine/models/app_workflow_config.py"


class _FieldFactory:
    def __getattr__(self, _name):
        def _field(*_args, **_kwargs):
            return None

        return _field


class _Api:
    @staticmethod
    def model(func):
        return func


class _Groups:
    ids = []


class _User:
    groups_id = _Groups()


class _Env(dict):
    uid = 7
    user = _User()

    def ref(self, *_args, **_kwargs):
        return None


def _install_odoo_stub():
    odoo = types.ModuleType("odoo")
    odoo.models = types.SimpleNamespace(Model=object, AbstractModel=object)
    odoo.fields = _FieldFactory()
    odoo.api = _Api()
    odoo._ = lambda text, *args, **kwargs: text % args if args else text

    tools = types.ModuleType("odoo.tools")
    safe_eval_mod = types.ModuleType("odoo.tools.safe_eval")
    safe_eval_mod.safe_eval = lambda value, *_args, **_kwargs: value
    tools.safe_eval = safe_eval_mod.safe_eval

    sys.modules["odoo"] = odoo
    sys.modules["odoo.tools"] = tools
    sys.modules["odoo.tools.safe_eval"] = safe_eval_mod


def _load_module(name, path):
    _install_odoo_stub()
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class ContractProjectionJsonBoundaryTests(unittest.TestCase):
    def test_runtime_governance_filter_serializes_non_json_scalars(self):
        module = _load_module("smart_core_test_contract_governance_filter", SERVICE_PATH)
        owner = types.SimpleNamespace(env=_Env(), groups_id=None)

        result = module.ContractGovernanceFilterService(owner).apply_runtime_filter(
            {
                "toolbar": {"header": [{"name": "sync", "amount": Decimal("12.30")}]},
                "layout": [{"name": "base", "updated_on": date(2026, 6, 30)}],
            },
            "x.demo",
        )

        self.assertEqual(result["toolbar"]["header"][0]["amount"], "12.30")
        self.assertEqual(result["layout"][0]["updated_on"], "2026-06-30")

    def test_search_contract_serializes_non_json_scalars(self):
        module = _load_module("smart_core_test_app_search_config", SEARCH_PATH)
        record = module.AppSearchConfig.__new__(module.AppSearchConfig)
        record.env = _Env()
        record.model = "x.demo"
        record.version = 3
        record.search_def = {
            "filters": [{"key": "recent", "since": date(2026, 6, 30)}],
            "group_by": [],
            "facets": {"enabled": True},
            "defaults": {"amount": Decimal("12.30")},
        }
        record.ensure_one = lambda: None

        result = record.get_search_contract(filter_runtime=False, include_user_filters=False)

        self.assertEqual(result["filters"][0]["since"], "2026-06-30")
        self.assertEqual(result["defaults"]["amount"], "12.30")

        result = record.get_search_contract(filter_runtime=True, include_user_filters=False)
        self.assertEqual(result["filters"][0]["since"], "2026-06-30")
        self.assertEqual(result["defaults"]["amount"], "12.30")

    def test_workflow_contract_serializes_non_json_scalars(self):
        module = _load_module("smart_core_test_app_workflow_config", WORKFLOW_PATH)
        record = module.AppWorkflowConfig.__new__(module.AppWorkflowConfig)
        record.env = _Env()
        record.workflows_def = {
            "states": [{"key": "draft", "updated_on": date(2026, 6, 30)}],
            "transitions": [{"key": "submit", "amount": Decimal("12.30")}],
        }
        record.ensure_one = lambda: None

        result = record.get_workflow_contract(filter_runtime=False)

        self.assertEqual(result["states"][0]["updated_on"], "2026-06-30")
        self.assertEqual(result["transitions"][0]["amount"], "12.30")


if __name__ == "__main__":
    unittest.main()
