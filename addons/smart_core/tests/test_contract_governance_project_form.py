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
                ]
            }
        },
        "fields": {
            "name": {"string": "名称", "type": "char", "required": True, "readonly": False},
            "project_type_id": {"string": "项目类型", "type": "many2one", "required": False, "readonly": False},
            "manager_id": {"string": "项目经理", "type": "many2one", "required": False, "readonly": False},
            "budget_total": {"string": "预算", "type": "monetary", "required": False, "readonly": False},
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
            {"key": "act_298_设置阶段的评分邮件模版", "label": "设置阶段的评分邮件模版", "kind": "open", "level": "header"},
            {"key": "obj_action_view_tasks_任务", "label": "任务", "kind": "object", "level": "smart"},
            {"key": "project.ir_cron_rating_project_ir_actions_server", "label": "项目：发送评级", "kind": "server", "level": "toolbar"},
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

        toolbar_header = ((out.get("toolbar") or {}).get("header") or [])
        self.assertEqual(toolbar_header, [])

        buttons = out.get("buttons") or []
        self.assertTrue(all(str(btn.get("kind", "")).lower() != "server" for btn in buttons if isinstance(btn, dict)))
        self.assertTrue(all("评分" not in str(btn.get("label", "")) for btn in buttons if isinstance(btn, dict)))

    def test_hud_mode_keeps_full_payload(self):
        data = _sample_payload()
        out = apply_contract_governance(data, "hud")

        fields = out.get("fields") or {}
        self.assertIn("create_uid", fields)
        self.assertIn("message_ids", fields)
        toolbar_header = ((out.get("toolbar") or {}).get("header") or [])
        self.assertGreaterEqual(len(toolbar_header), 1)


if __name__ == "__main__":
    unittest.main()
