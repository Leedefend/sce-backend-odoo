# -*- coding: utf-8 -*-
import json

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_compare


SYSTEM_DEFAULT_PROJECT_NAME = "系统默认项目（技术兜底）"
LEGACY_SYSTEM_DEFAULT_PROJECT_NAME = "系统默认项目（待完善）"
SYSTEM_DEFAULT_SUPPLIER_NAME = "系统默认供应商（技术兜底）"
LEGACY_SYSTEM_DEFAULT_SUPPLIER_NAME = "系统默认供应商（待完善）"
SYSTEM_DEFAULT_MATERIAL_NAME = "系统默认材料（技术兜底）"
SYSTEM_DEFAULT_WAREHOUSE_NAME = "系统默认仓库（技术兜底）"


class ScMaterialSystemDefaultMixin(models.AbstractModel):
    _name = "sc.material.system.default.mixin"
    _inherit = "sc.system.default.mixin"
    _description = "物资模型系统默认兜底"

    @api.model
    def _sc_default_project_id(self):
        project = self.env["project.project"].search(
            [("name", "in", [SYSTEM_DEFAULT_PROJECT_NAME, LEGACY_SYSTEM_DEFAULT_PROJECT_NAME])],
            limit=1,
        )
        if not project:
            project = self.env["project.project"].sudo().create(
                {
                    "name": SYSTEM_DEFAULT_PROJECT_NAME,
                    "company_id": self.env.company.id,
                }
            )
        elif project.name == LEGACY_SYSTEM_DEFAULT_PROJECT_NAME:
            project.sudo().write({"name": SYSTEM_DEFAULT_PROJECT_NAME})
        return project.id

    @api.model
    def _sc_default_supplier_id(self):
        partner = self.env["res.partner"].search(
            [("name", "in", [SYSTEM_DEFAULT_SUPPLIER_NAME, LEGACY_SYSTEM_DEFAULT_SUPPLIER_NAME])],
            limit=1,
        )
        if not partner:
            partner = self.env["res.partner"].sudo().create(
                {
                    "name": SYSTEM_DEFAULT_SUPPLIER_NAME,
                    "supplier_rank": 1,
                }
            )
        elif partner.name == LEGACY_SYSTEM_DEFAULT_SUPPLIER_NAME:
            partner.sudo().write({"name": SYSTEM_DEFAULT_SUPPLIER_NAME})
        return partner.id

    @api.model
    def _sc_default_product_id(self):
        product = self.env["product.product"].search([("default_code", "=", "SC-SYSTEM-DEFAULT-MATERIAL")], limit=1)
        if not product:
            product = self.env["product.product"].sudo().create(
                {
                    "name": SYSTEM_DEFAULT_MATERIAL_NAME,
                    "default_code": "SC-SYSTEM-DEFAULT-MATERIAL",
                    "type": "product",
                }
            )
        elif product.name != SYSTEM_DEFAULT_MATERIAL_NAME:
            product.sudo().write({"name": SYSTEM_DEFAULT_MATERIAL_NAME})
        return product.id

    @api.model
    def _sc_default_warehouse_id(self):
        warehouse = self.env["stock.warehouse"].search(
            [("company_id", "in", [self.env.company.id, False])],
            limit=1,
        )
        if not warehouse:
            warehouse = self.env["stock.warehouse"].sudo().create(
                {
                    "name": SYSTEM_DEFAULT_WAREHOUSE_NAME,
                    "code": "SDF",
                    "company_id": self.env.company.id,
                }
            )
        return warehouse.id

    @api.model
    def _sc_default_location_id(self, warehouse_id=False):
        warehouse = self.env["stock.warehouse"].browse(warehouse_id or self._sc_default_warehouse_id())
        return warehouse.lot_stock_id.id if warehouse and warehouse.lot_stock_id else False

    def _sc_get_or_create_material_cost_code(self):
        CostCode = self.env["project.cost.code"].sudo()
        cost_code = CostCode.search([("code", "=", "MAT"), ("type", "=", "material")], limit=1)
        if not cost_code:
            cost_code = CostCode.create(
                {
                    "code": "MAT",
                    "name": "材料成本",
                    "type": "material",
                    "note": "材料办理确认时自动归集的默认成本科目。",
                }
            )
        return cost_code

    def _sc_business_category_ledger_policy(self, code):
        category = self.env["sc.business.category"].sudo().search([("code", "=", code)], limit=1)
        if not category:
            return {}
        try:
            policy = json.loads(category.ledger_policy_json or "{}")
        except (TypeError, ValueError):
            policy = {}
        return policy if isinstance(policy, dict) else {}

    def _sc_business_category_cost_trigger(self, code, trigger, default=False):
        policy = self._sc_business_category_ledger_policy(code)
        triggers = policy.get("cost_triggers") or {}
        if not isinstance(triggers, dict):
            return default
        return bool(triggers.get(trigger, default))

    @api.model
    def _sc_material_business_category_code(self, vals=None):
        vals = vals or {}
        if self._name == "sc.material.outbound":
            outbound_type = vals.get("outbound_type")
            if not outbound_type:
                code = self.env.context.get("default_business_category_code") or self.env.context.get(
                    "current_business_category_code"
                )
                if code:
                    return code
                outbound_type = self.env.context.get("default_outbound_type") or "issue"
            return {
                "issue": "material.outbound",
                "return": "material.return",
                "transfer": "material.transfer",
                "loss": "material.loss",
            }.get(outbound_type, "material.outbound")
        code = self.env.context.get("default_business_category_code") or self.env.context.get(
            "current_business_category_code"
        )
        if code:
            return code
        return {
            "sc.material.purchase.request": "material.purchase.request",
            "sc.material.acceptance": "material.acceptance",
            "sc.material.inbound": "material.inbound",
            "sc.material.rfq": "material.rfq",
            "sc.material.settlement": "material.settlement",
        }.get(self._name)

    @api.model
    def _sc_resolve_material_business_category_id(self, vals=None):
        code = self._sc_material_business_category_code(vals)
        if not code:
            return False
        category = self.env["sc.business.category"].sudo().search(
            [("code", "=", code), ("target_model", "=", self._name)],
            limit=1,
        )
        return category.id if category else False

    @api.model
    def _sc_apply_system_defaults(self, vals, default_getters):
        defaulted_fields = []
        for field_name, getter_name in default_getters.items():
            if vals.get(field_name):
                continue
            value = getattr(self, getter_name)()
            if value is not False and value is not None:
                vals[field_name] = value
                defaulted_fields.append(field_name)
        self._sc_mark_system_defaults(vals, defaulted_fields)

    @api.model
    def _sc_apply_line_defaults(self, vals, *, require_supplier=False, require_unit_price=False):
        defaulted_fields = []
        if require_supplier and not vals.get("supplier_id"):
            vals["supplier_id"] = self._sc_default_supplier_id()
            defaulted_fields.append("supplier_id")
        catalog = self.env["sc.material.catalog"].browse(vals.get("material_catalog_id")) if vals.get("material_catalog_id") else False
        if catalog:
            if not vals.get("material_spec"):
                vals["material_spec"] = catalog.spec_model or ""
                defaulted_fields.append("material_spec")
        if not vals.get("product_id"):
            vals["product_id"] = self._sc_default_product_id()
            defaulted_fields.append("product_id")
        if not vals.get("qty"):
            vals["qty"] = 1.0
            defaulted_fields.append("qty")
        if require_unit_price and vals.get("unit_price") is None:
            vals["unit_price"] = 0.0
            defaulted_fields.append("unit_price")
        product = self.env["product.product"].browse(vals.get("product_id"))
        if product:
            if not vals.get("product_uom_id"):
                vals["product_uom_id"] = product.uom_id.id
                defaulted_fields.append("product_uom_id")
            if not vals.get("material_spec") and not catalog:
                vals["material_spec"] = product.default_code or product.display_name
                defaulted_fields.append("material_spec")
        self._sc_mark_system_defaults(vals, defaulted_fields)

    def _sc_warn_system_defaults_on_action(self, action_label):
        for record in self:
            default_hints = []
            if record.sc_has_system_default:
                default_hints.append(record.sc_system_default_fields or _("主单字段"))
            line_model = record._fields.get("line_ids")
            if line_model:
                line_defaults = record.line_ids.filtered("sc_has_system_default")
                if line_defaults:
                    line_fields = [value for value in line_defaults.mapped("sc_system_default_fields") if value]
                    default_hints.append(_("明细字段：%s") % ", ".join(line_fields or [_("未标明字段")]))
            if not default_hints or not hasattr(record, "message_post"):
                continue
            body = _(
                "%(action)s时发现本单含系统默认兜底值：%(fields)s。"
                "系统不阻断业务推进，请经办人或审批人在真实业务办理前补充完善。"
            ) % {
                "action": action_label,
                "fields": "；".join(default_hints),
            }
            try:
                author = self.env.ref("base.partner_root", raise_if_not_found=False)
                record.sudo().message_post(
                    body=body,
                    author_id=author.id if author else False,
                    subtype_xmlid="mail.mt_note",
                )
            except Exception:
                # 提醒不能反过来阻断业务动作；页面字段标识仍保留兜底痕迹。
                continue

    def _sc_require_state(self, allowed_states, action_label):
        allowed_states = set(allowed_states)
        for record in self:
            if record.state not in allowed_states:
                raise ValidationError(
                    _("%(action)s只能处理状态为%(states)s的单据。")
                    % {
                        "action": action_label,
                        "states": "、".join(sorted(allowed_states)),
                    }
                )

    def _sc_require_any_group(self, group_xmlids, action_label):
        if any(self.env.user.has_group(xmlid) for xmlid in group_xmlids):
            return
        raise ValidationError(_("你没有%(action)s的权限。") % {"action": action_label})

    def _sc_require_material_user(self, action_label):
        self._sc_require_any_group(
            [
                "smart_construction_core.group_sc_cap_business_initiator",
                "smart_construction_core.group_sc_cap_material_user",
                "smart_construction_core.group_sc_cap_material_manager",
            ],
            action_label,
        )

    def _sc_require_material_manager(self, action_label):
        self._sc_require_any_group(
            ["smart_construction_core.group_sc_cap_material_manager"],
            action_label,
        )

    def _sc_require_purchase_user(self, action_label):
        self._sc_require_any_group(
            [
                "smart_construction_core.group_sc_cap_purchase_user",
                "smart_construction_core.group_sc_cap_purchase_manager",
                "smart_construction_core.group_sc_cap_material_manager",
            ],
            action_label,
        )

    def _sc_require_purchase_manager(self, action_label):
        self._sc_require_any_group(
            [
                "smart_construction_core.group_sc_cap_purchase_manager",
                "smart_construction_core.group_sc_cap_material_manager",
            ],
            action_label,
        )

    def _sc_material_audit_payload(self):
        self.ensure_one()
        payload = {
            "name": getattr(self, "name", False),
            "state": getattr(self, "state", False),
            "project_id": self.project_id.id if getattr(self, "project_id", False) else False,
            "line_count": len(self.line_ids) if "line_ids" in self._fields else 0,
        }
        for field_name in (
            "supplier_id",
            "warehouse_id",
            "purchase_request_id",
            "purchase_order_id",
            "acceptance_id",
            "selected_supplier_id",
        ):
            if field_name in self._fields:
                value = self[field_name]
                payload[field_name] = value.id if value else False
        for field_name in ("amount_total", "amount_untaxed", "tax_amount", "total_qty"):
            if field_name in self._fields:
                payload[field_name] = float(self[field_name] or 0.0)
        return payload

    def _sc_audit_material_transition(self, event_code, before, after, action_name=None, reason=None):
        self.ensure_one()
        project = self.project_id if "project_id" in self._fields else False
        company = project.company_id if project else self.env.company
        return self.env["sc.audit.log"].write_event(
            event_code=event_code,
            model=self._name,
            res_id=self.id,
            action=action_name or event_code,
            before=before,
            after=after,
            reason=reason,
            company_id=company.id if company else False,
            project_id=project.id if project else False,
        )


class ScMaterialPurchaseRequest(models.Model):
    _name = "sc.material.purchase.request"
    _description = "材料采购申请"
    _inherit = ["mail.thread", "mail.activity.mixin", "sc.material.system.default.mixin"]
    _order = "request_date desc, id desc"

    name = fields.Char(string="申请单号", required=True, default="新建", tracking=True)
    project_id = fields.Many2one("project.project", string="项目", required=True, index=True, tracking=True)
    business_category_id = fields.Many2one(
        "sc.business.category",
        string="业务分类",
        index=True,
        ondelete="restrict",
        domain="[('target_model', '=', 'sc.material.purchase.request')]",
    )
    request_date = fields.Date(string="申请日期", default=fields.Date.context_today, index=True, tracking=True)
    required_date = fields.Date(string="期望到货日期", index=True)
    requester_id = fields.Many2one("res.users", string="申请人", default=lambda self: self.env.user, index=True)
    department_id = fields.Many2one("hr.department", string="申请部门", index=True)
    supplier_id = fields.Many2one("res.partner", string="拟采购供应商", domain=[("supplier_rank", ">", 0)], index=True)
    purpose = fields.Char(string="采购用途")
    source_material_plan_id = fields.Many2one("project.material.plan", string="来源材料计划", index=True)
    currency_id = fields.Many2one(
        "res.currency",
        string="币种",
        required=True,
        default=lambda self: self.env.company.currency_id.id,
    )
    amount_total = fields.Monetary(
        string="总金额",
        currency_field="currency_id",
        compute="_compute_purchase_request_boundary_fields",
        store=True,
        readonly=True,
    )
    invoice_amount = fields.Monetary(
        string="已开票金额",
        currency_field="currency_id",
        compute="_compute_purchase_request_boundary_fields",
        store=True,
        readonly=True,
    )
    payment_paid_amount = fields.Monetary(
        string="已付款金额",
        currency_field="currency_id",
        compute="_compute_purchase_request_boundary_fields",
        store=True,
        readonly=True,
    )
    payment_unpaid_amount = fields.Monetary(
        string="未付款金额",
        currency_field="currency_id",
        compute="_compute_purchase_request_boundary_fields",
        store=True,
        readonly=True,
    )
    uninvoiced_amount = fields.Monetary(
        string="未开票金额",
        currency_field="currency_id",
        compute="_compute_purchase_request_boundary_fields",
        store=True,
        readonly=True,
    )
    tax_rate_text = fields.Char(
        string="税率",
        compute="_compute_purchase_request_boundary_fields",
        store=True,
        readonly=True,
    )
    rfq_count = fields.Integer("询价单", compute="_compute_downstream_counts")
    purchase_order_count = fields.Integer("采购订单", compute="_compute_downstream_counts")
    state = fields.Selection(
        [
            ("draft", "草稿"),
            ("submitted", "已提交"),
            ("approved", "已确认"),
            ("cancel", "已取消"),
        ],
        string="状态",
        default="draft",
        index=True,
        tracking=True,
    )
    line_ids = fields.One2many("sc.material.purchase.request.line", "request_id", string="申请明细")
    note = fields.Text(string="申请说明")
    attachment_ids = fields.Many2many(
        "ir.attachment",
        "sc_material_purchase_request_attachment_rel",
        "request_id",
        "attachment_id",
        string="申请附件",
    )
    legacy_fact_model = fields.Char(string="来源通用模型", index=True)
    legacy_fact_id = fields.Integer(string="来源通用记录ID", index=True)
    legacy_fact_type = fields.Char(string="来源业务类型", index=True)

    _sql_constraints = [
        (
            "legacy_material_purchase_request_unique",
            "unique(legacy_fact_model, legacy_fact_id)",
            "来源通用材料采购申请已迁移为专业采购申请。",
        ),
    ]

    @api.constrains("request_date", "required_date")
    def _check_required_date(self):
        for record in self:
            if record.request_date and record.required_date and record.required_date < record.request_date:
                raise ValidationError(_("期望到货日期不能早于申请日期。"))

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env["ir.sequence"]
        for vals in vals_list:
            vals.setdefault("business_category_id", self._sc_resolve_material_business_category_id(vals))
            self._sc_apply_system_defaults(vals, {"project_id": "_sc_default_project_id"})
            if vals.get("name", "新建") == "新建":
                vals["name"] = seq.next_by_code("sc.material.purchase.request") or _("材料采购申请")
        return super().create(vals_list)

    def init(self):
        self.env.cr.execute(
            """
            UPDATE sc_material_purchase_request request
               SET business_category_id = category.id
              FROM sc_business_category category
             WHERE request.business_category_id IS NULL
               AND category.code = 'material.purchase.request'
               AND category.target_model = 'sc.material.purchase.request'
            """
        )

    @api.depends("line_ids.estimated_amount")
    def _compute_purchase_request_boundary_fields(self):
        for record in self:
            amount = sum(record.line_ids.mapped("estimated_amount"))
            record.amount_total = amount
            record.invoice_amount = 0.0
            record.payment_paid_amount = 0.0
            record.payment_unpaid_amount = amount
            record.uninvoiced_amount = amount
            record.tax_rate_text = False

    def action_submit(self):
        self._sc_require_material_user(_("提交采购申请"))
        for record in self:
            record._sc_require_state({"draft"}, _("提交采购申请"))
            if not record.line_ids:
                raise ValidationError(_("提交采购申请前必须维护申请明细。"))
            record.line_ids._check_qty()
        snapshots = {record.id: record._sc_material_audit_payload() for record in self}
        self._sc_warn_system_defaults_on_action(_("提交采购申请"))
        self.write({"state": "submitted"})
        for record in self:
            record._sc_audit_material_transition(
                "material_purchase_request_submitted",
                snapshots[record.id],
                record._sc_material_audit_payload(),
                action_name="action_submit",
            )
        return True

    def action_approve(self):
        self._sc_require_any_group(
            [
                "smart_construction_core.group_sc_cap_material_manager",
                "smart_construction_core.group_sc_cap_purchase_manager",
            ],
            _("审批采购申请"),
        )
        for record in self:
            record._sc_require_state({"submitted"}, _("审批采购申请"))
            record.line_ids._check_qty()
        snapshots = {record.id: record._sc_material_audit_payload() for record in self}
        self._sc_warn_system_defaults_on_action(_("审批采购申请"))
        self.write({"state": "approved"})
        for record in self:
            record._sc_audit_material_transition(
                "material_purchase_request_approved",
                snapshots[record.id],
                record._sc_material_audit_payload(),
                action_name="action_approve",
            )
        return True

    def action_cancel(self):
        self._sc_require_material_manager(_("取消采购申请"))
        self._sc_require_state({"draft", "submitted"}, _("取消采购申请"))
        snapshots = {record.id: record._sc_material_audit_payload() for record in self}
        self.write({"state": "cancel"})
        for record in self:
            record._sc_audit_material_transition(
                "material_purchase_request_cancelled",
                snapshots[record.id],
                record._sc_material_audit_payload(),
                action_name="action_cancel",
            )
        return True

    def action_reset_draft(self):
        self._sc_require_material_manager(_("重置采购申请为草稿"))
        self._sc_require_state({"cancel"}, _("重置采购申请为草稿"))
        snapshots = {record.id: record._sc_material_audit_payload() for record in self}
        self.write({"state": "draft"})
        for record in self:
            record._sc_audit_material_transition(
                "material_purchase_request_reset",
                snapshots[record.id],
                record._sc_material_audit_payload(),
                action_name="action_reset_draft",
            )
        return True

    def _compute_downstream_counts(self):
        Rfq = self.env["sc.material.rfq"].sudo()
        Order = self.env["purchase.order"].sudo()
        for record in self:
            record.rfq_count = Rfq.search_count(
                [("purchase_request_id", "=", record.id), ("state", "!=", "cancel")]
            )
            if "source_material_purchase_request_id" in Order._fields:
                record.purchase_order_count = Order.search_count(
                    [("source_material_purchase_request_id", "=", record.id), ("state", "!=", "cancel")]
                )
            else:
                record.purchase_order_count = 0

    def _require_approved_for_downstream(self, action_label):
        self.ensure_one()
        self._sc_require_state({"approved"}, action_label)
        if not self.line_ids:
            raise ValidationError(_("%s前必须维护申请明细。") % action_label)
        self.line_ids._check_qty()

    def _require_supplier_for_downstream(self, action_label):
        self.ensure_one()
        if not self.supplier_id:
            raise ValidationError(_("%s前必须维护拟采购供应商。") % action_label)

    def _prepare_rfq_line_vals(self, line):
        return {
            "source_material_plan_line_id": line.source_material_plan_line_id.id,
            "source_material_purchase_request_line_id": line.id,
            "supplier_id": self.supplier_id.id,
            "product_id": line.product_id.id,
            "material_catalog_id": line.material_catalog_id.id,
            "material_spec": line.material_spec,
            "product_uom_id": line.product_uom_id.id or line.product_id.uom_id.id,
            "qty": line.qty or 1.0,
            "unit_price": line.estimated_unit_price or 0.0,
            "note": line.note,
        }

    def _prepare_rfq_vals(self):
        self.ensure_one()
        return {
            "project_id": self.project_id.id,
            "purchase_request_id": self.id,
            "source_material_plan_id": self.source_material_plan_id.id,
            "due_date": self.required_date,
            "note": _("来源采购申请：%s") % (self.name or self.display_name),
            "line_ids": [
                (0, 0, self._prepare_rfq_line_vals(line))
                for line in self.line_ids
            ],
        }

    def action_create_rfq(self):
        self.ensure_one()
        self._sc_require_purchase_user(_("生成询价单"))
        self._require_approved_for_downstream(_("生成询价单"))
        self._require_supplier_for_downstream(_("生成询价单"))
        Rfq = self.env["sc.material.rfq"].sudo()
        rfq = Rfq.search(
            [("purchase_request_id", "=", self.id), ("state", "!=", "cancel")],
            order="id desc",
            limit=1,
        )
        if not rfq:
            before = self._sc_material_audit_payload()
            rfq = Rfq.create(self._prepare_rfq_vals())
            self._sc_audit_material_transition(
                "material_purchase_request_rfq_generated",
                before,
                self._sc_material_audit_payload(),
                action_name="action_create_rfq",
                reason=rfq.display_name,
            )
        return self._action_open_rfq(rfq)

    def _prepare_purchase_order_line_vals(self, line):
        material_name = line.material_catalog_id.display_name if line.material_catalog_id else line.product_id.display_name
        name = material_name
        if line.material_spec:
            name = "%s / %s" % (name, line.material_spec)
        if line.note:
            name = "%s\n%s" % (name, line.note)
        return {
            "product_id": line.product_id.id,
            "name": name,
            "product_qty": line.qty or 1.0,
            "product_uom": line.product_uom_id.id or line.product_id.uom_po_id.id or line.product_id.uom_id.id,
            "price_unit": line.estimated_unit_price or 0.0,
            "date_planned": fields.Datetime.now(),
            "project_id": self.project_id.id,
            "plan_line_id": line.source_material_plan_line_id.id,
            "source_material_purchase_request_line_id": line.id,
        }

    def _prepare_purchase_order_vals(self):
        self.ensure_one()
        return {
            "partner_id": self.supplier_id.id,
            "project_id": self.project_id.id,
            "plan_id": self.source_material_plan_id.id,
            "source_material_purchase_request_id": self.id,
            "origin": self.name,
            "order_line": [
                (0, 0, self._prepare_purchase_order_line_vals(line))
                for line in self.line_ids
            ],
        }

    def action_create_purchase_order(self):
        self.ensure_one()
        self._sc_require_purchase_manager(_("生成采购订单"))
        self._require_approved_for_downstream(_("生成采购订单"))
        self._require_supplier_for_downstream(_("生成采购订单"))
        Order = self.env["purchase.order"].sudo()
        order = Order.search(
            [("source_material_purchase_request_id", "=", self.id), ("state", "!=", "cancel")],
            order="id desc",
            limit=1,
        )
        if not order:
            before = self._sc_material_audit_payload()
            order = Order.create(self._prepare_purchase_order_vals())
            self._sc_audit_material_transition(
                "material_purchase_request_purchase_order_generated",
                before,
                self._sc_material_audit_payload(),
                action_name="action_create_purchase_order",
                reason=order.display_name,
            )
        return self._action_open_purchase_order(order)

    def _action_open_rfq(self, rfq):
        action = self.env.ref("smart_construction_core.action_sc_material_rfq").sudo().read()[0]
        action.update(
            {
                "views": [(self.env.ref("smart_construction_core.view_sc_material_rfq_form").id, "form")],
                "res_id": rfq.id,
                "domain": [("id", "=", rfq.id)],
                "context": {
                    "default_project_id": self.project_id.id,
                    "default_purchase_request_id": self.id,
                    "default_source_material_plan_id": self.source_material_plan_id.id,
                },
            }
        )
        return action

    def _action_open_purchase_order(self, order):
        action = self.env.ref("smart_construction_core.action_sc_purchase_order").sudo().read()[0]
        action.update(
            {
                "views": [(self.env.ref("purchase.purchase_order_form").id, "form")],
                "res_id": order.id,
                "domain": [("id", "=", order.id)],
                "context": {
                    "default_project_id": self.project_id.id,
                    "default_source_material_purchase_request_id": self.id,
                },
            }
        )
        return action

    def action_view_rfqs(self):
        self.ensure_one()
        action = self.env.ref("smart_construction_core.action_sc_material_rfq").sudo().read()[0]
        action.update(
            {
                "domain": [("purchase_request_id", "=", self.id)],
                "context": {
                    "default_project_id": self.project_id.id,
                    "default_purchase_request_id": self.id,
                    "default_source_material_plan_id": self.source_material_plan_id.id,
                },
            }
        )
        return action

    def action_view_purchase_orders(self):
        self.ensure_one()
        action = self.env.ref("smart_construction_core.action_sc_purchase_order").sudo().read()[0]
        action.update(
            {
                "domain": [("source_material_purchase_request_id", "=", self.id)],
                "context": {
                    "default_project_id": self.project_id.id,
                    "default_source_material_purchase_request_id": self.id,
                },
            }
        )
        return action

    def _prepare_acceptance_line_vals(self, line):
        qty = line.qty or 1.0
        return {
            "purchase_request_line_id": line.id,
            "product_id": line.product_id.id,
            "material_catalog_id": line.material_catalog_id.id,
            "material_spec": line.material_spec,
            "product_uom_id": line.product_uom_id.id,
            "planned_qty": qty,
            "received_qty": qty,
            "accepted_qty": qty,
            "issue_note": line.note,
        }


class ScMaterialPurchaseRequestLine(models.Model):
    _name = "sc.material.purchase.request.line"
    _description = "材料采购申请明细"
    _inherit = "sc.material.system.default.mixin"
    _order = "request_id, sequence, id"

    request_id = fields.Many2one("sc.material.purchase.request", string="采购申请", required=True, ondelete="cascade", index=True)
    sequence = fields.Integer(default=10)
    source_material_plan_line_id = fields.Many2one("project.material.plan.line", string="来源计划明细", index=True)
    project_id = fields.Many2one("project.project", string="项目", related="request_id.project_id", store=True, index=True)
    product_id = fields.Many2one("product.product", string="材料", required=True, index=True)
    material_catalog_id = fields.Many2one("sc.material.catalog", string="材料档案", index=True)
    material_spec = fields.Char(string="规格型号")
    product_uom_id = fields.Many2one("uom.uom", string="单位")
    qty = fields.Float(string="申请数量", required=True)
    estimated_unit_price = fields.Monetary(string="预计单价", currency_field="currency_id")
    estimated_amount = fields.Monetary(string="预计金额", currency_field="currency_id", compute="_compute_estimated_amount", store=True)
    currency_id = fields.Many2one(
        "res.currency",
        string="币种",
        required=True,
        default=lambda self: self.env.company.currency_id.id,
    )
    note = fields.Char(string="备注")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._sc_apply_line_defaults(vals)
        return super().create(vals_list)

    @api.depends("qty", "estimated_unit_price")
    def _compute_estimated_amount(self):
        for record in self:
            record.estimated_amount = record.qty * record.estimated_unit_price

    @api.onchange("product_id")
    def _onchange_product_id(self):
        for record in self:
            if record.product_id and not record.material_catalog_id:
                record.product_uom_id = record.product_id.uom_id
                if not record.material_spec:
                    record.material_spec = record.product_id.default_code or ""

    @api.onchange("material_catalog_id")
    def _onchange_material_catalog_id(self):
        for record in self:
            catalog = record.material_catalog_id
            if not catalog:
                continue
            record.material_spec = catalog.spec_model or record.material_spec

    @api.constrains("qty", "estimated_unit_price")
    def _check_qty(self):
        for record in self:
            if record.qty <= 0:
                raise ValidationError(_("申请数量必须大于0。"))
            if record.estimated_unit_price < 0:
                raise ValidationError(_("预计单价不能为负数。"))


class ScMaterialAcceptance(models.Model):
    _name = "sc.material.acceptance"
    _description = "材料进场验收"
    _inherit = ["mail.thread", "mail.activity.mixin", "sc.material.system.default.mixin"]
    _order = "acceptance_date desc, id desc"

    name = fields.Char(string="验收单号", required=True, default="新建", tracking=True)
    project_id = fields.Many2one("project.project", string="项目", required=True, index=True, tracking=True)
    business_category_id = fields.Many2one(
        "sc.business.category",
        string="业务分类",
        index=True,
        ondelete="restrict",
        domain="[('target_model', '=', 'sc.material.acceptance')]",
    )
    acceptance_date = fields.Date(string="验收日期", default=fields.Date.context_today, index=True, tracking=True)
    supplier_id = fields.Many2one("res.partner", string="供应商", index=True)
    purchase_order_id = fields.Many2one("purchase.order", string="采购订单", index=True)
    purchase_request_id = fields.Many2one("sc.material.purchase.request", string="采购申请", index=True)
    warehouse_id = fields.Many2one("stock.warehouse", string="仓库", index=True)
    dest_location_id = fields.Many2one("stock.location", string="入库库位", index=True)
    inspector_id = fields.Many2one("res.users", string="验收人", default=lambda self: self.env.user, index=True)
    supervisor_inspector_id = fields.Many2one("res.users", string="监理验收人", index=True)
    owner_inspector_id = fields.Many2one("res.users", string="甲方验收人", index=True)
    source_channel = fields.Selection([("pc", "PC"), ("app", "APP"), ("import", "导入")], string="来源端", default="pc", index=True)
    acceptance_flow = fields.Selection(
        [
            ("epc", "EPC验收"),
            ("supervisor", "监理验收"),
            ("owner", "甲方验收"),
            ("sampling", "送检"),
            ("return", "退场验收"),
            ("combined", "组合流程"),
        ],
        string="验收流程",
        default="combined",
        index=True,
    )
    sampling_required = fields.Boolean(string="需要送检")
    sampling_report_ref = fields.Char(string="送检报告编号", index=True)
    state = fields.Selection(
        [
            ("draft", "草稿"),
            ("submitted", "已提交"),
            ("accepted", "验收通过"),
            ("rejected", "验收不通过"),
            ("cancel", "已取消"),
        ],
        string="状态",
        default="draft",
        index=True,
        tracking=True,
    )
    line_ids = fields.One2many("sc.material.acceptance.line", "acceptance_id", string="验收明细")
    attachment_ids = fields.Many2many("ir.attachment", string="验收附件")
    note = fields.Text(string="验收说明")
    rejection_reason = fields.Text(string="不通过原因")
    legacy_fact_model = fields.Char(string="来源通用模型", index=True)
    legacy_fact_id = fields.Integer(string="来源通用记录ID", index=True)
    legacy_fact_type = fields.Char(string="来源业务类型", index=True)

    _sql_constraints = [
        (
            "legacy_material_acceptance_unique",
            "unique(legacy_fact_model, legacy_fact_id)",
            "来源通用材料记录已迁移为材料验收单。",
        ),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env["ir.sequence"]
        for vals in vals_list:
            vals.setdefault("business_category_id", self._sc_resolve_material_business_category_id(vals))
            self._apply_purchase_request_defaults(vals)
            self._apply_purchase_order_defaults(vals)
            self._sc_apply_system_defaults(vals, {"project_id": "_sc_default_project_id"})
            if vals.get("name", "新建") == "新建":
                vals["name"] = seq.next_by_code("sc.material.acceptance") or _("材料进场验收")
        return super().create(vals_list)

    def init(self):
        self.env.cr.execute(
            """
            UPDATE sc_material_acceptance acceptance
               SET business_category_id = category.id
              FROM sc_business_category category
             WHERE acceptance.business_category_id IS NULL
               AND category.code = 'material.acceptance'
               AND category.target_model = 'sc.material.acceptance'
            """
        )

    @api.model
    def _apply_purchase_request_defaults(self, vals):
        request_id = vals.get("purchase_request_id")
        if not request_id:
            return vals
        request = self.env["sc.material.purchase.request"].browse(request_id)
        if request.exists():
            vals.setdefault("project_id", request.project_id.id)
            vals.setdefault("note", request.note)
            if not vals.get("line_ids") and request.line_ids:
                vals["line_ids"] = [
                    (0, 0, request._prepare_acceptance_line_vals(line))
                    for line in request.line_ids
                ]
        return vals

    @api.model
    def _apply_purchase_order_defaults(self, vals):
        order_id = vals.get("purchase_order_id")
        if not order_id:
            return vals
        order = self.env["purchase.order"].browse(order_id)
        if order.exists():
            if order.project_id:
                vals.setdefault("project_id", order.project_id.id)
            vals.setdefault("supplier_id", order.partner_id.id)
            if not vals.get("line_ids") and order.order_line:
                vals["line_ids"] = [
                    (0, 0, self._prepare_purchase_order_acceptance_line_vals(line))
                    for line in order.order_line
                ]
        return vals

    @api.model
    def _prepare_purchase_order_acceptance_line_vals(self, line):
        qty = line.product_qty or 1.0
        rfq_line = line.source_material_rfq_line_id
        request_line = line.source_material_purchase_request_line_id
        material_catalog = rfq_line.material_catalog_id if rfq_line else request_line.material_catalog_id
        material_spec = rfq_line.material_spec if rfq_line else request_line.material_spec
        return {
            "purchase_order_line_id": line.id,
            "product_id": line.product_id.id,
            "material_catalog_id": material_catalog.id if material_catalog else False,
            "material_spec": material_spec or "",
            "product_uom_id": line.product_uom.id,
            "planned_qty": qty,
            "received_qty": qty,
            "accepted_qty": qty,
            "issue_note": line.name,
        }

    @api.onchange("purchase_request_id")
    def _onchange_purchase_request_id(self):
        for record in self:
            request = record.purchase_request_id
            if not request:
                continue
            record.project_id = request.project_id
            if not record.note:
                record.note = request.note
            record.line_ids = [(5, 0, 0)] + [
                (0, 0, request._prepare_acceptance_line_vals(line))
                for line in request.line_ids
            ]

    def action_load_purchase_request_lines(self):
        for record in self:
            record._onchange_purchase_request_id()
        return True

    @api.onchange("purchase_order_id")
    def _onchange_purchase_order_id(self):
        for record in self:
            order = record.purchase_order_id
            if not order:
                continue
            if order.project_id:
                record.project_id = order.project_id
            record.supplier_id = order.partner_id
            record.line_ids = [(5, 0, 0)] + [
                (0, 0, self._prepare_purchase_order_acceptance_line_vals(line))
                for line in order.order_line
            ]

    def action_load_purchase_order_lines(self):
        for record in self:
            record._onchange_purchase_order_id()
        return True

    def action_submit(self):
        self._sc_require_material_user(_("提交材料验收"))
        for record in self:
            record._sc_require_state({"draft"}, _("提交材料验收"))
            if not record.line_ids:
                raise ValidationError(_("提交前必须维护验收明细。"))
        snapshots = {record.id: record._sc_material_audit_payload() for record in self}
        self._sc_warn_system_defaults_on_action(_("提交材料验收"))
        self.write({"state": "submitted"})
        for record in self:
            record._sc_audit_material_transition(
                "material_acceptance_submitted",
                snapshots[record.id],
                record._sc_material_audit_payload(),
                action_name="action_submit",
            )
        return True

    def action_accept(self):
        self._sc_require_material_manager(_("验收通过"))
        for record in self:
            record._sc_require_state({"submitted"}, _("验收通过"))
            record.line_ids._check_quantities()
        snapshots = {record.id: record._sc_material_audit_payload() for record in self}
        self._sc_warn_system_defaults_on_action(_("验收通过"))
        self.write({"state": "accepted", "rejection_reason": False})
        for record in self:
            record._sc_audit_material_transition(
                "material_acceptance_accepted",
                snapshots[record.id],
                record._sc_material_audit_payload(),
                action_name="action_accept",
            )
        return True

    def action_reject(self):
        self._sc_require_material_manager(_("验收不通过"))
        for record in self:
            record._sc_require_state({"submitted"}, _("验收不通过"))
            if not record.rejection_reason:
                raise ValidationError(_("验收不通过前必须填写不通过原因。"))
        snapshots = {record.id: record._sc_material_audit_payload() for record in self}
        self.write({"state": "rejected"})
        for record in self:
            record._sc_audit_material_transition(
                "material_acceptance_rejected",
                snapshots[record.id],
                record._sc_material_audit_payload(),
                action_name="action_reject",
                reason=record.rejection_reason,
            )
        return True

    def action_cancel(self):
        self._sc_require_material_manager(_("取消材料验收"))
        self._sc_require_state({"draft", "submitted"}, _("取消材料验收"))
        snapshots = {record.id: record._sc_material_audit_payload() for record in self}
        self.write({"state": "cancel"})
        for record in self:
            record._sc_audit_material_transition(
                "material_acceptance_cancelled",
                snapshots[record.id],
                record._sc_material_audit_payload(),
                action_name="action_cancel",
            )
        return True

    def action_reset_draft(self):
        self._sc_require_material_manager(_("重置材料验收为草稿"))
        self._sc_require_state({"cancel", "rejected"}, _("重置材料验收为草稿"))
        snapshots = {record.id: record._sc_material_audit_payload() for record in self}
        self.write({"state": "draft"})
        for record in self:
            record._sc_audit_material_transition(
                "material_acceptance_reset",
                snapshots[record.id],
                record._sc_material_audit_payload(),
                action_name="action_reset_draft",
            )
        return True


class ScMaterialAcceptanceLine(models.Model):
    _name = "sc.material.acceptance.line"
    _description = "材料进场验收明细"
    _inherit = "sc.material.system.default.mixin"
    _order = "acceptance_id, sequence, id"

    acceptance_id = fields.Many2one("sc.material.acceptance", string="验收单", required=True, ondelete="cascade", index=True)
    sequence = fields.Integer(default=10)
    project_id = fields.Many2one("project.project", string="项目", related="acceptance_id.project_id", store=True, index=True)
    purchase_request_line_id = fields.Many2one("sc.material.purchase.request.line", string="来源申请明细", index=True)
    purchase_order_line_id = fields.Many2one("purchase.order.line", string="来源采购明细", index=True)
    product_id = fields.Many2one("product.product", string="材料", required=True, index=True)
    material_catalog_id = fields.Many2one("sc.material.catalog", string="材料档案", index=True)
    material_spec = fields.Char(string="规格型号")
    product_uom_id = fields.Many2one("uom.uom", string="单位")
    planned_qty = fields.Float(string="计划数量")
    received_qty = fields.Float(string="到场数量", required=True)
    accepted_qty = fields.Float(string="合格数量")
    rejected_qty = fields.Float(string="不合格数量")
    sampled_qty = fields.Float(string="送检数量")
    returned_qty = fields.Float(string="退场数量")
    result = fields.Selection([("accepted", "合格"), ("partial", "部分合格"), ("rejected", "不合格")], string="验收结果", default="accepted", index=True)
    quality_status = fields.Selection([("unknown", "未判定"), ("qualified", "合格"), ("unqualified", "不合格")], string="质量状态", default="unknown", index=True)
    issue_note = fields.Text(string="问题说明")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            input_qty = vals.get("qty")
            self._sc_apply_line_defaults(vals)
            default_qty = vals.pop("qty", None)
            if vals.get("received_qty") is None:
                vals["received_qty"] = input_qty or vals.get("accepted_qty") or default_qty or 1.0
                self._sc_mark_system_defaults(vals, ["received_qty"])
            if vals.get("accepted_qty") is None:
                vals["accepted_qty"] = vals.get("received_qty") or 1.0
                self._sc_mark_system_defaults(vals, ["accepted_qty"])
        return super().create(vals_list)

    @api.onchange("product_id")
    def _onchange_product_id(self):
        for record in self:
            if record.product_id and not record.material_catalog_id:
                record.product_uom_id = record.product_id.uom_id
                if not record.material_spec:
                    record.material_spec = record.product_id.default_code or ""

    @api.onchange("material_catalog_id")
    def _onchange_material_catalog_id(self):
        for record in self:
            catalog = record.material_catalog_id
            if not catalog:
                continue
            record.material_spec = catalog.spec_model or record.material_spec

    @api.constrains("received_qty", "accepted_qty", "rejected_qty", "sampled_qty", "returned_qty")
    def _check_quantities(self):
        for record in self:
            if record.received_qty < 0 or record.accepted_qty < 0 or record.rejected_qty < 0 or record.sampled_qty < 0 or record.returned_qty < 0:
                raise ValidationError(_("材料验收数量不能为负数。"))
            if record.accepted_qty + record.rejected_qty > record.received_qty:
                raise ValidationError(_("合格数量与不合格数量之和不能大于到场数量。"))
            if record.returned_qty > record.rejected_qty:
                raise ValidationError(_("退场数量不能大于不合格数量。"))


class ScMaterialInbound(models.Model):
    _name = "sc.material.inbound"
    _description = "材料入库单"
    _inherit = ["mail.thread", "mail.activity.mixin", "sc.material.system.default.mixin"]
    _order = "inbound_date desc, id desc"

    name = fields.Char(string="入库单号", required=True, default="新建", tracking=True)
    project_id = fields.Many2one("project.project", string="项目", required=True, index=True, tracking=True)
    business_category_id = fields.Many2one(
        "sc.business.category",
        string="业务分类",
        index=True,
        ondelete="restrict",
        domain="[('target_model', '=', 'sc.material.inbound')]",
    )
    inbound_date = fields.Date(string="入库日期", default=fields.Date.context_today, index=True, tracking=True)
    acceptance_id = fields.Many2one(
        "sc.material.acceptance",
        string="来源验收单",
        domain="[('state', '=', 'accepted')]",
        index=True,
    )
    supplier_id = fields.Many2one("res.partner", string="供应商", index=True)
    warehouse_id = fields.Many2one(
        "stock.warehouse",
        string="入库仓库",
        required=True,
        index=True,
        default=lambda self: self._default_warehouse_id(),
    )
    dest_location_id = fields.Many2one(
        "stock.location",
        string="入库库位",
        required=True,
        index=True,
        default=lambda self: self._default_dest_location_id(),
    )
    keeper_id = fields.Many2one("res.users", string="仓管员", default=lambda self: self.env.user, index=True)
    stock_picking_id = fields.Many2one("stock.picking", string="库存入库单", readonly=True, copy=False, index=True)
    currency_id = fields.Many2one("res.currency", string="币种", related="project_id.company_id.currency_id", store=True)
    operation_strategy = fields.Selection(
        related="project_id.operation_strategy",
        string="经营方式",
        store=True,
        readonly=True,
        index=True,
    )
    document_status = fields.Char(
        string="单据状态",
        compute="_compute_inbound_formal_visible_fields",
        store=True,
        readonly=True,
    )
    project_name_display = fields.Char(
        string="项目名称",
        compute="_compute_inbound_formal_visible_fields",
        store=True,
        readonly=True,
    )
    amount_total = fields.Monetary(string="金额合计", currency_field="currency_id", compute="_compute_amount_total", store=True)
    tax_included_amount = fields.Monetary(
        string="含税金额",
        currency_field="currency_id",
        compute="_compute_tax_included_amount",
        store=True,
        readonly=True,
    )
    tax_rate_text = fields.Char(
        string="税率",
        compute="_compute_inbound_boundary_fields",
        store=True,
        readonly=True,
    )
    payment_paid_amount = fields.Monetary(
        string="已付款金额",
        currency_field="currency_id",
        compute="_compute_inbound_boundary_fields",
        store=True,
        readonly=True,
    )
    payment_unpaid_amount = fields.Monetary(
        string="未付款金额",
        currency_field="currency_id",
        compute="_compute_inbound_boundary_fields",
        store=True,
        readonly=True,
    )
    settlement_settled_amount = fields.Monetary(
        string="已结算金额",
        currency_field="currency_id",
        compute="_compute_inbound_boundary_fields",
        store=True,
        readonly=True,
    )
    material_name_summary = fields.Char(string="材料名称", compute="_compute_inbound_line_summaries", store=True)
    material_spec_summary = fields.Char(string="规格型号", compute="_compute_inbound_line_summaries", store=True)
    material_uom_summary = fields.Char(string="单位", compute="_compute_inbound_line_summaries", store=True)
    quantity_summary = fields.Char(string="数量", compute="_compute_inbound_line_summaries", store=True)
    total_qty = fields.Float(string="入库数量合计", compute="_compute_inbound_line_summaries", store=True)
    unit_price_summary = fields.Char(string="单价", compute="_compute_inbound_line_summaries", store=True)
    line_note_summary = fields.Char(string="备注", compute="_compute_inbound_line_summaries", store=True)
    payment_status_text = fields.Char(
        string="付款状态",
        compute="_compute_inbound_formal_visible_fields",
        store=True,
        readonly=True,
    )
    settlement_status_text = fields.Char(
        string="结算状态",
        compute="_compute_inbound_formal_visible_fields",
        store=True,
        readonly=True,
    )
    source_created_by = fields.Char(
        string="录入人",
        compute="_compute_inbound_formal_visible_fields",
        store=True,
        readonly=True,
    )
    source_created_at = fields.Datetime(
        string="录入时间",
        compute="_compute_inbound_formal_visible_fields",
        store=True,
        readonly=True,
    )
    buyer_name = fields.Char(
        string="采购人",
        compute="_compute_inbound_formal_visible_fields",
        store=True,
        readonly=True,
    )
    state = fields.Selection(
        [
            ("draft", "草稿"),
            ("submitted", "已提交"),
            ("received", "已入库"),
            ("cancel", "已取消"),
        ],
        string="状态",
        default="draft",
        index=True,
        tracking=True,
    )
    attachment_ids = fields.Many2many(
        "ir.attachment",
        "sc_material_inbound_attachment_rel",
        "inbound_id",
        "attachment_id",
        string="附件",
    )
    line_ids = fields.One2many("sc.material.inbound.line", "inbound_id", string="入库明细")
    note = fields.Text(string="入库说明")
    source_transfer_outbound_id = fields.Many2one(
        "sc.material.outbound",
        string="来源调拨出库单",
        readonly=True,
        copy=False,
        index=True,
    )
    legacy_fact_model = fields.Char(string="来源通用模型", index=True)
    legacy_fact_id = fields.Integer(string="来源通用记录ID", index=True)
    legacy_fact_type = fields.Char(string="来源业务类型", index=True)

    _sql_constraints = [
        (
            "legacy_material_inbound_unique",
            "unique(legacy_fact_model, legacy_fact_id)",
            "来源通用材料入库记录已迁移为入库单。",
        ),
        (
            "source_transfer_outbound_unique",
            "unique(source_transfer_outbound_id)",
            "同一调拨出库单只能生成一张调入入库单。",
        ),
    ]

    @api.model
    def _default_warehouse_id(self):
        return self._sc_default_warehouse_id()

    @api.model
    def _default_dest_location_id(self):
        return self._sc_default_location_id(self._default_warehouse_id())

    @api.depends("line_ids.amount")
    def _compute_amount_total(self):
        for record in self:
            record.amount_total = sum(record.line_ids.mapped("amount"))

    @api.depends("amount_total")
    def _compute_tax_included_amount(self):
        for record in self:
            record.tax_included_amount = record.amount_total

    @api.depends("amount_total")
    def _compute_inbound_boundary_fields(self):
        for record in self:
            amount = record.amount_total or 0.0
            record.tax_rate_text = False
            record.payment_paid_amount = 0.0
            record.payment_unpaid_amount = amount
            record.settlement_settled_amount = 0.0

    @api.depends(
        "project_id",
        "create_uid",
        "create_date",
        "state",
    )
    def _compute_inbound_formal_visible_fields(self):
        state_labels = dict(self._fields["state"].selection)
        for record in self:
            record.document_status = state_labels.get(record.state) or False
            record.project_name_display = record.project_id.display_name if record.project_id else False
            record.payment_status_text = False
            record.settlement_status_text = False
            record.source_created_by = record.create_uid.name if record.create_uid else False
            record.source_created_at = record.create_date or False
            record.buyer_name = False

    @api.depends(
        "line_ids.product_id",
        "line_ids.material_catalog_id",
        "line_ids.material_spec",
        "line_ids.product_uom_id",
        "line_ids.qty",
        "line_ids.unit_price",
        "line_ids.note",
    )
    def _compute_inbound_line_summaries(self):
        for record in self:
            record.material_name_summary = record._summarize_inbound_line_text(
                line.material_catalog_id.display_name or line.product_id.display_name
                for line in record.line_ids
            )
            record.material_spec_summary = record._summarize_inbound_line_text(
                record.line_ids.mapped("material_spec")
            )
            record.material_uom_summary = record._summarize_inbound_line_text(
                record.line_ids.mapped("product_uom_id.name")
            )
            record.quantity_summary = record._summarize_inbound_line_text(
                record._format_summary_number(line.qty) for line in record.line_ids
            )
            record.total_qty = sum(record.line_ids.mapped("qty"))
            record.unit_price_summary = record._summarize_inbound_line_text(
                record._format_summary_number(line.unit_price) for line in record.line_ids
            )
            record.line_note_summary = record._summarize_inbound_line_text(record.line_ids.mapped("note"))

    @api.model
    def _format_summary_number(self, value):
        value = value or 0.0
        return ("%s" % value).rstrip("0").rstrip(".")

    @api.model
    def _summarize_inbound_line_text(self, values, limit=3):
        values = list(values)
        texts = []
        for value in values:
            if value in (False, None, "") or value in texts:
                continue
            texts.append(value)
            if len(texts) >= limit:
                break
        suffix = "等" if len([value for value in values if value not in (False, None, "")]) > len(texts) else ""
        return "、".join(texts) + suffix if texts else False

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env["ir.sequence"]
        for vals in vals_list:
            vals.setdefault("business_category_id", self._sc_resolve_material_business_category_id(vals))
            self._sc_apply_system_defaults(
                vals,
                {
                    "project_id": "_sc_default_project_id",
                    "warehouse_id": "_sc_default_warehouse_id",
                },
            )
            if not vals.get("dest_location_id"):
                vals["dest_location_id"] = self._sc_default_location_id(vals.get("warehouse_id"))
                self._sc_mark_system_defaults(vals, ["dest_location_id"])
            if vals.get("name", "新建") == "新建":
                vals["name"] = seq.next_by_code("sc.material.inbound") or _("材料入库单")
        return super().create(vals_list)

    def init(self):
        self.env.cr.execute(
            """
            UPDATE sc_material_inbound inbound
               SET business_category_id = category.id
              FROM sc_business_category category
             WHERE inbound.business_category_id IS NULL
               AND category.code = 'material.inbound'
               AND category.target_model = 'sc.material.inbound'
            """
        )
        self.env.cr.execute(
            """
            UPDATE sc_material_inbound inbound
               SET project_name_display = COALESCE(project.name->>'zh_CN', project.name->>'en_US')
              FROM project_project project
             WHERE inbound.project_id = project.id
               AND inbound.project_name_display IS NULL
            """
        )

    @api.onchange("warehouse_id")
    def _onchange_warehouse_id(self):
        for record in self:
            if record.warehouse_id and not record.dest_location_id:
                record.dest_location_id = record.warehouse_id.lot_stock_id

    @api.onchange("acceptance_id")
    def _onchange_acceptance_id(self):
        for record in self:
            acceptance = record.acceptance_id
            if not acceptance:
                continue
            record.project_id = acceptance.project_id
            record.supplier_id = acceptance.supplier_id
            record.line_ids = [(5, 0, 0)] + [
                (
                    0,
                    0,
                    {
                        "acceptance_line_id": line.id,
                        "product_id": line.product_id.id,
                        "material_catalog_id": line.material_catalog_id.id,
                        "material_spec": line.material_spec,
                        "product_uom_id": line.product_uom_id.id,
                        "qty": line.accepted_qty or line.received_qty,
                        "unit_price": line.purchase_order_line_id.price_unit
                        or line.purchase_request_line_id.estimated_unit_price
                        or 0.0,
                        "note": line.issue_note,
                    },
                )
                for line in acceptance.line_ids
                if line.result in ("accepted", "partial") and (line.accepted_qty or line.received_qty)
            ]

    def action_load_acceptance_lines(self):
        for record in self:
            record._onchange_acceptance_id()
        return True

    def action_submit(self):
        self._sc_require_material_user(_("提交材料入库"))
        for record in self:
            record._sc_require_state({"draft"}, _("提交材料入库"))
            if not record.line_ids:
                raise ValidationError(_("提交入库前必须维护入库明细。"))
            record.line_ids._check_qty()
        snapshots = {record.id: record._sc_material_audit_payload() for record in self}
        self._sc_warn_system_defaults_on_action(_("提交材料入库"))
        self.write({"state": "submitted"})
        for record in self:
            record._sc_audit_material_transition(
                "material_inbound_submitted",
                snapshots[record.id],
                record._sc_material_audit_payload(),
                action_name="action_submit",
            )
        return True

    def action_receive(self):
        self._sc_require_material_manager(_("确认材料入库"))
        for record in self:
            record._sc_require_state({"submitted"}, _("确认材料入库"))
            record.line_ids._check_qty()
            if record.acceptance_id and record.acceptance_id.state != "accepted":
                raise ValidationError(_("只有验收通过的材料才能办理入库。"))
        snapshots = {record.id: record._sc_material_audit_payload() for record in self}
        self._sc_warn_system_defaults_on_action(_("确认材料入库"))
        self.write({"state": "received"})
        for record in self:
            record._sc_audit_material_transition(
                "material_inbound_received",
                snapshots[record.id],
                record._sc_material_audit_payload(),
                action_name="action_receive",
            )
        return True

    def action_cancel(self):
        self._sc_require_material_manager(_("取消材料入库"))
        self._sc_require_state({"draft", "submitted"}, _("取消材料入库"))
        snapshots = {record.id: record._sc_material_audit_payload() for record in self}
        self.write({"state": "cancel"})
        for record in self:
            record._sc_audit_material_transition(
                "material_inbound_cancelled",
                snapshots[record.id],
                record._sc_material_audit_payload(),
                action_name="action_cancel",
            )
        return True

    def action_reset_draft(self):
        self._sc_require_material_manager(_("重置材料入库为草稿"))
        self._sc_require_state({"cancel"}, _("重置材料入库为草稿"))
        snapshots = {record.id: record._sc_material_audit_payload() for record in self}
        self.write({"state": "draft"})
        for record in self:
            record._sc_audit_material_transition(
                "material_inbound_reset",
                snapshots[record.id],
                record._sc_material_audit_payload(),
                action_name="action_reset_draft",
            )
        return True

class ScMaterialInboundLine(models.Model):
    _name = "sc.material.inbound.line"
    _description = "材料入库明细"
    _inherit = "sc.material.system.default.mixin"
    _order = "inbound_id, sequence, id"

    inbound_id = fields.Many2one("sc.material.inbound", string="入库单", required=True, ondelete="cascade", index=True)
    sequence = fields.Integer(default=10)
    project_id = fields.Many2one("project.project", string="项目", related="inbound_id.project_id", store=True, index=True)
    operation_strategy = fields.Selection(
        related="inbound_id.operation_strategy",
        string="经营方式",
        store=True,
        readonly=True,
        index=True,
    )
    acceptance_line_id = fields.Many2one("sc.material.acceptance.line", string="来源验收明细", index=True)
    product_id = fields.Many2one("product.product", string="材料", required=True, index=True)
    material_catalog_id = fields.Many2one("sc.material.catalog", string="材料档案", index=True)
    material_spec = fields.Char(string="规格型号")
    product_uom_id = fields.Many2one("uom.uom", string="单位")
    qty = fields.Float(string="入库数量", required=True)
    currency_id = fields.Many2one("res.currency", string="币种", related="inbound_id.project_id.company_id.currency_id", store=True)
    unit_price = fields.Monetary(string="单价", currency_field="currency_id")
    amount = fields.Monetary(string="金额", currency_field="currency_id", compute="_compute_amount", store=True)
    note = fields.Char(string="备注")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._sc_apply_line_defaults(vals)
        return super().create(vals_list)

    @api.depends("qty", "unit_price")
    def _compute_amount(self):
        for record in self:
            record.amount = record.qty * record.unit_price

    @api.onchange("product_id")
    def _onchange_product_id(self):
        for record in self:
            if record.product_id and not record.material_catalog_id:
                record.product_uom_id = record.product_id.uom_id
                if not record.material_spec:
                    record.material_spec = record.product_id.default_code or ""

    @api.onchange("material_catalog_id")
    def _onchange_material_catalog_id(self):
        for record in self:
            catalog = record.material_catalog_id
            if not catalog:
                continue
            record.material_spec = catalog.spec_model or record.material_spec

    @api.constrains("qty")
    def _check_qty(self):
        for record in self:
            if record.qty <= 0:
                raise ValidationError(_("入库数量必须大于0。"))


class ScMaterialOutbound(models.Model):
    _name = "sc.material.outbound"
    _description = "材料出库单"
    _inherit = ["mail.thread", "mail.activity.mixin", "tier.validation", "sc.material.system.default.mixin"]
    _order = "outbound_date desc, id desc"

    name = fields.Char(string="出库单号", required=True, default="新建", tracking=True)
    business_category_id = fields.Many2one(
        "sc.business.category",
        string="业务分类",
        index=True,
        ondelete="restrict",
        domain="[('target_model', '=', 'sc.material.outbound')]",
    )
    outbound_type = fields.Selection(
        [
            ("issue", "领用出库"),
            ("return", "退库"),
            ("transfer", "调拨"),
            ("loss", "损耗"),
        ],
        string="出库类型",
        default=lambda self: self.env.context.get("default_outbound_type") or "issue",
        required=True,
        index=True,
        tracking=True,
    )
    project_id = fields.Many2one("project.project", string="项目", required=True, index=True, tracking=True)
    company_id = fields.Many2one(
        "res.company",
        string="公司",
        related="project_id.company_id",
        store=True,
        readonly=True,
        index=True,
    )
    outbound_date = fields.Date(string="出库日期", default=fields.Date.context_today, index=True, tracking=True)
    warehouse_id = fields.Many2one(
        "stock.warehouse",
        string="出库仓库",
        required=True,
        index=True,
        default=lambda self: self._sc_default_warehouse_id(),
    )
    source_location_id = fields.Many2one(
        "stock.location",
        string="出库库位",
        required=True,
        index=True,
        default=lambda self: self._sc_default_location_id(),
    )
    receiver_id = fields.Many2one("res.partner", string="领用单位", index=True)
    receiver_user_id = fields.Many2one("res.users", string="领料人", index=True)
    keeper_id = fields.Many2one("res.users", string="仓管员", default=lambda self: self.env.user, index=True)
    dest_warehouse_id = fields.Many2one("stock.warehouse", string="调入仓库", index=True)
    attachment_ids = fields.Many2many(
        "ir.attachment",
        "sc_material_outbound_attachment_rel",
        "outbound_id",
        "attachment_id",
        string="出库附件",
    )
    dest_location_id = fields.Many2one("stock.location", string="调入库位", index=True)
    transfer_inbound_id = fields.Many2one(
        "sc.material.inbound",
        string="调入入库单",
        readonly=True,
        copy=False,
        index=True,
    )
    stock_picking_id = fields.Many2one("stock.picking", string="库存出库单", readonly=True, copy=False, index=True)
    state = fields.Selection(
        [
            ("draft", "草稿"),
            ("submitted", "已提交"),
            ("issued", "已出库"),
            ("cancel", "已取消"),
        ],
        string="状态",
        default="draft",
        index=True,
        tracking=True,
    )
    line_ids = fields.One2many("sc.material.outbound.line", "outbound_id", string="出库明细")
    purpose = fields.Char(string="领用用途")
    reject_reason = fields.Char(string="审批驳回原因", readonly=True, copy=False)
    note = fields.Text(string="出库说明")
    currency_id = fields.Many2one("res.currency", string="币种", required=True, default=lambda self: self.env.company.currency_id.id)
    amount_total = fields.Monetary(string="出库金额", currency_field="currency_id", compute="_compute_amount_total", store=True)
    legacy_fact_model = fields.Char(string="来源通用模型", index=True)
    legacy_fact_id = fields.Integer(string="来源通用记录ID", index=True)
    legacy_fact_type = fields.Char(string="来源业务类型", index=True)

    _sql_constraints = [
        (
            "legacy_material_outbound_unique",
            "unique(legacy_fact_model, legacy_fact_id)",
            "来源通用材料出库记录已迁移为出库单。",
        ),
    ]

    @api.depends("line_ids.amount")
    def _compute_amount_total(self):
        for record in self:
            record.amount_total = sum(record.line_ids.mapped("amount"))

    def _material_outbound_category_code(self):
        self.ensure_one()
        return {
            "issue": "material.outbound",
            "return": "material.return",
            "transfer": "material.transfer",
            "loss": "material.loss",
        }.get(self.outbound_type or "issue", "material.outbound")

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env["ir.sequence"]
        for vals in vals_list:
            vals.setdefault("business_category_id", self._sc_resolve_material_business_category_id(vals))
            self._sc_apply_system_defaults(
                vals,
                {
                    "project_id": "_sc_default_project_id",
                    "warehouse_id": "_sc_default_warehouse_id",
                },
            )
            if not vals.get("source_location_id"):
                vals["source_location_id"] = self._sc_default_location_id(vals.get("warehouse_id"))
                self._sc_mark_system_defaults(vals, ["source_location_id"])
            if vals.get("name", "新建") == "新建":
                vals["name"] = seq.next_by_code("sc.material.outbound") or _("材料出库单")
        return super().create(vals_list)

    def init(self):
        self.env.cr.execute(
            """
            UPDATE sc_material_outbound outbound
               SET business_category_id = category.id
              FROM sc_business_category category
             WHERE outbound.business_category_id IS NULL
               AND category.code = CASE COALESCE(outbound.outbound_type, 'issue')
                       WHEN 'return' THEN 'material.return'
                       WHEN 'transfer' THEN 'material.transfer'
                       WHEN 'loss' THEN 'material.loss'
                       ELSE 'material.outbound'
                   END
               AND category.target_model = 'sc.material.outbound'
            """
        )

    def action_submit(self):
        self._sc_require_material_user(_("提交材料出库"))
        for record in self:
            record._sc_require_state({"draft"}, _("提交材料出库"))
            if not record.line_ids:
                raise ValidationError(_("提交出库前必须维护出库明细。"))
            if record.outbound_type == "transfer" and not record.dest_warehouse_id:
                raise ValidationError(_("材料调拨必须维护调入仓库。"))
            if record.outbound_type == "loss" and not record.purpose:
                raise ValidationError(_("材料损耗必须填写损耗原因。"))
            record.line_ids._check_qty()
        snapshots = {record.id: record._sc_material_audit_payload() for record in self}
        self._sc_warn_system_defaults_on_action(_("提交材料出库"))
        self.write({"state": "submitted"})
        for record in self:
            record._sc_audit_material_transition(
                "material_outbound_submitted",
                snapshots[record.id],
                record._sc_material_audit_payload(),
                action_name="action_submit",
            )
        return True

    def action_issue(self):
        self._sc_require_material_manager(_("确认材料出库"))
        for record in self:
            record._sc_require_state({"submitted"}, _("确认材料出库"))
            record.line_ids._check_qty()
        records_to_issue = self.browse()
        for record in self:
            if record._requires_loss_approval() and record.validation_status != "validated":
                record._request_material_outbound_approval()
                continue
            records_to_issue |= record
        if not records_to_issue:
            return True
        return records_to_issue._complete_issue()

    def _complete_issue(self):
        self.ensure_one() if len(self) == 1 else None
        snapshots = {record.id: record._sc_material_audit_payload() for record in self}
        self._sc_warn_system_defaults_on_action(_("确认材料出库"))
        self.with_context(skip_validation_check=True).write({"state": "issued", "reject_reason": False})
        for record in self:
            record._sc_audit_material_transition(
                "material_outbound_issued",
                snapshots[record.id],
                record._sc_material_audit_payload(),
                action_name="action_issue",
            )
            if record._sc_business_category_cost_trigger(
                record._material_outbound_category_code(),
                "issue_project_cost_ledger",
                default=record.outbound_type in ("issue", "loss"),
            ):
                record._sync_cost_ledger_after_issue()
            record._sync_transfer_inbound_after_issue()
        return True

    def _requires_loss_approval(self):
        self.ensure_one()
        if self.outbound_type != "loss":
            return False
        return self.env["sc.approval.policy"].is_approval_required(self._name, company=self.company_id)

    def _request_material_outbound_approval(self):
        self.ensure_one()
        if self.review_ids and self.validation_status == "rejected":
            self.restart_validation()
        elif not self.review_ids or self.validation_status == "no":
            company = self.company_id or self.env.company
            reviews = self.with_company(company).with_context(
                allowed_company_ids=[company.id],
            ).request_validation()
            if not reviews:
                raise ValidationError(_("材料损耗已启用审批，但没有匹配的统一审批规则，请检查业务审批配置。"))
        else:
            return True
        self.sudo().message_post(body=_("材料损耗已发起统一审批，审批通过后才能确认损耗并写入项目成本。"))
        return True

    def _check_state_from_condition(self):
        self.ensure_one()
        parent = getattr(super(), "_check_state_from_condition", None)
        base_ok = parent() if parent else False
        return base_ok or self.state == "submitted"

    def _get_tier_reject_reason(self):
        self.ensure_one()
        reviews = self.review_ids.filtered(lambda review: review.status == "rejected" and review.comment)
        if reviews:
            return reviews.sorted(lambda review: review.write_date or review.create_date, reverse=True)[0].comment
        return _("统一审批驳回（未填写原因）")

    def action_on_tier_approved(self):
        for record in self:
            if record.state != "submitted":
                raise ValidationError(_("只有已提交的材料损耗单可以完成统一审批回调。"))
            if record.outbound_type != "loss":
                continue
            if record.validation_status != "validated":
                raise ValidationError(_("材料损耗尚未完成统一审批流程。"))
            record._complete_issue()

    def action_on_tier_rejected(self, reason=None):
        for record in self:
            if record.state != "submitted" or record.outbound_type != "loss":
                continue
            record.with_context(skip_validation_check=True).write(
                {"reject_reason": reason or record._get_tier_reject_reason()}
            )

    def _prepare_transfer_inbound_line_vals(self, line):
        self.ensure_one()
        return {
            "product_id": line.product_id.id,
            "material_catalog_id": line.material_catalog_id.id,
            "material_spec": line.material_spec,
            "product_uom_id": line.product_uom_id.id or line.product_id.uom_id.id,
            "qty": line.qty,
            "unit_price": line.unit_price or 0.0,
            "note": line.note,
        }

    def _prepare_transfer_inbound_vals(self):
        self.ensure_one()
        if self.outbound_type != "transfer":
            return {}
        if not self.dest_warehouse_id:
            raise ValidationError(_("材料调拨必须维护调入仓库。"))
        dest_location_id = self.dest_location_id.id or self._sc_default_location_id(self.dest_warehouse_id.id)
        if not dest_location_id:
            raise ValidationError(_("材料调拨必须维护调入库位。"))
        return {
            "project_id": self.project_id.id,
            "inbound_date": self.outbound_date or fields.Date.context_today(self),
            "warehouse_id": self.dest_warehouse_id.id,
            "dest_location_id": dest_location_id,
            "source_transfer_outbound_id": self.id,
            "note": _("来源调拨出库单：%s") % (self.name or self.display_name),
            "line_ids": [
                (0, 0, self._prepare_transfer_inbound_line_vals(line))
                for line in self.line_ids
            ],
        }

    def _sync_transfer_inbound_after_issue(self):
        self.ensure_one()
        if self.outbound_type != "transfer":
            return False
        Inbound = self.env["sc.material.inbound"].sudo()
        inbound = self.transfer_inbound_id or Inbound.search(
            [("source_transfer_outbound_id", "=", self.id)],
            limit=1,
        )
        if not inbound:
            inbound = Inbound.create(self._prepare_transfer_inbound_vals())
        if inbound.state == "draft":
            inbound.action_submit()
        if inbound.state == "submitted":
            inbound.action_receive()
        if inbound.state != "received":
            raise ValidationError(_("调拨入库单必须处于已入库状态。"))
        if self.transfer_inbound_id != inbound:
            self.sudo().write({"transfer_inbound_id": inbound.id})
        return inbound

    def action_open_transfer_inbound(self):
        self.ensure_one()
        inbound = self.transfer_inbound_id or self.env["sc.material.inbound"].sudo().search(
            [("source_transfer_outbound_id", "=", self.id)],
            limit=1,
        )
        if not inbound:
            raise ValidationError(_("当前调拨出库单尚未生成调入入库单。"))
        action = self.env.ref("smart_construction_core.action_sc_material_inbound_handling").sudo().read()[0]
        action.update(
            {
                "views": [(self.env.ref("smart_construction_core.view_sc_material_inbound_form").id, "form")],
                "res_id": inbound.id,
                "domain": [("id", "=", inbound.id)],
                "context": {"default_source_transfer_outbound_id": self.id},
            }
        )
        return action

    def _prepare_cost_ledger_vals(self, line, cost_code):
        material_name = line.material_catalog_id.display_name or line.product_id.display_name or self.name
        return {
            "project_id": self.project_id.id,
            "cost_code_id": cost_code.id,
            "date": self.outbound_date or fields.Date.context_today(self),
            "qty": line.qty,
            "uom_id": line.product_uom_id.id or line.product_id.uom_id.id,
            "amount": line.amount,
            "currency_id": self.currency_id.id,
            "partner_id": self.receiver_id.id,
            "source_model": self._name,
            "source_id": self.id,
            "source_line_id": line.id,
            "note": "%s - %s" % (self.name, material_name),
        }

    def _sync_cost_ledger_after_issue(self):
        self.ensure_one()
        cost_code = self._sc_get_or_create_material_cost_code()
        Ledger = self.env["project.cost.ledger"].sudo()
        for line in self.line_ids:
            vals = self._prepare_cost_ledger_vals(line, cost_code)
            ledger = Ledger.search(
                [
                    ("source_model", "=", self._name),
                    ("source_id", "=", self.id),
                    ("source_line_id", "=", line.id),
                ],
                limit=1,
            )
            if ledger:
                ledger.write(vals)
            else:
                Ledger.create(vals)

    def action_cancel(self):
        self._sc_require_material_manager(_("取消材料出库"))
        self._sc_require_state({"draft", "submitted"}, _("取消材料出库"))
        snapshots = {record.id: record._sc_material_audit_payload() for record in self}
        self.write({"state": "cancel"})
        for record in self:
            record._sc_audit_material_transition(
                "material_outbound_cancelled",
                snapshots[record.id],
                record._sc_material_audit_payload(),
                action_name="action_cancel",
            )
        return True

    def action_reset_draft(self):
        self._sc_require_material_manager(_("重置材料出库为草稿"))
        self._sc_require_state({"cancel"}, _("重置材料出库为草稿"))
        snapshots = {record.id: record._sc_material_audit_payload() for record in self}
        self.write({"state": "draft"})
        for record in self:
            record._sc_audit_material_transition(
                "material_outbound_reset",
                snapshots[record.id],
                record._sc_material_audit_payload(),
                action_name="action_reset_draft",
            )
        return True


class ScMaterialOutboundLine(models.Model):
    _name = "sc.material.outbound.line"
    _description = "材料出库明细"
    _inherit = "sc.material.system.default.mixin"
    _order = "outbound_id, sequence, id"

    outbound_id = fields.Many2one("sc.material.outbound", string="出库单", required=True, ondelete="cascade", index=True)
    sequence = fields.Integer(default=10)
    project_id = fields.Many2one("project.project", string="项目", related="outbound_id.project_id", store=True, index=True)
    product_id = fields.Many2one("product.product", string="材料", required=True, index=True)
    material_catalog_id = fields.Many2one("sc.material.catalog", string="材料档案", index=True)
    material_spec = fields.Char(string="规格型号")
    product_uom_id = fields.Many2one("uom.uom", string="单位")
    qty = fields.Float(string="出库数量", required=True)
    currency_id = fields.Many2one("res.currency", string="币种", related="outbound_id.currency_id", store=True, readonly=True)
    unit_price = fields.Monetary(string="出库单价", currency_field="currency_id")
    amount = fields.Monetary(string="出库金额", currency_field="currency_id", compute="_compute_amount", store=True)
    note = fields.Char(string="备注")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._sc_apply_line_defaults(vals)
        return super().create(vals_list)

    @api.depends("qty", "unit_price")
    def _compute_amount(self):
        for record in self:
            record.amount = record.qty * record.unit_price

    @api.onchange("product_id")
    def _onchange_product_id(self):
        for record in self:
            if record.product_id and not record.material_catalog_id:
                record.product_uom_id = record.product_id.uom_id
                if not record.material_spec:
                    record.material_spec = record.product_id.default_code or ""

    @api.onchange("material_catalog_id")
    def _onchange_material_catalog_id(self):
        for record in self:
            catalog = record.material_catalog_id
            if not catalog:
                continue
            record.material_spec = catalog.spec_model or record.material_spec

    @api.constrains("qty")
    def _check_qty(self):
        for record in self:
            if record.qty <= 0:
                raise ValidationError(_("出库数量必须大于0。"))


class ScMaterialRfq(models.Model):
    _name = "sc.material.rfq"
    _description = "材料询比价"
    _inherit = ["mail.thread", "mail.activity.mixin", "sc.material.system.default.mixin"]
    _order = "rfq_date desc, id desc"

    name = fields.Char(string="询价单号", required=True, default="新建", tracking=True)
    project_id = fields.Many2one("project.project", string="项目", required=True, index=True, tracking=True)
    business_category_id = fields.Many2one(
        "sc.business.category",
        string="业务分类",
        index=True,
        ondelete="restrict",
        domain="[('target_model', '=', 'sc.material.rfq')]",
    )
    purchase_request_id = fields.Many2one("sc.material.purchase.request", string="来源采购申请", index=True)
    source_material_plan_id = fields.Many2one("project.material.plan", string="来源材料计划", index=True)
    rfq_date = fields.Date(string="询价日期", default=fields.Date.context_today, index=True)
    due_date = fields.Date(string="报价截止日期", index=True)
    owner_id = fields.Many2one("res.users", string="经办人", default=lambda self: self.env.user, index=True)
    contact_name = fields.Char(string="联系人")
    contact_phone = fields.Char(string="联系电话")
    supplier_ids = fields.Many2many("res.partner", string="参与供应商", compute="_compute_supplier_ids")
    selected_supplier_id = fields.Many2one("res.partner", string="选定供应商", index=True, tracking=True)
    state = fields.Selection(
        [("draft", "草稿"), ("submitted", "已发起"), ("selected", "已定价"), ("cancel", "已取消")],
        string="状态",
        default="draft",
        index=True,
        tracking=True,
    )
    attachment_ids = fields.Many2many(
        "ir.attachment",
        "sc_material_rfq_attachment_rel",
        "rfq_id",
        "attachment_id",
        string="附件",
    )
    line_ids = fields.One2many("sc.material.rfq.line", "rfq_id", string="报价明细")
    note = fields.Text(string="询价说明")
    legacy_fact_model = fields.Char(string="来源通用模型", index=True)
    legacy_fact_id = fields.Integer(string="来源通用记录ID", index=True)
    legacy_fact_type = fields.Char(string="来源业务类型", index=True)

    _sql_constraints = [
        ("legacy_material_rfq_unique", "unique(legacy_fact_model, legacy_fact_id)", "来源通用询比价已迁移为专业询比价。"),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env["ir.sequence"]
        for vals in vals_list:
            vals.setdefault("business_category_id", self._sc_resolve_material_business_category_id(vals))
            self._sc_apply_system_defaults(vals, {"project_id": "_sc_default_project_id"})
            if vals.get("name", "新建") == "新建":
                vals["name"] = seq.next_by_code("sc.material.rfq") or _("材料询比价")
        return super().create(vals_list)

    def init(self):
        self.env.cr.execute(
            """
            UPDATE sc_material_rfq rfq
               SET business_category_id = category.id
              FROM sc_business_category category
             WHERE rfq.business_category_id IS NULL
               AND category.code = 'material.rfq'
               AND category.target_model = 'sc.material.rfq'
            """
        )

    @api.depends("line_ids.supplier_id")
    def _compute_supplier_ids(self):
        for record in self:
            record.supplier_ids = record.line_ids.mapped("supplier_id")

    def action_submit(self):
        self._sc_require_purchase_user(_("提交材料询比价"))
        for record in self:
            record._sc_require_state({"draft"}, _("提交材料询比价"))
            if not record.line_ids:
                raise ValidationError(_("发起询价前必须维护报价明细。"))
            record.line_ids._check_values()
        snapshots = {record.id: record._sc_material_audit_payload() for record in self}
        self._sc_warn_system_defaults_on_action(_("提交材料询比价"))
        self.write({"state": "submitted"})
        for record in self:
            record._sc_audit_material_transition(
                "material_rfq_submitted",
                snapshots[record.id],
                record._sc_material_audit_payload(),
                action_name="action_submit",
            )
        return True

    def action_select(self):
        self._sc_require_purchase_manager(_("选定材料报价"))
        selected_suppliers = {}
        for record in self:
            record._sc_require_state({"submitted"}, _("选定材料报价"))
            record.line_ids._check_values()
            selected = record.line_ids.filtered("selected")
            if not selected:
                raise ValidationError(_("定价前必须选择至少一条报价。"))
            selected_suppliers[record.id] = selected[0].supplier_id.id
        snapshots = {record.id: record._sc_material_audit_payload() for record in self}
        self._sc_warn_system_defaults_on_action(_("选定材料报价"))
        for record in self:
            record.write(
                {
                    "selected_supplier_id": selected_suppliers[record.id],
                    "state": "selected",
                }
            )
        for record in self:
            record._sc_audit_material_transition(
                "material_rfq_selected",
                snapshots[record.id],
                record._sc_material_audit_payload(),
                action_name="action_select",
            )
        return True

    def action_cancel(self):
        self._sc_require_purchase_manager(_("取消材料询比价"))
        self._sc_require_state({"draft", "submitted"}, _("取消材料询比价"))
        snapshots = {record.id: record._sc_material_audit_payload() for record in self}
        self.write({"state": "cancel"})
        for record in self:
            record._sc_audit_material_transition(
                "material_rfq_cancelled",
                snapshots[record.id],
                record._sc_material_audit_payload(),
                action_name="action_cancel",
            )
        return True

    def action_reset_draft(self):
        self._sc_require_purchase_manager(_("重置材料询比价为草稿"))
        self._sc_require_state({"cancel"}, _("重置材料询比价为草稿"))
        snapshots = {record.id: record._sc_material_audit_payload() for record in self}
        self.write({"state": "draft"})
        for record in self:
            record._sc_audit_material_transition(
                "material_rfq_reset",
                snapshots[record.id],
                record._sc_material_audit_payload(),
                action_name="action_reset_draft",
            )
        return True

    def _get_purchase_order_lines(self):
        self.ensure_one()
        selected = self.line_ids.filtered("selected")
        if selected:
            return selected
        if self.selected_supplier_id:
            supplier_lines = self.line_ids.filtered(lambda line: line.supplier_id == self.selected_supplier_id)
            if supplier_lines:
                return supplier_lines
        return self.line_ids.filtered(lambda line: line.quote_status != "abandoned")

    def _prepare_purchase_order_line_vals(self, line):
        material_name = line.material_catalog_id.display_name if line.material_catalog_id else line.product_id.display_name
        name = material_name
        if line.material_spec:
            name = "%s / %s" % (name, line.material_spec)
        if line.note:
            name = "%s\n%s" % (name, line.note)
        return {
            "product_id": line.product_id.id,
            "name": name,
            "product_qty": line.qty or 1.0,
            "product_uom": line.product_uom_id.id or line.product_id.uom_po_id.id or line.product_id.uom_id.id,
            "price_unit": line.unit_price,
            "date_planned": fields.Datetime.now(),
            "project_id": self.project_id.id,
            "plan_line_id": line.source_material_plan_line_id.id,
            "source_material_rfq_line_id": line.id,
            "source_material_purchase_request_line_id": line.source_material_purchase_request_line_id.id,
        }

    def action_create_purchase_order(self):
        self._sc_require_purchase_manager(_("生成采购订单"))
        purchase_orders = self.env["purchase.order"]
        for record in self:
            lines = record._get_purchase_order_lines()
            if not lines:
                raise ValidationError(_("生成采购订单前必须维护有效报价明细。"))
            suppliers = lines.mapped("supplier_id")
            if not suppliers:
                raise ValidationError(_("生成采购订单前报价明细必须有供应商。"))
            for supplier in suppliers:
                grouped_lines = lines.filtered(lambda line: line.supplier_id == supplier)
                purchase_orders |= self.env["purchase.order"].create(
                    {
                        "partner_id": supplier.id,
                        "project_id": record.project_id.id,
                        "plan_id": record.source_material_plan_id.id,
                        "source_material_rfq_id": record.id,
                        "origin": record.name,
                        "order_line": [
                            (0, 0, record._prepare_purchase_order_line_vals(line))
                            for line in grouped_lines
                        ],
                    }
                )
        action = self.env.ref("smart_construction_core.action_sc_purchase_order").sudo().read()[0]
        action["domain"] = [("id", "in", purchase_orders.ids)]
        if len(purchase_orders) == 1:
            action.update(
                {
                    "views": [(self.env.ref("purchase.purchase_order_form").id, "form")],
                    "res_id": purchase_orders.id,
                }
            )
        return action


class ScMaterialRfqLine(models.Model):
    _name = "sc.material.rfq.line"
    _description = "材料询比价明细"
    _inherit = "sc.material.system.default.mixin"
    _order = "rfq_id, sequence, id"

    rfq_id = fields.Many2one("sc.material.rfq", string="询价单", required=True, ondelete="cascade", index=True)
    sequence = fields.Integer(default=10)
    project_id = fields.Many2one("project.project", string="项目", related="rfq_id.project_id", store=True, index=True)
    source_material_plan_line_id = fields.Many2one("project.material.plan.line", string="来源计划明细", index=True)
    source_material_purchase_request_line_id = fields.Many2one(
        "sc.material.purchase.request.line",
        string="来源申请明细",
        index=True,
    )
    supplier_id = fields.Many2one("res.partner", string="供应商", required=True, index=True)
    supplier_contact_name = fields.Char(string="供应商联系人")
    supplier_contact_phone = fields.Char(string="供应商联系电话")
    quote_status = fields.Selection(
        [
            ("pending", "待报价"),
            ("quoted", "已报价"),
            ("abandoned", "放弃报价"),
        ],
        string="报价状态",
        default="pending",
        required=True,
        index=True,
    )
    product_id = fields.Many2one("product.product", string="材料", required=True, index=True)
    material_catalog_id = fields.Many2one("sc.material.catalog", string="材料档案", index=True)
    material_spec = fields.Char(string="规格型号")
    product_uom_id = fields.Many2one("uom.uom", string="单位")
    qty = fields.Float(string="询价数量", required=True)
    currency_id = fields.Many2one("res.currency", string="币种", required=True, default=lambda self: self.env.company.currency_id.id)
    unit_price = fields.Monetary(string="报价单价", currency_field="currency_id", required=True)
    amount = fields.Monetary(string="报价金额", currency_field="currency_id", compute="_compute_amount", store=True)
    tax_rate = fields.Float(string="税率%")
    selected = fields.Boolean(string="选中")
    note = fields.Char(string="备注")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._sc_apply_line_defaults(vals, require_supplier=True, require_unit_price=True)
            self._fill_supplier_contact_defaults(vals)
        return super().create(vals_list)

    @api.model
    def _fill_supplier_contact_defaults(self, vals):
        supplier_id = vals.get("supplier_id")
        if not supplier_id:
            return vals
        supplier = self.env["res.partner"].browse(supplier_id)
        if not vals.get("supplier_contact_name"):
            vals["supplier_contact_name"] = supplier.name
        if not vals.get("supplier_contact_phone"):
            vals["supplier_contact_phone"] = supplier.mobile or supplier.phone
        return vals

    @api.depends("qty", "unit_price")
    def _compute_amount(self):
        for record in self:
            record.amount = record.qty * record.unit_price

    @api.onchange("product_id")
    def _onchange_product_id(self):
        for record in self:
            if record.product_id and not record.material_catalog_id:
                record.product_uom_id = record.product_id.uom_id
                if not record.material_spec:
                    record.material_spec = record.product_id.default_code or ""

    @api.onchange("material_catalog_id")
    def _onchange_material_catalog_id(self):
        for record in self:
            catalog = record.material_catalog_id
            if catalog and not record.material_spec:
                record.material_spec = catalog.spec_model or ""

    @api.onchange("supplier_id")
    def _onchange_supplier_id(self):
        for record in self:
            if record.supplier_id:
                if not record.supplier_contact_name:
                    record.supplier_contact_name = record.supplier_id.name
                if not record.supplier_contact_phone:
                    record.supplier_contact_phone = record.supplier_id.mobile or record.supplier_id.phone

    @api.constrains("qty", "unit_price", "tax_rate")
    def _check_values(self):
        for record in self:
            if record.qty <= 0:
                raise ValidationError(_("询价数量必须大于0。"))
            if record.unit_price < 0:
                raise ValidationError(_("报价单价不能为负数。"))
            if record.tax_rate < 0:
                raise ValidationError(_("税率不能为负数。"))


class ScMaterialSettlement(models.Model):
    _name = "sc.material.settlement"
    _description = "材料结算"
    _inherit = ["mail.thread", "mail.activity.mixin", "sc.material.system.default.mixin"]
    _order = "settlement_date desc, id desc"

    name = fields.Char(string="结算单号", required=True, default="新建", tracking=True)
    project_id = fields.Many2one("project.project", string="项目", required=True, index=True, tracking=True)
    business_category_id = fields.Many2one(
        "sc.business.category",
        string="业务分类",
        index=True,
        ondelete="restrict",
        domain="[('target_model', '=', 'sc.material.settlement')]",
    )
    supplier_id = fields.Many2one("res.partner", string="供应商", required=True, index=True, tracking=True)
    purchase_order_id = fields.Many2one("purchase.order", string="采购订单", index=True)
    settlement_date = fields.Date(string="结算日期", default=fields.Date.context_today, index=True)
    owner_id = fields.Many2one("res.users", string="经办人", default=lambda self: self.env.user, index=True)
    currency_id = fields.Many2one("res.currency", string="币种", required=True, default=lambda self: self.env.company.currency_id.id)
    amount_untaxed = fields.Monetary(string="未税金额", currency_field="currency_id", compute="_compute_amounts", store=True)
    tax_amount = fields.Monetary(string="税额", currency_field="currency_id", compute="_compute_amounts", store=True)
    amount_total = fields.Monetary(string="结算金额", currency_field="currency_id", compute="_compute_amounts", store=True)
    payment_request_id = fields.Many2one(
        "payment.request",
        string="付款申请",
        readonly=True,
        copy=False,
        index=True,
    )
    payment_request_ids = fields.One2many(
        "payment.request",
        "material_settlement_id",
        string="关联付款申请",
        readonly=True,
    )
    payment_request_count = fields.Integer(
        string="付款申请数",
        compute="_compute_payment_summary",
    )
    payment_requested_amount = fields.Monetary(
        string="已申请付款",
        currency_field="currency_id",
        compute="_compute_payment_summary",
    )
    attachment_ids = fields.Many2many(
        "ir.attachment",
        "sc_material_settlement_attachment_rel",
        "settlement_id",
        "attachment_id",
        string="结算附件",
    )
    payment_paid_amount = fields.Monetary(
        string="已付款",
        currency_field="currency_id",
        compute="_compute_payment_summary",
    )
    payment_remaining_amount = fields.Monetary(
        string="未付款",
        currency_field="currency_id",
        compute="_compute_payment_summary",
    )
    state = fields.Selection(
        [("draft", "草稿"), ("submitted", "已提交"), ("confirmed", "已确认"), ("cancel", "已取消")],
        string="状态",
        default="draft",
        index=True,
        tracking=True,
    )
    line_ids = fields.One2many("sc.material.settlement.line", "settlement_id", string="结算明细")
    note = fields.Text(string="结算说明")
    legacy_fact_model = fields.Char(string="来源通用模型", index=True)
    legacy_fact_id = fields.Integer(string="来源通用记录ID", index=True)
    legacy_fact_type = fields.Char(string="来源业务类型", index=True)

    _sql_constraints = [
        ("legacy_material_settlement_unique", "unique(legacy_fact_model, legacy_fact_id)", "来源通用材料结算已迁移为专业结算。"),
    ]

    @api.depends("line_ids.amount_untaxed", "line_ids.tax_amount", "line_ids.amount_total")
    def _compute_amounts(self):
        for record in self:
            record.amount_untaxed = sum(record.line_ids.mapped("amount_untaxed"))
            record.tax_amount = sum(record.line_ids.mapped("tax_amount"))
            record.amount_total = sum(record.line_ids.mapped("amount_total"))

    @api.depends(
        "amount_total",
        "payment_request_ids.amount",
        "payment_request_ids.state",
        "payment_request_ids.ledger_line_ids.amount",
    )
    def _compute_payment_summary(self):
        for record in self:
            requests = record.payment_request_ids.filtered(lambda req: req.state != "cancel")
            requested_amount = sum(requests.mapped("amount"))
            paid_amount = sum(requests.mapped("ledger_line_ids.amount"))
            remaining = (record.amount_total or 0.0) - (paid_amount or 0.0)
            record.payment_request_count = len(requests)
            record.payment_requested_amount = requested_amount
            record.payment_paid_amount = paid_amount
            record.payment_remaining_amount = max(remaining, 0.0)

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env["ir.sequence"]
        for vals in vals_list:
            vals.setdefault("business_category_id", self._sc_resolve_material_business_category_id(vals))
            self._sc_apply_system_defaults(
                vals,
                {
                    "project_id": "_sc_default_project_id",
                    "supplier_id": "_sc_default_supplier_id",
                },
            )
            if vals.get("name", "新建") == "新建":
                vals["name"] = seq.next_by_code("sc.material.settlement") or _("材料结算")
        return super().create(vals_list)

    def init(self):
        self.env.cr.execute(
            """
            UPDATE sc_material_settlement settlement
               SET business_category_id = category.id
              FROM sc_business_category category
             WHERE settlement.business_category_id IS NULL
               AND category.code = 'material.settlement'
               AND category.target_model = 'sc.material.settlement'
            """
        )

    def action_submit(self):
        self._sc_require_material_user(_("提交材料结算"))
        for record in self:
            record._sc_require_state({"draft"}, _("提交材料结算"))
            if not record.line_ids:
                raise ValidationError(_("提交结算前必须维护结算明细。"))
            record.line_ids._check_values()
        snapshots = {record.id: record._sc_material_audit_payload() for record in self}
        self._sc_warn_system_defaults_on_action(_("提交材料结算"))
        self.write({"state": "submitted"})
        for record in self:
            record._sc_audit_material_transition(
                "material_settlement_submitted",
                snapshots[record.id],
                record._sc_material_audit_payload(),
                action_name="action_submit",
            )
        return True

    def action_confirm(self):
        self._sc_require_material_manager(_("确认材料结算"))
        for record in self:
            record._sc_require_state({"submitted"}, _("确认材料结算"))
            record.line_ids._check_values()
        snapshots = {record.id: record._sc_material_audit_payload() for record in self}
        self._sc_warn_system_defaults_on_action(_("确认材料结算"))
        self.write({"state": "confirmed"})
        for record in self:
            record._sync_downstream_after_confirm()
            record._sc_audit_material_transition(
                "material_settlement_confirmed",
                snapshots[record.id],
                record._sc_material_audit_payload(),
                action_name="action_confirm",
            )
        return True

    def _get_or_create_material_cost_code(self):
        return self._sc_get_or_create_material_cost_code()

    def _prepare_cost_ledger_vals(self, line, cost_code):
        material_name = line.material_catalog_id.display_name or line.product_id.display_name or self.name
        return {
            "project_id": self.project_id.id,
            "cost_code_id": cost_code.id,
            "date": self.settlement_date or fields.Date.context_today(self),
            "qty": line.qty,
            "uom_id": line.product_uom_id.id or line.product_id.uom_id.id,
            "amount": line.amount_untaxed,
            "currency_id": self.currency_id.id,
            "partner_id": self.supplier_id.id,
            "source_model": self._name,
            "source_id": self.id,
            "source_line_id": line.id,
            "note": "%s - %s" % (self.name, material_name),
        }

    def _sync_cost_ledger_after_confirm(self):
        self.ensure_one()
        cost_code = self._get_or_create_material_cost_code()
        Ledger = self.env["project.cost.ledger"].sudo()
        for line in self.line_ids:
            vals = self._prepare_cost_ledger_vals(line, cost_code)
            ledger = Ledger.search(
                [
                    ("source_model", "=", self._name),
                    ("source_id", "=", self.id),
                    ("source_line_id", "=", line.id),
                ],
                limit=1,
            )
            if ledger:
                ledger.write(vals)
            else:
                Ledger.create(vals)

    def _sync_payment_request_after_confirm(self):
        self.ensure_one()
        PaymentRequest = self.env["payment.request"].sudo()
        vals = {
            "type": "pay",
            "project_id": self.project_id.id,
            "partner_id": self.supplier_id.id,
            "amount": self.amount_total,
            "currency_id": self.currency_id.id,
            "date_request": self.settlement_date or fields.Date.context_today(self),
            "material_settlement_id": self.id,
            "note": _("由材料结算 %(name)s 确认后自动生成。") % {"name": self.name},
        }
        request = self.payment_request_id.sudo() if self.payment_request_id else PaymentRequest.search(
            [("material_settlement_id", "=", self.id)],
            limit=1,
        )
        if request:
            if request.state in ("draft", "cancel"):
                request.write(vals)
        else:
            request = PaymentRequest.create(vals)
        if request and self.payment_request_id != request:
            self.write({"payment_request_id": request.id})
        return request

    def _material_payment_requested_amount(self, exclude_request=False):
        self.ensure_one()
        domain = [
            ("material_settlement_id", "=", self.id),
            ("type", "=", "pay"),
            ("state", "!=", "cancel"),
        ]
        if exclude_request:
            domain.append(("id", "!=", exclude_request.id))
        data = self.env["payment.request"].sudo().read_group(domain, ["amount:sum"], [])
        return data[0].get("amount_sum", data[0].get("amount", 0.0)) if data else 0.0

    def _material_payment_remaining_amount(self, exclude_request=False):
        self.ensure_one()
        return (self.amount_total or 0.0) - self._material_payment_requested_amount(exclude_request=exclude_request)

    def _prepare_material_payment_request_vals(self, amount):
        self.ensure_one()
        return {
            "type": "pay",
            "project_id": self.project_id.id,
            "partner_id": self.supplier_id.id,
            "amount": amount,
            "currency_id": self.currency_id.id,
            "date_request": fields.Date.context_today(self),
            "material_settlement_id": self.id,
            "note": _("由材料结算 %(name)s 生成剩余付款申请。") % {"name": self.name},
        }

    def action_create_remaining_payment_request(self):
        self.ensure_one()
        self._sc_require_material_manager(_("生成剩余付款申请"))
        self._sc_require_state({"confirmed"}, _("生成剩余付款申请"))
        draft_request = self.payment_request_ids.filtered(lambda req: req.state == "draft")[:1]
        if draft_request:
            self.payment_request_id = draft_request.id
            return self._action_open_payment_request(draft_request)
        remaining = self._material_payment_remaining_amount()
        rounding = self.currency_id.rounding if self.currency_id else 0.01
        if float_compare(remaining, 0.0, precision_rounding=rounding) <= 0:
            raise ValidationError(_("材料结算已无剩余可申请付款金额。"))
        request = self.env["payment.request"].sudo().create(
            self._prepare_material_payment_request_vals(remaining)
        )
        self.payment_request_id = request.id
        return self._action_open_payment_request(request)

    def _sync_downstream_after_confirm(self):
        for record in self:
            if record._sc_business_category_cost_trigger("material.settlement", "confirm_project_cost_ledger", default=True):
                record._sync_cost_ledger_after_confirm()
            if record._sc_business_category_cost_trigger("material.settlement", "confirm_payment_request", default=True):
                record._sync_payment_request_after_confirm()

    def action_open_payment_request(self):
        self.ensure_one()
        requests = self.payment_request_ids.filtered(lambda req: req.state != "cancel")
        if not requests:
            raise ValidationError(_("当前材料结算尚未生成付款申请。"))
        if len(requests) == 1:
            return self._action_open_payment_request(requests[0])
        action = self.env.ref("smart_construction_core.action_payment_request").sudo().read()[0]
        action.update(
            {
                "domain": [("id", "in", requests.ids)],
                "context": {
                    "default_project_id": self.project_id.id,
                    "default_partner_id": self.supplier_id.id,
                    "default_material_settlement_id": self.id,
                    "default_type": "pay",
                },
            }
        )
        return action

    def _action_open_payment_request(self, request):
        self.ensure_one()
        action = self.env.ref("smart_construction_core.action_payment_request").sudo().read()[0]
        action.update(
            {
                "views": [(self.env.ref("smart_construction_core.view_payment_request_form").id, "form")],
                "res_id": request.id,
                "domain": [("id", "=", request.id)],
                "context": {
                    "default_project_id": self.project_id.id,
                    "default_partner_id": self.supplier_id.id,
                    "default_material_settlement_id": self.id,
                    "default_type": "pay",
                },
            }
        )
        return action

    def action_cancel(self):
        self._sc_require_material_manager(_("取消材料结算"))
        self._sc_require_state({"draft", "submitted"}, _("取消材料结算"))
        snapshots = {record.id: record._sc_material_audit_payload() for record in self}
        self.write({"state": "cancel"})
        for record in self:
            record._sc_audit_material_transition(
                "material_settlement_cancelled",
                snapshots[record.id],
                record._sc_material_audit_payload(),
                action_name="action_cancel",
            )
        return True

    def action_reset_draft(self):
        self._sc_require_material_manager(_("重置材料结算为草稿"))
        self._sc_require_state({"cancel"}, _("重置材料结算为草稿"))
        snapshots = {record.id: record._sc_material_audit_payload() for record in self}
        self.write({"state": "draft"})
        for record in self:
            record._sc_audit_material_transition(
                "material_settlement_reset",
                snapshots[record.id],
                record._sc_material_audit_payload(),
                action_name="action_reset_draft",
            )
        return True


class ScMaterialSettlementLine(models.Model):
    _name = "sc.material.settlement.line"
    _description = "材料结算明细"
    _inherit = "sc.material.system.default.mixin"
    _order = "settlement_id, sequence, id"

    settlement_id = fields.Many2one("sc.material.settlement", string="结算单", required=True, ondelete="cascade", index=True)
    sequence = fields.Integer(default=10)
    project_id = fields.Many2one("project.project", string="项目", related="settlement_id.project_id", store=True, index=True)
    product_id = fields.Many2one("product.product", string="材料", required=True, index=True)
    material_catalog_id = fields.Many2one("sc.material.catalog", string="材料档案", index=True)
    material_spec = fields.Char(string="规格型号")
    product_uom_id = fields.Many2one("uom.uom", string="单位")
    qty = fields.Float(string="结算数量", required=True)
    currency_id = fields.Many2one("res.currency", string="币种", related="settlement_id.currency_id", store=True)
    unit_price = fields.Monetary(string="结算单价", currency_field="currency_id", required=True)
    tax_rate = fields.Float(string="税率%")
    amount_untaxed = fields.Monetary(string="未税金额", currency_field="currency_id", compute="_compute_amounts", store=True)
    tax_amount = fields.Monetary(string="税额", currency_field="currency_id", compute="_compute_amounts", store=True)
    amount_total = fields.Monetary(string="含税金额", currency_field="currency_id", compute="_compute_amounts", store=True)
    note = fields.Char(string="备注")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._sc_apply_line_defaults(vals, require_unit_price=True)
        return super().create(vals_list)

    @api.depends("qty", "unit_price", "tax_rate")
    def _compute_amounts(self):
        for record in self:
            amount_untaxed = record.qty * record.unit_price
            tax_amount = amount_untaxed * record.tax_rate / 100
            record.amount_untaxed = amount_untaxed
            record.tax_amount = tax_amount
            record.amount_total = amount_untaxed + tax_amount

    @api.onchange("product_id")
    def _onchange_product_id(self):
        for record in self:
            if record.product_id and not record.material_catalog_id:
                record.product_uom_id = record.product_id.uom_id
                if not record.material_spec:
                    record.material_spec = record.product_id.default_code or ""

    @api.onchange("material_catalog_id")
    def _onchange_material_catalog_id(self):
        for record in self:
            catalog = record.material_catalog_id
            if not catalog:
                continue
            record.material_spec = catalog.spec_model or record.material_spec

    @api.constrains("qty", "unit_price", "tax_rate")
    def _check_values(self):
        for record in self:
            if record.qty <= 0:
                raise ValidationError(_("结算数量必须大于0。"))
            if record.unit_price < 0:
                raise ValidationError(_("结算单价不能为负数。"))
            if record.tax_rate < 0:
                raise ValidationError(_("税率不能为负数。"))
