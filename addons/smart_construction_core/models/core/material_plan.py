# -*- coding: utf-8 -*-
import logging

from odoo import _, api, fields, models
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class ProjectMaterialPlan(models.Model):
    _name = "project.material.plan"
    _description = "物资计划"
    _inherit = ["mail.thread", "mail.activity.mixin", "tier.validation"]
    _order = "id desc"

    name = fields.Char("单号", default="新建", copy=False, readonly=True)
    project_id = fields.Many2one("project.project", string="项目", required=True, index=True)
    business_category_id = fields.Many2one(
        "sc.business.category",
        string="业务分类",
        index=True,
        ondelete="restrict",
        domain="[('target_model', '=', 'project.material.plan')]",
    )
    company_id = fields.Many2one(
        "res.company",
        string="公司",
        related="project_id.company_id",
        store=True,
        readonly=True,
    )
    date_plan = fields.Date("需用日期")
    total_plan_qty = fields.Float(string="计划数量", compute="_compute_plan_totals", store=True)
    total_bill_qty = fields.Float(string="清单数量", compute="_compute_plan_totals", store=True)
    total_unplanned_qty = fields.Float(string="未计划数量", compute="_compute_plan_totals", store=True)
    material_name_summary = fields.Char(string="材料名称", compute="_compute_line_summaries", store=True)
    material_spec_summary = fields.Char(string="规格型号", compute="_compute_line_summaries", store=True)
    material_uom_summary = fields.Char(string="单位", compute="_compute_line_summaries", store=True)
    line_note_summary = fields.Char(string="备注", compute="_compute_line_summaries", store=True)
    line_attachment_count = fields.Integer(string="附件数", compute="_compute_line_summaries", store=True)
    attachment_ids = fields.Many2many(
        "ir.attachment",
        "project_material_plan_attachment_rel",
        "plan_id",
        "attachment_id",
        string="附件",
    )
    state = fields.Selection(
        [
            ("draft", "草稿"),
            ("submit", "已提交"),
            ("approved", "已批准"),
            ("done", "已完成"),
            ("cancel", "已取消"),
        ],
        default="draft",
        string="状态",
        tracking=True,
        index=True,
    )

    line_ids = fields.One2many("project.material.plan.line", "plan_id", string="计划明细")
    legacy_fact_model = fields.Char(string="来源通用模型", index=True)
    legacy_fact_id = fields.Integer(string="来源通用记录ID", index=True)
    legacy_fact_type = fields.Char(string="来源业务类型", index=True)

    submitted_by = fields.Many2one("res.users", string="提交人", readonly=True, tracking=True)
    submitted_at = fields.Datetime(string="提交时间", readonly=True, tracking=True)
    approved_by = fields.Many2one("res.users", string="批准人", readonly=True, tracking=True)
    approved_at = fields.Datetime(string="批准时间", readonly=True, tracking=True)
    reject_reason = fields.Char(string="驳回原因", readonly=True, tracking=True)

    purchase_order_count = fields.Integer("采购单", compute="_compute_po_counts")
    purchase_line_count = fields.Integer("采购明细", compute="_compute_po_counts")
    purchase_request_count = fields.Integer("采购申请", compute="_compute_purchase_request_count")

    _sql_constraints = [
        (
            "legacy_material_plan_unique",
            "unique(legacy_fact_model, legacy_fact_id)",
            "来源通用材料计划已迁移为材料计划。",
        ),
    ]

    def _resolve_business_category_id(self, vals):
        code = self.env.context.get("default_business_category_code") or self.env.context.get(
            "current_business_category_code"
        ) or "material.plan"
        category = self.env["sc.business.category"].sudo().search(
            [("code", "=", code), ("target_model", "=", "project.material.plan")],
            limit=1,
        )
        return category.id if category else False

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals.setdefault("business_category_id", self._resolve_business_category_id(vals))
        return super().create(vals_list)

    def init(self):
        self.env.cr.execute(
            """
            UPDATE project_material_plan plan
               SET business_category_id = category.id
              FROM sc_business_category category
             WHERE plan.business_category_id IS NULL
               AND category.code = 'material.plan'
               AND category.target_model = 'project.material.plan'
            """
        )

    @api.depends("line_ids.quantity", "line_ids.bill_qty")
    def _compute_plan_totals(self):
        for rec in self:
            planned = sum(rec.line_ids.mapped("quantity"))
            bill = sum(rec.line_ids.mapped("bill_qty"))
            rec.total_plan_qty = planned
            rec.total_bill_qty = bill
            rec.total_unplanned_qty = max(bill - planned, 0.0)

    @api.depends(
        "line_ids.material_name",
        "line_ids.spec",
        "line_ids.spec_model",
        "line_ids.uom_id",
        "line_ids.material_uom_text",
        "line_ids.note",
        "line_ids.attachment_ids",
    )
    def _compute_line_summaries(self):
        for rec in self:
            rec.material_name_summary = rec._summarize_line_text(rec.line_ids.mapped("material_name"))
            rec.material_spec_summary = rec._summarize_line_text(
                line.spec_model or line.spec for line in rec.line_ids
            )
            rec.material_uom_summary = rec._summarize_line_text(
                line.material_uom_text or line.uom_id.name for line in rec.line_ids
            )
            rec.line_note_summary = rec._summarize_line_text(rec.line_ids.mapped("note"))
            rec.line_attachment_count = sum(len(line.attachment_ids) for line in rec.line_ids)

    @api.model
    def _summarize_line_text(self, values, limit=3):
        values = list(values)
        texts = []
        for value in values:
            if not value or value in texts:
                continue
            texts.append(value)
            if len(texts) >= limit:
                break
        suffix = "等" if len([value for value in values if value]) > len(texts) else ""
        return "、".join(texts) + suffix if texts else False

    def _message_post_non_blocking(self, body):
        for rec in self:
            try:
                rec.message_post(body=body)
            except Exception as exc:
                _logger.warning(
                    "Skip project.material.plan chatter message for %s: %s",
                    rec.display_name,
                    exc,
                )

    def _get_material_approver(self):
        self.ensure_one()
        # 物资负责人（若项目上有定义）
        if hasattr(self.project_id, "material_manager_id") and self.project_id.material_manager_id:
            return self.project_id.material_manager_id
        # 退化为项目负责人
        if getattr(self.project_id, "user_id", False):
            return self.project_id.user_id
        # 最后退化为当前用户
        return self.env.user

    def _normalize_lines_uom(self):
        """Validate material identity without forcing product-management semantics."""
        for line in self.line_ids:
            if not line.material_catalog_id:
                raise UserError(_("计划行缺少材料档案，请补全后再提交。"))
            line._ensure_technical_product()
            if not line.material_uom_text and line.uom_id:
                line.material_uom_text = line.uom_id.name

    def _check_business_anchor(self):
        for rec in self:
            if not rec.project_id:
                raise UserError(_("物资计划必须关联项目。"))
            if not rec.line_ids:
                raise UserError(_("请先填写物资计划明细再提交。"))
            for line in rec.line_ids:
                if not line.material_catalog_id:
                    raise UserError(_("计划行缺少材料档案，请补全后再提交。"))
                if line.quantity <= 0:
                    raise UserError(_("物资计划数量必须大于0。"))

    def _snapshot_audit_payload(self):
        self.ensure_one()
        return {
            "name": self.name,
            "state": self.state,
            "project_id": self.project_id.id if self.project_id else False,
            "line_count": len(self.line_ids),
            "total_plan_qty": float(self.total_plan_qty or 0.0),
            "total_bill_qty": float(self.total_bill_qty or 0.0),
            "total_unplanned_qty": float(self.total_unplanned_qty or 0.0),
            "submitted_by": self.submitted_by.id if self.submitted_by else False,
            "approved_by": self.approved_by.id if self.approved_by else False,
        }

    def _audit_transition(self, event_code, before, after, reason=None, action_name=None):
        self.ensure_one()
        company = self.company_id or self.env.company
        return self.env["sc.audit.log"].write_event(
            event_code=event_code,
            model=self._name,
            res_id=self.id,
            action=action_name or event_code,
            before=before,
            after=after,
            reason=reason,
            company_id=company.id if company else False,
            project_id=self.project_id.id if self.project_id else False,
        )

    def action_submit(self):
        seq = self.env["ir.sequence"]
        for rec in self:
            if rec.state != "draft":
                raise UserError(_("只有草稿状态的物资计划可以提交。"))
            if not (
                self.env.user.has_group("smart_construction_core.group_sc_cap_business_initiator")
                or self.env.user.has_group("smart_construction_core.group_sc_cap_material_user")
            ):
                raise UserError(_("你没有提交物资计划的权限。"))
            rec._check_business_anchor()
            rec._normalize_lines_uom()
            before = rec._snapshot_audit_payload()
            if rec.name == "新建":
                rec.name = seq.next_by_code("project.material.plan") or rec.name
            rec.write(
                {
                    "state": "submit",
                    "submitted_by": self.env.user.id,
                    "submitted_at": fields.Datetime.now(),
                    "reject_reason": False,
                }
            )
            rec.invalidate_recordset()
            company = rec.company_id or self.env.company
            rec.with_company(company).with_context(
                allowed_company_ids=[company.id],
            ).request_validation()
            rec._message_post_non_blocking(_("物资计划已提交，进入审批流程。"))
            rec._audit_transition(
                "material_plan_submitted",
                before,
                rec._snapshot_audit_payload(),
                action_name="action_submit",
            )

    def action_approve(self):
        for rec in self:
            if rec.state != "submit":
                raise UserError(_("只有已提交状态的物资计划可以批准。"))
            if not self.env.user.has_group("smart_construction_core.group_sc_cap_material_manager"):
                raise UserError(_("你没有审批物资计划的权限。"))
            rec._check_business_anchor()
            before = rec._snapshot_audit_payload()
            rec.write(
                {
                    "state": "approved",
                    "approved_by": self.env.user.id,
                    "approved_at": fields.Datetime.now(),
                }
            )
            rec.activity_unlink(["mail.mail_activity_data_todo"])
            rec._message_post_non_blocking(_("物资计划已批准。"))
            rec._audit_transition(
                "material_plan_approved",
                before,
                rec._snapshot_audit_payload(),
                action_name="action_approve",
            )

    def action_reject(self, reason=None):
        for rec in self:
            if rec.state != "submit":
                raise UserError(_("只有已提交状态的物资计划可以驳回。"))
            if not self.env.user.has_group("smart_construction_core.group_sc_cap_material_manager"):
                raise UserError(_("你没有驳回物资计划的权限。"))
            before = rec._snapshot_audit_payload()
            rec.activity_unlink(["mail.mail_activity_data_todo"])
            rec.write(
                {
                    "state": "draft",
                    "reject_reason": reason or _("未填写原因"),
                }
            )
            rec._message_post_non_blocking(_("物资计划被驳回：%s") % rec.reject_reason)
            rec._audit_transition(
                "material_plan_rejected",
                before,
                rec._snapshot_audit_payload(),
                reason=rec.reject_reason,
                action_name="action_reject",
            )

    # ==== Tier 回调 ====
    def action_on_tier_approved(self):
        for rec in self:
            if rec.state != "submit":
                raise UserError(_("只有已提交状态的物资计划可以执行审批通过回调。"))
            if rec.validation_status != "validated":
                raise UserError(_("物资计划尚未完成统一审批流程。"))
            rec._check_business_anchor()
            before = rec._snapshot_audit_payload()
            rec.write(
                {
                    "state": "approved",
                    "approved_by": self.env.user.id,
                    "approved_at": fields.Datetime.now(),
                }
            )
            rec._message_post_non_blocking(_("物资计划审批通过。"))
            rec._audit_transition(
                "material_plan_approved",
                before,
                rec._snapshot_audit_payload(),
                action_name="action_on_tier_approved",
            )

    def action_on_tier_rejected(self, reason=None):
        for rec in self:
            if rec.state != "submit":
                raise UserError(_("只有已提交状态的物资计划可以执行审批驳回回调。"))
            before = rec._snapshot_audit_payload()
            rec.write(
                {
                    "state": "draft",
                    "reject_reason": reason or _("未填写原因"),
                }
            )
            rec._message_post_non_blocking(_("物资计划审批驳回：%s") % rec.reject_reason)
            rec._audit_transition(
                "material_plan_rejected",
                before,
                rec._snapshot_audit_payload(),
                reason=rec.reject_reason,
                action_name="action_on_tier_rejected",
            )

    def action_done(self):
        for rec in self:
            if rec.state != "approved":
                raise UserError(_("只有已批准状态的物资计划可以完成。"))
            if not self.env.user.has_group("smart_construction_core.group_sc_cap_material_manager"):
                raise UserError(_("你没有完成物资计划的权限。"))
            rec._check_business_anchor()
            before = rec._snapshot_audit_payload()
            rec.state = "done"
            rec._audit_transition(
                "material_plan_done",
                before,
                rec._snapshot_audit_payload(),
                action_name="action_done",
            )

    def action_cancel(self):
        for rec in self:
            if rec.state not in ("draft", "submit", "approved"):
                raise UserError(_("只有草稿、已提交或已批准状态的物资计划可以取消。"))
            if not self.env.user.has_group("smart_construction_core.group_sc_cap_material_manager"):
                raise UserError(_("你没有取消物资计划的权限。"))
            before = rec._snapshot_audit_payload()
            rec.state = "cancel"
            rec._audit_transition(
                "material_plan_cancelled",
                before,
                rec._snapshot_audit_payload(),
                action_name="action_cancel",
            )

    def _compute_po_counts(self):
        PurchaseLine = self.env["purchase.order.line"].sudo()
        for rec in self:
            if "plan_id" in PurchaseLine._fields:
                lines = PurchaseLine.search([("plan_id", "=", rec.id)])
                rec.purchase_line_count = len(lines)
                rec.purchase_order_count = len(lines.mapped("order_id"))
            else:
                rec.purchase_line_count = 0
                rec.purchase_order_count = 0

    def _compute_purchase_request_count(self):
        Request = self.env["sc.material.purchase.request"].sudo()
        for rec in self:
            if "source_material_plan_id" in Request._fields:
                rec.purchase_request_count = Request.search_count(
                    [("source_material_plan_id", "=", rec.id), ("state", "!=", "cancel")]
                )
            else:
                rec.purchase_request_count = 0

    def _prepare_purchase_request_line_vals(self, line):
        line._ensure_technical_product()
        return {
            "source_material_plan_line_id": line.id,
            "product_id": line.product_id.id,
            "material_catalog_id": line.material_catalog_id.id,
            "material_spec": line.spec_model or line.spec or "",
            "product_uom_id": line.uom_id.id or line.product_id.uom_id.id,
            "qty": line.quantity or 1.0,
            "note": line.note,
        }

    def _prepare_purchase_request_vals(self):
        self.ensure_one()
        return {
            "project_id": self.project_id.id,
            "required_date": self.date_plan,
            "purpose": _("由材料计划 %s 生成") % (self.name or self.display_name),
            "source_material_plan_id": self.id,
            "line_ids": [
                (0, 0, self._prepare_purchase_request_line_vals(line))
                for line in self.line_ids
            ],
            "note": _("来源材料计划：%s") % (self.name or self.display_name),
        }

    def action_create_purchase_request(self):
        self.ensure_one()
        if not (
            self.env.user.has_group("smart_construction_core.group_sc_cap_material_user")
            or self.env.user.has_group("smart_construction_core.group_sc_cap_material_manager")
        ):
            raise UserError(_("你没有生成采购申请的权限。"))
        if self.state != "approved":
            raise UserError(_("只有已批准状态的物资计划可以生成采购申请。"))
        self._check_business_anchor()
        self._normalize_lines_uom()
        Request = self.env["sc.material.purchase.request"].sudo()
        request = Request.search(
            [("source_material_plan_id", "=", self.id), ("state", "!=", "cancel")],
            order="id desc",
            limit=1,
        )
        if not request:
            before = self._snapshot_audit_payload()
            request = Request.create(self._prepare_purchase_request_vals())
            self._message_post_non_blocking(_("已由物资计划生成采购申请：%s") % request.display_name)
            self._audit_transition(
                "material_plan_purchase_request_generated",
                before,
                self._snapshot_audit_payload(),
                reason=request.display_name,
                action_name="action_create_purchase_request",
            )
        return self._action_open_purchase_request(request)

    def _action_open_purchase_request(self, request):
        action = self.env.ref("smart_construction_core.action_sc_material_purchase_request").sudo().read()[0]
        action.update(
            {
                "views": [(self.env.ref("smart_construction_core.view_sc_material_purchase_request_form").id, "form")],
                "res_id": request.id,
                "domain": [("id", "=", request.id)],
                "context": {
                    "default_project_id": self.project_id.id,
                    "default_source_material_plan_id": self.id,
                },
            }
        )
        return action

    def action_view_purchase_requests(self):
        self.ensure_one()
        action = self.env.ref("smart_construction_core.action_sc_material_purchase_request").sudo().read()[0]
        action.update(
            {
                "domain": [("source_material_plan_id", "=", self.id)],
                "context": {
                    "default_project_id": self.project_id.id,
                    "default_source_material_plan_id": self.id,
                },
            }
        )
        return action

    def action_view_purchase_orders(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id("purchase.purchase_rfq")
        action["domain"] = [("plan_id", "=", self.id)] if "plan_id" in self.env["purchase.order"]._fields else [("id", "=", 0)]
        ctx = action.get("context") or {}
        if isinstance(ctx, str):
            try:
                ctx = safe_eval(ctx)
            except Exception:
                ctx = {}
        ctx.update({"default_plan_id": self.id, "search_default_plan_id": self.id})
        action["context"] = ctx
        return action

    def action_view_purchase_lines(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id("purchase.purchase_line_form_action")
        action["domain"] = [("plan_id", "=", self.id)] if "plan_id" in self.env["purchase.order.line"]._fields else [("id", "=", 0)]
        ctx = action.get("context") or {}
        if isinstance(ctx, str):
            try:
                ctx = safe_eval(ctx)
            except Exception:
                ctx = {}
        ctx.update({"default_plan_id": self.id, "search_default_plan_id": self.id})
        action["context"] = ctx
        return action

    def _check_state_from_condition(self):
        """
        OCA Tier Validation gate.
        默认实现通常依赖上游的状态字段/条件字段；我们自定义了 state，
        因此明确声明：submit 状态即可发起审批。
        """
        self.ensure_one()
        # 兼容父类（如果上游也实现了该方法）
        parent = getattr(super(ProjectMaterialPlan, self), "_check_state_from_condition", None)
        base_ok = parent() if parent else False
        return base_ok or (self.state == "submit")

class ProjectMaterialPlanLine(models.Model):
    _name = "project.material.plan.line"
    _description = "物资计划行"
    _order = "id"

    plan_id = fields.Many2one(
        "project.material.plan",
        string="计划单",
        required=True,
        ondelete="cascade",
        index=True,
    )
    material_catalog_id = fields.Many2one("sc.material.catalog", string="材料档案", index=True)
    product_id = fields.Many2one("product.product", string="材料", required=True)
    material_name = fields.Char(string="材料名称", compute="_compute_material_text", store=True)
    spec = fields.Char("规格")
    spec_model = fields.Char(string="规格型号", compute="_compute_material_text", store=True)
    quantity = fields.Float("数量", default=1.0)
    bill_qty = fields.Float(string="清单数量")
    unplanned_qty = fields.Float(string="未计划数量", compute="_compute_unplanned_qty", store=True)
    uom_id = fields.Many2one("uom.uom", string="单位")
    material_uom_text = fields.Char(string="单位文本")
    vendor_id = fields.Many2one(
        "res.partner",
        string="建议供应商",
        domain="[('supplier_rank','>',0)]",
    )
    note = fields.Char("备注")
    attachment_ids = fields.Many2many(
        "ir.attachment",
        "project_material_plan_line_attachment_rel",
        "line_id",
        "attachment_id",
        string="附件",
    )

    @api.model
    def _default_technical_product_id(self):
        product = self.env["product.product"].search([("default_code", "=", "SC-SYSTEM-DEFAULT-MATERIAL")], limit=1)
        if not product:
            product = self.env["product.product"].sudo().create(
                {
                    "name": "系统默认材料（技术兜底）",
                    "default_code": "SC-SYSTEM-DEFAULT-MATERIAL",
                    "type": "product",
                }
            )
        return product.id

    @api.depends("material_catalog_id", "product_id", "spec")
    def _compute_material_text(self):
        for line in self:
            catalog = line.material_catalog_id
            line.material_name = catalog.name if catalog else (line.product_id.display_name if line.product_id else False)
            line.spec_model = line.spec or catalog.spec_model

    @api.depends("quantity", "bill_qty")
    def _compute_unplanned_qty(self):
        for line in self:
            line.unplanned_qty = max(line.bill_qty - line.quantity, 0.0)

    @api.model_create_multi
    def create(self, vals_list):
        Product = self.env["product.product"]
        for vals in vals_list:
            catalog = self.env["sc.material.catalog"].browse(vals.get("material_catalog_id")) if vals.get("material_catalog_id") else False
            if catalog:
                vals.setdefault("spec", catalog.spec_model or False)
                vals.setdefault("material_uom_text", catalog.uom_text or False)
            if not vals.get("product_id"):
                vals["product_id"] = self._default_technical_product_id()
            if not vals.get("uom_id") and vals.get("product_id"):
                product = Product.browse(vals["product_id"])
                vals["uom_id"] = (product.uom_po_id or product.uom_id).id
        return super().create(vals_list)

    @api.onchange("material_catalog_id")
    def _onchange_material_catalog_id(self):
        for line in self:
            catalog = line.material_catalog_id
            if not catalog:
                continue
            if not line.spec:
                line.spec = catalog.spec_model
            line.material_uom_text = catalog.uom_text
            line._ensure_technical_product()

    @api.onchange("product_id")
    def _onchange_product_id_set_uom(self):
        for line in self:
            if line.product_id and not line.material_catalog_id:
                line.uom_id = line.product_id.uom_po_id or line.product_id.uom_id
                line.material_uom_text = line.uom_id.name

    @api.constrains("product_id", "uom_id")
    def _check_uom_category(self):
        for line in self:
            if line.material_catalog_id:
                continue
            if line.product_id and line.uom_id:
                base_uom = line.product_id.uom_po_id or line.product_id.uom_id
                if line.uom_id.category_id != base_uom.category_id:
                    raise ValidationError(_("计划行单位必须与材料单位同类别"))

    def _ensure_technical_product(self):
        for line in self:
            if not line.product_id:
                line.product_id = line._default_technical_product_id()

    # 硬约束：非草稿状态禁止修改/删除明细
    def write(self, vals):
        lock_fields = {"material_catalog_id", "spec", "quantity", "uom_id", "material_uom_text", "vendor_id", "note"}
        for line in self:
            if line.plan_id and line.plan_id.state != "draft" and lock_fields.intersection(vals):
                raise UserError(_("已确认/完成的物资计划不允许修改明细。"))
        return super().write(vals)

    def unlink(self):
        for line in self:
            if line.plan_id and line.plan_id.state != "draft":
                raise UserError(_("已确认/完成的物资计划不允许删除明细。"))
        return super().unlink()
