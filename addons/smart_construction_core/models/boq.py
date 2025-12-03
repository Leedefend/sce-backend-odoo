# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ProjectBoqLine(models.Model):
    """工程量清单（平铺）
    同一项目下允许重复清单编码，用编码 + 项目特征/备注等区分不同位置/部位。
    """

    _name = "project.boq.line"
    _description = "工程量清单"
    _order = "project_id, sequence, id"

    project_id = fields.Many2one(
        "project.project",
        string="项目",
        required=True,
        index=True,
        ondelete="cascade",
    )
    sequence = fields.Integer("序号", default=10)
    section_type = fields.Selection(
        [
            ("building", "建筑"),
            ("installation", "安装/机电"),
            ("decoration", "装饰"),
            ("landscape", "景观"),
            ("other", "其他"),
        ],
        string="工程类别",
    )
    code = fields.Char("清单编码", required=True, index=True)
    name = fields.Char("清单名称", required=True)
    spec = fields.Char("规格/项目特征")
    division_name = fields.Char("分部工程名称", index=True)
    single_name = fields.Char(
        "单项工程",
        help="如：建筑与装饰工程、安装工程等；来源于清单表头或导入模板。"
    )
    unit_name = fields.Char(
        "单位工程",
        help="如：具体单体名称；来源于清单表头或导入模板。"
    )
    uom_id = fields.Many2one("uom.uom", string="单位", required=True)
    quantity = fields.Float("工程量", default=0.0)
    price = fields.Monetary("单价", currency_field="currency_id")
    amount = fields.Monetary(
        "合价",
        currency_field="currency_id",
        compute="_compute_amount",
        store=True,
    )

    currency_id = fields.Many2one(
        "res.currency",
        string="币种",
        related="project_id.company_id.currency_id",
        store=True,
        readonly=True,
    )

    cost_item_id = fields.Many2one(
        "sc.dictionary",
        string="成本项",
        domain=[("type", "=", "cost_item")],
    )
    task_id = fields.Many2one(
        "project.task",
        string="关联任务",
        ondelete="set null",
        index=True,
    )
    structure_id = fields.Many2one(
        "sc.project.structure",
        string="工程结构节点",
        ondelete="set null",
        index=True,
    )
    unit_structure_id = fields.Many2one(
        "sc.project.structure",
        string="所属单位工程节点",
        compute="_compute_structure_levels",
        store=True,
        index=True,
    )
    single_structure_id = fields.Many2one(
        "sc.project.structure",
        string="所属单项工程节点",
        compute="_compute_structure_levels",
        store=True,
        index=True,
    )
    work_id = fields.Many2one(
        "construction.work.breakdown",
        string="施工工序结构",
        ondelete="set null",
        index=True,
    )

    remark = fields.Char("备注")
    is_provisional = fields.Boolean("暂列/暂估")
    category = fields.Selection(
        [
            ("subitem", "分部分项"),
            ("measure", "措施项目"),
            ("other", "其他项目"),
        ],
        string="项目类别",
        index=True,
    )
    # 编码分段（按清单规范 12 位编码拆分）
    code_cat = fields.Char("工程分类码", compute="_compute_code_segments", store=True, index=True)
    code_prof = fields.Char("专业工程码", compute="_compute_code_segments", store=True, index=True)
    code_division = fields.Char("分部工程码", compute="_compute_code_segments", store=True, index=True)
    code_subdivision = fields.Char("分项工程码", compute="_compute_code_segments", store=True, index=True)
    code_item = fields.Char("清单项目码", compute="_compute_code_segments", store=True, index=True)

    source_type = fields.Selection(
        [
            ("tender", "招标清单"),
            ("contract", "合同清单"),
            ("settlement", "结算清单"),
        ],
        string="清单来源",
        default="contract",
        index=True,
    )
    version = fields.Char("版本号/批次", help="预留给多次导入或版本管理使用", index=True)

    @api.depends("quantity", "price")
    def _compute_amount(self):
        for rec in self:
            qty = rec.quantity or 0.0
            price = rec.price or 0.0
            rec.amount = qty * price

    @api.depends("structure_id", "structure_id.parent_id", "structure_id.parent_id.parent_id")
    def _compute_structure_levels(self):
        for rec in self:
            unit_node = False
            single_node = False
            node = rec.structure_id
            while node:
                if node.structure_type == "unit" and not unit_node:
                    unit_node = node
                if node.structure_type == "single" and not single_node:
                    single_node = node
                node = node.parent_id
            rec.unit_structure_id = unit_node
            rec.single_structure_id = single_node

    @api.depends("code")
    def _compute_code_segments(self):
        for rec in self:
            code = (rec.code or "").strip()
            if code.isdigit() and len(code) == 12:
                rec.code_cat = code[:2]
                rec.code_prof = code[:4]
                rec.code_division = code[:6]
                rec.code_subdivision = code[:9]
                rec.code_item = code[:12]
            else:
                rec.code_cat = False
                rec.code_prof = False
                rec.code_division = False
                rec.code_subdivision = False
                rec.code_item = False

    _sql_constraints = []
