# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.addons.smart_core.core.ui_base_contract_asset_event_queue import pop_scene_keys
from odoo.addons.smart_core.core.ui_base_contract_asset_producer import refresh_ui_base_contract_assets


class UiBaseContractAsset(models.Model):
    _name = "sc.ui.base.contract.asset"
    _description = "Scene UI Base Contract Asset"
    _order = "write_date desc, id desc"

    name = fields.Char(string="Name", required=True)
    contract_kind = fields.Selection(
        selection=[("ui_base", "UI Base")],
        string="Contract Kind",
        default="ui_base",
        required=True,
        index=True,
    )
    scene_key = fields.Char(string="Scene Key", required=True, index=True)
    role_code = fields.Char(string="Role Code", index=True)
    company_id = fields.Many2one("res.company", string="Company", index=True)
    scope_hash = fields.Char(string="Scope Hash", index=True)
    source_type = fields.Selection(
        selection=[
            ("runtime_intent", "Runtime Intent"),
            ("precompile", "Precompile"),
            ("snapshot_import", "Snapshot Import"),
            ("replay_capture", "Replay Capture"),
            ("seed", "Seed"),
        ],
        string="Source Type",
        default="runtime_intent",
        required=True,
        index=True,
    )
    status = fields.Selection(
        selection=[("draft", "Draft"), ("active", "Active"), ("archived", "Archived")],
        string="Status",
        default="active",
        required=True,
        index=True,
    )
    asset_version = fields.Char(string="Asset Version", default="v1", required=True, index=True)
    asset_hash = fields.Char(string="Asset Hash")
    source_ref = fields.Char(string="Source Ref")
    code_version = fields.Char(string="Code Version", index=True)
    generated_at = fields.Datetime(string="Generated At", default=fields.Datetime.now, required=True, index=True)
    payload_json = fields.Text(string="Payload JSON", required=True)

    _sql_constraints = [
        (
            "sc_ui_base_contract_asset_scope_version_uniq",
            "unique(contract_kind, scene_key, role_code, company_id, asset_version)",
            "A UI base contract asset already exists for this scene scope and version.",
        ),
    ]

    @api.constrains("status", "contract_kind", "scene_key", "role_code", "company_id")
    def _check_single_active_per_scope(self):
        for record in self:
            if record.status != "active":
                continue
            duplicate = self.search(
                [
                    ("id", "!=", record.id),
                    ("status", "=", "active"),
                    ("contract_kind", "=", record.contract_kind),
                    ("scene_key", "=", record.scene_key),
                    ("role_code", "=", record.role_code or False),
                    ("company_id", "=", record.company_id.id or False),
                ],
                limit=1,
            )
            if duplicate:
                raise ValidationError("Only one active asset is allowed for the same contract scope.")

    @api.model
    def refresh_assets_for_scene_keys(
        self,
        scene_keys=None,
        limit: int = 50,
        source_type: str = "precompile",
        code_version: str = "",
    ):
        return refresh_ui_base_contract_assets(
            self.env,
            scene_keys=list(scene_keys or []),
            limit=int(limit or 0) or 50,
            role_code=None,
            company_id=self.env.company.id if self.env.company else None,
            source_type=source_type,
            code_version=code_version,
        )

    @api.model
    def cron_refresh_ui_base_contract_assets(self, limit: int = 50):
        queue_batch = pop_scene_keys(self.env, limit=int(limit or 0) or 50)
        scene_keys = queue_batch.get("scene_keys") if isinstance(queue_batch.get("scene_keys"), list) else []
        source_type = "event_queue" if scene_keys else "precompile"
        produced = self.refresh_assets_for_scene_keys(
            scene_keys=scene_keys,
            limit=limit,
            source_type=source_type,
            code_version="",
        )
        if isinstance(produced, dict):
            produced["queue"] = {
                "popped_count": int(queue_batch.get("popped_count") or 0),
                "remaining_count": int(queue_batch.get("remaining_count") or 0),
                "source_type": source_type,
            }
        return produced
