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
        string="主供应商",
        required=True,
        domain=[("supplier_rank", ">", 0)],
    )
    partner_ids = fields.Many2many(
        "res.partner",
        string="其他参与供应商",
        domain=[("supplier_rank", ">", 0)],
        help="同一询比价可同时维护多家供应商报价；主供应商会自动纳入参与范围。",
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
            raise UserError(_("你没有生成询比价的权限。"))
        # 仅允许已批准的计划生成询比价
        for rec in records:
            parent = rec if rec._name == "project.material.plan" else getattr(rec, "plan_id", False)
            if parent and getattr(parent, "state", False) != "approved":
                raise UserError(_("物资计划未批准，不能生成询比价。"))
            if rec._name == "project.material.plan" and rec.state != "approved":
                raise UserError(_("物资计划未批准，不能生成询比价。"))

        suppliers = self.partner_id | self.partner_ids
        matched_lines = []
        for line, parent in self._iter_plan_lines(records):
            partner = getattr(line, "partner_id", False) or getattr(line, "vendor_id", False)
            if partner and partner in suppliers:
                matched_lines.append((line, parent))

        # 如果明细未标注供应商或与选择不符，回退为“该计划下全部明细”
        if not matched_lines:
            matched_lines = list(self._iter_plan_lines(records))

        MaterialRfq = self.env["sc.material.rfq"]
        created_rfqs = MaterialRfq.browse()
        grouped_lines = {}

        for line, parent in matched_lines:
            grouped_lines.setdefault(parent, []).append(line)

        for parent, lines in grouped_lines.items():
            project = getattr(parent, "project_id", False)
            if not project:
                raise UserError(_("物资计划缺少项目，不能生成询比价。"))
            rfq_vals = {
                "project_id": project.id,
                "source_material_plan_id": parent.id if parent._name == "project.material.plan" else False,
                "note": self.note or getattr(parent, "name", False) or _("物资计划生成"),
                "line_ids": [],
            }
            for line in lines:
                material_catalog = getattr(line, "material_catalog_id", False)
                if not material_catalog:
                    raise UserError(_("物资计划缺少材料档案，请补全材料档案后再生成询比价。"))
                product = getattr(line, "product_id", None)
                if not product:
                    product = self.env["product.product"].search([("default_code", "=", "SC-SYSTEM-DEFAULT-MATERIAL")], limit=1)
                if not product:
                    raise UserError(_("缺少系统默认材料兜底记录，请联系管理员。"))
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
                if not uom:
                    raise UserError(_("计划行缺少计量单位，请补全后再生成询比价。"))
                for supplier in suppliers:
                    rfq_vals["line_ids"].append(
                        (
                            0,
                            0,
                            {
                                "source_material_plan_line_id": line.id
                                if line._name == "project.material.plan.line"
                                else False,
                                "supplier_id": supplier.id,
                                "product_id": product.id,
                                "material_catalog_id": material_catalog.id,
                                "material_spec": getattr(line, "spec_model", False)
                                or getattr(line, "spec", False)
                                or material_catalog.spec_model,
                                "product_uom_id": uom.id,
                                "qty": qty,
                                "unit_price": getattr(line, "price_unit", None) or getattr(line, "price", None) or 0.0,
                                "note": getattr(line, "note", False),
                            },
                        )
                    )
            created_rfqs |= MaterialRfq.create(rfq_vals)

        _logger.warning("✅ material_plan_to_rfq.py 已加载")
        action = {
            "type": "ir.actions.act_window",
            "name": _("询价单"),
            "res_model": "sc.material.rfq",
            "view_mode": "tree,form",
            "domain": [("id", "in", created_rfqs.ids)],
        }
        return action
