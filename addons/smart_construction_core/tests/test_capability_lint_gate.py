# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged


@tagged("sc_smoke")
class TestCapabilityLintGate(TransactionCase):
    def test_capability_lint_passes(self):
        issues = self.env["sc.capability"].lint_capabilities()
        self.assertFalse(issues, f"capability lint issues: {issues}")
