# -*- coding: utf-8 -*-
import unittest

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
        lifecycle = out.get("lifecycle") or {}
        self.assertIsInstance(lifecycle, dict)
        self.assertIn("state_field", lifecycle)
        self.assertIn("allowed_transitions", lifecycle)
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
