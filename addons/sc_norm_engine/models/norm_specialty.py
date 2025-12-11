from odoo import api, fields, models


class ScNormSpecialty(models.Model):
    _name = "sc.norm.specialty"
    _description = "Norm Specialty (Sichuan 2015)"
    _order = "sequence, code"

    code = fields.Char("专业代码", required=True)
    name = fields.Char("专业名称", required=True)
    sheet_name = fields.Char("原始 Sheet 名")
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)

    chapter_ids = fields.One2many("sc.norm.chapter", "specialty_id", string="章节")
    item_ids = fields.One2many("sc.norm.item", "specialty_id", string="定额子目")

    _sql_constraints = [
        ("code_uniq", "unique(code)", "专业代码必须唯一！"),
    ]


class ScNormChapter(models.Model):
    _name = "sc.norm.chapter"
    _description = "Norm Chapter"
    _order = "specialty_id, sequence, code"

    code = fields.Char("章节代码", required=True)
    name = fields.Char("章节名称", required=True)
    specialty_id = fields.Many2one(
        "sc.norm.specialty",
        string="所属专业",
        required=True,
        ondelete="cascade",
    )
    sequence = fields.Integer(default=10)

    norm_code_start = fields.Char("开始定额号")
    norm_code_end = fields.Char("结束定额号")

    item_ids = fields.One2many("sc.norm.item", "chapter_id", string="定额子目")

    _sql_constraints = [
        (
            "chapter_uniq",
            "unique(specialty_id, code)",
            "同一专业下章节代码不能重复！",
        ),
    ]


class ScNormItem(models.Model):
    _name = "sc.norm.item"
    _description = "Norm Item (Quota Line)"
    _order = "specialty_id, code"

    code = fields.Char("定额编号", required=True)
    name = fields.Char("项目名称", required=True)

    specialty_id = fields.Many2one(
        "sc.norm.specialty",
        string="所属专业",
        required=True,
        ondelete="cascade",
    )
    chapter_id = fields.Many2one(
        "sc.norm.chapter",
        string="所属章节",
        ondelete="set null",
    )

    unit_raw = fields.Char("原始单位")
    uom_id = fields.Many2one("uom.uom", string="计量单位")

    price_total = fields.Float("综合单价")
    cost_direct = fields.Float("直接费")
    cost_labor = fields.Float("人工费")
    cost_material = fields.Float("材料费")
    cost_machine = fields.Float("机械费")
    fee_rate = fields.Float("费率", help="机械费率或配合比费率等")
    cost_misc = fields.Float("综合费")

    work_desc = fields.Text("工作内容")
    line_no = fields.Integer("原始序号/行号")

    _sql_constraints = [
        (
            "item_code_uniq",
            "unique(specialty_id, code)",
            "同一专业下定额编号不能重复！",
        ),
    ]

    @api.onchange("unit_raw")
    def _onchange_unit_raw(self):
        """单位别名映射可后续实现。"""
        return
