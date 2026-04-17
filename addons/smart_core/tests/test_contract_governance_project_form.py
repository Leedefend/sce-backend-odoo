# -*- coding: utf-8 -*-
import ast
import unittest
from pathlib import Path

from ..utils.contract_governance import (
    apply_contract_governance,
    apply_project_form_domain_override,
    register_contract_domain_override,
)


def _sample_payload():
    return {
        "head": {"model": "project.project", "view_type": "form"},
        "views": {
            "form": {
                "layout": [
                    {"type": "header"},
                    {"type": "sheet"},
                    {"type": "field", "name": "name"},
                    {"type": "field", "name": "project_code"},
                    {"type": "field", "name": "code"},
                    {"type": "field", "name": "project_type_id"},
                    {"type": "field", "name": "create_uid"},
                    {"type": "field", "name": "message_ids"},
                    {"type": "field", "name": "budget_total"},
                    {"type": "field", "name": "manager_id"},
                    {"type": "field", "name": "company_id"},
                    {"type": "field", "name": "analytic_account_id"},
                    {"type": "field", "name": "phase_key"},
                    {"type": "field", "name": "stage_id"},
                    {"type": "field", "name": "last_update_status"},
                    {"type": "field", "name": "privacy_visibility"},
                    {"type": "field", "name": "rating_status"},
                    {"type": "field", "name": "rating_status_period"},
                ]
            }
        },
        "fields": {
            "name": {"string": "名称", "type": "char", "required": True, "readonly": False},
            "project_code": {"string": "项目编号", "type": "char", "required": False, "readonly": True},
            "code": {"string": "项目编号(别名)", "type": "char", "required": False, "readonly": True},
            "project_type_id": {"string": "项目类型", "type": "many2one", "required": False, "readonly": False},
            "manager_id": {"string": "项目经理", "type": "many2one", "required": False, "readonly": False},
            "owner_id": {"string": "项目负责人", "type": "many2one", "required": False, "readonly": False},
            "company_id": {"string": "公司", "type": "many2one", "required": False, "readonly": False},
            "analytic_account_id": {"string": "分析账户", "type": "many2one", "required": False, "readonly": False},
            "budget_total": {"string": "预算", "type": "monetary", "required": False, "readonly": False},
            "phase_key": {
                "string": "项目阶段",
                "type": "selection",
                "required": False,
                "readonly": False,
                "selection": [["initiation", "立项"], ["archive", "归档"]],
            },
            "stage_id": {"string": "阶段", "type": "many2one", "required": False, "readonly": False},
            "last_update_status": {"string": "最后更新状态", "type": "selection", "required": True, "readonly": False},
            "privacy_visibility": {"string": "可见性", "type": "selection", "required": True, "readonly": False},
            "rating_status": {"string": "客户评价状态", "type": "selection", "required": True, "readonly": False},
            "rating_status_period": {"string": "点评频率", "type": "selection", "required": True, "readonly": False},
            "create_uid": {"string": "创建人", "type": "many2one", "required": False, "readonly": True},
            "message_ids": {"string": "消息", "type": "one2many", "required": False, "readonly": False},
        },
        "permissions": {
            "field_groups": {
                "name": {"groups_xmlids": []},
                "project_type_id": {"groups_xmlids": []},
                "budget_total": {"groups_xmlids": []},
                "create_uid": {"groups_xmlids": []},
                "message_ids": {"groups_xmlids": []},
            }
        },
        "toolbar": {
            "header": [
                {"key": "smart_construction_core.action_project_initiation", "label": "项目立项", "kind": "open"},
                {"key": "project.ir_cron_rating_project_ir_actions_server", "label": "项目：发送评级", "kind": "server"},
            ]
        },
        "buttons": [
            {"key": "obj_action_sc_submit_提交立项", "label": "提交立项", "kind": "object", "level": "header"},
            {"key": "obj_action_view_tasks_查看任务", "label": "查看任务", "kind": "object", "level": "header"},
            {
                "key": "obj_action_sc_approve_审批",
                "label": "审批通过",
                "kind": "object",
                "level": "header",
                "groups_xmlids": ["smart_construction_core.group_sc_finance_approver"],
                "required_roles": ["finance_manager"],
            },
            {"key": "act_298_设置阶段的评分邮件模版", "label": "设置阶段的评分邮件模版", "kind": "open", "level": "header"},
            {"key": "obj_action_view_tasks_任务", "label": "任务", "kind": "object", "level": "smart"},
            {"key": "project.ir_cron_rating_project_ir_actions_server", "label": "项目：发送评级", "kind": "server", "level": "toolbar"},
        ],
        "capabilities": [
            {
                "key": "project.read",
                "name": "项目读取",
                "status": "active",
                "reason_code": "",
            },
            {
                "key": "finance.approval",
                "name": "财务审批",
                "status": "beta",
            },
            {
                "key": "contract.edit",
                "name": "合同编辑",
                "status": "ga",
                "tags": ["readonly"],
            },
        ],
        "scenes": [
            {
                "code": "projects.ledger",
                "name": "项目台账",
                "is_default": True,
                "access": {
                    "allowed": True,
                    "required_capabilities": ["project.read"],
                },
                "tiles": [
                    {"key": "project.overview", "title": "项目概览"},
                    {"key": "project.workflow", "title": "进入下一阶段"},
                ],
                "list_profile": {
                    "columns": ["name", "stage_id", "end_date"],
                    "hidden_columns": ["message_needaction"],
                    "row_primary": "name",
                    "row_secondary": "stage_id",
                },
            }
        ],
    }


def _sample_list_payload():
    return {
        "head": {"model": "project.project", "view_type": "tree"},
        "search": {
            "filters": [
                {"key": "activities_today", "label": "今日活动"},
                {"key": "296", "label": "296"},
                {"key": "demo_filter", "label": "项目（演示）"},
                {"key": "in_progress", "label": "进行中"},
                {"key": "manager", "label": "项目管理员"},
                {"key": "recent", "label": "最近活动"},
                {"key": "archived", "label": "已存档"},
                {"key": "tags", "label": "标签"},
                {"key": "status", "label": "状态"},
                {"key": "date_end", "label": "结束日期"},
            ]
        },
        "buttons": [
            {"key": "open_tasks", "label": "查看任务", "kind": "open"},
            {"key": "project_update_all_action", "label": "project_update_all_action", "kind": "object"},
            {"key": "296", "label": "296", "kind": "open"},
        ],
        "toolbar": {
            "header": [
                {"key": "smart_construction_demo.action_sc_project_list_showcase", "label": "项目列表（演示）", "kind": "open"},
                {"key": "smart_construction_core.action_sc_project_list", "label": "项目列表", "kind": "open"},
            ]
        },
    }


def _sample_kanban_payload():
    return {
        "head": {"model": "project.project", "view_type": "kanban"},
        "views": {
            "kanban": {
                "fields": ["name", "manager_id", "stage_id", "end_date", "budget_total", "message_ids"],
                "template_qweb": None,
            }
        },
        "fields": {
            "name": {"string": "名称", "type": "char", "required": True, "readonly": False},
            "project_code": {"string": "项目编号", "type": "char", "required": False, "readonly": False},
            "manager_id": {"string": "项目经理", "type": "many2one", "required": False, "readonly": False},
            "stage_id": {"string": "阶段", "type": "many2one", "required": False, "readonly": False},
            "lifecycle_state": {"string": "生命周期", "type": "selection", "required": False, "readonly": False},
            "end_date": {"string": "截止日期", "type": "date", "required": False, "readonly": False},
            "budget_total": {"string": "预算", "type": "monetary", "required": False, "readonly": False},
            "message_ids": {"string": "消息", "type": "one2many", "required": False, "readonly": False},
        },
    }


def _sample_company_form_payload():
    return {
        "head": {"model": "res.company", "view_type": "tree,form"},
        "render_profile": "create",
        "views": {
            "form": {
                "layout": [
                    {"type": "sheet", "children": [
                        {"type": "field", "name": "name", "fieldInfo": {"label": "Company Name"}},
                        {"type": "field", "name": "sc_short_name", "fieldInfo": {"label": "Short Name"}},
                        {"type": "field", "name": "sc_credit_code", "fieldInfo": {"label": "Credit Code"}},
                        {"type": "field", "name": "sc_contact_phone", "fieldInfo": {"label": "Phone"}},
                        {"type": "field", "name": "sc_address", "fieldInfo": {"label": "Address"}},
                        {"type": "field", "name": "sc_is_active", "fieldInfo": {"label": "Active"}},
                        {"type": "field", "name": "currency_id", "fieldInfo": {"label": "Currency"}},
                    ]},
                ]
            }
        },
        "fields": {
            "name": {"string": "公司名称", "type": "char", "required": True, "readonly": False},
            "sc_short_name": {"string": "公司简称", "type": "char", "required": False, "readonly": False},
            "sc_credit_code": {"string": "统一社会信用代码", "type": "char", "required": False, "readonly": False},
            "sc_contact_phone": {"string": "联系电话", "type": "char", "required": False, "readonly": False},
            "sc_address": {"string": "地址", "type": "char", "required": False, "readonly": False},
            "sc_is_active": {"string": "启用", "type": "boolean", "required": False, "readonly": False},
            "currency_id": {"string": "货币", "type": "many2one", "required": False, "readonly": False},
        },
        "toolbar": {
            "header": [
                {"key": "open_companies", "label": "Companies", "kind": "open"},
            ]
        },
        "buttons": [
            {"key": "apply_defaults", "label": "Apply", "kind": "object", "level": "header"},
            {"key": "inalterability", "label": "Data Inalterability Check", "kind": "object", "level": "header"},
        ],
    }


def _sample_nested_project_form_payload():
    payload = _sample_payload()
    payload["views"]["form"]["layout"] = [
        {"type": "header"},
        {
            "type": "sheet",
            "name": "project_sheet",
            "children": [
                {
                    "type": "group",
                    "name": "project_head",
                    "children": [
                        {"type": "field", "name": "name"},
                        {"type": "field", "name": "project_type_id"},
                    ],
                },
                {
                    "type": "notebook",
                    "name": "project_notebook",
                    "children": [
                        {
                            "type": "page",
                            "name": "description",
                            "string": "描述",
                            "children": [
                                {
                                    "type": "group",
                                    "name": "description_group",
                                    "children": [
                                        {"type": "field", "name": "privacy_visibility"},
                                        {"type": "field", "name": "rating_status"},
                                    ],
                                }
                            ],
                        },
                        {
                            "type": "page",
                            "name": "settings",
                            "string": "设置",
                            "children": [
                                {
                                    "type": "group",
                                    "name": "settings_group",
                                    "children": [
                                        {"type": "field", "name": "manager_id"},
                                        {"type": "field", "name": "company_id"},
                                        {"type": "field", "name": "analytic_account_id"},
                                    ],
                                }
                            ],
                        },
                    ],
                },
            ],
        },
    ]
    return payload


def _collect_layout_field_names(nodes):
    ordered = []

    def walk(node):
        if isinstance(node, list):
            for item in node:
                walk(item)
            return
        if not isinstance(node, dict):
            return
        if node.get("type") == "field":
            name = node.get("name")
            if name and name not in ordered:
                ordered.append(name)
        for key in ("children", "tabs", "pages", "nodes", "items"):
            nested = node.get(key)
            if isinstance(nested, list):
                walk(nested)

    walk(nodes)
    return ordered


class TestProjectFormGovernance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        register_contract_domain_override(
            "smart_core.tests.project_form",
            apply_project_form_domain_override,
            priority=5,
        )

    def test_user_mode_filters_technical_fields_and_noisy_actions(self):
        data = _sample_payload()
        out = apply_contract_governance(data, "user")

        fields = out.get("fields") or {}
        self.assertIn("name", fields)
        self.assertIn("project_type_id", fields)
        self.assertIn("manager_id", fields)
        self.assertNotIn("create_uid", fields)
        self.assertNotIn("message_ids", fields)

        layout = ((out.get("views") or {}).get("form") or {}).get("layout") or []
        layout_field_names = [item.get("name") for item in layout if isinstance(item, dict) and item.get("type") == "field"]
        self.assertGreaterEqual(len(layout_field_names), 1)
        self.assertEqual(layout_field_names[0], "name")
        self.assertNotIn("create_uid", layout_field_names)
        self.assertNotIn("message_ids", layout_field_names)
        visible_fields = out.get("visible_fields") or []
        self.assertIsInstance(visible_fields, list)
        self.assertIn("name", visible_fields)
        self.assertIn("manager_id", visible_fields)
        self.assertIn("budget_total", visible_fields)
        self.assertNotIn("create_uid", visible_fields)

    def test_user_mode_preserves_native_project_form_layout_hierarchy(self):
        data = _sample_nested_project_form_payload()
        out = apply_contract_governance(data, "user")

        layout = ((out.get("views") or {}).get("form") or {}).get("layout") or []
        self.assertEqual(layout[0].get("type"), "header")
        self.assertEqual(layout[1].get("type"), "sheet")

        sheet_children = layout[1].get("children") or []
        notebook = next((node for node in sheet_children if isinstance(node, dict) and node.get("type") == "notebook"), {})
        self.assertEqual(notebook.get("name"), "project_notebook")

        pages = notebook.get("children") or []
        page_names = [node.get("name") for node in pages if isinstance(node, dict)]
        self.assertEqual(page_names, ["description", "settings"])

        description_page = next((node for node in pages if isinstance(node, dict) and node.get("name") == "description"), {})
        settings_page = next((node for node in pages if isinstance(node, dict) and node.get("name") == "settings"), {})
        description_group = (description_page.get("children") or [])[0]
        settings_group = (settings_page.get("children") or [])[0]

        description_fields = [node.get("name") for node in (description_group.get("children") or []) if isinstance(node, dict)]
        settings_fields = [node.get("name") for node in (settings_group.get("children") or []) if isinstance(node, dict)]

        self.assertEqual(description_fields, ["privacy_visibility", "rating_status"])
        self.assertEqual(settings_fields, ["manager_id", "company_id", "analytic_account_id"])

    def test_user_mode_backfills_visible_fields_into_layout(self):
        data = _sample_payload()
        # Simulate a native parser layout that kept the visible allow-list but
        # omitted a subset of business fields from the structural tree.
        data["views"]["form"]["layout"] = [
            {"type": "header"},
            {"type": "sheet"},
            {"type": "field", "name": "name"},
            {"type": "field", "name": "project_type_id"},
            {"type": "field", "name": "manager_id"},
            {"type": "field", "name": "company_id"},
            {"type": "field", "name": "analytic_account_id"},
            {"type": "field", "name": "phase_key"},
            {"type": "field", "name": "last_update_status"},
            {"type": "field", "name": "privacy_visibility"},
            {"type": "field", "name": "rating_status"},
            {"type": "field", "name": "rating_status_period"},
        ]
        out = apply_contract_governance(data, "user")

        visible_fields = out.get("visible_fields") or []
        layout = ((out.get("views") or {}).get("form") or {}).get("layout") or []
        layout_field_names = _collect_layout_field_names(layout)

        self.assertIn("owner_id", visible_fields)
        self.assertIn("budget_total", visible_fields)
        self.assertIn("stage_id", visible_fields)
        self.assertIn("owner_id", layout_field_names)
        self.assertIn("budget_total", layout_field_names)
        self.assertIn("stage_id", layout_field_names)
        self.assertEqual(layout[1].get("type"), "sheet")
        sheet_children = layout[1].get("children") or []
        backfill_group = next(
            (node for node in sheet_children if isinstance(node, dict) and node.get("name") == "visible_fields_backfill_group"),
            {},
        )
        self.assertEqual(backfill_group.get("string"), "补充业务信息")
        backfill_children = [node for node in (backfill_group.get("children") or []) if isinstance(node, dict)]
        backfill_fields = [node.get("name") for node in backfill_children]
        self.assertEqual(set(backfill_fields), {"owner_id", "budget_total", "stage_id"})
        for node in backfill_children:
            field_info = node.get("fieldInfo") if isinstance(node.get("fieldInfo"), dict) else {}
            self.assertEqual(field_info.get("label"), out["fields"][node.get("name")]["string"])
            if out["fields"][node.get("name")]["type"] == "many2one":
                self.assertEqual(field_info.get("widget"), "many2one")

    def test_generic_semantic_governance_no_longer_backfills_layout(self):
        source_path = Path(__file__).resolve().parents[1] / "utils" / "contract_governance.py"
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        calls = []

        class Finder(ast.NodeVisitor):
            def visit_FunctionDef(self, node):
                if node.name != "_apply_form_render_semantics":
                    return
                self.generic_visit(node)

            def visit_Call(self, node):
                func = node.func
                if isinstance(func, ast.Name) and func.id == "_backfill_form_layout_from_visible_fields":
                    calls.append(node.lineno)
                self.generic_visit(node)

        Finder().visit(tree)

        self.assertEqual(calls, [])

    def test_user_mode_governs_enterprise_company_create_form(self):
        data = _sample_company_form_payload()
        out = apply_contract_governance(data, "user")

        self.assertEqual(out.get("visible_fields"), [
            "name",
            "sc_short_name",
            "sc_credit_code",
            "sc_contact_phone",
            "sc_address",
            "sc_is_active",
        ])

        layout = ((out.get("views") or {}).get("form") or {}).get("layout") or []
        self.assertEqual(len(layout), 1)
        sheet = layout[0]
        self.assertEqual(sheet.get("type"), "sheet")
        group = (sheet.get("children") or [])[0]
        self.assertEqual(group.get("string"), "企业基础信息")
        field_nodes = group.get("children") or []
        self.assertEqual([node.get("name") for node in field_nodes], [
            "name",
            "sc_short_name",
            "sc_credit_code",
            "sc_contact_phone",
            "sc_address",
            "sc_is_active",
        ])
        self.assertEqual(field_nodes[0].get("string"), "公司名称")
        self.assertEqual(field_nodes[1].get("string"), "公司简称")

        self.assertEqual((out.get("toolbar") or {}).get("header"), [])
        self.assertEqual(out.get("buttons"), [])
        self.assertNotIn("message_ids", visible_fields)
        form_profile = out.get("form_profile") or {}
        self.assertIsInstance(form_profile, dict)
        self.assertIsInstance(form_profile.get("core_fields"), list)
        self.assertIsInstance(form_profile.get("advanced_fields"), list)
        self.assertIn("name", form_profile.get("core_fields") or [])
        view_form_profile = (((out.get("views") or {}).get("form") or {}).get("form_profile")) or {}
        self.assertEqual(view_form_profile.get("core_fields"), form_profile.get("core_fields"))

        toolbar_header = ((out.get("toolbar") or {}).get("header") or [])
        self.assertEqual(toolbar_header, [])

        buttons = out.get("buttons") or []
        self.assertTrue(all(str(btn.get("kind", "")).lower() != "server" for btn in buttons if isinstance(btn, dict)))
        self.assertTrue(all("评分" not in str(btn.get("label", "")) for btn in buttons if isinstance(btn, dict)))
        action_groups = out.get("action_groups") or []
        self.assertIsInstance(action_groups, list)
        if action_groups:
            first_group = action_groups[0]
            self.assertIn("key", first_group)
            self.assertIn("label", first_group)
            self.assertIn("actions", first_group)
            self.assertLessEqual(len(first_group.get("actions") or []), 5)
        scene_actions = ((out.get("semantic_page") or {}).get("actions")) or {}
        self.assertEqual(scene_actions.get("owner_layer"), "scene_orchestration")
        self.assertIsInstance(scene_actions.get("header_actions"), list)
        self.assertIsInstance(scene_actions.get("record_actions"), list)
        self.assertEqual(
            [row.get("key") for row in scene_actions.get("header_actions") or []],
            [row.get("key") for row in buttons if isinstance(row, dict) and row.get("level") == "header"],
        )
        self.assertEqual(
            [row.get("key") for row in scene_actions.get("record_actions") or []],
            [row.get("key") for row in buttons if isinstance(row, dict) and row.get("level") in {"smart", "row"}],
        )
        scene_contract = out.get("scene_contract_v1") or {}
        self.assertEqual(scene_contract.get("contract_version"), "v1")
        self.assertEqual(scene_contract.get("owner_layer"), "scene_orchestration")
        self.assertEqual(
            ((scene_contract.get("semantic_page") or {}).get("actions") or {}).get("owner_layer"),
            "scene_orchestration",
        )
        self.assertTrue(((scene_contract.get("actions") or {}).get("primary_actions") or []))
        lifecycle = out.get("lifecycle") or {}
        self.assertIsInstance(lifecycle, dict)
        self.assertIn("state_field", lifecycle)
        self.assertIn("allowed_transitions", lifecycle)
        workflow_surface = out.get("workflow_surface") or {}
        self.assertEqual(workflow_surface.get("owner_layer"), "business_fact")
        self.assertEqual(workflow_surface.get("state_field"), lifecycle.get("state_field"))
        self.assertIsInstance(workflow_surface.get("states"), list)
        self.assertIsInstance(workflow_surface.get("transitions"), list)
        filters = ((out.get("search") or {}).get("filters")) or []
        self.assertLessEqual(len(filters), 8)
        self.assertEqual(out.get("render_profile"), "create")
        self.assertTrue(out.get("hide_filters_on_create"))
        field_groups = out.get("field_groups") or []
        self.assertIsInstance(field_groups, list)
        self.assertGreaterEqual(len(field_groups), 2)
        core_group = next((grp for grp in field_groups if isinstance(grp, dict) and grp.get("name") == "core"), {})
        self.assertLessEqual(len(core_group.get("fields") or []), 8)
        self.assertFalse(bool(core_group.get("collapsible")))
        advanced_group = next((grp for grp in field_groups if isinstance(grp, dict) and grp.get("name") == "advanced"), {})
        self.assertTrue(bool(advanced_group.get("collapsible")))
        self.assertTrue(bool(advanced_group.get("collapsed_by_default")))
        primary_count = sum(1 for btn in buttons if isinstance(btn, dict) and btn.get("semantic") == "primary_action")
        self.assertLessEqual(primary_count, 1)
        for btn in buttons:
            if not isinstance(btn, dict):
                continue
            self.assertIn(btn.get("semantic"), {"primary_action", "secondary", "danger"})
            self.assertIsInstance(btn.get("visible_profiles"), list)
        field_policies = out.get("field_policies") or {}
        self.assertIsInstance(field_policies, dict)
        self.assertIn("name", field_policies)
        self.assertIsInstance((field_policies.get("name") or {}).get("visible_profiles"), list)
        self.assertIsInstance((field_policies.get("name") or {}).get("required_profiles"), list)
        for business_on_create in ("project_type_id", "manager_id", "budget_total"):
            policy = field_policies.get(business_on_create) or {}
            self.assertIn("create", policy.get("visible_profiles") or [])
        for hidden_on_create in (
            "project_code",
            "code",
            "company_id",
            "analytic_account_id",
            "stage_id",
            "last_update_status",
            "privacy_visibility",
            "rating_status",
            "rating_status_period",
        ):
            policy = field_policies.get(hidden_on_create) or {}
            self.assertNotIn("create", policy.get("visible_profiles") or [])
            self.assertEqual(policy.get("required_profiles") or [], [])
        action_policies = out.get("action_policies") or {}
        self.assertIsInstance(action_policies, dict)
        self.assertGreaterEqual(len(action_policies), 1)
        submit_policy = action_policies.get("obj_action_sc_submit_提交立项") or {}
        enabled_when = submit_policy.get("enabled_when") if isinstance(submit_policy, dict) else {}
        self.assertIsInstance(enabled_when, dict)
        self.assertIn("conditions", enabled_when)
        self.assertIsInstance(enabled_when.get("condition_expr"), dict)
        approve_policy = action_policies.get("obj_action_sc_approve_审批") or {}
        approve_enabled = approve_policy.get("enabled_when") if isinstance(approve_policy, dict) else {}
        self.assertIsInstance(approve_enabled, dict)
        self.assertIsInstance(approve_enabled.get("required_groups"), list)
        self.assertIsInstance(approve_enabled.get("required_roles"), list)
        validation_rules = out.get("validation_rules") or []
        self.assertIsInstance(validation_rules, list)
        self.assertTrue(any((rule or {}).get("code") == "REQUIRED" for rule in validation_rules if isinstance(rule, dict)))
        required_rules = [rule for rule in validation_rules if isinstance(rule, dict) and rule.get("code") == "REQUIRED"]
        required_fields = [str(rule.get("field")) for rule in required_rules]
        self.assertEqual(required_fields, ["name"])
        sql_rule = next((rule for rule in validation_rules if isinstance(rule, dict) and rule.get("code") == "SQL_CHECK"), {})
        self.assertNotIn("expr", sql_rule)
        capabilities = out.get("capabilities") or []
        self.assertEqual(len(capabilities), 3)
        for cap in capabilities:
            self.assertIn("group_key", cap)
            self.assertIn("group_label", cap)
            self.assertIn("group_icon", cap)
            self.assertIn("capability_state", cap)
            self.assertIn("capability_state_reason", cap)
            self.assertIn(cap.get("status"), {"ga", "beta", "alpha"})
            self.assertIn(cap.get("state"), {"READY", "LOCKED", "PREVIEW"})
            self.assertIn(cap.get("capability_state"), {"allow", "readonly", "deny", "pending", "coming_soon"})
        cap_index = {cap.get("key"): cap for cap in capabilities}
        self.assertEqual((cap_index.get("project.read") or {}).get("capability_state"), "allow")
        self.assertEqual((cap_index.get("finance.approval") or {}).get("capability_state"), "pending")
        self.assertEqual((cap_index.get("contract.edit") or {}).get("capability_state"), "readonly")

    def test_project_form_governance_applies_when_view_type_contains_form(self):
        data = _sample_payload()
        data["head"]["view_type"] = "tree,form"
        data["id"] = "new"
        out = apply_contract_governance(data, "user")

        self.assertEqual(out.get("render_profile"), "create")
        fields = out.get("fields") or {}
        self.assertNotIn("project_code", fields)
        self.assertNotIn("code", fields)

        field_policies = out.get("field_policies") or {}
        for hidden_on_create in ("project_code", "code"):
            policy = field_policies.get(hidden_on_create) or {}
            self.assertNotIn("create", policy.get("visible_profiles") or [])

    def test_hud_mode_keeps_full_payload(self):
        data = _sample_payload()
        out = apply_contract_governance(data, "hud")

        fields = out.get("fields") or {}
        self.assertIn("create_uid", fields)
        self.assertIn("message_ids", fields)
        self.assertEqual(out.get("render_profile"), "create")
        self.assertTrue(out.get("hide_filters_on_create"))
        self.assertIsInstance(out.get("field_policies"), dict)
        self.assertIsInstance(out.get("action_policies"), dict)
        self.assertIsInstance(out.get("validation_rules"), list)
        toolbar_header = ((out.get("toolbar") or {}).get("header") or [])
        self.assertGreaterEqual(len(toolbar_header), 1)
        scenes = out.get("scenes") or []
        self.assertIsInstance(scenes, list)
        if scenes:
            first_scene = scenes[0]
            self.assertIn("scene_meta", first_scene)
            self.assertIn("list_profile", first_scene)
            scene_meta = first_scene.get("scene_meta") or {}
            self.assertIn("purpose", scene_meta)
            self.assertIn("core_action", scene_meta)
            self.assertIn("priority_actions", scene_meta)
            self.assertIn("role_relevance_score", scene_meta)
            list_profile = first_scene.get("list_profile") or {}
            self.assertIn("primary_field", list_profile)
            self.assertIn("status_field", list_profile)
            self.assertIn("urgency_score", list_profile)
            self.assertIn("highlight_rule", list_profile)
        capabilities = out.get("capabilities") or []
        self.assertEqual(len(capabilities), 3)
        sql_rules = [rule for rule in (out.get("validation_rules") or []) if isinstance(rule, dict) and rule.get("code") == "SQL_CHECK"]
        if sql_rules:
            self.assertIn("expr", sql_rules[0])
        if capabilities:
            ordered_keys = list(capabilities[0].keys())
            self.assertGreaterEqual(len(ordered_keys), 5)
            self.assertEqual(ordered_keys[0], "key")
            self.assertEqual(ordered_keys[1], "name")
        for cap in capabilities:
            self.assertIn("group_key", cap)
            self.assertIn("group_label", cap)
            self.assertIn("group_icon", cap)
            self.assertIn("group_sequence", cap)

    def test_user_mode_list_surface_filters_noisy_contract_items(self):
        data = _sample_list_payload()
        out = apply_contract_governance(data, "user")

        filters = ((out.get("search") or {}).get("filters")) or []
        self.assertLessEqual(len(filters), 8)
        filter_keys = [str(item.get("key")) for item in filters if isinstance(item, dict)]
        self.assertNotIn("296", filter_keys)
        self.assertNotIn("demo_filter", filter_keys)

        buttons = out.get("buttons") or []
        button_keys = [str(item.get("key")) for item in buttons if isinstance(item, dict)]
        self.assertIn("open_tasks", button_keys)
        self.assertNotIn("296", button_keys)
        self.assertNotIn("project_update_all_action", button_keys)

        toolbar_header = ((out.get("toolbar") or {}).get("header")) or []
        toolbar_keys = [str(item.get("key")) for item in toolbar_header if isinstance(item, dict)]
        self.assertNotIn("smart_construction_demo.action_sc_project_list_showcase", toolbar_keys)
        self.assertIn("smart_construction_core.action_sc_project_list", toolbar_keys)
        groups = out.get("action_groups") or []
        self.assertIsInstance(groups, list)
        if groups:
            self.assertIn("key", groups[0])
            self.assertIn("actions", groups[0])
        surface_policies = out.get("surface_policies") or {}
        self.assertIsInstance(surface_policies, dict)
        self.assertGreaterEqual(int(surface_policies.get("filters_primary_max", 0)), 0)
        self.assertGreaterEqual(int(surface_policies.get("actions_primary_max", 0)), 0)
        self.assertLessEqual(int(surface_policies.get("filters_primary_max", 99)), 4)
        self.assertLessEqual(int(surface_policies.get("actions_primary_max", 99)), 3)
        list_profile = out.get("list_profile") or {}
        list_semantics = ((out.get("semantic_page") or {}).get("list_semantics")) or {}
        self.assertEqual(list_semantics.get("owner_layer"), "scene_orchestration")
        self.assertEqual(
            [row.get("name") for row in list_semantics.get("columns") or []],
            list_profile.get("columns") or [],
        )
        self.assertEqual(list_semantics.get("row_primary"), list_profile.get("row_primary"))
        self.assertEqual(list_semantics.get("status_field"), list_profile.get("status_field"))
        scene_contract = out.get("scene_contract_v1") or {}
        self.assertEqual(scene_contract.get("contract_version"), "v1")
        scene_list_semantics = ((scene_contract.get("semantic_page") or {}).get("list_semantics")) or {}
        self.assertEqual(scene_list_semantics.get("owner_layer"), "scene_orchestration")
        self.assertEqual(
            [row.get("name") for row in scene_list_semantics.get("columns") or []],
            list_profile.get("columns") or [],
        )
        self.assertTrue((scene_contract.get("search_surface") or {}).get("filters"))
        self.assertTrue((scene_contract.get("actions") or {}).get("primary_actions"))

    def test_project_kanban_adds_profile_and_filters_fields(self):
        data = _sample_kanban_payload()
        out = apply_contract_governance(data, "user")

        profile = out.get("kanban_profile") or {}
        self.assertIsInstance(profile, dict)
        self.assertIsInstance(profile.get("primary_fields"), list)
        self.assertIsInstance(profile.get("secondary_fields"), list)
        self.assertIsInstance(profile.get("status_fields"), list)
        self.assertTrue(profile.get("title_field"))

        kanban_view = ((out.get("views") or {}).get("kanban")) or {}
        self.assertEqual((kanban_view.get("kanban_profile") or {}).get("title_field"), profile.get("title_field"))
        fields = kanban_view.get("fields") or []
        self.assertIsInstance(fields, list)
        self.assertIn("name", fields)
        self.assertNotIn("message_ids", fields)

    def test_action_open_form_surface_is_not_overwritten_by_multi_view_head(self):
        data = _sample_payload()
        data["head"]["view_type"] = "kanban,tree,form"
        data["view_type"] = "form"
        data["render_profile"] = "edit"
        data["res_id"] = 2
        data["views"]["kanban"] = _sample_kanban_payload()["views"]["kanban"]

        out = apply_contract_governance(data, "user")

        visible_fields = out.get("visible_fields") or []
        self.assertNotIn("kanban_profile", out)
        self.assertIn("project_type_id", visible_fields)
        self.assertIn("owner_id", visible_fields)
        self.assertIn("company_id", visible_fields)
        self.assertGreater(len(visible_fields), 7)

    def test_ui_contract_handler_does_not_apply_governance_after_service_shape(self):
        source_path = Path(__file__).resolve().parents[1] / "handlers" / "ui_contract.py"
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        calls = []

        class Finder(ast.NodeVisitor):
            def visit_FunctionDef(self, node):
                if node.name == "handle":
                    self.generic_visit(node)

            def visit_Call(self, node):
                func = node.func
                if isinstance(func, ast.Name) and func.id == "apply_contract_governance":
                    calls.append(node.lineno)
                self.generic_visit(node)

        Finder().visit(tree)

        self.assertEqual(calls, [])

    def test_governance_preserves_native_notebook_tab_labels(self):
        data = _sample_payload()
        data["head"]["view_type"] = "kanban,tree,form"
        data["view_type"] = "form"
        data["render_profile"] = "edit"
        data["res_id"] = 2
        data["views"]["form"]["layout"] = [
            {
                "type": "notebook",
                "tabs": [
                    {"type": "page", "title": "页签1", "label": "页签1", "string": "投标管理"},
                    {"type": "page", "title": "Time Management", "label": "Time Management", "string": "Settings"},
                ],
            }
        ]

        out = apply_contract_governance(data, "user")
        tabs = ((((out.get("views") or {}).get("form") or {}).get("layout") or [])[0] or {}).get("tabs") or []

        self.assertEqual(tabs[0].get("title"), "投标管理")
        self.assertEqual(tabs[0].get("label"), "投标管理")
        self.assertEqual(tabs[1].get("title"), "设置")
        self.assertEqual(tabs[1].get("label"), "设置")

    def test_user_mode_realigns_access_policy_after_field_governance(self):
        data = _sample_payload()
        data["access_policy"] = {
            "mode": "block",
            "reason_code": "RELATION_READ_FORBIDDEN_CORE",
            "message": "core field access blocked: alias_model_id",
            "policy_source": "core_fields",
            "blocked_fields": [
                {"field": "alias_model_id", "model": "ir.model", "reason_code": "RELATION_READ_FORBIDDEN"},
            ],
            "degraded_fields": [
                {"field": "message_ids", "model": "mail.message", "reason_code": "RELATION_READ_FORBIDDEN"},
            ],
        }
        data["warnings"] = ["access_policy:block:RELATION_READ_FORBIDDEN_CORE", "other_warning"]

        out = apply_contract_governance(data, "user")
        policy = out.get("access_policy") or {}
        self.assertEqual(policy.get("mode"), "allow")
        self.assertEqual(policy.get("reason_code"), "")
        self.assertEqual(policy.get("blocked_fields"), [])
        self.assertEqual(policy.get("degraded_fields"), [])

        warnings = out.get("warnings") or []
        self.assertNotIn("access_policy:block:RELATION_READ_FORBIDDEN_CORE", warnings)
        self.assertEqual(warnings, ["other_warning"])


if __name__ == "__main__":
    unittest.main()
