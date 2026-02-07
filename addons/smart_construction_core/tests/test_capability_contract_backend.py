# -*- coding: utf-8 -*-
from uuid import uuid4

from odoo.tests.common import TransactionCase, tagged


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
