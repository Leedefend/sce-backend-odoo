# -*- coding: utf-8 -*-
from collections import defaultdict

from odoo import models, fields, api
from odoo.exceptions import UserError


# =========================
# 工程结构 / 清单
# =========================
class ScProjectStructure(models.Model):
    _name = 'sc.project.structure'
    _description = '项目工程结构（WBS）'
    _parent_name = 'parent_id'
    _parent_store = True
    _order = 'project_id, parent_path, sequence, id'

    name = fields.Char('名称', required=True)
    code = fields.Char('编码', index=True)
    project_id = fields.Many2one(
        'project.project', '项目',
        required=True, index=True, ondelete='cascade'
    )
    parent_id = fields.Many2one(
        'sc.project.structure', '上级结构',
        index=True, ondelete='cascade'
    )
    child_ids = fields.One2many(
        'sc.project.structure', 'parent_id',
        string='下级节点'
    )
    parent_path = fields.Char(index=True)

    sequence = fields.Integer('排序', default=10)
    level = fields.Integer('层级', compute='_compute_level', store=True)
    structure_type = fields.Selection(
        [
            ('single', '单项工程'),
            ('unit', '单位工程'),
            ('division', '分部工程'),
            ('subdivision', '分项工程'),
            ('item', '清单项目'),
        ],
        string='结构类型',
        default='item',
        index=True,
    )

    boq_line_ids = fields.One2many(
        'project.boq.line', 'structure_id',
        string='清单行'
    )

    qty_total = fields.Float('汇总工程量', compute='_compute_totals', store=True)
    amount_total = fields.Monetary('汇总合价', compute='_compute_totals', store=True)
    currency_id = fields.Many2one(
        'res.currency',
        related='project_id.company_id.currency_id',
        readonly=True,
        store=True,
    )

    @api.depends('parent_id.level')
    def _compute_level(self):
        for rec in self:
            rec.level = (rec.parent_id.level or 0) + 1 if rec.parent_id else 1

    @api.depends(
        'boq_line_ids.quantity',
        'boq_line_ids.amount',
        'child_ids.qty_total',
        'child_ids.amount_total',
    )
    def _compute_totals(self):
        """自下而上汇总工程量与合价。"""
        for node in self:
            if node.structure_type == 'item':
                qty = sum(node.boq_line_ids.mapped('quantity'))
                amt = sum(node.boq_line_ids.mapped('amount'))
            else:
                qty = sum(node.child_ids.mapped('qty_total'))
                amt = sum(node.child_ids.mapped('amount_total'))
            node.qty_total = qty
            node.amount_total = amt


# =========================
# 项目阶段定义
# =========================
class ProjectProjectStage(models.Model):
    _inherit = "project.project.stage"
    _description = "项目阶段"
    _order = "sequence, id"

    
    is_default = fields.Boolean("默认阶段", default=False)
    description = fields.Text("说明")
    mail_template_id = fields.Many2one(
        "mail.template",
        string="阶段通知模板",
        help="当项目进入该阶段时可用于通知的邮件模板。"
    )

# =========================
# 项目扩展
# =========================
class ProjectProject(models.Model):
    _inherit = 'project.project'

    # ---------- 默认阶段 ----------
    def _default_stage_id(self):
        stage = self.env['project.project.stage'].search(
            [('is_default', '=', True)], limit=1
        )
        return stage.id

    # ---------- 基础属性 ----------
    project_code = fields.Char(
        '项目编号',
        default='新项目',
        copy=False,
        tracking=True,
        readonly=True,
    )
    project_type_id = fields.Many2one(
        'sc.dictionary', string='项目类型',
        domain=[('type', '=', 'project_type')]
    )
    project_category_id = fields.Many2one(
        'sc.dictionary', string='项目类别',
        domain=[('type', '=', 'project_category')]
    )
    stage_id = fields.Many2one(
        'project.project.stage',
        string='阶段',
        default=_default_stage_id,
        required=True,
        tracking=True,
    )
    owner_id = fields.Many2one('res.partner', string='业主单位')
    owner_contact = fields.Char('业主联系人')
    manager_id = fields.Many2one('res.users', string='项目经理')
    cost_manager_id = fields.Many2one('res.users', string='成本负责人')
    doc_manager_id = fields.Many2one('res.users', string='资料负责人')
    location = fields.Char('项目地点')
    contract_no = fields.Char('主合同编号')

    start_date = fields.Date('计划开工日期')
    end_date = fields.Date('计划竣工日期')

    lifecycle_state = fields.Selection(
        [
            ('draft', '立项'),
            ('in_progress', '在建'),
            ('paused', '停工'),
            ('done', '竣工'),
            ('closing', '结算中'),
            ('warranty', '保修期'),
            ('closed', '关闭'),
        ],
        string='项目状态',
        default='draft',
        tracking=True,
        help='驱动项目级联动控制：暂停/关闭禁止新增进度、成本等业务数据；结算中限制部分操作。'
    )
    phase_key = fields.Selection(
        [
            ('initiation', '立项阶段'),
            ('execution', '执行阶段'),
            ('settlement', '结算阶段'),
            ('finance', '资金阶段'),
            ('archive', '资料归档'),
        ],
        string='项目阶段',
        tracking=True,
        help='用于对齐 WBS / 财务节点的阶段标识，可结合审批流与报表过滤使用。'
    )

    responsibility_ids = fields.One2many(
        'project.responsibility', 'project_id',
        string='责任矩阵'
    )

    # ---------- 成本与进度总控 ----------
    company_currency_id = fields.Many2one(
        'res.currency', string='公司本位币',
        related='company_id.currency_id',
        store=True, readonly=True
    )

    budget_total = fields.Monetary(
        '目标成本(预算)', currency_field='company_currency_id',
        help='项目立项时确定的目标成本总额。'
    )
    cost_committed = fields.Monetary(
        '已承诺成本', currency_field='company_currency_id',
        help='已通过合同/订单等形式锁定的成本。'
    )
    cost_actual = fields.Monetary(
        '已发生成本', currency_field='company_currency_id',
        help='已实际记账的成本。'
    )
    cost_variance = fields.Monetary(
        '成本差异', currency_field='company_currency_id',
        compute='_compute_costs', store=True
    )

    plan_percent = fields.Float(
        '计划完成率(%)',
        help='结合工期或产值计划给出的阶段性目标完成率。'
    )
    actual_percent = fields.Float(
        '实际完成率(%)',
        help='结合工程量计量或节点验收计算出的真实进度。'
    )

    # ---------- 项目维度：预算/成本/进度/WBS/BOQ ----------
    budget_ids = fields.One2many(
        'project.budget', 'project_id',
        string='预算版本'
    )
    cost_ledger_ids = fields.One2many(
        'project.cost.ledger', 'project_id',
        string='成本台账'
    )
    tender_bid_ids = fields.One2many(
        'tender.bid', 'project_id',
        string='投标记录'
    )
    progress_entry_ids = fields.One2many(
        'project.progress.entry', 'project_id',
        string='进度计量'
    )
    work_ids = fields.One2many(
        'construction.work.breakdown', 'project_id',
        string='工程结构'
    )
    boq_line_ids = fields.One2many(
        'project.boq.line', 'project_id',
        string='工程量清单'
    )
    structure_ids = fields.One2many(
        'sc.project.structure', 'project_id',
        string='工程结构（WBS）'
    )
    wbs_count = fields.Integer(
        '工程结构数', compute='_compute_wbs_count'
    )
    boq_amount_total = fields.Monetary(
        '清单总额', currency_field='company_currency_id',
        compute='_compute_boq_stats', store=True
    )
    boq_amount_building = fields.Monetary(
        '建筑工程额', currency_field='company_currency_id',
        compute='_compute_boq_stats', store=True
    )
    boq_amount_installation = fields.Monetary(
        '安装工程额', currency_field='company_currency_id',
        compute='_compute_boq_stats', store=True
    )

    # ---------- 成本控制衍生指标 ----------
    budget_active_id = fields.Many2one(
        'project.budget', string='当前预算',
        compute='_compute_cost_control_stats', readonly=True
    )
    budget_active_cost_target = fields.Monetary(
        '当前预算成本', currency_field='company_currency_id',
        compute='_compute_cost_control_stats', readonly=True
    )
    budget_active_revenue_target = fields.Monetary(
        '当前预算收入', currency_field='company_currency_id',
        compute='_compute_cost_control_stats', readonly=True
    )
    budget_count = fields.Integer(
        '预算版本数', compute='_compute_cost_control_stats'
    )
    cost_ledger_amount_actual = fields.Monetary(
        '台账实际成本', currency_field='company_currency_id',
        compute='_compute_cost_control_stats', readonly=True
    )
    cost_ledger_entry_count = fields.Integer(
        '台账记录数', compute='_compute_cost_control_stats'
    )
    cost_budget_gap = fields.Monetary(
        '预算差异(台账)', currency_field='company_currency_id',
        compute='_compute_cost_control_stats', readonly=True,
        help='当前预算成本与台账实际成本之间的差值。'
    )
    progress_entry_count = fields.Integer(
        '进度记录数', compute='_compute_cost_control_stats'
    )
    progress_rate_latest = fields.Float(
        '最新进度(%)', compute='_compute_cost_control_stats',
        help='取项目进度计量记录中最新/最大完成率。'
    )

    # ---------- 工程资料维度 ----------
    document_ids = fields.One2many(
        'sc.project.document', 'project_id',
        string='工程资料'
    )
    wbs_ids = fields.One2many(
        'construction.work.breakdown', 'project_id',
        string='工程结构'
    )
    tender_count = fields.Integer(
        '投标数', compute='_compute_tender_stats'
    )
    document_count = fields.Integer(
        '资料数量', compute='_compute_document_stats'
    )
    document_required_count = fields.Integer(
        '必备资料数', compute='_compute_document_stats'
    )
    document_missing_count = fields.Integer(
        '缺失必备资料', compute='_compute_document_stats'
    )
    document_completion_rate = fields.Float(
        '资料完备率(%)', compute='_compute_document_stats', readonly=True
    )

    # ---------- 合同 & 驾驶舱指标 ----------
    contract_amount = fields.Monetary(
        '合同总额', currency_field='company_currency_id',
        compute='_compute_contract_stats', readonly=True
    )
    subcontract_amount = fields.Monetary(
        '分包合同金额', currency_field='company_currency_id',
        compute='_compute_contract_stats', readonly=True
    )
    dashboard_revenue_actual = fields.Monetary(
        '实际收入', currency_field='company_currency_id',
        compute='_compute_dashboard_overview', readonly=True
    )
    dashboard_cost_actual = fields.Monetary(
        '实际成本', currency_field='company_currency_id',
        compute='_compute_dashboard_overview', readonly=True
    )
    dashboard_profit_actual = fields.Monetary(
        '项目毛利', currency_field='company_currency_id',
        compute='_compute_dashboard_overview', readonly=True
    )
    dashboard_invoice_amount = fields.Monetary(
        '已开票金额', currency_field='company_currency_id',
        compute='_compute_dashboard_overview', readonly=True
    )
    dashboard_payment_in = fields.Monetary(
        '收款申请金额', currency_field='company_currency_id',
        compute='_compute_dashboard_overview', readonly=True
    )
    dashboard_payment_out = fields.Monetary(
        '付款申请金额', currency_field='company_currency_id',
        compute='_compute_dashboard_overview', readonly=True
    )
    dashboard_document_completion = fields.Float(
        '资料完备率(%)', compute='_compute_dashboard_overview', readonly=True
    )
    dashboard_progress_rate = fields.Float(
        '驾驶舱进度(%)', compute='_compute_dashboard_overview', readonly=True
    )

    _sql_constraints = [
        ('project_code_unique', 'unique(project_code)', '项目编号不能重复。'),
    ]

    # ---------- 小工具：统一打开项目相关 action ----------
    def _action_open_related(self, xml_id, domain=None, extra_context=None):
        """统一封装打开与当前项目相关的 Action."""
        self.ensure_one()
        action = self.env.ref(xml_id).read()[0]

        # domain：默认过滤当前项目
        base_domain = [('project_id', '=', self.id)]
        if domain:
            base_domain += domain
        action['domain'] = base_domain

        # context：统一注入默认/搜索项目
        ctx = dict(self._context or {})
        ctx.setdefault('default_project_id', self.id)
        ctx.setdefault('search_default_project_id', self.id)
        if extra_context:
            ctx.update(extra_context)
        action['context'] = ctx
        return action

    # ---------- 成本差异 ----------
    @api.depends('budget_total', 'cost_actual')
    def _compute_costs(self):
        for project in self:
            project.cost_variance = (project.budget_total or 0.0) - (project.cost_actual or 0.0)

    # ---------- 创建/初始化 ----------
    @api.model_create_multi
    def create(self, vals_list):
        sequence = self.env['ir.sequence']
        default_stage = self._default_stage_id()
        for vals in vals_list:
            if not vals.get('project_code'):
                vals['project_code'] = sequence.next_by_code('project.project.code') or '新项目'
            if not vals.get('stage_id') and default_stage:
                vals['stage_id'] = default_stage
            if not vals.get('lifecycle_state'):
                vals['lifecycle_state'] = 'draft'
        return super().create(vals_list)

    def init(self):
        # 确保老项目也有默认阶段
        res = super().init()
        default_stage = self._default_stage_id()
        if default_stage:
            projects = self.env['project.project'].search([('stage_id', '=', False)])
            if projects:
                projects.write({'stage_id': default_stage})
        return res

    # ---------- 工程量清单统计 ----------
    @api.depends('boq_line_ids.amount', 'boq_line_ids.section_type')
    def _compute_boq_stats(self):
        amount_map = {}
        install_map = {}
        build_map = {}

        if self.ids:
            BoqLine = self.env['project.boq.line']
            data = BoqLine.read_group(
                [('project_id', 'in', self.ids)],
                ['amount:sum'],
                ['project_id', 'section_type']
            )
            for rec in data:
                project_id = rec['project_id'][0]
                amount = rec.get('amount_sum', rec.get('amount', 0.0)) or 0.0
                section = rec.get('section_type') or ''
                amount_map[project_id] = amount_map.get(project_id, 0.0) + amount
                if section == 'building':
                    build_map[project_id] = build_map.get(project_id, 0.0) + amount
                if section == 'installation':
                    install_map[project_id] = install_map.get(project_id, 0.0) + amount

        for project in self:
            project.boq_amount_total = amount_map.get(project.id, 0.0)
            project.boq_amount_building = build_map.get(project.id, 0.0)
            project.boq_amount_installation = install_map.get(project.id, 0.0)

    # ---------- 工程资料统计 ----------
    @api.depends('document_ids.is_mandatory', 'document_ids.state')
    def _compute_document_stats(self):
        for project in self:
            docs = project.document_ids
            project.document_count = len(docs)

            required_docs = docs.filtered(lambda d: d.is_mandatory)
            project.document_required_count = len(required_docs)

            missing = len(required_docs.filtered(lambda d: d.state != 'done'))
            project.document_missing_count = missing

            if project.document_required_count:
                done = project.document_required_count - missing
                project.document_completion_rate = done / project.document_required_count * 100.0
            else:
                project.document_completion_rate = 100.0 if project.document_count else 0.0

    # ---------- 成本控制 & 进度衍生指标 ----------
    @api.depends(
        'budget_ids.is_active',
        'budget_ids.amount_cost_target',
        'budget_ids.amount_revenue_target',
        'cost_ledger_ids.amount',
        'progress_entry_ids.progress_rate'
    )
    def _compute_cost_control_stats(self):
        ledger_amount_map = {}
        ledger_count_map = {}
        progress_rate_map = {}
        progress_count_map = {}

        if self.ids:
            # 成本台账汇总
            ledger_read = self.env['project.cost.ledger'].read_group(
                [('project_id', 'in', self.ids)],
                ['amount:sum'],
                ['project_id']
            )
            for rec in ledger_read:
                project_id = rec['project_id'][0]
                ledger_amount_map[project_id] = rec.get('amount_sum', rec.get('amount', 0.0)) or 0.0
                ledger_count_map[project_id] = rec.get('__count', 0)

            # 进度记录汇总（取最大进度）
            progress_read = self.env['project.progress.entry'].read_group(
                [('project_id', 'in', self.ids)],
                ['progress_rate:max'],
                ['project_id']
            )
            for rec in progress_read:
                project_id = rec['project_id'][0]
                progress_rate_map[project_id] = rec.get('progress_rate_max', rec.get('progress_rate', 0.0)) or 0.0
                progress_count_map[project_id] = rec.get('__count', 0)

        for project in self:
            budgets = project.budget_ids
            active_budget = budgets.filtered(lambda b: b.is_active)
            if not active_budget:
                active_budget = budgets
            active_budget = active_budget.sorted(
                key=lambda b: (b.version_date or b.create_date or fields.Date.today()),
                reverse=True
            )[:1]
            budget_rec = active_budget[:1]

            project.budget_active_id = budget_rec.id if budget_rec else False
            project.budget_active_cost_target = budget_rec.amount_cost_target if budget_rec else 0.0
            project.budget_active_revenue_target = budget_rec.amount_revenue_target if budget_rec else 0.0
            project.budget_count = len(budgets)

            ledger_amount = ledger_amount_map.get(project.id, 0.0) or 0.0
            project.cost_ledger_amount_actual = ledger_amount
            project.cost_ledger_entry_count = ledger_count_map.get(project.id, 0)
            project.cost_budget_gap = (project.budget_active_cost_target or 0.0) - ledger_amount

            project.progress_entry_count = progress_count_map.get(project.id, 0)
            project.progress_rate_latest = progress_rate_map.get(project.id, 0.0)

    # ---------- 驾驶舱汇总 ----------
    @api.depends(
        'cost_ledger_ids.amount',
        'document_ids.is_mandatory',
        'document_ids.state',
        'progress_rate_latest',
    )
    def _compute_dashboard_overview(self):
        revenue_map = defaultdict(float)
        invoice_model = self.env['account.move.line']
        move_model = self.env['account.move']

        # 收入 & 开票金额（按项目汇总收入科目 / 发票金额）
        if self.ids:
            # --- 行级收入汇总 ---
            invoice_domain = [
                ('project_id', 'in', self.ids),
                ('move_id.state', '=', 'posted'),
                ('move_id.move_type', 'in', ['out_invoice', 'out_refund']),
                '|',
                ('account_id.internal_group', '=', 'income'),
                ('account_id.account_type', '=', 'income'),
            ]
            invoice_read = invoice_model.read_group(
                invoice_domain,
                ['balance:sum'],
                ['project_id']
            )
            revenue_line_map = {}
            for rec in invoice_read:
                project = rec.get('project_id')
                if not project:
                    continue
                project_id = project[0]
                balance_val = rec.get('balance_sum', rec.get('balance', 0.0)) or 0.0
                # 收入科目 balance 为负数，这里转正
                revenue_line_map[project_id] = revenue_line_map.get(project_id, 0.0) - balance_val

            # --- 发票级兜底（避免行级未带 project 或科目未归类收入） ---
            move_read = move_model.read_group(
                [
                    ('project_id', 'in', self.ids),
                    ('state', '=', 'posted'),
                    ('move_type', 'in', ['out_invoice', 'out_refund']),
                ],
                ['amount_total_signed:sum'],
                ['project_id']
            )
            revenue_move_map = {}
            for rec in move_read:
                project_id = rec['project_id'][0]
                revenue_move_map[project_id] = rec.get('amount_total_signed_sum', rec.get('amount_total_signed', 0.0)) or 0.0

            # 组合：优先行级（更精准），若为 0 则使用发票级；两者均有值则行级+发票级（通常发票级仅在行级缺失时有值）
            for pid in self.ids:
                line_val = revenue_line_map.get(pid, 0.0)
                move_val = revenue_move_map.get(pid, 0.0)
                if line_val:
                    revenue_map[pid] += line_val
                if not line_val and move_val:
                    revenue_map[pid] += move_val

        # 收/付款申请金额
        payment_in_map = defaultdict(float)
        payment_out_map = defaultdict(float)
        if self.ids and 'payment.request' in self.env:
            payment_read = self.env['payment.request'].read_group(
                [
                    ('project_id', 'in', self.ids),
                    ('state', '=', 'done'),
                ],
                ['amount:sum'],
                ['project_id', 'type']
            )
            for rec in payment_read:
                project_id = rec['project_id'][0]
                amount = rec['amount_sum'] or 0.0
                if rec['type'] == 'receive':
                    payment_in_map[project_id] += amount
                else:
                    payment_out_map[project_id] += amount

        for project in self:
            cost_val = project.cost_ledger_amount_actual or 0.0
            revenue_val = revenue_map.get(project.id, 0.0)

            project.dashboard_cost_actual = cost_val
            project.dashboard_revenue_actual = revenue_val
            project.dashboard_invoice_amount = revenue_val
            project.dashboard_profit_actual = revenue_val - cost_val
            project.dashboard_payment_in = payment_in_map.get(project.id, 0.0)
            project.dashboard_payment_out = payment_out_map.get(project.id, 0.0)
            project.dashboard_document_completion = project.document_completion_rate
            project.dashboard_progress_rate = project.progress_rate_latest or 0.0

    # ---------- WBS / 投标统计 ----------
    @api.depends('structure_ids')
    def _compute_wbs_count(self):
        for project in self:
            project.wbs_count = len(project.structure_ids)

    @api.depends('tender_bid_ids')
    def _compute_tender_stats(self):
        for project in self:
            project.tender_count = len(project.tender_bid_ids)

    # ========== Action 打开各种子模块 ==========
    def action_open_project_budget(self):
        return self._action_open_related('smart_construction_core.action_project_budget')

    def action_open_project_cost_ledger(self):
        return self._action_open_related('smart_construction_core.action_project_cost_ledger')

    def action_open_project_progress_entry(self):
        return self._action_open_related('smart_construction_core.action_project_progress_entry')

    def action_open_cost_compare(self):
        return self._action_open_related('smart_construction_core.action_project_cost_compare')

    def action_open_profit_compare(self):
        return self._action_open_related('smart_construction_core.action_project_profit_compare')

    def action_open_wbs(self):
        self.ensure_one()
        action = self.env.ref('smart_construction_core.action_sc_project_structure').read()[0]
        action['domain'] = [('project_id', '=', self.id)]
        action['context'] = {'default_project_id': self.id}
        return action

    def action_open_boq_import(self):
        """Open BOQ import wizard with current project prefilled."""
        self.ensure_one()
        action = self.env.ref('smart_construction_core.action_project_boq_import_wizard').read()[0]
        action['context'] = {'default_project_id': self.id}
        return action

    def action_generate_structure_from_boq(self):
        """
        从工程量清单自动生成工程结构（WBS）
        规则（v1）：
          - 单项工程/单位工程来自清单行（导入表头解析）
          - 编码支持定长分段（默认 2/4/6/9/12）或点分层级
          - 生成层级：单项 → 单位 → 分部 → 分项工程（= 清单行）
          - 叶子节点 = 每条 12 位清单编码，对应清单行
        """
        Structure = self.env['sc.project.structure']

        def _get_or_create(project_id, s_type, code_val, name_val, parent_node, struct_map, seq=10):
            """按类型+编码/名称幂等获取节点。"""
            key = (project_id, s_type, code_val or name_val)
            node = struct_map.get(key)
            if not node:
                node = Structure.create({
                    'project_id': project_id,
                    'parent_id': parent_node.id if parent_node else False,
                    'structure_type': s_type,
                    'code': code_val or False,
                    'name': name_val,
                    'sequence': seq,
                })
                struct_map[key] = node
            else:
                # 若已有分部节点但名称仍是编码，且有更友好的名称可用，则更新
                if s_type == 'division' and code_val and name_val and node.name == node.code and node.name != name_val:
                    node.name = name_val
            return node

        def _division_from_line(line):
            """优先取字段，其次从备注中提取“[分部]xxx”"""
            if line.division_name:
                return line.division_name
            remark = (line.remark or '')
            if '[分部]' in remark:
                parts = remark.split('[分部]', 1)[1]
                # 截断后续标点
                for sep in ['；', ';', '，', ',', ' ']:
                    parts = parts.split(sep)[0]
                return parts.strip() or False
            return False

        for project in self:
            lines = project.boq_line_ids.filtered(lambda l: (l.code or '').strip())
            if not lines:
                continue

            # 预先收集分部编码 -> 分部名称映射，优先使用导入时的分部标题
            division_name_map = {}
            for ln in lines:
                div_name = _division_from_line(ln)
                if ln.code_division and div_name:
                    division_name_map[ln.code_division] = div_name

            existing = Structure.search([('project_id', '=', project.id)])
            struct_map = {
                (s.project_id.id, s.structure_type, s.code or s.name): s for s in existing
            }
            skipped = []

            for ln in lines:
                code = (ln.code or '').strip()
                if not code:
                    skipped.append('(空编码)')
                    continue

                # 单项/单位工程节点
                single_name = (ln.single_name or '').strip() or (ln.code_cat or '未分类单项工程')
                unit_name = (ln.unit_name or '').strip() or '未分类单位工程'
                node_single = _get_or_create(project.id, 'single', False, single_name, False, struct_map, seq=5)
                node_unit = _get_or_create(project.id, 'unit', False, unit_name, node_single, struct_map, seq=10)

                # 清单编码分段（按 12 位标准）
                if not (ln.code_item and len(ln.code_item) == 12):
                    skipped.append(code)
                    continue

                # 直接按“分部 -> 分项工程(清单行)”两级建树
                segments = [
                    (ln.code_division, 'division'),
                    (ln.code_item, 'item'),
                ]

                parent = node_unit
                for idx, (seg_code, s_type) in enumerate(segments):
                    if not seg_code:
                        continue
                    if s_type == 'item':
                        node_name = ln.name
                    elif s_type == 'division':
                        node_name = division_name_map.get(seg_code) or ln.division_name or seg_code
                    else:
                        node_name = seg_code
                    parent = _get_or_create(project.id, s_type, seg_code, node_name, parent, struct_map, seq=20 + idx)

                if parent and ln.structure_id != parent:
                    ln.structure_id = parent.id

            if skipped:
                project.message_post(
                    body=("生成工程结构时跳过以下编码（格式不符合规则或段解析为空）：<br/>%s"
                          % "<br/>".join(skipped))
                )

        return True

    def action_generate_wbs_from_boq(self):
        """兼容命名：调用标准 WBS 生成逻辑。"""
        return self.action_generate_structure_from_boq()

    # ---------- 项目治理 / 流程控制 ----------
    def _ensure_operation_allowed(self, operation_label="该操作", blocked_states=None):
        """在项目层面做统一的流程闸口控制。"""
        blocked_states = blocked_states or ('paused', 'closed')
        state_label = dict(self._fields['lifecycle_state'].selection)
        for project in self:
            if project.lifecycle_state in blocked_states:
                raise UserError(
                    f"项目[{project.display_name}] 当前处于“{state_label.get(project.lifecycle_state, project.lifecycle_state)}”状态，"
                    f"不允许执行{operation_label}。"
                )

    def action_set_state(self, target_state):
        """轻量状态切换入口，便于在表单按钮中调用。"""
        allowed = [key for key, _ in self._fields['lifecycle_state'].selection]
        if target_state not in allowed:
            raise UserError("无效的项目状态。")
        self.write({'lifecycle_state': target_state})
        return True


# =========================
# 项目责任矩阵
# =========================
class ProjectResponsibility(models.Model):
    _name = 'project.responsibility'
    _description = '项目责任矩阵'
    _order = 'project_id, role_key, id'

    project_id = fields.Many2one(
        'project.project', string='项目',
        required=True, index=True, ondelete='cascade'
    )
    company_id = fields.Many2one(
        'res.company', string='公司',
        related='project_id.company_id',
        store=True, readonly=True
    )
    role_key = fields.Selection(
        [
            ('manager', '项目经理'),
            ('cost', '成本负责人'),
            ('finance', '财务'),
            ('cashier', '出纳'),
            ('material', '材料员'),
            ('safety', '安全员'),
            ('quality', '质检员'),
            ('document', '资料员'),
        ],
        string='角色',
        required=True,
    )
    user_id = fields.Many2one(
        'res.users', string='责任人',
        required=True, index=True
    )
    note = fields.Char('说明/授权范围')

    _sql_constraints = [
        (
            'project_role_unique',
            'unique(project_id, role_key)',
            '同一项目下每个角色仅允许指派一人。'
        )
    ]
