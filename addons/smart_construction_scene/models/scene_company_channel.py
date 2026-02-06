# -*- coding: utf-8 -*-
from odoo import api, fields, models

CHANNELS = [("stable", "Stable"), ("beta", "Beta"), ("dev", "Dev")]


class ScSceneCompanyChannel(models.Model):
    _name = "sc.scene.company.channel"
    _description = "SC Scene Company Channel"
    _order = "company_id"
    _rec_name = "company_id"

    company_id = fields.Many2one("res.company", required=True, ondelete="cascade")
    channel = fields.Selection(CHANNELS, required=True, default="stable")

    _sql_constraints = [
        ("sc_scene_company_channel_company_uniq", "unique(company_id)", "Company already configured."),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._sync_params()
        return records

    def write(self, vals):
        res = super().write(vals)
        self._sync_params()
        return res

    def _sync_params(self):
        param = self.env["ir.config_parameter"].sudo()
        for rec in self:
            key = f"sc.scene.channel.company.{rec.company_id.id}"
            param.set_param(key, rec.channel)
