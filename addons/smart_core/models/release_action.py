# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo import fields, models


class ScReleaseAction(models.Model):
    _name = "sc.release.action"
    _description = "SC Release Action"
    _order = "requested_at desc, id desc"

    active = fields.Boolean(default=True)
    name = fields.Char(required=True)
    action_type = fields.Selection(
        [
            ("promote_snapshot", "Promote Snapshot"),
            ("rollback_snapshot", "Rollback Snapshot"),
        ],
        required=True,
        index=True,
    )
    state = fields.Selection(
        [
            ("pending", "Pending"),
            ("running", "Running"),
            ("succeeded", "Succeeded"),
            ("failed", "Failed"),
        ],
        default="pending",
        required=True,
        index=True,
    )
    product_key = fields.Char(required=True, index=True)
    base_product_key = fields.Char(required=True, index=True)
    edition_key = fields.Char(required=True, index=True)
    requested_by_user_id = fields.Many2one("res.users", string="Requested By", ondelete="set null")
    requested_at = fields.Datetime(required=True, default=fields.Datetime.now, index=True)
    executed_at = fields.Datetime()
    completed_at = fields.Datetime()
    source_snapshot_id = fields.Many2one(
        "sc.edition.release.snapshot",
        string="Source Snapshot",
        ondelete="set null",
    )
    target_snapshot_id = fields.Many2one(
        "sc.edition.release.snapshot",
        string="Target Snapshot",
        ondelete="set null",
    )
    result_snapshot_id = fields.Many2one(
        "sc.edition.release.snapshot",
        string="Result Snapshot",
        ondelete="set null",
    )
    reason_code = fields.Char()
    note = fields.Text()
    request_payload_json = fields.Json(required=True, default=dict)
    result_payload_json = fields.Json(required=True, default=dict)
    diagnostics_json = fields.Json(required=True, default=dict)

    def to_runtime_dict(self) -> dict:
        self.ensure_one()
        return {
            "id": int(self.id),
            "name": str(self.name or "").strip(),
            "action_type": str(self.action_type or "").strip(),
            "state": str(self.state or "").strip() or "pending",
            "product_key": str(self.product_key or "").strip(),
            "base_product_key": str(self.base_product_key or "").strip(),
            "edition_key": str(self.edition_key or "").strip(),
            "requested_by_user_id": int(self.requested_by_user_id.id) if self.requested_by_user_id else 0,
            "requested_at": self.requested_at.isoformat() if self.requested_at else "",
            "executed_at": self.executed_at.isoformat() if self.executed_at else "",
            "completed_at": self.completed_at.isoformat() if self.completed_at else "",
            "source_snapshot_id": int(self.source_snapshot_id.id) if self.source_snapshot_id else 0,
            "target_snapshot_id": int(self.target_snapshot_id.id) if self.target_snapshot_id else 0,
            "result_snapshot_id": int(self.result_snapshot_id.id) if self.result_snapshot_id else 0,
            "reason_code": str(self.reason_code or "").strip(),
            "note": str(self.note or "").strip(),
            "request_payload_json": self.request_payload_json if isinstance(self.request_payload_json, dict) else {},
            "result_payload_json": self.result_payload_json if isinstance(self.result_payload_json, dict) else {},
            "diagnostics_json": self.diagnostics_json if isinstance(self.diagnostics_json, dict) else {},
        }
