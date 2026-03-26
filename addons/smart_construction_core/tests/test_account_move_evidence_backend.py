# -*- coding: utf-8 -*-

from odoo.tests import TransactionCase
from odoo.tests.common import tagged


@tagged("sc_smoke", "account_move_evidence_backend")
class TestAccountMoveEvidenceBackend(TransactionCase):
    def setUp(self):
        super().setUp()
        self.env["ir.config_parameter"].sudo().set_param(
            "smart_construction_core.sc_cost_from_account_move",
            "True",
        )
        self.project = self.env["project.project"].create({"name": "Account Move Evidence Project"})
        self.wbs = self.env["construction.work.breakdown"].create(
            {
                "name": "Account Move WBS",
                "code": "AM-WBS",
                "project_id": self.project.id,
            }
        )
        self.cost_code = self.env["project.cost.code"].create(
            {
                "name": "Account Move Cost",
                "code": "AM-COST",
                "type": "material",
            }
        )
        self.partner = self.env["res.partner"].create({"name": "Account Move Vendor"})
        self.expense_account = self.env["account.account"].create(
            {
                "name": "Evidence Expense",
                "code": "EVEXP01",
                "account_type": "expense",
            }
        )
        self.offset_account = self.env["account.account"].create(
            {
                "name": "Evidence Payable",
                "code": "EVPAY01",
                "account_type": "liability_current",
            }
        )
        self.journal = self.env["account.journal"].create(
            {
                "name": "Evidence General Journal",
                "code": "EVPJ",
                "type": "general",
                "default_account_id": self.offset_account.id,
            }
        )

    def _create_move(self):
        return self.env["account.move"].create(
            {
                "move_type": "entry",
                "partner_id": self.partner.id,
                "project_id": self.project.id,
                "journal_id": self.journal.id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Cost line",
                            "account_id": self.expense_account.id,
                            "debit": 200.0,
                            "credit": 0.0,
                            "project_id": self.project.id,
                            "wbs_id": self.wbs.id,
                            "cost_code_id": self.cost_code.id,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "name": "Offset line",
                            "account_id": self.offset_account.id,
                            "debit": 0.0,
                            "credit": 200.0,
                        },
                    ),
                ],
            }
        )

    def test_post_creates_cost_ledger_and_evidence(self):
        move = self._create_move()
        move._post(soft=False)
        move._create_cost_ledger_entries()
        self.env["sc.evidence.policy"].ensure_account_move_cost_evidence(move)

        ledger = self.env["project.cost.ledger"].search(
            [
                ("source_model", "=", "account.move.line"),
                ("source_id", "=", move.id),
                ("project_id", "=", self.project.id),
            ],
            limit=1,
        )
        self.assertTrue(ledger)

        evidence = self.env["sc.business.evidence"].sudo().search(
            [
                ("source_model", "=", "project.cost.ledger"),
                ("source_id", "=", ledger.id),
                ("evidence_type", "=", "cost"),
            ],
            limit=1,
        )
        self.assertTrue(evidence)
        self.assertEqual(evidence.amount, 200.0)

    def test_button_draft_cleans_cost_ledger_and_evidence(self):
        move = self._create_move()
        move._post(soft=False)
        move._create_cost_ledger_entries()
        self.env["sc.evidence.policy"].ensure_account_move_cost_evidence(move)
        ledger = self.env["project.cost.ledger"].search(
            [
                ("source_model", "=", "account.move.line"),
                ("source_id", "=", move.id),
                ("project_id", "=", self.project.id),
            ],
            limit=1,
        )
        self.assertTrue(ledger)

        move.button_draft()

        remaining_ledger = self.env["project.cost.ledger"].search_count(
            [
                ("source_model", "=", "account.move.line"),
                ("source_id", "=", move.id),
                ("project_id", "=", self.project.id),
            ]
        )
        remaining_evidence = self.env["sc.business.evidence"].sudo().search_count(
            [
                ("source_model", "=", "project.cost.ledger"),
                ("source_id", "=", ledger.id),
                ("evidence_type", "=", "cost"),
            ]
        )
        self.assertEqual(remaining_ledger, 0)
        self.assertEqual(remaining_evidence, 0)
