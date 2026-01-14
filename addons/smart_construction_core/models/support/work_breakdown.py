# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ConstructionWorkBreakdown(models.Model):
    """
    工程结构树（WBS）：
    - 按项目建立一棵树，承载单项/单位/分部/分项/检验批等层级；
    - 供工程量清单、任务等对象挂接；
    - 支持自底向上的工程量/金额汇总。
    """

    _name = "construction.work.breakdown"
    _description = "工程结构(WBS)"
    _parent_name = "parent_id"
    _parent_store = True
    _order = "project_id, parent_path, sequence, id"

    name = fields.Char("名称", required=True)
    code = fields.Char("编码")
    active = fields.Boolean("有效", default=True)
    project_id = fields.Many2one(
        "project.project",
        string="项目",
        required=True,
        index=True,
        ondelete="cascade",
        domain=[],
        check_company=False,  # 避免自动生成 company_id 依赖域
    )
    company_id = fields.Many2one(
        "res.company",
        string="公司",
        related="project_id.company_id",
        store=True,
        readonly=True,
    )

    parent_id = fields.Many2one(
        "construction.work.breakdown",
        string="上级节点",
        index=True,
        ondelete="cascade",
    )
    parent_path = fields.Char(index=True, unaccent=False)
    child_ids = fields.One2many(
        "construction.work.breakdown",
        "parent_id",
        string="下级节点",
    )

    sequence = fields.Integer("序号", default=10)
    # 便于调试/报表的层级深度，根=0
    level = fields.Integer("层级", compute="_compute_level", store=True, recursive=True)
    level_type = fields.Selection(
        [
            ("single", "单项工程"),
            ("unit", "单位工程"),
            ("sub_division", "分部工程"),
            ("sub_section", "分项工程"),
            ("inspection_lot", "检验批"),
            ("location", "施工部位"),
            ("other", "其他"),
        ],
        string="层级类型",
        required=True,
        default="sub_section",
    )

    boq_line_ids = fields.One2many(
        "project.boq.line", "work_id",
        string="关联清单"
    )
    task_ids = fields.One2many(
        "project.task", "work_id",
        string="关联任务"
    )

    boq_quantity_total = fields.Float(
        "清单工程量合计",
        compute="_compute_totals",
        store=True,
        recursive=True,
    )
    boq_amount_total = fields.Monetary(
        "清单合价合计",
        compute="_compute_totals",
        store=True,
        currency_field="currency_id",
        recursive=True,
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="币种",
        related="project_id.company_id.currency_id",
        store=True,
        readonly=True,
    )

    @api.depends("parent_id.level")
    def _compute_level(self):
        """父层级+1，根节点为0。"""
        for rec in self:
            rec.level = rec.parent_id.level + 1 if rec.parent_id else 0

    @api.depends(
        "boq_line_ids.quantity",
        "boq_line_ids.amount",
        "child_ids.boq_quantity_total",
        "child_ids.boq_amount_total",
    )
    def _compute_totals(self):
        """自底向上汇总：本节点挂的清单 + 子节点汇总值。"""
        for rec in self:
            self_qty = sum(rec.boq_line_ids.mapped("quantity"))
            self_amt = sum(rec.boq_line_ids.mapped("amount"))
            child_qty = sum(rec.child_ids.mapped("boq_quantity_total"))
            child_amt = sum(rec.child_ids.mapped("boq_amount_total"))
            rec.boq_quantity_total = self_qty + child_qty
            rec.boq_amount_total = self_amt + child_amt

    @api.constrains("parent_id", "project_id")
    def _check_parent_project(self):
        """父子节点必须同一项目，避免跨项目串树。"""
        for rec in self:
            if rec.parent_id and rec.parent_id.project_id != rec.project_id:
                raise ValidationError("工程结构的父节点与子节点必须属于同一项目。")

    _sql_constraints = [
        (
            "project_code_type_unique",
            "unique(project_id, code, level_type)",
            "同一项目下，工程结构的编码和层级类型不能重复。",
        ),
    ]

    def action_build_hierarchy_from_code(self):
        """根据已有分项的编码自动补齐单位/分部层级，并设置父子关系。"""
        for project in self.mapped("project_id"):
            nodes = self.search(
                [
                    ("project_id", "=", project.id),
                    ("level_type", "=", "sub_section"),
                    ("code", "!=", False),
                ]
            )
            unit_map = {}
            section_map = {}
            for node in nodes:
                code = (node.code or "").strip()
                if len(code) < 4:
                    continue
                unit_code = code[:2]
                section_code = code[:4]

                unit = unit_map.get(unit_code)
                if not unit:
                    unit = self.search(
                        [
                            ("project_id", "=", project.id),
                            ("level_type", "=", "unit"),
                            ("code", "=", unit_code),
                        ],
                        limit=1,
                    )
                    if not unit:
                        unit = self.create(
                            {
                                "project_id": project.id,
                                "level_type": "unit",
                                "code": unit_code,
                                "name": f"单位工程 {unit_code}",
                            }
                        )
                    unit_map[unit_code] = unit

                section = section_map.get(section_code)
                if not section:
                    section = self.search(
                        [
                            ("project_id", "=", project.id),
                            ("level_type", "=", "sub_division"),
                            ("code", "=", section_code),
                        ],
                        limit=1,
                    )
                    if not section:
                        section = self.create(
                            {
                                "project_id": project.id,
                                "level_type": "sub_division",
                                "code": section_code,
                                "name": f"分部工程 {section_code}",
                                "parent_id": unit.id,
                            }
                        )
                    section_map[section_code] = section

                if node.parent_id != section:
                    node.parent_id = section.id

    def _exec_structure_action(self, view_key):
        ctx = dict(self.env.context or {})
        project_id = False
        if self and self[0].project_id:
            project_id = self[0].project_id.id
        project_id = project_id or ctx.get("default_project_id") or ctx.get("project_id") or ctx.get("active_id")
        if not project_id:
            next_action = {
                "type": "ir.actions.act_window",
                "name": "项目列表",
                "res_model": "project.project",
                "view_mode": "kanban,tree,form",
                "views": [(False, "kanban"), (False, "tree"), (False, "form")],
                "target": "current",
                "context": ctx,
            }
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": "执行结构",
                    "message": "请先选择项目，将跳转到项目列表。",
                    "type": "warning",
                    "sticky": False,
                    "next": next_action,
                },
            }

        ctx.setdefault("default_project_id", project_id)
        ctx.setdefault("search_default_project_id", project_id)
        ctx["sc_exec_view"] = view_key
        if view_key == "wbs":
            view = self.env.ref("smart_construction_core.view_exec_structure_wbs_tree")
            search_view = self.env.ref("smart_construction_core.view_project_wbs_search")
            return {
                "type": "ir.actions.act_window",
                "name": "执行结构",
                "res_model": "construction.work.breakdown",
                "view_mode": "tree,form",
                "views": [(view.id, "tree"), (False, "form")],
                "search_view_id": search_view.id,
                "domain": [("project_id", "=", project_id)],
                "context": ctx,
                "target": "current",
            }
        view = self.env.ref("smart_construction_core.view_exec_structure_structure_tree")
        search_view = self.env.ref("smart_construction_core.view_sc_project_structure_search")
        return {
            "type": "ir.actions.act_window",
            "name": "执行结构",
            "res_model": "sc.project.structure",
            "view_mode": "tree,form",
            "views": [(view.id, "tree"), (False, "form")],
            "search_view_id": search_view.id,
            "domain": [("project_id", "=", project_id)],
            "context": ctx,
            "target": "current",
        }

    def action_open_exec_wbs(self):
        return self._exec_structure_action("wbs")

    def action_open_exec_structure(self):
        return self._exec_structure_action("structure")


class ProjectWbs(models.Model):
    """
    兼容层：将历史的 project.wbs 模型指向统一的工程结构表。
    所有字段与逻辑复用 construction.work.breakdown，避免旧引用报错。
    """

    _name = "project.wbs"
    _description = "工程结构(WBS)兼容层"
    _inherit = "construction.work.breakdown"
    _table = "construction_work_breakdown"
