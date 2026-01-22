# -*- coding: utf-8 -*-
import time

from odoo import api, fields, models


class ScSignupThrottle(models.Model):
    _name = "sc.signup.throttle"
    _description = "Signup rate limit"

    key = fields.Char(required=True, index=True)
    count = fields.Integer(default=0, required=True)
    window_start = fields.Integer(default=0, required=True)
    last_seen = fields.Integer(default=0, required=True)

    @api.model
    def check_and_bump(self, key, window_sec, max_count):
        now = int(time.time())
        rec = self.sudo().search([("key", "=", key)], limit=1)
        if not rec:
            self.sudo().create(
                {
                    "key": key,
                    "count": 1,
                    "window_start": now,
                    "last_seen": now,
                }
            )
            return True

        if now - rec.window_start >= int(window_sec):
            rec.sudo().write(
                {
                    "count": 1,
                    "window_start": now,
                    "last_seen": now,
                }
            )
            return True

        if rec.count >= int(max_count):
            return False

        rec.sudo().write(
            {
                "count": rec.count + 1,
                "last_seen": now,
            }
        )
        return True

    @api.model
    def gc_expired(self):
        icp = self.env["ir.config_parameter"].sudo()
        try:
            days = int(icp.get_param("sc.signup.ratelimit.gc_days", "7") or 7)
        except ValueError:
            days = 7
        days = max(days, 0)
        if days == 0:
            return 0
        cutoff = int(time.time()) - days * 86400
        records = self.sudo().search([("last_seen", "<", cutoff)])
        count = len(records)
        if count:
            records.unlink()
        return count
