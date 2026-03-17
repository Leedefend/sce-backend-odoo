# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged

from odoo.addons.smart_core.governance.scene_normalizer import SceneNormalizer


@tagged("post_install", "-at_install", "smart_core", "scene_target")
class TestSceneNormalizerTargetResolution(TransactionCase):
    def test_xmlid_resolution_overrides_stale_numeric_ids(self):
        normalizer = SceneNormalizer()
        scenes = [
            {
                "code": "projects.list",
                "target": {
                    "action_id": 519,
                    "menu_id": 329,
                    "action_xmlid": "smart_construction_core.action_sc_project_list",
                    "menu_xmlid": "smart_construction_core.menu_sc_root",
                },
            }
        ]
        diagnostics = {
            "normalize_warnings": [],
            "resolve_errors": [],
        }

        normalizer.resolve_targets(self.env, scenes, [], diagnostics)

        target = (scenes[0] or {}).get("target") or {}
        expected_action_id = self.env.ref("smart_construction_core.action_sc_project_list").id
        expected_menu_id = self.env.ref("smart_construction_core.menu_sc_root").id
        self.assertEqual(target.get("action_id"), expected_action_id)
        self.assertEqual(target.get("menu_id"), expected_menu_id)
        self.assertNotIn("action_xmlid", target)
        self.assertNotIn("menu_xmlid", target)
        mismatch_codes = {
            str(item.get("code") or "")
            for item in (diagnostics.get("resolve_errors") or [])
            if isinstance(item, dict)
        }
        self.assertIn("TARGET_ID_XMLID_MISMATCH", mismatch_codes)

