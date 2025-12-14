# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.osv import expression


class ProjectDictionary(models.Model):
    _name = "project.dictionary"
    _description = "工程项目数据字典"
    # 先按 type，再按 sequence，再按 code/name 排序，便于字典维护
    _order = "type, sequence, code, name"
    _parent_name = "parent_id"
    _parent_store = True

    # === 基础字段 ===
    name = fields.Char("名称", required=True)
    code = fields.Char("编码")
    type = fields.Selection(
        [
            # 既有类型（保持兼容）
            ("project_type", "项目类型"),
            ("cost_item", "成本项"),
            ("uom", "计量单位"),
            # 新增：定额体系四层结构
            ("discipline", "专业"),
            ("chapter", "章节"),
            ("quota_item", "定额项目"),
            ("sub_item", "子目"),
        ],
        required=True,
        index=True,
        string="类别",
    )

    sequence = fields.Integer("顺序", default=10)
    active = fields.Boolean("启用", default=True)

    # === 树形结构支持 ===
    parent_id = fields.Many2one(
        "project.dictionary",
        string="上级条目",
        index=True,
        ondelete="restrict",
    )
    child_ids = fields.One2many("project.dictionary", "parent_id", string="下级条目")

    level = fields.Integer(
        "层级",
        compute="_compute_level",
        store=True,
        readonly=True,
        recursive=True,
    )

    full_name = fields.Char(
        "全路径名称",
        compute="_compute_full_name",
        store=True,
        readonly=True,
        help="自动拼接“上级 / 本级名称”，方便搜索与导入匹配",
        recursive=True,
    )
    parent_path = fields.Char(index=True, unaccent=False)
    # === 层级导航锚点：便于子目列表按专业/章节分组 ===
    discipline_id = fields.Many2one(
        "project.dictionary",
        string="专业",
        compute="_compute_hierarchy_refs",
        store=True,
        readonly=True,
    )
    chapter_id = fields.Many2one(
        "project.dictionary",
        string="章节",
        compute="_compute_hierarchy_refs",
        store=True,
        readonly=True,
    )

    # === 约束：同一类型下 code 唯一 ===
    _sql_constraints = [
        (
            "code_type_uniq",
            "unique(code, type)",
            "同一类别下，编码必须唯一！",
        ),
    ]

    # ========= 计算字段 =========

    @api.depends("parent_id", "parent_id.level")
    def _compute_level(self):
        """自动计算层级：无上级为 1，有上级在其基础上 +1。"""
        for rec in self:
            if rec.parent_id:
                rec.level = (rec.parent_id.level or 1) + 1
            else:
                rec.level = 1

    @api.depends("name", "parent_id", "parent_id.full_name")
    def _compute_full_name(self):
        """全路径名称：父级 full_name + ' / ' + 自己的 name。"""
        for rec in self:
            if rec.parent_id:
                parent_label = rec.parent_id.full_name or rec.parent_id.name or ""
                rec.full_name = f"{parent_label} / {rec.name or ''}"
            else:
                rec.full_name = rec.name or ""

    @api.depends(
        "type",
        "parent_id",
        "parent_id.type",
        "parent_id.parent_id",
        "parent_id.parent_id.type",
        "parent_id.parent_id.parent_id",
        "parent_id.parent_id.parent_id.type",
    )
    def _compute_hierarchy_refs(self):
        """为子目回填所属的专业/章节，方便列表分组与筛选。"""
        for rec in self:
            discipline = False
            chapter = False
            if rec.type == "sub_item" and rec.parent_id:
                node = rec.parent_id
                for _ in range(4):
                    if not node:
                        break
                    if node.type == "discipline" and not discipline:
                        discipline = node
                    elif node.type == "chapter" and not chapter:
                        chapter = node
                    node = node.parent_id
            rec.discipline_id = discipline
            rec.chapter_id = chapter

    # ========= 业务校验 =========

    @api.constrains("type", "parent_id")
    def _check_hierarchy_type(self):
        """
        简单的类型层级规则（后续可根据需要再调整）：
        - 专业（discipline）：不允许有上级
        - 章节（chapter）：上级必须是 专业
        - 定额项目（quota_item）：上级必须是 章节
        - 子目（sub_item）：上级必须是 章节 或 定额项目（支持三层/四层定额）
        其它老类型暂不强制校验，保持兼容。
        """
        for rec in self:
            if not rec.parent_id:
                if rec.type in ("chapter", "quota_item", "sub_item"):
                    raise ValidationError("章节/定额项目/子目必须指定上级条目。")
                continue

            p_type = rec.parent_id.type
            if rec.type == "discipline":
                raise ValidationError("“专业”不应设置上级条目。")
            elif rec.type == "chapter" and p_type != "discipline":
                raise ValidationError("“章节”的上级必须是“专业”。")
            elif rec.type == "quota_item" and p_type != "chapter":
                raise ValidationError("“定额项目”的上级必须是“章节”。")
            elif rec.type == "sub_item" and p_type not in ("quota_item", "chapter"):
                raise ValidationError("“子目”的上级必须是“章节”或“定额项目”。")

    # === 定额子目字段（type = 'sub_item' 时有效） ===
    quota_code = fields.Char("定额编号")
    uom_id = fields.Many2one("uom.uom", string="单位")
    price_total = fields.Float("综合单价")
    price_direct = fields.Float("直接费")
    price_labor = fields.Float("人工费")
    price_material = fields.Float("材料费")
    price_machine = fields.Float("机械费")
    amount_misc = fields.Float("综合费/附加费")
    rate_misc = fields.Float("费率")
    work_content = fields.Text("工作内容")
    raw_line = fields.Text("原始行数据(JSON)")

    # ========= 前端定额中心辅助 =========
    def action_open_quota_center(self):
        """打开左树右明细的定额中心。"""
        return {
            "type": "ir.actions.client",
            "tag": "project_quota_center",
            "name": "定额中心",
        }

    @api.model
    def get_quota_tree(self):
        """前端左侧树：返回定额体系节点（专业-章节-项目-子目）。"""
        # 左侧树仅展示分类层级，避免一次性加载全部子目导致前端卡顿
        records = self.search(
            [("type", "in", ("discipline", "chapter", "quota_item")), ("active", "=", True)],
            order="parent_path",
        )

        def to_node(rec):
            return {
                "id": rec.id,
                "name": rec.name,
                "type": rec.type,
                "quota_code": rec.quota_code,
                "parent_id": rec.parent_id.id or False,
                "has_children": bool(rec.child_ids),
            }

        return [to_node(r) for r in records]

    @api.model
    def get_quota_domain_by_node(self, node_id):
        """根据左树节点返回右侧子目列表的 domain。"""
        if not node_id:
            return [("type", "=", "sub_item")]

        node = self.browse(node_id)
        if not node:
            return [("type", "=", "sub_item")]

        if node.type == "discipline":
            return [("type", "=", "sub_item"), ("discipline_id", "=", node.id)]
        if node.type == "chapter":
            return [("type", "=", "sub_item"), ("chapter_id", "child_of", node.id)]
        # quota_item 或 sub_item
        return [("type", "=", "sub_item"), ("parent_id", "child_of", node.id)]

    @api.model
    def get_quota_search_domain(self, node_id=None, search_term=None, only_active=False):
        """统一构造定额中心的搜索 domain，避免前端拼装出非法结构。"""
        base = self.get_quota_domain_by_node(node_id) if node_id else [("type", "=", "sub_item")]

        if only_active:
            base = expression.AND([base, [("active", "=", True)]])

        term = (search_term or "").strip()
        if not term:
            return base

        tokens = [t for t in term.split() if t]
        if not tokens:
            return base

        token_domains = [["|", ("quota_code", "ilike", t), ("name", "ilike", t)] for t in tokens]
        search_domain = token_domains[0]
        for td in token_domains[1:]:
            search_domain = expression.AND([search_domain, td])

        return expression.AND([base, search_domain])
