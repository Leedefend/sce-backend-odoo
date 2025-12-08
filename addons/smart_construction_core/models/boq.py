# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ProjectBoqLine(models.Model):
    """工程量清单（平铺）
    同一项目下允许重复清单编码，用编码 + 项目特征/备注等区分不同位置/部位。
    """

    _name = "project.boq.line"
    _description = "工程量清单"
    _order = "project_id, parent_path, sequence, id"
    _parent_store = True
    _parent_name = "parent_id"

    project_id = fields.Many2one(
        "project.project",
        string="项目",
        required=True,
        index=True,
        ondelete="cascade",
    )

    # 树状层级结构（章/节/子目/清单项等）
    parent_id = fields.Many2one(
        "project.boq.line",
        string="上级清单",
        index=True,
        ondelete="cascade",
    )
    child_ids = fields.One2many(
        "project.boq.line",
        "parent_id",
        string="下级清单",
    )
    parent_path = fields.Char(index=True)
    level = fields.Integer(
        "层级",
        compute="_compute_level",
        store=True,
        help="0=顶级（章），1=第二级（节），以此类推。",
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
        help="按专业大类归类清单，用于统计。",
    )
    code = fields.Char("清单编码", required=True, index=True)
    name = fields.Char("清单名称", required=True)
    spec = fields.Char("规格/项目特征")
    division_name = fields.Char("分部工程名称", index=True)
    single_name = fields.Char(
        "单项工程",
        help="工程下的单项工程名称；来源于清单表头或导入模板。",
        index=True,
    )
    unit_name = fields.Char(
        "单位工程",
        help="单项工程下的单位工程/单体/标段名称；来源于清单表头或导入模板。",
        index=True,
    )
    major_name = fields.Char(
        "专业名称",
        help="如：建筑与装饰工程、消防站给排水工程等；来源于清单表头【】内的内容。",
        index=True,
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
        recursive=True,
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
    boq_category = fields.Selection(
        [
            ("boq", "分部分项清单"),
            ("unit_measure", "单价措施清单"),
            ("total_measure", "总价措施清单"),
            ("fee", "规费"),
            ("tax", "税金"),
            ("other", "其他费用"),
        ],
        string="清单类别",
        default="boq",
        index=True,
        help="用于区分分部分项/措施/规费/税金，避免不同类别清单在汇总时混淆。",
    )
    fee_type_id = fields.Many2one(
        "sc.dictionary",
        string="规费类别",
        domain=[("type", "=", "fee_type")],
    )
    tax_type_id = fields.Many2one(
        "sc.dictionary",
        string="税种",
        domain=[("type", "=", "tax_type")],
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
    sheet_index = fields.Integer("来源Sheet序号")
    sheet_name = fields.Char("来源Sheet名称")

    @api.depends("quantity", "price")
    def _compute_amount(self):
        for rec in self:
            qty = rec.quantity or 0.0
            price = rec.price or 0.0
            rec.amount = qty * price

    @api.model_create_multi
    def create(self, vals_list):
        """Ensure project_id is set, inheriting from parent when missing."""
        for vals in vals_list:
            if not vals.get("project_id") and vals.get("parent_id"):
                parent = self.browse(vals["parent_id"])
                if parent.exists():
                    vals["project_id"] = parent.project_id.id
        return super().create(vals_list)

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

    @api.depends("parent_path")
    def _compute_level(self):
        """基于 parent_path 计算层级深度。
        parent_path 形如 '12/45/78/' → split('/') 长度 - 2 = 层级。
        """
        for rec in self:
            if rec.parent_path:
                rec.level = max(len(rec.parent_path.split("/")) - 2, 0)
            else:
                rec.level = 0
