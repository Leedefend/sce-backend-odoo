# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ScEnterprisePost(models.Model):
    _name = "sc.enterprise.post"
    _description = "Enterprise Post"
    _order = "company_id, sequence, name, id"

    name = fields.Char("岗位名称", required=True)
    code = fields.Char("岗位编码")
    sequence = fields.Integer("排序", default=10)
    company_id = fields.Many2one(
        "res.company",
        string="所属公司",
        required=True,
        default=lambda self: self.env.company,
    )
    active = fields.Boolean("启用", default=True)
    note = fields.Text("备注")
    sc_user_count = fields.Integer("用户数", compute="_compute_sc_user_count")

    _sql_constraints = [
        (
            "sc_enterprise_post_company_name_uniq",
            "unique(company_id, name)",
            "同一公司下岗位名称必须唯一。",
        ),
        (
            "sc_enterprise_post_company_code_uniq",
            "unique(company_id, code)",
            "同一公司下岗位编码必须唯一。",
        ),
    ]

    def _compute_sc_user_count(self):
        grouped = self.env["res.users"].sudo().read_group(
            [("sc_post_id", "in", self.ids)],
            ["sc_post_id"],
            ["sc_post_id"],
        )
        counts = {
            item["sc_post_id"][0]: item["sc_post_id_count"]
            for item in grouped
            if item.get("sc_post_id")
        }
        for post in self:
            post.sc_user_count = int(counts.get(post.id, 0))

    @api.constrains("code")
    def _check_code_not_blank(self):
        for post in self:
            if post.code is not False and not (post.code or "").strip():
                raise ValidationError(_("岗位编码不能为空白字符。"))

    def action_open_enterprise_users(self):
        self.ensure_one()
        action = self.env.ref("smart_enterprise_base.action_enterprise_user").sudo().read()[0]
        action["name"] = _("用户设置：%s") % self.display_name
        action["domain"] = [
            ("company_id", "=", self.company_id.id),
            "|",
            ("sc_post_id", "=", self.id),
            ("sc_post_ids", "in", self.id),
        ]
        action["context"] = {
            "default_company_id": self.company_id.id,
            "default_sc_post_id": self.id,
            "search_default_company_id": self.company_id.id,
            "search_default_sc_post_id": self.id,
            "sc_post_name": self.display_name,
        }
        return action
