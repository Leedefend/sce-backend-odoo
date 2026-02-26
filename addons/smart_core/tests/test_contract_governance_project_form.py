# -*- coding: utf-8 -*-
import unittest

from ..utils.contract_governance import apply_contract_governance


def _sample_payload():
    return {
        "head": {"model": "project.project", "view_type": "form"},
        "views": {
            "form": {
                "layout": [
                    {"type": "header"},
                    {"type": "sheet"},
                    {"type": "field", "name": "name"},
                    {"type": "field", "name": "project_type_id"},
                    {"type": "field", "name": "create_uid"},
                    {"type": "field", "name": "message_ids"},
                    {"type": "field", "name": "budget_total"},
                    {"type": "field", "name": "manager_id"},
                    {"type": "field", "name": "phase_key"},
                    {"type": "field", "name": "stage_id"},
                ]
            }
        },
        "fields": {
            "name": {"string": "名称", "type": "char", "required": True, "readonly": False},
            "project_type_id": {"string": "项目类型", "type": "many2one", "required": False, "readonly": False},
            "manager_id": {"string": "项目经理", "type": "many2one", "required": False, "readonly": False},
            "budget_total": {"string": "预算", "type": "monetary", "required": False, "readonly": False},
            "phase_key": {
                "string": "项目阶段",
                "type": "selection",
                "required": False,
                "readonly": False,
                "selection": [["initiation", "立项"], ["archive", "归档"]],
            },
            "stage_id": {"string": "阶段", "type": "many2one", "required": False, "readonly": False},
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


class TestProjectFormGovernance(unittest.TestCase):
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
        self.assertNotIn("create_uid", layout_field_names)
        self.assertNotIn("message_ids", layout_field_names)
        self.assertIn("name", layout_field_names)
        # layout should cover selected field surface, not only original sparse field nodes
        self.assertIn("manager_id", layout_field_names)
        self.assertIn("budget_total", layout_field_names)

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
        for cap in capabilities:
            self.assertIn("group_key", cap)
            self.assertIn("group_label", cap)
            self.assertIn("group_icon", cap)
            self.assertIn("group_sequence", cap)


if __name__ == "__main__":
    unittest.main()
