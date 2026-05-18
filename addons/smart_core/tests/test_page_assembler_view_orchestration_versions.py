#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import importlib.util
import sys
import types
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = ROOT / "addons/smart_core/app_config_engine/services/assemblers/page_assembler.py"


def _install_module(name, **attrs):
    module = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(module, key, value)
    sys.modules[name] = module
    return module


def _load_page_assembler():
    for name in list(sys.modules):
        if name == "odoo" or name.startswith("odoo."):
            sys.modules.pop(name, None)
    odoo = _install_module("odoo", _=lambda value: value)
    _install_module("odoo.http", request=types.SimpleNamespace(env=None))
    odoo.http = sys.modules["odoo.http"]
    _install_module("odoo.addons")
    smart_core = _install_module("odoo.addons.smart_core")
    app_config = _install_module("odoo.addons.smart_core.app_config_engine")
    services = _install_module("odoo.addons.smart_core.app_config_engine.services")
    assemblers = _install_module("odoo.addons.smart_core.app_config_engine.services.assemblers")
    utils = _install_module("odoo.addons.smart_core.utils")
    smart_core.__path__ = [str(ROOT / "addons/smart_core")]
    app_config.__path__ = [str(ROOT / "addons/smart_core/app_config_engine")]
    services.__path__ = [str(ROOT / "addons/smart_core/app_config_engine/services")]
    assemblers.__path__ = [str(ROOT / "addons/smart_core/app_config_engine/services/assemblers")]
    utils.__path__ = [str(ROOT / "addons/smart_core/utils")]
    _install_module(
        "odoo.addons.smart_core.utils.delete_policy",
        resolve_unlink_policy=lambda *_args, **_kwargs: {},
    )
    _install_module(
        "odoo.addons.smart_core.utils.extension_hooks",
        call_extension_hook_first=lambda *_args, **_kwargs: None,
    )
    _install_module(
        "odoo.addons.smart_core.app_config_engine.utils.misc",
        safe_eval=lambda value: value,
    )
    _install_module(
        "odoo.addons.smart_core.app_config_engine.utils.view_utils",
        extract_tree_columns_strict=lambda *_args, **_kwargs: ([], None),
        normalize_cols_safely=lambda value: value,
    )
    module_name = "odoo.addons.smart_core.app_config_engine.services.assemblers.page_assembler"
    sys.modules.pop(module_name, None)
    spec = importlib.util.spec_from_file_location(module_name, MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module.PageAssembler


class PageAssemblerViewOrchestrationVersionTests(unittest.TestCase):
    def setUp(self):
        self.PageAssembler = _load_page_assembler()
        self.assembler = self.PageAssembler.__new__(self.PageAssembler)

    def test_append_view_version_token_adds_search_orchestration_version(self):
        versions = {"view": "12:native", "search": 4}

        self.assembler._append_view_version_token(versions, "7:9.3")

        self.assertEqual(versions["view"], "12:native,7:9.3")
        self.assertEqual(versions["search"], 4)

    def test_append_view_version_token_is_idempotent(self):
        versions = {"view": "12:native,7:9.3"}

        self.assembler._append_view_version_token(versions, "7:9.3")

        self.assertEqual(versions["view"], "12:native,7:9.3")

    def test_coerce_calendar_preserves_orchestrated_slot_semantics(self):
        result = self.assembler._coerce_view_contract_semantics(
            "calendar",
            {
                "calendar": {
                    "date_start": "planned_start",
                    "date_stop": "planned_stop",
                    "date_slots": {"start": "planned_start", "stop": "planned_stop"},
                    "color_slots": {"color": "user_id"},
                    "fields": [{"name": "planned_start"}],
                }
            },
        )

        self.assertEqual(result["date_start"], "planned_start")
        self.assertEqual(result["date_slots"]["start"], "planned_start")
        self.assertEqual(result["color_slots"]["color"], "user_id")
        self.assertEqual(result["fields"][0]["name"], "planned_start")

    def test_coerce_dashboard_preserves_orchestrated_slots(self):
        result = self.assembler._coerce_view_contract_semantics(
            "dashboard",
            {
                "dashboard": {
                    "cards": [{"name": "revenue"}],
                    "kpis": [{"name": "margin"}],
                    "metric_slots": {"primary": ["amount_total"]},
                    "navigation_slots": {"next": "project.dashboard.enter"},
                }
            },
        )

        self.assertEqual(result["cards"][0]["name"], "revenue")
        self.assertEqual(result["kpis"][0]["name"], "margin")
        self.assertEqual(result["metric_slots"]["primary"], ["amount_total"])
        self.assertEqual(result["navigation_slots"]["next"], "project.dashboard.enter")


if __name__ == "__main__":
    unittest.main()
