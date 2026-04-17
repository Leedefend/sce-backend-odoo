# -*- coding: utf-8 -*-
import ast
import pathlib

from odoo.tests.common import TransactionCase, tagged

from ..handlers.load_contract import LoadContractHandler
from ..app_config_engine.services.contract_service import ContractService
from ..app_config_engine.services.page_policy_service import PagePolicyService
from ..v2.services.ui_contract_service import UIContractServiceV2
from ..utils.contract_governance import apply_contract_governance


@tagged("post_install", "-at_install", "smart_core", "load_contract_capability_profile")
class TestLoadContractCapabilityProfile(TransactionCase):
    def _make_handler(self):
        return LoadContractHandler.__new__(LoadContractHandler)

    def test_tree_searchpanel_recommends_native_fallback(self):
        handler = self._make_handler()
        data = {
            "views": {
                "tree": {
                    "columns": ["name", "state"],
                    "capabilities": {"inline_edit": False},
                }
            },
            "search": {
                "filters": [{"name": "mine", "string": "My"}],
                "search_panel": {"enabled": True, "sections": [{"key": "state"}]},
            },
            "fields": {"name": {"type": "char"}, "state": {"type": "selection"}},
            "head": {"model": "project.task", "view_type": "tree"},
            "permissions": {"read": True, "write": True, "create": True, "unlink": False},
        }

        handler._inject_semantic_contract(data)

        capability_profile = ((data.get("semantic_page") or {}).get("capability_profile") or {})
        list_semantics = ((data.get("semantic_page") or {}).get("list_semantics") or {})
        render_policy = capability_profile.get("render_policy") or {}
        primary = (capability_profile.get("view_profiles") or {}).get("tree") or {}

        self.assertEqual(capability_profile.get("primary_view_type"), "tree")
        self.assertEqual(render_policy.get("recommended_runtime"), "native")
        self.assertEqual((render_policy.get("fallback_action") or {}).get("key"), "open_native")
        self.assertIn("searchpanel_full_ecosystem", primary.get("unsupported_features") or [])
        self.assertEqual(list_semantics.get("page_size"), 50)
        self.assertTrue(list_semantics.get("supports_export_current_result"))

    def test_form_inline_subview_recommends_native_fallback(self):
        handler = self._make_handler()
        data = {
            "views": {
                "form": {
                    "layout": [{"type": "group", "children": []}],
                    "subviews": {
                        "line_ids": {
                            "policies": {"inline_edit": True},
                            "tree": {"columns": ["name", "amount"]},
                        }
                    },
                }
            },
            "fields": {
                "name": {"type": "char"},
                "line_ids": {"type": "one2many", "relation": "x.line"},
            },
            "head": {"model": "x.form", "view_type": "form"},
            "permissions": {"read": True, "write": True, "create": True, "unlink": False},
        }

        handler._inject_semantic_contract(data)

        capability_profile = ((data.get("semantic_page") or {}).get("capability_profile") or {})
        form_semantics = ((data.get("semantic_page") or {}).get("form_semantics") or {})
        render_policy = capability_profile.get("render_policy") or {}
        primary = (capability_profile.get("view_profiles") or {}).get("form") or {}

        self.assertEqual(render_policy.get("recommended_runtime"), "native")
        self.assertIn("complex_one2many_inline_edit", primary.get("unsupported_features") or [])
        self.assertIn("FORM_INLINE_SUBVIEW_NATIVE_FALLBACK", primary.get("reason_codes") or [])
        relations = form_semantics.get("relation_fields") or []
        self.assertEqual(relations[0].get("takeover_hint"), "native")
        self.assertIn("line_ids", form_semantics.get("field_behavior_map") or {})

    def test_kanban_keeps_lightweight_frontend_profile(self):
        handler = self._make_handler()
        data = {
            "views": {
                "kanban": {
                    "fields": ["name", "stage_id", "amount_total"],
                    "quick_actions": [{"name": "action_open"}],
                    "stages_field": "stage_id",
                }
            },
            "fields": {
                "name": {"type": "char"},
                "stage_id": {"type": "many2one"},
                "amount_total": {"type": "monetary"},
            },
            "head": {"model": "project.project", "view_type": "kanban"},
            "permissions": {"read": True, "write": True, "create": True, "unlink": False},
        }

        handler._inject_semantic_contract(data)

        capability_profile = ((data.get("semantic_page") or {}).get("capability_profile") or {})
        kanban_semantics = ((data.get("semantic_page") or {}).get("kanban_semantics") or {})
        render_policy = capability_profile.get("render_policy") or {}
        primary = (capability_profile.get("view_profiles") or {}).get("kanban") or {}

        self.assertEqual(render_policy.get("recommended_runtime"), "frontend")
        self.assertEqual(primary.get("support_tier"), "lightweight")
        self.assertIn("drag_drop", primary.get("unsupported_features") or [])
        self.assertEqual(kanban_semantics.get("group_by_field"), "stage_id")
        self.assertEqual(kanban_semantics.get("support_tier"), "lightweight")

    def test_form_field_restriction_keeps_tree_columns(self):
        service = PagePolicyService.__new__(PagePolicyService)
        data = {
            "views": {
                "tree": {
                    "columns": ["name", "company_id", "sc_department_id"],
                },
                "form": {
                    "layout": [
                        {
                            "type": "sheet",
                            "children": [
                                {"type": "field", "name": "name"},
                                {"type": "field", "name": "login"},
                                {"type": "field", "name": "active"},
                            ],
                        }
                    ],
                },
            },
            "fields": {
                "name": {"string": "名称", "type": "char"},
                "login": {"string": "登录账号", "type": "char"},
                "active": {"string": "启用", "type": "boolean"},
                "company_id": {"string": "所属公司", "type": "many2one"},
                "sc_department_id": {"string": "部门", "type": "many2one"},
            },
        }

        service.restrict_form_fields_to_layout(data)

        self.assertEqual(data.get("visible_fields"), ["name", "login", "active"])
        self.assertIn("company_id", data.get("fields") or {})
        self.assertIn("sc_department_id", data.get("fields") or {})
        self.assertIn("login", data.get("fields") or {})

    def test_page_assembler_no_longer_calls_form_field_restriction(self):
        source_path = pathlib.Path(__file__).resolve().parents[1] / "app_config_engine" / "services" / "assemblers" / "page_assembler.py"
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        calls = []

        class Finder(ast.NodeVisitor):
            def visit_FunctionDef(self, node):
                if node.name != "assemble_page_contract":
                    return
                self.generic_visit(node)

            def visit_Call(self, node):
                func = node.func
                if isinstance(func, ast.Attribute) and func.attr == "_restrict_form_fields_to_layout":
                    calls.append(node.lineno)
                self.generic_visit(node)

        Finder().visit(tree)

        self.assertEqual(calls, [])

    def test_contract_service_preserves_semantic_layout_and_tab_titles(self):
        service = ContractService.__new__(ContractService)
        contract = {
            "data": {
                "views": {
                    "form": {
                        "layout": [
                            {
                                "type": "notebook",
                                "children": [],
                                "tabs": [
                                    {
                                        "children": [
                                            {
                                                "type": "page",
                                                "children": [
                                                    {"type": "field", "name": "name"},
                                                ],
                                                "attributes": {"string": "项目概览"},
                                            }
                                        ],
                                    }
                                ],
                            }
                        ],
                    }
                },
                "semantic_page": {
                    "form_semantics": {},
                },
            }
        }

        service._normalize_form_structure_semantics(contract)

        semantic_page = contract.get("data", {}).get("semantic_page") or {}
        form_semantics = semantic_page.get("form_semantics") or {}
        layout = form_semantics.get("layout")
        notebook = (((contract.get("data") or {}).get("views") or {}).get("form") or {}).get("layout") or []
        notebook = notebook[0] if notebook else {}
        tabs = notebook.get("tabs") or []

        self.assertIsInstance(layout, list)
        self.assertEqual(form_semantics.get("layout_source"), "views.form.layout")
        self.assertEqual(form_semantics.get("layout_section_count"), 1)
        self.assertEqual(tabs[0].get("title"), "项目概览")
        self.assertEqual(tabs[0].get("label"), "项目概览")
        self.assertEqual(notebook.get("label"), "项目概览")

    def test_v2_ui_contract_service_preserves_semantic_layout(self):
        contract = {
            "views": {
                "form": {
                    "layout": [
                        {
                            "type": "notebook",
                            "children": [],
                            "tabs": [
                                {
                                    "children": [
                                        {
                                            "type": "page",
                                            "children": [
                                                {"type": "field", "name": "name"},
                                            ],
                                            "name": "实施详情",
                                        }
                                    ],
                                }
                            ],
                        }
                    ],
                }
            },
            "semantic_page": {
                "form_semantics": {},
            },
        }

        normalized = UIContractServiceV2._normalize_form_structure_semantics(contract)
        form_semantics = (((normalized.get("semantic_page") or {}).get("form_semantics") or {}))
        layout = form_semantics.get("layout")
        notebook = (((normalized.get("views") or {}).get("form") or {}).get("layout") or [])
        notebook = notebook[0] if notebook else {}
        tabs = notebook.get("tabs") or []

        self.assertIsInstance(layout, list)
        self.assertEqual(form_semantics.get("layout_source"), "views.form.layout")
        self.assertEqual(form_semantics.get("layout_section_count"), 1)
        self.assertEqual(tabs[0].get("title"), "实施详情")
        self.assertEqual(tabs[0].get("label"), "实施详情")
        self.assertEqual(notebook.get("label"), "实施详情")

    def test_notebook_tab_titles_prefer_native_string_over_placeholders(self):
        service = ContractService.__new__(ContractService)
        contract = {
            "data": {
                "views": {
                    "form": {
                        "layout": [
                            {
                                "type": "notebook",
                                "tabs": [
                                    {"type": "page", "title": "页签1", "label": "页签1", "string": "投标管理"},
                                    {"type": "page", "title": "Time Management", "label": "Time Management", "string": "Settings"},
                                ],
                            }
                        ],
                    }
                },
                "semantic_page": {"form_semantics": {}},
            }
        }

        service._normalize_form_structure_semantics(contract)

        tabs = (((contract.get("data") or {}).get("views") or {}).get("form") or {}).get("layout")[0].get("tabs")
        self.assertEqual(tabs[0].get("title"), "投标管理")
        self.assertEqual(tabs[0].get("label"), "投标管理")
        self.assertEqual(tabs[1].get("title"), "设置")
        self.assertEqual(tabs[1].get("label"), "设置")

    def test_v2_notebook_tab_titles_prefer_native_string_over_placeholders(self):
        contract = {
            "views": {
                "form": {
                    "layout": [
                        {
                            "type": "notebook",
                            "tabs": [
                                {"type": "page", "title": "页签1", "label": "页签1", "string": "投标管理"},
                                {"type": "page", "title": "Time Management", "label": "Time Management", "string": "Settings"},
                            ],
                        }
                    ],
                }
            },
            "semantic_page": {"form_semantics": {}},
        }

        normalized = UIContractServiceV2._normalize_form_structure_semantics(contract)

        tabs = (((normalized.get("views") or {}).get("form") or {}).get("layout") or [])[0].get("tabs")
        self.assertEqual(tabs[0].get("title"), "投标管理")
        self.assertEqual(tabs[0].get("label"), "投标管理")
        self.assertEqual(tabs[1].get("title"), "设置")
        self.assertEqual(tabs[1].get("label"), "设置")

    def test_project_form_backfill_nodes_keep_field_info(self):
        data = {
            "head": {"model": "project.project", "view_type": "form"},
            "views": {
                "form": {
                    "layout": [
                        {
                            "type": "sheet",
                            "children": [
                                {"type": "field", "name": "name"},
                            ],
                        }
                    ],
                }
            },
            "fields": {
                "name": {"string": "名称", "type": "char", "required": True, "readonly": False},
                "stage_id": {"string": "阶段", "type": "many2one", "required": False, "readonly": False},
                "owner_id": {"string": "业主单位", "type": "many2one", "required": False, "readonly": False},
            },
        }

        governed = apply_contract_governance(data, "user")
        layout = ((governed.get("views") or {}).get("form") or {}).get("layout") or []
        sheet = layout[0]
        backfill_group = next(
            (node for node in (sheet.get("children") or []) if isinstance(node, dict) and node.get("name") == "visible_fields_backfill_group"),
            {},
        )
        children = [node for node in (backfill_group.get("children") or []) if isinstance(node, dict)]
        self.assertTrue(children)
        for node in children:
            field_info = node.get("fieldInfo") if isinstance(node.get("fieldInfo"), dict) else {}
            self.assertEqual(field_info.get("label"), governed["fields"][node["name"]]["string"])
            if governed["fields"][node["name"]]["type"] == "many2one":
                self.assertEqual(field_info.get("widget"), "many2one")

    def test_project_task_form_governance_uses_whitelist_and_labels(self):
        data = {
            "governance_primary_model": "project.task",
            "head": {"model": "project.task", "view_type": "form"},
            "views": {
                "form": {
                    "layout": [
                        {
                            "type": "sheet",
                            "children": [
                                {"type": "field", "name": "name"},
                                {"type": "field", "name": "project_id"},
                                {"type": "field", "name": "stage_id"},
                                {"type": "field", "name": "sc_state"},
                                {"type": "field", "name": "user_ids"},
                                {"type": "field", "name": "date_deadline"},
                                {"type": "field", "name": "priority"},
                                {"type": "field", "name": "description"},
                                {"type": "field", "name": "message_ids"},
                            ],
                        }
                    ],
                }
            },
            "fields": {
                "name": {"type": "char", "string": "Name"},
                "project_id": {"type": "many2one", "string": "Project"},
                "stage_id": {"type": "many2one", "string": "Stage"},
                "sc_state": {"type": "selection", "string": "SC State"},
                "user_ids": {"type": "many2many", "string": "Assignees"},
                "date_deadline": {"type": "date", "string": "Deadline"},
                "priority": {"type": "selection", "string": "Priority"},
                "description": {"type": "text", "string": "Description"},
                "message_ids": {"type": "one2many", "string": "Messages"},
            },
        }

        governed = apply_contract_governance(data, "user")

        self.assertEqual(
            governed.get("visible_fields"),
            ["name", "project_id", "stage_id", "sc_state", "user_ids", "date_deadline", "priority", "description"],
        )
        groups = governed.get("field_groups") or []
        self.assertEqual(groups[0].get("label"), "任务基础信息")
        layout = (((governed.get("views") or {}).get("form") or {}).get("layout") or [])
        first_group = (((layout[0] or {}).get("children") or [])[0] or {})
        first_fields = first_group.get("children") or []
        field_names = [row.get("name") for row in first_fields if isinstance(row, dict)]
        self.assertIn("name", field_names)
        self.assertIn("project_id", field_names)
        self.assertNotIn("message_ids", field_names)

    def test_project_and_task_tree_governance_emits_list_profile(self):
        project_data = {
            "governance_primary_model": "project.project",
            "head": {"model": "project.project", "view_type": "tree"},
            "views": {"tree": {"columns": ["sequence", "name", "message_needaction", "stage_id"]}},
            "fields": {
                "name": {"type": "char", "string": "Name"},
                "user_id": {"type": "many2one", "string": "Manager"},
                "partner_id": {"type": "many2one", "string": "Customer"},
                "stage_id": {"type": "many2one", "string": "Stage"},
                "lifecycle_state": {"type": "selection", "string": "Lifecycle"},
                "date_start": {"type": "date", "string": "Start"},
                "date": {"type": "date", "string": "End"},
                "sequence": {"type": "integer", "string": "Sequence"},
            },
        }
        task_data = {
            "governance_primary_model": "project.task",
            "head": {"model": "project.task", "view_type": "tree"},
            "views": {"tree": {"columns": ["sequence", "name", "stage_id", "message_needaction"]}},
            "fields": {
                "name": {"type": "char", "string": "Name"},
                "project_id": {"type": "many2one", "string": "Project"},
                "user_ids": {"type": "many2many", "string": "Assignees"},
                "stage_id": {"type": "many2one", "string": "Stage"},
                "sc_state": {"type": "selection", "string": "SC State"},
                "date_deadline": {"type": "date", "string": "Deadline"},
                "priority": {"type": "selection", "string": "Priority"},
                "sequence": {"type": "integer", "string": "Sequence"},
            },
        }

        project_governed = apply_contract_governance(project_data, "user")
        task_governed = apply_contract_governance(task_data, "user")

        self.assertEqual(
            ((project_governed.get("list_profile") or {}).get("columns") or []),
            ["name", "user_id", "partner_id", "stage_id", "lifecycle_state", "date_start", "date"],
        )
        self.assertEqual(
            ((task_governed.get("list_profile") or {}).get("columns") or []),
            ["name", "project_id", "user_ids", "stage_id", "sc_state", "date_deadline", "priority"],
        )
        task_semantic_columns = (((task_governed.get("semantic_page") or {}).get("list_semantics") or {}).get("columns") or [])
        self.assertEqual(task_semantic_columns[0].get("label"), "任务名称")
