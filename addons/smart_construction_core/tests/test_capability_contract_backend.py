# -*- coding: utf-8 -*-
from uuid import uuid4

from odoo.tests.common import TransactionCase, tagged

from odoo.addons.smart_construction_core.handlers.capability_visibility_report import (
    CapabilityVisibilityReportHandler,
    _suggested_action_for_reason,
)


@tagged("sc_smoke", "capability_contract_backend")
class TestCapabilityContractBackend(TransactionCase):
    def _key(self, prefix):
        return f"{prefix}_{uuid4().hex[:8]}"

    def test_access_result_normalizes_locked_reason(self):
        Cap = self.env["sc.capability"]
        normalized = Cap._normalize_access_result(
            {"visible": True, "allowed": False, "state": "LOCKED", "reason_code": "", "reason": ""}
        )
        self.assertEqual(normalized.get("reason_code"), "ACCESS_RESTRICTED")
        self.assertTrue(bool(normalized.get("reason")))

    def test_tile_public_dict_contains_scope_and_access_fields(self):
        Cap = self.env["sc.capability"]
        Scene = self.env["sc.scene"]
        Tile = self.env["sc.scene.tile"]

        main = Cap.create(
            {
                "key": self._key("main"),
                "name": "Main Capability",
                "required_flag": self._key("feature"),
                "status": "ga",
            }
        )
        scene = Scene.create({"name": "Backend Contract Scene", "code": self._key("scene")})
        tile = Tile.create({"scene_id": scene.id, "capability_id": main.id, "visible": True})

        payload = tile.to_public_dict(self.env.user)
        self.assertIn("role_scope", payload)
        self.assertIn("capability_scope", payload)
        self.assertIn("allowed", payload)
        self.assertIn("user_visible", payload)
        self.assertEqual(payload.get("state"), "LOCKED")
        self.assertEqual(payload.get("reason_code"), "FEATURE_DISABLED")

    def test_locked_capability_is_visible_but_not_allowed(self):
        Cap = self.env["sc.capability"]
        project_group = self.env.ref("smart_construction_core.group_sc_cap_project_manager")
        hidden = Cap.create(
            {
                "key": self._key("hidden_init"),
                "name": "Hidden Init Capability",
                "required_group_ids": [(6, 0, [project_group.id])],
                "status": "ga",
            }
        )
        locked = Cap.create(
            {
                "key": self._key("main_init"),
                "name": "Init Main Capability",
                "required_flag": self._key("feature_init"),
                "status": "ga",
            }
        )

        self.assertTrue(locked._user_visible(self.env.user))
        self.assertFalse(locked._user_allowed(self.env.user))
        self.assertFalse(hidden._user_visible(self.env.user))

    def test_visibility_report_exposes_locked_samples_and_state_counts(self):
        Cap = self.env["sc.capability"]
        project_group = self.env.ref("smart_construction_core.group_sc_cap_project_manager")
        Cap.create(
            {
                "key": self._key("hidden_group"),
                "name": "Hidden Group Capability",
                "required_group_ids": [(6, 0, [project_group.id])],
                "status": "ga",
            }
        )
        locked = Cap.create(
            {
                "key": self._key("locked_flag"),
                "name": "Locked Flag Capability",
                "required_flag": self._key("feature"),
                "status": "ga",
            }
        )

        handler = CapabilityVisibilityReportHandler(self.env, payload={})
        result = handler.handle()
        self.assertTrue(result.get("ok"))
        data = result.get("data") or {}
        state_rows = data.get("state_counts") or []
        self.assertIsInstance(state_rows, list)
        sample_rows = (data.get("locked_samples") or []) + (data.get("hidden_samples") or [])
        if sample_rows:
            self.assertTrue(any("suggested_action" in row for row in sample_rows))

    def test_suggested_action_mapping(self):
        self.assertEqual(
            _suggested_action_for_reason(reason_code="PERMISSION_DENIED", state="LOCKED"),
            "request_access",
        )
        self.assertEqual(
            _suggested_action_for_reason(reason_code="FEATURE_DISABLED", state="LOCKED"),
            "enable_feature_flag",
        )
        self.assertEqual(
            _suggested_action_for_reason(reason_code="", state="PREVIEW"),
            "wait_release",
        )
