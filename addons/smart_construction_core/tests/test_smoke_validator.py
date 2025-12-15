# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged


@tagged("sc_smoke", "smoke_validator")
class TestValidatorSmoke(TransactionCase):

    def test_validator_runs(self):
        payload = self.env["sc.data.validator"].run()
        self.assertIn("rules", payload)
        self.assertIn("issues_total", payload)
        # at least rule registry is wired
        self.assertGreaterEqual(len(payload["rules"]), 1)

    def test_validator_catches_missing_settlement(self):
        project = self.env["project.project"].create({"name": "Validator Project"})
        partner = self.env["res.partner"].create({"name": "Validator Partner"})
        bad_pr = self.env["payment.request"].create(
            {
                "name": "VAL-PR-BAD",
                "type": "pay",
                "project_id": project.id,
                "partner_id": partner.id,
                "amount": 100,
                "state": "approve",  # 规则要求此状态必须关联结算单
            }
        )
        payload = self.env["sc.data.validator"].run()
        rule = next(r for r in payload["rules"] if r["rule"] == "three_way_link_integrity")
        issue_ids = [i["res_id"] for i in rule.get("issues", [])]
        self.assertIn(bad_pr.id, issue_ids)
