# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime, timedelta

from odoo import fields

from odoo.addons.smart_core.governance.scene_drift_engine import is_critical_drift_warn
from odoo.addons.smart_core.utils.contract_governance import is_truthy


class AutoDegradeEngine:
    def _get_policy(self, env) -> dict:
        defaults = {
            "enabled": True,
            "critical_threshold_resolve_errors": 1,
            "critical_threshold_drift_warn": 1,
            "action": "rollback_pinned",
        }
        try:
            config = env["ir.config_parameter"].sudo()
        except Exception:
            return defaults

        def _get_int(name: str, fallback: int) -> int:
            try:
                raw = config.get_param(name)
                return int(raw) if raw not in (None, "") else fallback
            except Exception:
                return fallback

        enabled_raw = config.get_param("sc.scene.auto_degrade.enabled")
        enabled = defaults["enabled"] if enabled_raw in (None, "") else is_truthy(enabled_raw)
        action = (config.get_param("sc.scene.auto_degrade.action") or defaults["action"]).strip().lower()
        if action not in {"rollback_pinned", "stable_latest"}:
            action = defaults["action"]

        return {
            "enabled": enabled,
            "critical_threshold_resolve_errors": max(1, _get_int("sc.scene.auto_degrade.critical_threshold.resolve_errors", 1)),
            "critical_threshold_drift_warn": max(1, _get_int("sc.scene.auto_degrade.critical_threshold.drift_warn", 1)),
            "action": action,
        }

    def _get_notify_policy(self, env) -> dict:
        defaults = {
            "enabled": True,
            "channels": ["internal"],
        }
        try:
            config = env["ir.config_parameter"].sudo()
        except Exception:
            return defaults

        enabled_raw = config.get_param("sc.scene.auto_degrade.notify.enabled")
        enabled = defaults["enabled"] if enabled_raw in (None, "") else is_truthy(enabled_raw)
        raw_channels = (config.get_param("sc.scene.auto_degrade.notify.channels") or "internal").strip().lower()
        allowed = {"email", "internal", "webhook"}
        channels = [item.strip() for item in raw_channels.split(",") if item.strip() in allowed]
        if not channels:
            channels = ["internal"]
        return {"enabled": enabled, "channels": channels}

    def _notify(self, env, *, user, trace_id: str, reason_codes: list, action_taken: str, from_channel: str, to_channel: str):
        policy = self._get_notify_policy(env)
        if not policy.get("enabled"):
            return {"sent": False, "channels": [], "trace_id": trace_id or ""}

        sent_channels = []
        message_payload = {
            "trace_id": trace_id or "",
            "reason_codes": list(reason_codes or []),
            "action_taken": action_taken,
            "from_channel": from_channel,
            "to_channel": to_channel,
            "company_id": user.company_id.id if user and user.company_id else None,
            "suggestion": "Please review scene targets and resolve critical drift/resolve errors.",
        }
        body = (
            "Auto-degrade triggered.\n"
            f"trace_id={message_payload['trace_id']}\n"
            f"action_taken={action_taken}\n"
            f"from={from_channel} to={to_channel}\n"
            f"reason_codes={','.join(message_payload['reason_codes']) or '-'}"
        )

        for channel in policy.get("channels") or []:
            if channel == "internal":
                try:
                    env["sc.audit.log"].sudo().write_event(
                        event_code="SCENE_AUTO_DEGRADE_NOTIFY",
                        model="system.init",
                        res_id=0,
                        action="auto_degrade_notify_internal",
                        after={"channel": "internal", **message_payload},
                        reason="auto degrade internal notification",
                        trace_id=trace_id or "",
                        company_id=message_payload["company_id"],
                    )
                    sent_channels.append("internal")
                except Exception:
                    pass
            elif channel == "email":
                try:
                    partner = user.partner_id if user else None
                    email_to = partner.email if partner and partner.email else None
                    if email_to:
                        mail_model = env["mail.mail"].sudo()
                        mail_model.create({
                            "subject": "[Scene] Auto-degrade triggered",
                            "body_html": body.replace("\n", "<br/>"),
                            "email_to": email_to,
                        })
                        sent_channels.append("email")
                except Exception:
                    pass
            elif channel == "webhook":
                try:
                    env["sc.audit.log"].sudo().write_event(
                        event_code="SCENE_AUTO_DEGRADE_NOTIFY",
                        model="system.init",
                        res_id=0,
                        action="auto_degrade_notify_webhook_pending",
                        after={"channel": "webhook", **message_payload},
                        reason="auto degrade webhook notification placeholder",
                        trace_id=trace_id or "",
                        company_id=message_payload["company_id"],
                    )
                    sent_channels.append("webhook")
                except Exception:
                    pass

        return {"sent": bool(sent_channels), "channels": sent_channels, "trace_id": trace_id or ""}

    def _log_once(self, env, *, trace_id: str, user, from_channel: str, to_channel: str, reason_codes: list, action_taken: str):
        try:
            log_model = env["sc.scene.governance.log"].sudo()
            now = datetime.utcnow()
            window_start = fields.Datetime.to_string(now - timedelta(minutes=1))
            domain = [
                ("action", "=", "auto_degrade_triggered"),
                ("created_at", ">=", window_start),
            ]
            if trace_id:
                domain.append(("trace_id", "=", trace_id))
            if log_model.search_count(domain):
                return
            log_model.create({
                "action": "auto_degrade_triggered",
                "actor_id": user.id if user and user.id else None,
                "company_id": user.company_id.id if user and user.company_id else None,
                "from_channel": from_channel,
                "to_channel": to_channel,
                "reason": "auto degrade triggered by scene diagnostics",
                "trace_id": trace_id or "",
                "payload_json": {
                    "reason_codes": list(reason_codes or []),
                    "action_taken": action_taken,
                },
                "created_at": fields.Datetime.now(),
            })
            return
        except Exception:
            pass

        try:
            audit = env["sc.audit.log"].sudo()
            now = datetime.utcnow()
            window_start = fields.Datetime.to_string(now - timedelta(minutes=1))
            domain = [
                ("event_code", "=", "SCENE_AUTO_DEGRADE_TRIGGERED"),
                ("ts", ">=", window_start),
            ]
            if trace_id:
                domain.append(("trace_id", "=", trace_id))
            if audit.search_count(domain):
                return
            audit.write_event(
                event_code="SCENE_AUTO_DEGRADE_TRIGGERED",
                model="system.init",
                res_id=0,
                action="auto_degrade_triggered",
                after={
                    "from_channel": from_channel,
                    "to_channel": to_channel,
                    "reason_codes": list(reason_codes or []),
                    "action_taken": action_taken,
                },
                reason="auto degrade triggered by scene diagnostics",
                trace_id=trace_id or "",
                company_id=user.company_id.id if user and user.company_id else None,
            )
        except Exception:
            return

    def evaluate(self, env, diagnostics: dict, user, trace_id: str, scene_channel: str) -> dict:
        policy = self._get_policy(env)
        result = {
            "triggered": False,
            "reason_codes": [],
            "action_taken": "none",
            "notifications": {"sent": False, "channels": []},
            "policy": policy,
            "pre_counts": {
                "critical_resolve_errors_count": 0,
                "critical_drift_warn_count": 0,
            },
        }
        if not policy.get("enabled"):
            return result

        resolve_errors = diagnostics.get("resolve_errors") if isinstance(diagnostics.get("resolve_errors"), list) else []
        drift = diagnostics.get("drift") if isinstance(diagnostics.get("drift"), list) else []
        critical_resolve_errors_count = len(
            [
                entry for entry in resolve_errors
                if isinstance(entry, dict) and str(entry.get("severity") or "").strip().lower() == "critical"
            ]
        )
        critical_drift_warn_count = len([entry for entry in drift if is_critical_drift_warn(entry)])
        result["pre_counts"] = {
            "critical_resolve_errors_count": critical_resolve_errors_count,
            "critical_drift_warn_count": critical_drift_warn_count,
        }

        reason_codes = []
        if critical_resolve_errors_count >= int(policy.get("critical_threshold_resolve_errors") or 1):
            reason_codes.append("critical_resolve_errors")
        if critical_drift_warn_count >= int(policy.get("critical_threshold_drift_warn") or 1):
            reason_codes.append("critical_drift_warn")
        if not reason_codes:
            return result

        action = policy.get("action") or "rollback_pinned"
        to_channel = "stable"
        rollback_active = action == "rollback_pinned"
        try:
            config = env["ir.config_parameter"].sudo()
            config.set_param("sc.scene.rollback", "1" if rollback_active else "0")
            config.set_param("sc.scene.use_pinned", "1" if rollback_active else "0")
        except Exception:
            pass

        self._log_once(
            env,
            trace_id=trace_id,
            user=user,
            from_channel=scene_channel,
            to_channel=to_channel,
            reason_codes=reason_codes,
            action_taken=action,
        )
        notify_result = self._notify(
            env,
            user=user,
            trace_id=trace_id,
            reason_codes=reason_codes,
            action_taken=action,
            from_channel=scene_channel,
            to_channel=to_channel,
        )

        result["triggered"] = True
        result["reason_codes"] = reason_codes
        result["action_taken"] = action
        result["notifications"] = notify_result
        return result
