from odoo import models, fields

class UIDynamicConfig(models.Model):
    _name = "ui.dynamic.config"
    _description = "UI Dynamic Configuration"

    model = fields.Char(required=True)         # 如 project.project
    view_id = fields.Many2one('ir.ui.view')    # 绑定视图，可选
    path = fields.Char(required=True)          # 节点唯一路径标识
    override_data = fields.Json(required=True) # 覆盖数据（字段属性、可见性等）
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.company)
    user_id = fields.Many2one('res.users', string="User")
