# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged

from ..handlers.load_contract import LoadContractHandler
from ..app_config_engine.services.assemblers.page_assembler import PageAssembler
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
        assembler = PageAssembler.__new__(PageAssembler)
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

        assembler._restrict_form_fields_to_layout(data)

        self.assertEqual(data.get("visible_fields"), ["name", "login", "active"])
        self.assertIn("company_id", data.get("fields") or {})
        self.assertIn("sc_department_id", data.get("fields") or {})
        self.assertIn("login", data.get("fields") or {})

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
