# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError


class ProjectFundingBaseline(models.Model):
    _name = "project.funding.baseline"
    _description = "Project Funding Baseline"
    _order = "id desc"

    project_id = fields.Many2one(
        "project.project",
        string="项目",
        required=True,
        index=True,
        ondelete="cascade",
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="币种",
        related="project_id.company_id.currency_id",
        store=True,
        readonly=True,
    )
    total_amount = fields.Monetary(
        string="资金上限",
        currency_field="currency_id",
        required=True,
    )
    state = fields.Selection(
        [
            ("draft", "草稿"),
            ("active", "生效"),
            ("closed", "关闭"),
        ],
        string="状态",
        default="draft",
        index=True,
        required=True,
    )

    def _check_funding_ready(self, project):
        if not project.is_funding_ready():
            raise UserError("项目未满足资金承载条件，不能建立资金基准。")

    def _check_single_active(self, project, exclude_ids=None):
        domain = [
            ("project_id", "=", project.id),
            ("state", "=", "active"),
        ]
        if exclude_ids:
            domain.append(("id", "not in", exclude_ids))
        if self.search_count(domain):
            raise UserError("项目已存在生效中的资金基准。")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            project_id = vals.get("project_id")
            if project_id:
                project = self.env["project.project"].browse(project_id)
                self._check_funding_ready(project)
                if vals.get("state") == "active":
                    self._check_single_active(project)
        return super().create(vals_list)

    def write(self, vals):
        state_to_active = vals.get("state") == "active"
        project_id = vals.get("project_id")
        for rec in self:
            project = self.env["project.project"].browse(project_id) if project_id else rec.project_id
            if project:
                if "project_id" in vals or "state" in vals:
                    self._check_funding_ready(project)
                if state_to_active or (project_id and rec.state == "active"):
                    self._check_single_active(project, exclude_ids=rec.ids)
        return super().write(vals)
