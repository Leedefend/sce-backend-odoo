# -*- coding: utf-8 -*-
import json
import os

from odoo import fields

SCENE_CHANNELS = {"stable", "beta", "dev"}


class SceneGovernanceService:
    def __init__(self, env, user=None):
        self.env = env
        self.user = user or env.user

    def _require_reason(self, reason):
        if not reason or not str(reason).strip():
            raise ValueError("reason is required")

    def _log(self, action, *, company_id=None, from_channel=None, to_channel=None, reason, payload=None, trace_id=None):
        Log = self.env["sc.scene.governance.log"].sudo()
        Log.create({
            "action": action,
            "actor_id": self.user.id if self.user else None,
            "company_id": company_id,
            "from_channel": from_channel,
            "to_channel": to_channel,
            "reason": reason,
            "trace_id": trace_id,
            "payload_json": payload or {},
            "created_at": fields.Datetime.now(),
        })

    def set_company_channel(self, company_id, channel, reason, trace_id=None):
        self._require_reason(reason)
        channel = (channel or "").strip().lower()
        if channel not in SCENE_CHANNELS:
            raise ValueError("invalid channel")
        config = self.env["ir.config_parameter"].sudo()
        key = f"sc.scene.channel.company.{company_id}"
        before = config.get_param(key)
        config.set_param(key, channel)
        self._log(
            "switch_channel",
            company_id=company_id,
            from_channel=before,
            to_channel=channel,
            reason=reason,
            payload={"key": key},
            trace_id=trace_id,
        )
        return True

    def pin_stable(self, reason, trace_id=None):
        self._require_reason(reason)
        root = os.environ.get("SCENE_CONTRACT_ROOT") or "/mnt/extra-addons"
        latest = os.path.join(root, "docs/contract/exports/scenes/stable/LATEST.json")
        with open(latest, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
        self.env["ir.config_parameter"].sudo().set_param("sc.scene.contract.pinned", json.dumps(payload))
        self._log(
            "pin_stable",
            reason=reason,
            payload={"source": latest},
            trace_id=trace_id,
        )
        return True

    def rollback_stable(self, reason, trace_id=None):
        self._require_reason(reason)
        self.env["ir.config_parameter"].sudo().set_param("sc.scene.rollback", "1")
        self._log(
            "rollback",
            reason=reason,
            payload={"mode": "stable_pinned"},
            trace_id=trace_id,
        )
        return True

    def export_contract(self, channel, reason, trace_id=None):
        self._require_reason(reason)
        channel = (channel or "").strip().lower()
        if channel not in SCENE_CHANNELS:
            raise ValueError("invalid channel")
        self._log(
            "export_contract",
            from_channel=None,
            to_channel=channel,
            reason=reason,
            payload={"channel": channel},
            trace_id=trace_id,
        )
        return True

    def snapshot_update(self, channel, reason, trace_id=None):
        self._require_reason(reason)
        channel = (channel or "").strip().lower()
        if channel not in SCENE_CHANNELS:
            raise ValueError("invalid channel")
        self._log(
            "update_snapshot",
            from_channel=None,
            to_channel=channel,
            reason=reason,
            payload={"channel": channel},
            trace_id=trace_id,
        )
        return True
