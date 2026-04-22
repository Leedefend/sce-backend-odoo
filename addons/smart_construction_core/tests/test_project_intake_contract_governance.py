# -*- coding: utf-8 -*-
import unittest

from odoo.addons.smart_core.utils.contract_governance import apply_contract_governance
from odoo.addons.smart_construction_core.services import contract_governance_overrides  # noqa: F401


def _payload(scene_key="projects.intake", render_profile="create", menu_xmlid=None):
    return {
        "head": {
            "model": "project.project",
            "view_type": "form",
            "scene_key": scene_key,
            "render_profile": render_profile,
            "menu_xmlid": menu_xmlid,
        },
        "model": "project.project",
        "scene_key": scene_key,
        "render_profile": render_profile,
        "menu_xmlid": menu_xmlid,
        "views": {
            "form": {
                "layout": [
                    {"type": "sheet"},
                    {"type": "field", "name": "name"},
                    {"type": "field", "name": "manager_id"},
                ]
            }
        },
        "fields": {
            "name": {"string": "名称", "type": "char", "required": True, "readonly": False},
            "manager_id": {
                "string": "项目管理员",
                "type": "many2one",
                "required": False,
                "readonly": False,
            },
        },
    }


class ProjectIntakeContractGovernanceCase(unittest.TestCase):
    def test_project_intake_create_contract_receives_scene_governance(self):
        governed = apply_contract_governance(_payload(), "user")

        governance = governed.get("form_governance") or {}
        self.assertEqual(governance.get("surface"), "project_intake")
        self.assertEqual(governance.get("create_flow_mode"), "standard")
        self.assertEqual(governance.get("autosave_scope"), "project_intake_standard")
        self.assertEqual(governance.get("primary_action_label"), "创建项目")
        self.assertEqual(
            governance.get("post_create_target"),
            {
                "intent": "project.dashboard.enter",
                "route": "/s/project.management",
            },
        )

    def test_project_quick_create_contract_receives_quick_governance(self):
        governed = apply_contract_governance(
            _payload(
                scene_key="",
                menu_xmlid="smart_construction_core.menu_sc_project_quick_create",
            ),
            "user",
        )

        governance = governed.get("form_governance") or {}
        self.assertEqual(governance.get("surface"), "project_intake")
        self.assertEqual(governance.get("create_flow_mode"), "quick")
        self.assertEqual(governance.get("autosave_scope"), "project_intake_quick")
        self.assertEqual(governance.get("primary_action_label"), "创建并进入项目驾驶舱")
        self.assertEqual(
            governance.get("post_create_target"),
            {
                "intent": "project.dashboard.enter",
                "route": "/s/project.management",
            },
        )

    def test_non_intake_project_contract_is_not_overridden(self):
        governed = apply_contract_governance(_payload(scene_key="projects.list"), "user")

        governance = governed.get("form_governance") or {}
        self.assertNotEqual(governance.get("surface"), "project_intake")
        self.assertIsNone(governance.get("create_flow_mode"))
        self.assertIsNone(governance.get("post_create_target"))

    def test_non_create_project_contract_is_not_overridden(self):
        governed = apply_contract_governance(_payload(render_profile="edit"), "user")

        governance = governed.get("form_governance") or {}
        self.assertNotEqual(governance.get("surface"), "project_intake")
        self.assertIsNone(governance.get("create_flow_mode"))
        self.assertIsNone(governance.get("post_create_target"))


if __name__ == "__main__":
    unittest.main()
