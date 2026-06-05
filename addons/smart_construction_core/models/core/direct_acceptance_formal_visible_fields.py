# -*- coding: utf-8 -*-
from odoo import fields, models


def _add_legacy_visible_fields(namespace):
    namespace["legacy_acceptance_label"] = fields.Char(string="验收菜单", readonly=True, index=True)
    for index in range(1, 61):
        namespace[f"legacy_visible_{index:02d}"] = fields.Char(
            string=f"验收可见字段{index:02d}",
            readonly=True,
        )


class ProjectMaterialPlanDirectAcceptanceVisible(models.Model):
    _inherit = "project.material.plan"

    _add_legacy_visible_fields(locals())


class MaterialRfqDirectAcceptanceVisible(models.Model):
    _inherit = "sc.material.rfq"

    _add_legacy_visible_fields(locals())


class MaterialInboundDirectAcceptanceVisible(models.Model):
    _inherit = "sc.material.inbound"

    _add_legacy_visible_fields(locals())


class LaborUsageDirectAcceptanceVisible(models.Model):
    _inherit = "sc.labor.usage"

    _add_legacy_visible_fields(locals())


class SubcontractRequestDirectAcceptanceVisible(models.Model):
    _inherit = "sc.subcontract.request"

    _add_legacy_visible_fields(locals())


class EquipmentUsageDirectAcceptanceVisible(models.Model):
    _inherit = "sc.equipment.usage"

    _add_legacy_visible_fields(locals())


class MaterialRentalOrderDirectAcceptanceVisible(models.Model):
    _inherit = "sc.material.rental.order"

    _add_legacy_visible_fields(locals())


class HrPayrollDocumentDirectAcceptanceVisible(models.Model):
    _inherit = "sc.hr.payroll.document"

    _add_legacy_visible_fields(locals())


class FundAccountOperationDirectAcceptanceVisible(models.Model):
    _inherit = "sc.fund.account.operation"

    _add_legacy_visible_fields(locals())


class ConstructionDiaryDirectAcceptanceVisible(models.Model):
    _inherit = "sc.construction.diary"

    _add_legacy_visible_fields(locals())
