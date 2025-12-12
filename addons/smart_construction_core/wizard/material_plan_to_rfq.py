# -*- coding: utf-8 -*-
import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class MaterialPlanToRfqWizard(models.TransientModel):
    _name = "material.plan.to.rfq.wizard"
    _description = "Material Plan To RFQ"

    partner_id = fields.Many2one(
        "res.partner",
        string="供应商",
        required=True,
        domain=[("supplier_rank", ">", 0)],
    )
    note = fields.Text(string="备注")

    def _get_active_records(self):
        """Return active records from context without hard-coding model names."""
        self.ensure_one()
        active_model = self._context.get("active_model")
        active_ids = self._context.get("active_ids", [])
        if not active_model or not active_ids:
            raise UserError(_("请从物资计划中选择待生成的行后再操作。"))
        try:
            records = self.env[active_model].browse(active_ids)
        except KeyError:
            raise UserError(_("无法解析当前数据类型，请联系管理员。"))
        return records

    def _iter_plan_lines(self, records):
        """Yield plan lines for further processing."""
        for rec in records:
            lines = getattr(rec, "line_ids", False)
            if lines:
                for line in lines:
                    yield line, rec
            else:
                yield rec, rec

    def action_generate_rfq(self):
        self.ensure_one()
        records = self._get_active_records()

        # 权限：物资经办或主管
        if not self.env.user.has_group("smart_construction_core.group_sc_cap_material_user") and not self.env.user.has_group("smart_construction_core.group_sc_cap_material_manager"):
            raise UserError(_("你没有生成采购单的权限。"))
        # 仅允许已批准的计划生成采购单
        for rec in records:
            parent = rec if rec._name == "project.material.plan" else getattr(rec, "plan_id", False)
            if parent and getattr(parent, "state", False) != "approved":
                raise UserError(_("物资计划未批准，不能生成采购单。"))
            if rec._name == "project.material.plan" and rec.state != "approved":
                raise UserError(_("物资计划未批准，不能生成采购单。"))

        matched_lines = []
        for line, parent in self._iter_plan_lines(records):
            partner = getattr(line, "partner_id", False) or getattr(line, "vendor_id", False)
            if partner and partner.id == self.partner_id.id:
                matched_lines.append((line, parent))

        # 如果明细未标注供应商或与选择不符，回退为“该计划下全部明细”
        if not matched_lines:
            matched_lines = list(self._iter_plan_lines(records))

        PurchaseOrder = self.env["purchase.order"]
        PurchaseOrderLine = self.env["purchase.order.line"]
        created_orders = self.env["purchase.order"]

        for line, parent in matched_lines:
            product = getattr(line, "product_id", None)
            project = getattr(line, "project_id", False) or getattr(parent, "project_id", False)
            company = getattr(line, "company_id", False) or getattr(parent, "company_id", False) or self.env.company
            origin = getattr(parent, "name", False) or _("物资计划")
            po_vals = {
                "partner_id": self.partner_id.id,
                "company_id": company.id if company else False,
                "origin": origin,
            }
            if project and "project_id" in PurchaseOrder._fields:
                po_vals["project_id"] = project.id
            if "plan_id" in PurchaseOrder._fields:
                po_vals["plan_id"] = parent.id
            po = PurchaseOrder.create(po_vals)
            created_orders |= po

            qty = (
                getattr(line, "qty", None)
                or getattr(line, "product_qty", None)
                or getattr(line, "quantity", None)
                or getattr(line, "requested_qty", None)
                or 1.0
            )
            uom = getattr(line, "product_uom_id", None) or getattr(line, "uom_id", None)
            if not uom and product and hasattr(product, "uom_po_id"):
                uom = product.uom_po_id or product.uom_id
            price = getattr(line, "price_unit", None) or getattr(line, "price", None) or 0.0
            name = getattr(line, "name", None) or getattr(line, "display_name", None) or _("物资计划明细")

            if not uom:
                raise UserError(_("计划行缺少计量单位，请补全后再生成采购单。"))
            if product:
                base_uom = product.uom_po_id or product.uom_id
                if uom.category_id != base_uom.category_id:
                    raise UserError(
                        _("物料 %s 的计量单位 %s 与产品默认采购单位 %s 不属于同一类别，请调整产品或计划行。")
                        % (product.display_name, uom.display_name, base_uom.display_name)
                    )
            if not product:
                raise UserError(_("物资计划缺少物料，请补全物料信息后再生成采购单。"))

            PurchaseOrderLine.create(
                {
                    "order_id": po.id,
                    "name": name,
                    "product_id": product.id if product else False,
                    "product_qty": qty,
                    "product_uom": (product.uom_po_id or uom).id if product else (uom.id if uom else False),
                    "price_unit": price,
                    "date_planned": fields.Date.context_today(self),
                    "company_id": company.id if company else False,
                    "plan_line_id": line.id if "plan_line_id" in PurchaseOrderLine._fields else False,
                }
            )

        _logger.warning("✅ material_plan_to_rfq.py 已加载")
        action = {
            "type": "ir.actions.act_window",
            "name": _("询价单"),
            "res_model": "purchase.order",
            "view_mode": "tree,form",
            "domain": [("id", "in", created_orders.ids)],
        }
        return action
