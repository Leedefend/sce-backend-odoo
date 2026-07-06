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


class _LegacyPolicyModel:
    def apply_to_view_contract(self, contract, *, model_name, view_type, action_id=None, view_id=None, excluded_field_names=None):
        excluded = {str(name or "").strip() for name in (excluded_field_names or []) if str(name or "").strip()}
        out = dict(contract or {})
        layout = out.get("layout")
        if isinstance(layout, list):
            out["layout"] = self._filter_layout(layout, excluded)
        return out

    def _filter_layout(self, nodes, excluded):
        result = []
        for node in nodes:
            if not isinstance(node, dict):
                continue
            row = dict(node)
            if row.get("type") == "field" and row.get("name") == "email" and "email" not in excluded:
                continue
            children = row.get("children")
            if isinstance(children, list):
                row["children"] = self._filter_layout(children, excluded)
            result.append(row)
        return result


class _Env(dict):
    pass


class _Model:
    _fields = {
        "name": object(),
        "email": object(),
        "company_id": object(),
        "amount_total": object(),
        "start_date": object(),
        "end_date": object(),
        "user_id": object(),
        "state": object(),
    }

    def fields_get(self):
        return {
            "name": {"string": "Name", "type": "char"},
            "email": {"string": "Email", "type": "char"},
        }


class TestViewOrchestrator(unittest.TestCase):
    def setUp(self):
        self.ViewOrchestrator = _load_orchestrator()

    def _compose(self, payload, contract, view_type, *, legacy_policy=False):
        env = _Env({"ui.business.config.contract": _ConfigModel(payload), "res.partner": _Model()})
        if legacy_policy:
            env["ui.form.field.policy"] = _LegacyPolicyModel()
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
                        "filters": [
                            {"name": "late", "label": "Late", "domain": [["active", "=", False]], "sequence": 20},
                            {"name": "active_customers", "label": "Active", "domain": [["active", "=", True]], "sequence": 10},
                        ],
                        "groupBys": [
                            {"name": "by_state", "field": "state", "label": "State", "sequence": 20},
                            {"name": "by_company", "field": "company_id", "label": "Company", "sequence": 10},
                        ],
                    }
                }
            }
        }

        result, calls = self._compose(payload, {"search": {"filters": [], "group_by": []}}, "search")

        self.assertEqual(result["search"]["filters"][0]["name"], "active_customers")
        self.assertEqual(result["search"]["filters"][0]["key"], "active_customers")
        self.assertEqual(result["search"]["filters"][0]["label"], "Active")
        self.assertEqual(result["search"]["group_by"][0]["field"], "company_id")
        self.assertEqual(result["search"]["group_by"][0]["label"], "Company")
        self.assertEqual(calls[0][1]["view_type"], "search")
        self.assertEqual((result["governance"]["view_orchestration"])["owner_layer"], "business_view_orchestration")
        trace = result["source_trace"]["view_orchestration"]
        self.assertEqual(trace["owner_layer"], "business_view_orchestration")
        self.assertEqual(trace["view_type"], "search")
        self.assertEqual(trace["action_id"], 11)
        self.assertEqual(trace["view_id"], 22)
        self.assertEqual(trace["business_config_contracts"][0]["id"], 9)

    def test_form_view_can_use_business_config_layout_overlay(self):
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
                                        "name": "flat_fields",
                                        "columns": 3,
                                        "children": [
                                            {"type": "field", "name": "email"},
                                            {"type": "field", "name": "missing_field"},
                                            {"type": "field", "name": "name"},
                                        ],
                                    }
                                ],
                            }
                        ],
                        "fields": [
                            {"name": "name", "label": "Partner Name", "sequence": 10},
                            {"name": "email", "label": "Email Alias", "sequence": 20},
                        ],
                    }
                }
            }
        }
        source_layout = [
            {
                "type": "sheet",
                "children": [
                    {"type": "group", "name": "native_group", "children": [{"type": "field", "name": "name"}]}
                ],
            }
        ]

        result, _calls = self._compose(payload, {"layout": source_layout}, "form")

        sheet = result["layout"][0]
        group = sheet["children"][0]
        self.assertEqual(group.get("name"), "flat_fields")
        self.assertEqual(group.get("columns"), 3)
        self.assertEqual([row.get("name") for row in group.get("children")], ["name", "email"])
        self.assertEqual(group["children"][0].get("label"), "Partner Name")
        self.assertNotIn("native_group", str(result["layout"]))
        self.assertNotIn("missing_field", str(result["layout"]))

    def test_form_view_appends_missing_fields_to_declared_group(self):
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
                                        "name": "primary",
                                        "string": "Primary",
                                        "children": [{"type": "field", "name": "name"}],
                                    }
                                ],
                            }
                        ],
                        "fields": [
                            {"name": "name", "label": "Partner Name", "sequence": 10, "group_title": "Primary"},
                            {"name": "email", "label": "Email Alias", "sequence": 20, "group_title": "Primary"},
                        ],
                    }
                }
            }
        }

        result, _calls = self._compose(payload, {"layout": []}, "form")

        group = result["layout"][0]["children"][0]
        self.assertEqual(group.get("string"), "Primary")
        self.assertEqual([row.get("name") for row in group.get("children")], ["name", "email"])
        self.assertNotIn("business_config_orchestration_fields", str(result["layout"]))

    def test_form_view_can_compose_entry_semantic_surface_without_layout_overlay(self):
        payload = {
            "view_orchestration": {
                "views": {
                    "form": {
                        "composition_mode": "entry_semantic_surface",
                        "sections": [
                            {"title": "Primary", "sequence": 10, "columns": 2, "fields": ["name"]},
                            {"title": "Contact", "sequence": 20, "columns": 2, "fields": ["email"]},
                        ],
                        "fields": [
                            {"name": "email", "label": "Email Alias", "sequence": 20, "group_title": "Contact"},
                            {"name": "name", "label": "Partner Name", "sequence": 10, "group_title": "Primary"},
                        ],
                    }
                }
            }
        }
        source_layout = [
            {
                "type": "sheet",
                "children": [
                    {"type": "group", "name": "native_group", "children": [{"type": "field", "name": "company_id"}]}
                ],
            }
        ]

        result, _calls = self._compose(payload, {"layout": source_layout}, "form")

        self.assertEqual([group.get("string") for group in result["layout"]], ["Primary", "Contact"])
        self.assertEqual(result["layout"][0].get("columns"), 2)
        self.assertEqual([field.get("name") for field in result["layout"][0]["children"]], ["name"])
        self.assertEqual(result["layout"][0]["children"][0].get("label"), "Partner Name")
        self.assertEqual([field.get("name") for field in result["layout"][1]["children"]], ["email"])
        self.assertNotIn("native_group", str(result["layout"]))

    def test_pivot_view_uses_business_config_measures_dimensions_and_defaults(self):
        payload = {
            "view_orchestration": {
                "views": {
                    "pivot": {
                        "measures": [{"name": "amount_total", "label": "Amount", "sequence": 20}],
                        "dimensions": [{"name": "company_id", "label": "Company", "sequence": 10}],
                        "defaults": {"measure": "amount_total"},
                        "chart_policy": {"type": "bar"},
                    }
                }
            }
        }

        result, _calls = self._compose(payload, {"pivot": {"measures": ["legacy"]}}, "pivot")

        self.assertEqual(result["pivot"]["measures"][0]["name"], "amount_total")
        self.assertEqual(result["pivot"]["measures"][0]["label"], "Amount")
        self.assertEqual(result["pivot"]["dimensions"][0]["name"], "company_id")
        self.assertEqual(result["pivot"]["dimensions"][0]["label"], "Company")
        self.assertEqual(result["pivot"]["defaults"]["measure"], "amount_total")
        self.assertEqual(result["pivot"]["chart_policy"]["type"], "bar")

    def test_generic_view_uses_business_config_slots_and_actions(self):
        payload = {
            "view_orchestration": {
                "views": {
                    "kanban": {
                        "fields": [
                            {"name": "email", "label": "Email", "sequence": 10},
                            {"name": "name", "label": "Name", "sequence": 20},
                            {"name": "state", "visible": False, "sequence": 30},
                        ],
                        "slots": {"primary": ["name", "state", "email"]},
                        "actions": [{"name": "open", "intent": "form.open"}],
                    }
                }
            }
        }

        result, _calls = self._compose(payload, {"kanban": {}}, "kanban")

        self.assertEqual([row["name"] for row in result["kanban"]["fields"]], ["email", "name"])
        self.assertEqual(result["kanban"]["fields"][0]["label"], "Email")
        self.assertEqual(result["kanban"]["slots"]["primary"], ["email", "name"])
        self.assertEqual(result["kanban"]["actions"][0]["intent"], "form.open")

    def test_graph_view_uses_business_config_scalar_and_display_rows(self):
        payload = {
            "view_orchestration": {
                "views": {
                    "graph": {
                        "type": "line",
                        "measure": "amount_total",
                        "dimension": "company_id",
                        "measures": [{"name": "amount_total", "label": "Amount", "sequence": 20}],
                        "dimensions": [{"name": "company_id", "label": "Company", "sequence": 10}],
                    }
                }
            }
        }

        result, _calls = self._compose(payload, {"graph": {}}, "graph")

        self.assertEqual(result["graph"]["type"], "line")
        self.assertEqual(result["graph"]["measure"], "amount_total")
        self.assertEqual(result["graph"]["dimension"], "company_id")
        self.assertEqual(result["graph"]["dimensions"][0]["label"], "Company")

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

    def test_form_view_uses_business_config_field_display_policy(self):
        payload = {
            "view_orchestration": {
                "views": {
                    "form": {
                        "fields": [
                            {
                                "name": "email",
                                "label": "Contact Email",
                                "readonly": True,
                                "required": "true",
                                "help": "Shown to the customer",
                                "widget": "email",
                                "class": "important",
                                "sequence": 10,
                            }
                        ]
                    }
                }
            }
        }
        contract = {
            "layout": [
                {
                    "type": "sheet",
                    "children": [
                        {
                            "type": "field",
                            "name": "email",
                            "fieldInfo": {"name": "email", "label": "Email"},
                        }
                    ],
                }
            ]
        }

        result, _calls = self._compose(payload, contract, "form")
        field = result["layout"][0]["children"][0]

        self.assertEqual(field["label"], "Contact Email")
        self.assertTrue(field["readonly"])
        self.assertTrue(field["required"])
        self.assertEqual(field["help"], "Shown to the customer")
        self.assertEqual(field["widget"], "email")
        self.assertEqual(field["fieldInfo"]["label"], "Contact Email")

    def test_business_config_declared_form_fields_are_not_overridden_by_legacy_policy(self):
        payload = {
            "view_orchestration": {
                "views": {
                    "form": {
                        "fields": [{"name": "email", "label": "Contract Email", "sequence": 10}]
                    }
                }
            }
        }
        contract = {
            "layout": [
                {
                    "type": "sheet",
                    "children": [
                        {"type": "field", "name": "email", "fieldInfo": {"name": "email", "label": "Email"}},
                    ],
                }
            ]
        }

        result, _calls = self._compose(payload, contract, "form", legacy_policy=True)

        fields = result["layout"][0]["children"]
        self.assertEqual([field["name"] for field in fields], ["email"])
        self.assertEqual(fields[0]["label"], "Contract Email")
        governance = result["governance"]["view_orchestration"]
        self.assertEqual(governance["business_config_form_fields"], ["email"])
        self.assertFalse(governance["legacy_field_policy_overlay"])

    def test_legacy_policy_still_applies_to_fields_not_declared_by_business_config(self):
        payload = {
            "view_orchestration": {
                "views": {
                    "form": {
                        "fields": [{"name": "name", "label": "Partner", "sequence": 10}]
                    }
                }
            }
        }
        contract = {
            "layout": [
                {
                    "type": "sheet",
                    "children": [
                        {"type": "field", "name": "name"},
                        {"type": "field", "name": "email"},
                    ],
                }
            ]
        }

        result, _calls = self._compose(payload, contract, "form", legacy_policy=True)

        fields = result["layout"][0]["children"]
        self.assertEqual([field["name"] for field in fields], ["name"])
        self.assertTrue(result["governance"]["view_orchestration"]["legacy_field_policy_overlay"])

    def test_form_view_uses_business_config_field_order_in_native_layout(self):
        payload = {
            "view_orchestration": {
                "views": {
                    "form": {
                        "fields": [
                            {"name": "email", "sequence": 10},
                            {"name": "name", "sequence": 20},
                        ]
                    }
                }
            }
        }
        contract = {
            "layout": [
                {
                    "type": "sheet",
                    "children": [
                        {"type": "field", "name": "name"},
                        {"type": "field", "name": "email"},
                    ],
                }
            ]
        }

        result, _calls = self._compose(payload, contract, "form")

        self.assertEqual([node["name"] for node in result["layout"][0]["children"]], ["email", "name"])

    def test_list_view_uses_business_config_column_display_policy(self):
        payload = {
            "view_orchestration": {
                "views": {
                    "tree": {
                        "columns": [
                            {
                                "name": "email",
                                "label": "Contact Email",
                                "readonly": True,
                                "help": "Shown to the customer",
                                "widget": "email",
                                "width": "180px",
                                "sequence": 10,
                            }
                        ]
                    }
                }
            }
        }
        contract = {"columns": ["email"], "columns_schema": [{"name": "email", "label": "Email"}]}

        result, _calls = self._compose(payload, contract, "tree")
        column = result["columns_schema"][0]

        self.assertEqual(column["label"], "Contact Email")
        self.assertTrue(column["readonly"])
        self.assertEqual(column["help"], "Shown to the customer")
        self.assertEqual(column["widget"], "email")
        self.assertEqual(column["width"], "180px")

    def test_list_view_uses_business_config_view_options(self):
        payload = {
            "view_orchestration": {
                "views": {
                    "tree": {
                        "columns": [{"name": "email", "sequence": 10}],
                        "order": "write_date desc",
                        "page_size": 80,
                        "row_classes": [{"class": "late", "expr": "date_deadline < today"}],
                        "domain": {"base": [["active", "=", True]]},
                        "context": {"default_active": True},
                    }
                }
            }
        }
        contract = {"columns": ["email"], "columns_schema": [{"name": "email"}], "page_size": 20}

        result, _calls = self._compose(payload, contract, "tree")

        self.assertEqual(result["order"], "write_date desc")
        self.assertEqual(result["page_size"], 80)
        self.assertEqual(result["row_classes"][0]["class"], "late")
        self.assertEqual(result["domain"]["base"][0][0], "active")
        self.assertTrue(result["context"]["default_active"])

    def test_dashboard_view_uses_business_config_cards_and_kpis(self):
        payload = {
            "view_orchestration": {
                "views": {
                    "dashboard": {
                        "title": "Executive Overview",
                        "cards": [{"name": "revenue", "label": "Revenue"}],
                        "kpis": [{"name": "win_rate", "label": "Win Rate"}],
                    }
                }
            }
        }

        result, _calls = self._compose(payload, {"dashboard": {}}, "dashboard")

        self.assertEqual(result["dashboard"]["title"], "Executive Overview")
        self.assertEqual(result["dashboard"]["cards"][0]["name"], "revenue")
        self.assertEqual(result["dashboard"]["kpis"][0]["name"], "win_rate")

    def test_runtime_orchestration_drops_unknown_field_refs_from_existing_configs(self):
        payload = {
            "view_orchestration": {
                "views": {
                    "tree": {
                        "columns": [
                            {"name": "email", "sequence": 10},
                            {"name": "missing_column", "sequence": 20},
                        ],
                        "default_group_by": "missing_group",
                        "actions": [{"name": "open_dashboard", "intent": "project.dashboard.enter"}],
                    }
                }
            }
        }
        contract = {
            "columns": ["name", "email"],
            "columns_schema": [{"name": "name"}, {"name": "email"}],
        }

        result, _calls = self._compose(payload, contract, "tree")

        self.assertEqual(result["columns"], ["email", "name"])
        self.assertEqual([row["name"] for row in result["columns_schema"]], ["email", "name"])
        self.assertEqual(result["row_actions"][0]["intent"], "project.dashboard.enter")
        self.assertNotIn("default_group_by", result)


if __name__ == "__main__":
    unittest.main()
