# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo import _, api, models
from odoo.exceptions import UserError


class EvidencePolicyService(models.AbstractModel):
    _name = "sc.evidence.policy"
    _description = "Smart Construction Evidence Policy"

    @api.model
    def ensure_records(self, records, *, evidence_type=None, auto_build=False, event_code="evidence_policy_check"):
        if auto_build and records:
            self.env["sc.evidence.builder"].build(records, event_code=event_code)
        Evidence = self.env["sc.business.evidence"].sudo()
        for record in records:
            domain = [
                ("source_model", "=", str(record._name or "")),
                ("source_id", "=", int(record.id)),
            ]
            if evidence_type:
                domain.append(("evidence_type", "=", str(evidence_type)))
            if not Evidence.search_count(domain):
                raise UserError(
                    _("Evidence missing for %(model)s#%(id)s, operation not allowed.")
                    % {"model": record._name, "id": int(record.id)}
                )
        return True

    @api.model
    def ensure_account_move_cost_evidence(self, moves):
        Ledger = self.env["project.cost.ledger"].sudo()
        for move in moves.filtered(lambda item: item.project_id and item.move_type in ("in_invoice", "entry")):
            eligible_lines = move.line_ids.filtered(lambda line: line._is_cost_ledger_candidate())
            if not eligible_lines:
                continue
            ledgers = Ledger.search(
                [
                    ("source_model", "=", "account.move.line"),
                    ("source_line_id", "in", eligible_lines.ids),
                ]
            )
            covered_line_ids = {int(line_id or 0) for line_id in ledgers.mapped("source_line_id")}
            missing_lines = [line for line in eligible_lines if int(line.id) not in covered_line_ids]
            if missing_lines:
                raise UserError(
                    _("Cost evidence production missing ledger rows for posted move %(name)s.")
                    % {"name": move.display_name}
                )
            self.ensure_records(ledgers, evidence_type="cost", auto_build=True, event_code="account_move_posted")
        return True
