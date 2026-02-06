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
        try:
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
            return
        except Exception:
            pass

        # fallback keeps governance evidence available even when scene governance models are unavailable
        try:
            Audit = self.env["sc.audit.log"].sudo()
            Audit.write_event(
                event_code="SCENE_GOVERNANCE_ACTION",
                model="scene.governance",
                res_id=0,
                action=action,
                after={
                    "company_id": company_id,
                    "from_channel": from_channel,
                    "to_channel": to_channel,
                    "payload": payload or {},
                },
                reason=reason,
                trace_id=trace_id or "",
                company_id=company_id,
            )
        except Exception:
            return

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
        return {
            "action": "set_channel",
            "company_id": company_id,
            "from_channel": before or "stable",
            "to_channel": channel,
            "trace_id": trace_id or "",
        }

    def pin_stable(self, reason, trace_id=None):
        self._require_reason(reason)
        root = os.environ.get("SCENE_CONTRACT_ROOT") or "/mnt/extra-addons"
        latest = os.path.join(root, "docs/contract/exports/scenes/stable/LATEST.json")
        with open(latest, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
        config = self.env["ir.config_parameter"].sudo()
        config.set_param("sc.scene.contract.pinned", json.dumps(payload))
        config.set_param("sc.scene.use_pinned", "1")
        config.set_param("sc.scene.rollback", "1")
        self._log(
            "pin_stable",
            reason=reason,
            payload={"source": latest},
            trace_id=trace_id,
        )
        return {
            "action": "pin_stable",
            "from_channel": "stable",
            "to_channel": "stable",
            "trace_id": trace_id or "",
        }

    def rollback_stable(self, reason, trace_id=None):
        self._require_reason(reason)
        config = self.env["ir.config_parameter"].sudo()
        config.set_param("sc.scene.rollback", "1")
        config.set_param("sc.scene.use_pinned", "1")
        self._log(
            "rollback",
            reason=reason,
            payload={"mode": "stable_pinned"},
            trace_id=trace_id,
        )
        return {
            "action": "rollback",
            "from_channel": "stable",
            "to_channel": "stable",
            "trace_id": trace_id or "",
        }

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
        return {
            "action": "export_contract",
            "from_channel": None,
            "to_channel": channel,
            "trace_id": trace_id or "",
        }

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
