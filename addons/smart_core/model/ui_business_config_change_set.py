# -*- coding: utf-8 -*-
from __future__ import annotations

import hashlib
import json
import secrets
from datetime import timedelta

from odoo import api, fields, models
from odoo.exceptions import ValidationError


REVERSIBLE_CONFIG_TYPES = {
    "form",
    "list",
    "search",
    "analysis",
    "menu",
}
ACTIVE_CHANGE_SET_STATES = {"draft", "validating", "ready", "failed"}


def stable_payload_hash(payload) -> str:
    value = payload if isinstance(payload, (dict, list)) else {}
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class UIBusinessConfigChangeSet(models.Model):
    _name = "ui.business.config.change.set"
    _description = "UI Business Config Change Set"
    _order = "write_date desc, id desc"

    name = fields.Char(required=True, default="未发布配置变更")
    token = fields.Char(required=True, default=lambda self: secrets.token_urlsafe(24), copy=False, index=True)
    state = fields.Selection([
        ("draft", "Draft"),
        ("validating", "Validating"),
        ("ready", "Ready"),
        ("publishing", "Publishing"),
        ("published", "Published"),
        ("failed", "Failed"),
        ("discarded", "Discarded"),
        ("superseded", "Superseded"),
    ], required=True, default="draft", index=True)
    user_id = fields.Many2one("res.users", required=True, default=lambda self: self.env.user, readonly=True, index=True)
    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company, readonly=True, index=True)
    role_key = fields.Char(index=True)
    database_name = fields.Char(required=True, default=lambda self: self.env.cr.dbname, readonly=True)
    expires_at = fields.Datetime(required=True, default=lambda self: fields.Datetime.now() + timedelta(hours=8), index=True)
    preview_token = fields.Char(copy=False, index=True)
    preview_expires_at = fields.Datetime(copy=False)
    publish_request_id = fields.Char(copy=False, index=True)
    published_at = fields.Datetime(copy=False)
    failure_message = fields.Text(copy=False)
    rollback_snapshot_json = fields.Json(default=dict, copy=False)
    publish_result_json = fields.Json(default=dict, copy=False)
    item_ids = fields.One2many("ui.business.config.change.set.item", "change_set_id", string="Items")

    _sql_constraints = [
        ("token_unique", "unique(token)", "变更集令牌必须唯一。"),
        ("publish_request_unique", "unique(publish_request_id)", "发布请求ID必须唯一。"),
    ]

    def _is_expired(self) -> bool:
        self.ensure_one()
        return bool(self.expires_at and self.expires_at <= fields.Datetime.now())

    def assert_owner_scope(self, *, role_key: str = ""):
        self.ensure_one()
        if self.user_id != self.env.user or self.company_id != self.env.company:
            raise ValidationError("CHANGE_SET_SCOPE_FORBIDDEN")
        if self.database_name != self.env.cr.dbname:
            raise ValidationError("CHANGE_SET_DATABASE_MISMATCH")
        requested_role = str(role_key or "").strip()
        if requested_role != str(self.role_key or "").strip():
            raise ValidationError("CHANGE_SET_ROLE_MISMATCH")
        if self._is_expired():
            raise ValidationError("CHANGE_SET_EXPIRED")
        return self

    def issue_preview_token(self) -> str:
        self.ensure_one()
        self.assert_owner_scope(role_key=str(self.role_key or ""))
        if self.state not in {"draft", "ready", "failed"}:
            raise ValidationError("CHANGE_SET_NOT_PREVIEWABLE")
        token = secrets.token_urlsafe(32)
        self.write({
            "preview_token": token,
            "preview_expires_at": fields.Datetime.now() + timedelta(minutes=20),
        })
        return token

    def serialize(self, *, include_payload: bool = True) -> dict:
        self.ensure_one()
        return {
            "id": int(self.id),
            "token": str(self.token or ""),
            "state": str(self.state or ""),
            "name": str(self.name or ""),
            "user_id": int(self.user_id.id or 0),
            "company_id": int(self.company_id.id or 0),
            "role_key": str(self.role_key or ""),
            "database_name": str(self.database_name or ""),
            "expires_at": fields.Datetime.to_string(self.expires_at) if self.expires_at else "",
            "published_at": fields.Datetime.to_string(self.published_at) if self.published_at else "",
            "failure_message": str(self.failure_message or ""),
            "item_count": len(self.item_ids),
            "items": [item.serialize(include_payload=include_payload) for item in self.item_ids.sorted("id")],
            "publish_result": self.publish_result_json or {},
        }


class UIBusinessConfigChangeSetItem(models.Model):
    _name = "ui.business.config.change.set.item"
    _description = "UI Business Config Change Set Item"
    _order = "id"

    change_set_id = fields.Many2one("ui.business.config.change.set", required=True, ondelete="cascade", index=True)
    config_type = fields.Selection([
        ("form", "Form"),
        ("list", "List"),
        ("search", "Search"),
        ("analysis", "Analysis"),
        ("menu", "Menu"),
    ], required=True, index=True)
    target_key = fields.Char(required=True, index=True)
    model = fields.Char(required=True, index=True)
    view_type = fields.Char(index=True)
    action_id = fields.Integer(index=True)
    view_id = fields.Integer(index=True)
    role_key = fields.Char(index=True)
    target_contract_id = fields.Many2one("ui.business.config.contract", ondelete="set null", index=True)
    base_version_no = fields.Integer(default=0)
    base_payload_hash = fields.Char(required=True)
    draft_payload = fields.Json(required=True, default=dict)
    diff_summary = fields.Json(default=dict)
    reversible = fields.Boolean(default=True, required=True)
    risk_level = fields.Selection([("low", "Low"), ("medium", "Medium"), ("high", "High")], default="low", required=True)
    validation_result = fields.Json(default=dict)
    publish_result = fields.Json(default=dict)

    _sql_constraints = [
        ("change_set_target_unique", "unique(change_set_id, target_key)", "同一变更集中的配置目标不能重复。"),
    ]

    @api.constrains("config_type", "reversible")
    def _check_reversible_type(self):
        for rec in self:
            if rec.config_type not in REVERSIBLE_CONFIG_TYPES or not rec.reversible:
                raise ValidationError("变更集只允许可逆合同配置。")

    def serialize(self, *, include_payload: bool = True) -> dict:
        self.ensure_one()
        row = {
            "id": int(self.id),
            "config_type": str(self.config_type or ""),
            "target_key": str(self.target_key or ""),
            "model": str(self.model or ""),
            "view_type": str(self.view_type or ""),
            "action_id": int(self.action_id or 0),
            "view_id": int(self.view_id or 0),
            "role_key": str(self.role_key or ""),
            "current_contract_id": int(self.target_contract_id.id or 0),
            "current_version": int(self.base_version_no or 0),
            "current_payload_hash": str(self.base_payload_hash or ""),
            "diff_summary": self.diff_summary or {},
            "reversible": bool(self.reversible),
            "risk_level": str(self.risk_level or "low"),
            "validation_result": self.validation_result or {},
            "publish_result": self.publish_result or {},
        }
        if include_payload:
            row["draft_payload"] = self.draft_payload or {}
        return row
