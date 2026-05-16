# -*- coding: utf-8 -*-
import importlib.util
import sys
import types
import unittest
from pathlib import Path


def _install_module(name):
    module = types.ModuleType(name)
    sys.modules[name] = module
    return module


def _load_orchestrator():
    root = Path(__file__).resolve().parents[1]
    _install_module("odoo")
    _install_module("odoo.addons")
    smart_core_mod = _install_module("odoo.addons.smart_core")
    core_mod = _install_module("odoo.addons.smart_core.core")
    smart_core_mod.__path__ = [str(root)]
    core_mod.__path__ = [str(root / "core")]
    for module_name in (
        "odoo.addons.smart_core.core.source_authority",
        "odoo.addons.smart_core.core.view_orchestration_contract",
        "odoo.addons.smart_core.core.view_orchestrator",
    ):
        sys.modules.pop(module_name, None)
    for filename, module_name in (
        ("source_authority.py", "odoo.addons.smart_core.core.source_authority"),
        ("view_orchestration_contract.py", "odoo.addons.smart_core.core.view_orchestration_contract"),
        ("view_orchestrator.py", "odoo.addons.smart_core.core.view_orchestrator"),
    ):
        spec = importlib.util.spec_from_file_location(module_name, root / "core" / filename)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
    return sys.modules["odoo.addons.smart_core.core.view_orchestrator"].ViewOrchestrator


class _Config:
    id = 9
    name = "demo"
    version_no = 3

    def __init__(self, payload):
        self.contract_json = payload


class _ConfigModel:
    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    def _effective_view_orchestration_contracts(self, model_name, **kwargs):
        self.calls.append((model_name, kwargs))
        return [_Config(self.payload)]


class _Env(dict):
    pass


class TestViewOrchestrator(unittest.TestCase):
    def setUp(self):
        self.ViewOrchestrator = _load_orchestrator()

    def _compose(self, payload, contract, view_type):
        env = _Env({"ui.business.config.contract": _ConfigModel(payload)})
        result = self.ViewOrchestrator(env).compose(
            contract,
            model_name="res.partner",
            view_type=view_type,
            action_id=11,
            view_id=22,
        )
        return result, env["ui.business.config.contract"].calls

    def test_search_view_uses_business_config_filters_and_group_by(self):
        payload = {
            "view_orchestration": {
                "views": {
                    "search": {
                        "filters": [{"name": "active_customers", "domain": [["active", "=", True]]}],
                        "groupBys": [{"name": "by_company", "field": "company_id"}],
                    }
                }
            }
        }

        result, calls = self._compose(payload, {"search": {"filters": [], "group_by": []}}, "search")

        self.assertEqual(result["search"]["filters"][0]["name"], "active_customers")
        self.assertEqual(result["search"]["group_by"][0]["field"], "company_id")
        self.assertEqual(calls[0][1]["view_type"], "search")
        self.assertEqual((result["governance"]["view_orchestration"])["owner_layer"], "business_view_orchestration")
        trace = result["source_trace"]["view_orchestration"]
        self.assertEqual(trace["owner_layer"], "business_view_orchestration")
        self.assertEqual(trace["view_type"], "search")
        self.assertEqual(trace["action_id"], 11)
        self.assertEqual(trace["view_id"], 22)
        self.assertEqual(trace["business_config_contracts"][0]["id"], 9)

    def test_pivot_view_uses_business_config_measures_dimensions_and_defaults(self):
        payload = {
            "view_orchestration": {
                "views": {
                    "pivot": {
                        "measures": ["amount_total"],
                        "dimensions": ["company_id"],
                        "defaults": {"measure": "amount_total"},
                        "chart_policy": {"type": "bar"},
                    }
                }
            }
        }

        result, _calls = self._compose(payload, {"pivot": {"measures": ["legacy"]}}, "pivot")

        self.assertEqual(result["pivot"]["measures"], ["amount_total"])
        self.assertEqual(result["pivot"]["dimensions"], ["company_id"])
        self.assertEqual(result["pivot"]["defaults"]["measure"], "amount_total")
        self.assertEqual(result["pivot"]["chart_policy"]["type"], "bar")

    def test_generic_view_uses_business_config_slots_and_actions(self):
        payload = {
            "view_orchestration": {
                "views": {
                    "kanban": {
                        "slots": {"primary": ["name", "email"]},
                        "actions": [{"name": "open", "intent": "form.open"}],
                    }
                }
            }
        }

        result, _calls = self._compose(payload, {"kanban": {}}, "kanban")

        self.assertEqual(result["kanban"]["slots"]["primary"], ["name", "email"])
        self.assertEqual(result["kanban"]["actions"][0]["intent"], "form.open")

    def test_calendar_view_uses_business_config_date_resource_and_color_slots(self):
        payload = {
            "view_orchestration": {
                "views": {
                    "calendar": {
                        "date_slots": {"start": "start_date", "stop": "end_date"},
                        "resource_slots": {"owner": "user_id"},
                        "color_slots": {"state": "state"},
                    }
                }
            }
        }

        result, _calls = self._compose(payload, {"calendar": {}}, "calendar")

        self.assertEqual(result["calendar"]["date_slots"]["start"], "start_date")
        self.assertEqual(result["calendar"]["resource_slots"]["owner"], "user_id")
        self.assertEqual(result["calendar"]["color_slots"]["state"], "state")

    def test_dashboard_view_uses_business_config_metric_chart_and_navigation_slots(self):
        payload = {
            "view_orchestration": {
                "views": {
                    "dashboard": {
                        "metric_slots": {"primary": ["amount_total"]},
                        "chart_slots": {"trend": {"type": "line"}},
                        "navigation_slots": {"next": "project.dashboard.enter"},
                    }
                }
            }
        }

        result, _calls = self._compose(payload, {"dashboard": {}}, "dashboard")

        self.assertEqual(result["dashboard"]["metric_slots"]["primary"], ["amount_total"])
        self.assertEqual(result["dashboard"]["chart_slots"]["trend"]["type"], "line")
        self.assertEqual(result["dashboard"]["navigation_slots"]["next"], "project.dashboard.enter")

    def test_list_view_uses_business_config_row_actions(self):
        payload = {
            "view_orchestration": {
                "views": {
                    "tree": {
                        "columns": [{"name": "name", "sequence": 10}],
                        "actions": [{"name": "open_dashboard", "intent": "project.dashboard.enter"}],
                    }
                }
            }
        }

        result, _calls = self._compose(payload, {"columns": ["name"], "row_actions": []}, "tree")

        self.assertEqual(result["row_actions"][0]["intent"], "project.dashboard.enter")

    def test_form_view_uses_business_config_action_slots_without_field_rows(self):
        payload = {
            "view_orchestration": {
                "views": {
                    "form": {
                        "action_slots": {
                            "header_buttons": [{"name": "approve", "intent": "record.approve"}],
                            "stat_buttons": [{"name": "analytics", "intent": "analytics.open"}],
                        }
                    }
                }
            }
        }

        result, _calls = self._compose(payload, {"layout": [], "header_buttons": []}, "form")

        self.assertEqual(result["header_buttons"][0]["intent"], "record.approve")
        self.assertEqual(result["stat_buttons"][0]["intent"], "analytics.open")


if __name__ == "__main__":
    unittest.main()
