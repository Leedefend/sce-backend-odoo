# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install", "sc_approval_policy")
class TestApprovalPolicyToggleBackend(TransactionCase):
    def test_approval_required_toggle_normalizes_mode_and_runtime(self):
        policy = self.env.ref("smart_construction_core.approval_policy_receipt_income").sudo()

        policy.write({"active": True, "approval_required": False, "mode": "none"})
        self.assertFalse(
            self.env["sc.approval.policy"].is_approval_required(policy.target_model, company=policy.company_id)
        )

        policy.write({"approval_required": True})
        self.assertTrue(policy.approval_required)
        self.assertEqual(policy.mode, "single")
        self.assertTrue(
            self.env["sc.approval.policy"].is_approval_required(policy.target_model, company=policy.company_id)
        )

        policy.write({"approval_required": False})
        self.assertFalse(policy.approval_required)
        self.assertEqual(policy.mode, "none")
        self.assertFalse(
            self.env["sc.approval.policy"].is_approval_required(policy.target_model, company=policy.company_id)
        )

    def test_mode_change_keeps_approval_required_consistent(self):
        policy = self.env.ref("smart_construction_core.approval_policy_settlement_adjustment").sudo()

        policy.write({"active": True, "mode": "linear"})
        self.assertTrue(policy.approval_required)

        policy.write({"mode": "none"})
        self.assertFalse(policy.approval_required)
