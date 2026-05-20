# -*- coding: utf-8 -*-
from odoo import fields, models


class ScListBatchArchiveConstructionContractLine(models.Model):
    _inherit = "construction.contract.line"
    active = fields.Boolean(string="有效", default=True, index=True)


class ScListBatchArchivePaymentRequest(models.Model):
    _inherit = "payment.request"
    active = fields.Boolean(string="有效", default=True, index=True)


class ScListBatchArchiveProjectBoqLine(models.Model):
    _inherit = "project.boq.line"
    active = fields.Boolean(string="有效", default=True, index=True)


class ScListBatchArchiveProjectBudgetCostAlloc(models.Model):
    _inherit = "project.budget.cost.alloc"
    active = fields.Boolean(string="有效", default=True, index=True)


class ScListBatchArchiveProjectFundingBaseline(models.Model):
    _inherit = "project.funding.baseline"
    active = fields.Boolean(string="有效", default=True, index=True)


class ScListBatchArchiveProjectMaterialPlan(models.Model):
    _inherit = "project.material.plan"
    active = fields.Boolean(string="有效", default=True, index=True)


class ScListBatchArchiveProjectProgressEntry(models.Model):
    _inherit = "project.progress.entry"
    active = fields.Boolean(string="有效", default=True, index=True)


class ScListBatchArchivePurchaseOrder(models.Model):
    _inherit = "purchase.order"
    active = fields.Boolean(string="有效", default=True, index=True)


class ScListBatchArchiveApprovalScope(models.Model):
    _inherit = "sc.approval.scope"
    active = fields.Boolean(string="有效", default=True, index=True)


class ScListBatchArchiveAttendanceCheckin(models.Model):
    _inherit = "sc.attendance.checkin"
    active = fields.Boolean(string="有效", default=True, index=True)


class ScListBatchArchiveCheckStandardItem(models.Model):
    _inherit = "sc.check.standard.item"
    active = fields.Boolean(string="有效", default=True, index=True)


class ScListBatchArchiveContractEvent(models.Model):
    _inherit = "sc.contract.event"
    active = fields.Boolean(string="有效", default=True, index=True)


class ScListBatchArchiveDocumentAdminDocument(models.Model):
    _inherit = "sc.document.admin.document"
    active = fields.Boolean(string="有效", default=True, index=True)


class ScListBatchArchiveEquipmentPlan(models.Model):
    _inherit = "sc.equipment.plan"
    active = fields.Boolean(string="有效", default=True, index=True)


class ScListBatchArchiveEquipmentPrice(models.Model):
    _inherit = "sc.equipment.price"
    active = fields.Boolean(string="有效", default=True, index=True)


class ScListBatchArchiveEquipmentRequest(models.Model):
    _inherit = "sc.equipment.request"
    active = fields.Boolean(string="有效", default=True, index=True)


class ScListBatchArchiveEquipmentSettlement(models.Model):
    _inherit = "sc.equipment.settlement"
    active = fields.Boolean(string="有效", default=True, index=True)


class ScListBatchArchiveEquipmentUsage(models.Model):
    _inherit = "sc.equipment.usage"
    active = fields.Boolean(string="有效", default=True, index=True)


class ScListBatchArchiveHazardSource(models.Model):
    _inherit = "sc.hazard.source"
    active = fields.Boolean(string="有效", default=True, index=True)


class ScListBatchArchiveHistoryTodo(models.Model):
    _inherit = "sc.history.todo"
    active = fields.Boolean(string="有效", default=True, index=True)


class ScListBatchArchiveHrPayrollDocument(models.Model):
    _inherit = "sc.hr.payroll.document"
    active = fields.Boolean(string="有效", default=True, index=True)


class ScListBatchArchiveLaborPlan(models.Model):
    _inherit = "sc.labor.plan"
    active = fields.Boolean(string="有效", default=True, index=True)


class ScListBatchArchiveLaborPrice(models.Model):
    _inherit = "sc.labor.price"
    active = fields.Boolean(string="有效", default=True, index=True)


class ScListBatchArchiveLaborRequest(models.Model):
    _inherit = "sc.labor.request"
    active = fields.Boolean(string="有效", default=True, index=True)


class ScListBatchArchiveLaborSettlement(models.Model):
    _inherit = "sc.labor.settlement"
    active = fields.Boolean(string="有效", default=True, index=True)


class ScListBatchArchiveLaborUsage(models.Model):
    _inherit = "sc.labor.usage"
    active = fields.Boolean(string="有效", default=True, index=True)


class ScListBatchArchiveMaterialAcceptance(models.Model):
    _inherit = "sc.material.acceptance"
    active = fields.Boolean(string="有效", default=True, index=True)


class ScListBatchArchiveMaterialInbound(models.Model):
    _inherit = "sc.material.inbound"
    active = fields.Boolean(string="有效", default=True, index=True)


class ScListBatchArchiveMaterialOutbound(models.Model):
    _inherit = "sc.material.outbound"
    active = fields.Boolean(string="有效", default=True, index=True)


class ScListBatchArchiveMaterialPurchaseRequest(models.Model):
    _inherit = "sc.material.purchase.request"
    active = fields.Boolean(string="有效", default=True, index=True)


class ScListBatchArchiveMaterialRentalOrder(models.Model):
    _inherit = "sc.material.rental.order"
    active = fields.Boolean(string="有效", default=True, index=True)


class ScListBatchArchiveMaterialRentalPlan(models.Model):
    _inherit = "sc.material.rental.plan"
    active = fields.Boolean(string="有效", default=True, index=True)


class ScListBatchArchiveMaterialRentalSettlement(models.Model):
    _inherit = "sc.material.rental.settlement"
    active = fields.Boolean(string="有效", default=True, index=True)


class ScListBatchArchiveMaterialRfq(models.Model):
    _inherit = "sc.material.rfq"
    active = fields.Boolean(string="有效", default=True, index=True)


class ScListBatchArchiveMaterialSettlement(models.Model):
    _inherit = "sc.material.settlement"
    active = fields.Boolean(string="有效", default=True, index=True)


class ScListBatchArchiveMaterialSettlementLine(models.Model):
    _inherit = "sc.material.settlement.line"
    active = fields.Boolean(string="有效", default=True, index=True)


class ScListBatchArchiveOfficeAdminDocument(models.Model):
    _inherit = "sc.office.admin.document"
    active = fields.Boolean(string="有效", default=True, index=True)


class ScListBatchArchivePackInstallation(models.Model):
    _inherit = "sc.pack.installation"
    active = fields.Boolean(string="有效", default=True, index=True)


class ScListBatchArchivePlan(models.Model):
    _inherit = "sc.plan"
    active = fields.Boolean(string="有效", default=True, index=True)


class ScListBatchArchivePlanReport(models.Model):
    _inherit = "sc.plan.report"
    active = fields.Boolean(string="有效", default=True, index=True)


class ScListBatchArchiveProjectDocument(models.Model):
    _inherit = "sc.project.document"
    active = fields.Boolean(string="有效", default=True, index=True)


class ScListBatchArchiveProjectStructure(models.Model):
    _inherit = "sc.project.structure"
    active = fields.Boolean(string="有效", default=True, index=True)


class ScListBatchArchiveQualityIssue(models.Model):
    _inherit = "sc.quality.issue"
    active = fields.Boolean(string="有效", default=True, index=True)


class ScListBatchArchiveQualityRecheck(models.Model):
    _inherit = "sc.quality.recheck"
    active = fields.Boolean(string="有效", default=True, index=True)


class ScListBatchArchiveQualityRectification(models.Model):
    _inherit = "sc.quality.rectification"
    active = fields.Boolean(string="有效", default=True, index=True)


class ScListBatchArchiveRiskItem(models.Model):
    _inherit = "sc.risk.item"
    active = fields.Boolean(string="有效", default=True, index=True)


class ScListBatchArchiveSafetyDisclosure(models.Model):
    _inherit = "sc.safety.disclosure"
    active = fields.Boolean(string="有效", default=True, index=True)


class ScListBatchArchiveSafetyIssue(models.Model):
    _inherit = "sc.safety.issue"
    active = fields.Boolean(string="有效", default=True, index=True)


class ScListBatchArchiveSafetyPatrolTask(models.Model):
    _inherit = "sc.safety.patrol.task"
    active = fields.Boolean(string="有效", default=True, index=True)


class ScListBatchArchiveSafetyPlan(models.Model):
    _inherit = "sc.safety.plan"
    active = fields.Boolean(string="有效", default=True, index=True)


class ScListBatchArchiveSafetyRecheck(models.Model):
    _inherit = "sc.safety.recheck"
    active = fields.Boolean(string="有效", default=True, index=True)


class ScListBatchArchiveSafetyRectification(models.Model):
    _inherit = "sc.safety.rectification"
    active = fields.Boolean(string="有效", default=True, index=True)


class ScListBatchArchiveSceneVersion(models.Model):
    _inherit = "sc.scene.version"
    active = fields.Boolean(string="有效", default=True, index=True)


class ScListBatchArchiveSettlementOrder(models.Model):
    _inherit = "sc.settlement.order"
    active = fields.Boolean(string="有效", default=True, index=True)


class ScListBatchArchiveSitePhotoBatch(models.Model):
    _inherit = "sc.site.photo.batch"
    active = fields.Boolean(string="有效", default=True, index=True)


class ScListBatchArchiveSubcontractPlan(models.Model):
    _inherit = "sc.subcontract.plan"
    active = fields.Boolean(string="有效", default=True, index=True)


class ScListBatchArchiveSubcontractPrice(models.Model):
    _inherit = "sc.subcontract.price"
    active = fields.Boolean(string="有效", default=True, index=True)


class ScListBatchArchiveSubcontractRegister(models.Model):
    _inherit = "sc.subcontract.register"
    active = fields.Boolean(string="有效", default=True, index=True)


class ScListBatchArchiveSubcontractRequest(models.Model):
    _inherit = "sc.subcontract.request"
    active = fields.Boolean(string="有效", default=True, index=True)


class ScListBatchArchiveSubcontractSettlement(models.Model):
    _inherit = "sc.subcontract.settlement"
    active = fields.Boolean(string="有效", default=True, index=True)


class ScListBatchArchiveWorkflowInstance(models.Model):
    _inherit = "sc.workflow.instance"
    active = fields.Boolean(string="有效", default=True, index=True)


class ScListBatchArchiveWorkflowLog(models.Model):
    _inherit = "sc.workflow.log"
    active = fields.Boolean(string="有效", default=True, index=True)


class ScListBatchArchiveWorkflowWorkitem(models.Model):
    _inherit = "sc.workflow.workitem"
    active = fields.Boolean(string="有效", default=True, index=True)


class ScListBatchArchiveTenderBid(models.Model):
    _inherit = "tender.bid"
    active = fields.Boolean(string="有效", default=True, index=True)


class ScListBatchArchiveTenderDocPurchase(models.Model):
    _inherit = "tender.doc.purchase"
    active = fields.Boolean(string="有效", default=True, index=True)


class ScListBatchArchiveTenderGuarantee(models.Model):
    _inherit = "tender.guarantee"
    active = fields.Boolean(string="有效", default=True, index=True)


class ScListBatchArchiveTenderOpening(models.Model):
    _inherit = "tender.opening"
    active = fields.Boolean(string="有效", default=True, index=True)
