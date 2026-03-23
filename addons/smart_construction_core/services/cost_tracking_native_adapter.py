# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo import fields


class CostTrackingNativeAdapter:
    """Prepared native cost adapter based on account.move."""

    SUPPORTED_MOVE_TYPES = ("in_invoice", "in_refund", "entry")

    def __init__(self, env):
        self.env = env

    def _model(self, model_name):
        try:
            return self.env[model_name]
        except Exception:
            return None

    def _has_fields(self, model_name, field_names):
        model = self._model(model_name)
        if model is None:
            return False
        model_fields = getattr(model, "_fields", {})
        return all(str(name) in model_fields for name in (field_names or ()))

    def move_domain(self, project):
        if not project or not self._has_fields("account.move", ["project_id", "move_type"]):
            return [("id", "=", 0)]
        return [
            ("project_id", "=", int(project.id)),
            ("move_type", "in", list(self.SUPPORTED_MOVE_TYPES)),
        ]

    def recent_moves(self, project, *, limit=5):
        Move = self._model("account.move")
        if Move is None or not project:
            return []
        Move = Move.sudo()
        try:
            rows = Move.search(self.move_domain(project), order="date desc,id desc", limit=max(int(limit or 0), 0))
        except Exception:
            return []
        return [self._move_payload(row) for row in rows]

    def summary(self, project):
        summary = {
            "project_id": int(getattr(project, "id", 0) or 0),
            "carrier_model": "account.move",
            "secondary_context_model": "project.project",
            "supported_move_types": list(self.SUPPORTED_MOVE_TYPES),
            "move_count": 0,
            "posted_move_count": 0,
            "draft_move_count": 0,
            "vendor_bill_count": 0,
            "journal_entry_count": 0,
            "posted_cost_amount": 0.0,
            "draft_cost_amount": 0.0,
            "total_cost_amount": 0.0,
            "currency_name": "",
            "latest_move_date": "",
            "as_of_date": str(fields.Date.today()),
            "prepared_boundary": "account_move_project_cost_recording_only",
        }
        moves = self.recent_moves(project, limit=5)
        Move = self._model("account.move")
        if Move is None or not project:
            summary["recent_moves"] = moves
            return summary
        Move = Move.sudo()

        try:
            all_moves = Move.search(self.move_domain(project), order="date desc,id desc")
        except Exception:
            summary["recent_moves"] = moves
            return summary

        posted_amount = 0.0
        draft_amount = 0.0
        latest_move_date = ""
        currency_name = ""
        move_count = 0
        posted_move_count = 0
        draft_move_count = 0
        vendor_bill_count = 0
        journal_entry_count = 0
        for move in all_moves:
            move_count += 1
            move_type = str(getattr(move, "move_type", "") or "")
            if move_type in ("in_invoice", "in_refund"):
                vendor_bill_count += 1
            elif move_type == "entry":
                journal_entry_count += 1
            state = str(getattr(move, "state", "") or "")
            amount = self._cost_amount(move)
            if state == "posted":
                posted_move_count += 1
                posted_amount += amount
            else:
                draft_move_count += 1
                draft_amount += amount
            if not latest_move_date:
                latest_move_date = str(getattr(move, "date", "") or "")
            if not currency_name:
                currency_name = str(getattr(getattr(move, "currency_id", None), "name", "") or "")

        summary.update(
            {
                "move_count": move_count,
                "posted_move_count": posted_move_count,
                "draft_move_count": draft_move_count,
                "vendor_bill_count": vendor_bill_count,
                "journal_entry_count": journal_entry_count,
                "posted_cost_amount": round(posted_amount, 2),
                "draft_cost_amount": round(draft_amount, 2),
                "total_cost_amount": round(posted_amount + draft_amount, 2),
                "currency_name": currency_name,
                "latest_move_date": latest_move_date,
                "recent_moves": moves,
            }
        )
        return summary

    def _cost_amount(self, move):
        move_type = str(getattr(move, "move_type", "") or "")
        if move_type in ("in_invoice", "in_refund"):
            try:
                return abs(float(getattr(move, "amount_total_signed", 0.0) or 0.0))
            except Exception:
                return 0.0
        amount = 0.0
        for line in getattr(move, "line_ids", []):
            try:
                internal_group = str(getattr(getattr(line, "account_id", None), "internal_group", "") or "")
                debit = float(getattr(line, "debit", 0.0) or 0.0)
            except Exception:
                continue
            if internal_group in ("expense", "asset") and debit > 0:
                amount += debit
        return round(amount, 2)

    def _move_payload(self, move):
        expense_lines = []
        for line in getattr(move, "line_ids", []):
            try:
                internal_group = str(getattr(getattr(line, "account_id", None), "internal_group", "") or "")
                debit = float(getattr(line, "debit", 0.0) or 0.0)
            except Exception:
                continue
            if internal_group in ("expense", "asset") and debit > 0:
                expense_lines.append(line)
        primary_line = expense_lines[0] if expense_lines else None
        project = getattr(move, "project_id", None)
        cost_code = getattr(primary_line, "cost_code_id", None) if primary_line else None
        return {
            "move_id": int(getattr(move, "id", 0) or 0),
            "name": str(getattr(move, "name", "") or getattr(move, "ref", "") or ""),
            "date": str(getattr(move, "date", "") or ""),
            "state": str(getattr(move, "state", "") or ""),
            "move_type": str(getattr(move, "move_type", "") or ""),
            "partner_name": str(getattr(getattr(move, "partner_id", None), "display_name", "") or ""),
            "amount": self._cost_amount(move),
            "currency_name": str(getattr(getattr(move, "currency_id", None), "name", "") or ""),
            "description": str(getattr(primary_line, "name", "") or getattr(move, "ref", "") or getattr(move, "name", "") or ""),
            "category_name": str(getattr(cost_code, "path_display", "") or getattr(cost_code, "display_name", "") or ""),
            "category_type": str(getattr(cost_code, "type", "") or ""),
            "project_id": int(getattr(project, "id", 0) or 0),
            "project_name": str(getattr(project, "display_name", "") or ""),
        }
