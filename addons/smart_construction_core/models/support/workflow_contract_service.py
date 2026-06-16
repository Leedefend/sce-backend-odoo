# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo import api, models
from odoo.addons.smart_construction_core.models.support import operating_metrics as opm
from odoo.tools.float_utils import float_compare


def _simple_approval_profiles(model_names):
    profile = {
        "state_field": "state",
        "state_phase": {
            "draft": "draft",
            "submitted": "under_review",
            "submit": "under_review",
            "approved": "approved",
            "rejected": "rejected",
            "cancel": "cancelled",
        },
        "state_actions": {
            "draft": ["submit", "cancel"],
            "submitted": ["approve", "reopen", "cancel"],
            "submit": ["approve", "reopen", "cancel"],
            "rejected": ["reopen", "cancel"],
        },
        "method_by_action": {
            "submit": "action_submit",
            "approve": "action_approve",
            "reopen": "action_reset_draft",
            "cancel": "action_cancel",
        },
    }
    return {name: dict(profile) for name in model_names}


def _simple_close_issue_profiles(model_names):
    profile = {
        "state_field": "state",
        "state_phase": {
            "draft": "draft",
            "submitted": "submitted",
            "rectifying": "open",
            "rechecking": "under_review",
            "closed": "closed",
            "cancel": "cancelled",
        },
        "state_actions": {
            "draft": ["submit", "cancel"],
            "submitted": ["complete", "cancel"],
            "rectifying": ["complete", "cancel"],
            "rechecking": ["complete", "cancel"],
        },
        "method_by_action": {
            "submit": "action_submit",
            "complete": "action_close",
            "cancel": "action_cancel",
        },
    }
    return {name: dict(profile) for name in model_names}


def _submit_confirm_profiles(model_names):
    profile = {
        "state_field": "state",
        "state_phase": {
            "draft": "draft",
            "submitted": "submitted",
            "confirmed": "approved",
            "cancel": "cancelled",
        },
        "state_actions": {
            "draft": ["submit", "cancel"],
            "submitted": ["complete", "reopen", "cancel"],
        },
        "method_by_action": {
            "submit": "action_submit",
            "complete": "action_confirm",
            "reopen": "action_reset_draft",
            "cancel": "action_cancel",
        },
        "label_by_action": {
            "complete": "确认",
        },
    }
    return {name: dict(profile) for name in model_names}


def _in_progress_done_profiles(model_names):
    profile = {
        "state_field": "state",
        "state_phase": {
            "draft": "draft",
            "in_progress": "open",
            "done": "done",
            "cancel": "cancelled",
        },
        "state_actions": {
            "draft": ["submit", "complete", "cancel"],
            "in_progress": ["complete", "reopen", "cancel"],
            "cancel": ["reopen"],
        },
        "method_by_action": {
            "submit": "action_submit",
            "complete": "action_done",
            "reopen": "action_reset_draft",
            "cancel": "action_cancel",
        },
    }
    return {name: dict(profile) for name in model_names}


def _confirm_done_profiles(model_names):
    profile = {
        "state_field": "state",
        "state_phase": {
            "draft": "draft",
            "confirmed": "approved",
            "in_progress": "open",
            "done": "done",
            "cancel": "cancelled",
            "cancelled": "cancelled",
            "legacy_confirmed": "legacy_confirmed",
        },
        "state_actions": {
            "draft": ["submit", "complete", "cancel"],
            "confirmed": ["complete", "reopen", "cancel"],
            "in_progress": ["complete", "reopen", "cancel"],
            "cancel": ["reopen"],
            "cancelled": ["reopen"],
        },
        "method_by_action": {
            "submit": "action_confirm",
            "complete": "action_done",
            "reopen": "action_reset_draft",
            "cancel": "action_cancel",
        },
        "label_by_action": {
            "submit": "确认",
        },
    }
    return {name: dict(profile) for name in model_names}


class ScWorkflowContractService(models.AbstractModel):
    _name = "sc.workflow.contract.service"
    _description = "施工业务表单状态与审批流统一投影服务"

    SOURCE_KIND = "sc_backend_workflow_contract_v1"
    SOURCE_AUTHORITIES = (
        "odoo_model_state",
        "base_tier_validation",
        "sc.approval.policy",
        "business_model_methods",
    )

    PROFILE_BY_MODEL = {
        "payment.request": {
            "state_field": "state",
            "state_phase": {
                "draft": "draft",
                "submit": "under_review",
                "approve": "under_review",
                "approved": "approved",
                "rejected": "rejected",
                "done": "done",
                "cancel": "cancelled",
            },
            "state_actions": {
                "draft": ["save_draft", "submit", "cancel"],
                "submit": ["approve", "reject", "cancel"],
                "approve": ["approve", "reject", "cancel"],
                "approved": ["complete", "cancel"],
                "rejected": ["submit", "cancel"],
            },
            "method_by_action": {
                "submit": "action_submit",
                "approve": "action_approval_decision",
                "reject": "reject_tier",
                "complete": "action_done",
                "cancel": "action_cancel",
            },
        },
        "sc.settlement.order": {
            "state_field": "state",
            "state_phase": {
                "draft": "draft",
                "submit": "under_review",
                "approve": "approved",
                "done": "done",
                "cancel": "cancelled",
            },
            "state_actions": {
                "draft": ["save_draft", "submit", "cancel"],
                "submit": ["approve", "reject", "cancel"],
                "approve": ["complete", "cancel"],
            },
            "method_by_action": {
                "submit": "action_submit",
                "approve": "validate_tier",
                "reject": "reject_tier",
                "complete": "action_done",
                "cancel": "action_cancel",
            },
        },
        "sc.expense.claim": {
            "state_field": "state",
            "state_phase": {
                "draft": "draft",
                "submit": "under_review",
                "approved": "approved",
                "done": "done",
                "legacy_confirmed": "legacy_confirmed",
                "cancel": "cancelled",
            },
            "state_actions": {
                "draft": ["save_draft", "submit", "cancel"],
                "submit": ["approve", "reject", "cancel"],
                "approved": ["complete", "cancel"],
            },
            "method_by_action": {
                "submit": "action_submit",
                "approve": "validate_tier",
                "reject": "reject_tier",
                "complete": "action_done",
                "cancel": "action_cancel",
            },
        },
        "construction.contract": {
            "state_field": "state",
            "state_phase": {
                "draft": "draft",
                "confirmed": "approved",
                "running": "effective",
                "closed": "done",
                "cancel": "cancelled",
            },
            "state_actions": {
                "draft": ["submit", "cancel"],
                "confirmed": ["activate", "complete", "cancel"],
                "running": ["complete", "cancel"],
                "cancel": ["reopen"],
            },
            "approval_actions": ["approve", "reject"],
            "method_by_action": {
                "submit": "action_confirm",
                "approve": "validate_tier",
                "reject": "reject_tier",
                "activate": "action_set_running",
                "complete": "action_close",
                "cancel": "action_cancel",
                "reopen": "action_reset_draft",
            },
        },
        "construction.contract.expense": {
            "state_field": "state",
            "state_phase": {
                "draft": "draft",
                "confirmed": "approved",
                "running": "effective",
                "closed": "done",
                "cancel": "cancelled",
            },
            "state_actions": {
                "draft": ["submit", "cancel"],
                "confirmed": ["activate", "complete", "cancel"],
                "running": ["complete", "cancel"],
                "cancel": ["reopen"],
            },
            "approval_actions": ["approve", "reject"],
            "method_by_action": {
                "submit": "action_confirm",
                "approve": "validate_tier",
                "reject": "reject_tier",
                "activate": "action_set_running",
                "complete": "action_close",
                "cancel": "action_cancel",
                "reopen": "action_reset_draft",
            },
        },
        "construction.contract.income": {
            "state_field": "state",
            "state_phase": {
                "draft": "draft",
                "confirmed": "approved",
                "running": "effective",
                "closed": "done",
                "cancel": "cancelled",
            },
            "state_actions": {
                "draft": ["submit", "cancel"],
                "confirmed": ["activate", "complete", "cancel"],
                "running": ["complete", "cancel"],
                "cancel": ["reopen"],
            },
            "approval_actions": ["approve", "reject"],
            "method_by_action": {
                "submit": "action_confirm",
                "approve": "validate_tier",
                "reject": "reject_tier",
                "activate": "action_set_running",
                "complete": "action_close",
                "cancel": "action_cancel",
                "reopen": "action_reset_draft",
            },
        },
        "sc.payment.execution": {
            "state_field": "state",
            "state_phase": {
                "draft": "draft",
                "confirmed": "approved",
                "paid": "done",
                "legacy_confirmed": "legacy_confirmed",
                "cancel": "cancelled",
            },
            "state_actions": {
                "draft": ["submit", "complete", "cancel"],
                "confirmed": ["complete", "cancel"],
                "paid": ["cancel"],
            },
            "approval_actions": ["approve", "reject"],
            "method_by_action": {
                "submit": "action_confirm",
                "approve": "validate_tier",
                "reject": "reject_tier",
                "complete": "action_paid",
                "cancel": "action_cancel",
            },
            "label_by_action": {
                "complete": "已付款",
            },
        },
        "sc.receipt.income": {
            "state_field": "state",
            "state_phase": {
                "draft": "draft",
                "confirmed": "approved",
                "received": "done",
                "legacy_confirmed": "legacy_confirmed",
                "cancel": "cancelled",
            },
            "state_actions": {
                "draft": ["submit", "complete", "cancel"],
                "confirmed": ["complete", "cancel"],
            },
            "approval_actions": ["approve", "reject"],
            "method_by_action": {
                "submit": "action_confirm",
                "approve": "validate_tier",
                "reject": "reject_tier",
                "complete": "action_received",
                "cancel": "action_cancel",
            },
            "label_by_action": {
                "complete": "已收款",
            },
        },
        "sc.invoice.registration": {
            "state_field": "state",
            "state_phase": {
                "draft": "draft",
                "confirmed": "approved",
                "registered": "done",
                "legacy_confirmed": "legacy_confirmed",
                "cancel": "cancelled",
            },
            "state_actions": {
                "draft": ["submit", "complete", "cancel"],
                "confirmed": ["complete", "cancel"],
            },
            "approval_actions": ["approve", "reject"],
            "method_by_action": {
                "submit": "action_confirm",
                "approve": "validate_tier",
                "reject": "reject_tier",
                "complete": "action_register",
                "cancel": "action_cancel",
            },
            "label_by_action": {
                "complete": "已登记",
            },
        },
        "sc.self.funding.registration": {
            "state_field": "state",
            "state_phase": {
                "draft": "draft",
                "confirmed": "approved",
                "done": "done",
                "cancel": "cancelled",
            },
            "state_actions": {
                "draft": ["submit", "complete", "cancel"],
                "confirmed": ["complete", "cancel"],
            },
            "approval_actions": ["approve", "reject"],
            "method_by_action": {
                "submit": "action_confirm",
                "approve": "validate_tier",
                "reject": "reject_tier",
                "complete": "action_done",
                "cancel": "action_cancel",
            },
        },
        "sc.financing.loan": {
            "state_field": "state",
            "state_phase": {
                "draft": "draft",
                "confirmed": "approved",
                "done": "done",
                "legacy_confirmed": "legacy_confirmed",
                "cancel": "cancelled",
            },
            "state_actions": {
                "draft": ["submit", "complete", "cancel"],
                "confirmed": ["complete", "cancel"],
            },
            "approval_actions": ["approve", "reject"],
            "method_by_action": {
                "submit": "action_confirm",
                "approve": "validate_tier",
                "reject": "reject_tier",
                "complete": "action_done",
                "cancel": "action_cancel",
            },
        },
        "sc.treasury.reconciliation": {
            "state_field": "state",
            "state_phase": {
                "draft": "draft",
                "confirmed": "approved",
                "reconciled": "done",
                "legacy_confirmed": "legacy_confirmed",
                "cancel": "cancelled",
            },
            "state_actions": {
                "draft": ["submit", "complete", "cancel"],
                "confirmed": ["complete", "cancel"],
            },
            "approval_actions": ["approve", "reject"],
            "method_by_action": {
                "submit": "action_confirm",
                "approve": "validate_tier",
                "reject": "reject_tier",
                "complete": "action_reconcile",
                "cancel": "action_cancel",
            },
            "label_by_action": {
                "complete": "对账完成",
            },
        },
        "sc.general.contract": {
            "state_field": "state",
            "state_phase": {
                "draft": "draft",
                "confirmed": "approved",
                "signed": "effective",
                "cancel": "cancelled",
            },
            "state_actions": {
                "draft": ["submit", "cancel"],
                "confirmed": ["cancel"],
                "signed": ["cancel"],
            },
            "approval_actions": ["approve", "reject"],
            "method_by_action": {
                "submit": "action_confirm",
                "approve": "validate_tier",
                "reject": "reject_tier",
                "cancel": "action_cancel",
            },
        },
        "sc.settlement.adjustment": {
            "state_field": "state",
            "state_phase": {
                "draft": "draft",
                "confirmed": "approved",
                "legacy_confirmed": "legacy_confirmed",
                "cancel": "cancelled",
            },
            "state_actions": {
                "draft": ["submit"],
                "confirmed": ["cancel"],
            },
            "approval_actions": ["approve", "reject"],
            "method_by_action": {
                "submit": "action_confirm",
                "approve": "validate_tier",
                "reject": "reject_tier",
                "cancel": "action_cancel",
            },
        },
        **_simple_approval_profiles((
            "sc.equipment.plan",
            "sc.equipment.request",
            "sc.labor.plan",
            "sc.labor.request",
            "sc.material.purchase.request",
            "sc.material.rental.plan",
            "sc.safety.disclosure",
            "sc.safety.plan",
            "sc.subcontract.plan",
            "sc.subcontract.request",
        )),
        "project.material.plan": {
            "state_field": "state",
            "state_phase": {
                "draft": "draft",
                "submit": "under_review",
                "approved": "approved",
                "done": "done",
                "cancel": "cancelled",
            },
            "state_actions": {
                "draft": ["submit", "cancel"],
                "submit": ["approve", "reject", "cancel"],
                "approved": ["complete", "cancel"],
            },
            "approval_actions": ["approve", "reject"],
            "method_by_action": {
                "submit": "action_submit",
                "approve": "validate_tier",
                "reject": "reject_tier",
                "complete": "action_done",
                "cancel": "action_cancel",
            },
        },
        **_simple_close_issue_profiles((
            "sc.quality.issue",
            "sc.safety.issue",
        )),
        **_submit_confirm_profiles((
            "sc.equipment.settlement",
            "sc.equipment.usage",
            "sc.labor.settlement",
            "sc.labor.usage",
            "sc.material.settlement",
            "sc.subcontract.settlement",
        )),
        **_in_progress_done_profiles((
            "sc.dashboard.cockpit.fact",
            "sc.document.admin.document",
            "sc.hr.payroll.document",
            "sc.office.admin.document",
            "sc.workbench.item",
        )),
        **_confirm_done_profiles((
            "sc.fund.account.operation",
            "sc.plan",
        )),
        "sc.construction.diary": {
            "state_field": "state",
            "state_phase": {
                "draft": "draft",
                "confirmed": "approved",
                "done": "done",
                "legacy_confirmed": "legacy_confirmed",
                "cancel": "cancelled",
            },
            "state_actions": {
                "draft": ["submit", "complete", "cancel"],
                "confirmed": ["complete", "cancel"],
            },
            "method_by_action": {
                "submit": "action_confirm",
                "complete": "action_done",
                "cancel": "action_cancel",
            },
            "label_by_action": {
                "submit": "确认",
            },
        },
        "sc.contract.event": {
            "state_field": "state",
            "state_phase": {
                "draft": "draft",
                "submitted": "under_review",
                "approved": "approved",
                "rejected": "rejected",
                "done": "done",
                "cancel": "cancelled",
            },
            "state_actions": {
                "draft": ["submit", "cancel"],
                "submitted": ["approve", "reject", "cancel"],
                "approved": ["complete", "cancel"],
                "rejected": ["cancel"],
            },
            "method_by_action": {
                "submit": "action_submit",
                "approve": "action_approve",
                "complete": "action_done",
                "cancel": "action_cancel",
            },
        },
        "sc.tax.deduction.registration": {
            "state_field": "state",
            "state_phase": {
                "draft": "draft",
                "confirmed": "approved",
                "deducted": "done",
                "legacy_confirmed": "legacy_confirmed",
                "cancel": "cancelled",
            },
            "state_actions": {
                "draft": ["submit", "complete", "cancel"],
                "confirmed": ["complete", "cancel"],
            },
            "method_by_action": {
                "submit": "action_confirm",
                "complete": "action_deduct",
                "cancel": "action_cancel",
            },
            "label_by_action": {
                "submit": "确认",
                "complete": "已抵扣",
            },
        },
        "sc.subcontract.register": {
            "state_field": "state",
            "state_phase": {
                "draft": "draft",
                "active": "effective",
                "closed": "closed",
                "cancel": "cancelled",
            },
            "state_actions": {
                "draft": ["submit", "cancel"],
                "active": ["complete", "reopen", "cancel"],
            },
            "method_by_action": {
                "submit": "action_register",
                "complete": "action_close",
                "reopen": "action_reset_draft",
                "cancel": "action_cancel",
            },
            "label_by_action": {
                "submit": "确认登记",
                "complete": "关闭",
            },
        },
        "project.progress.entry": {
            "state_field": "state",
            "state_phase": {"draft": "draft", "submitted": "submitted"},
            "state_actions": {"draft": ["submit"]},
            "method_by_action": {"submit": "action_submit_progress"},
            "label_by_action": {"submit": "提交"},
        },
        "project.risk.action": {
            "state_field": "state",
            "state_phase": {"open": "open", "claimed": "open", "escalated": "open", "closed": "closed"},
            "state_actions": {"open": ["complete"], "claimed": ["complete"], "escalated": ["complete"]},
            "method_by_action": {"complete": "action_close"},
            "label_by_action": {"complete": "关闭"},
        },
        "project.settlement": {
            "state_field": "state",
            "state_phase": {"draft": "draft", "confirmed": "approved", "done": "done", "cancel": "cancelled"},
            "state_actions": {"draft": ["submit", "cancel"], "confirmed": ["complete", "cancel"]},
            "method_by_action": {
                "submit": "action_confirm",
                "complete": "action_done",
                "cancel": "action_cancel",
            },
            "label_by_action": {"submit": "确认"},
        },
        "sc.attendance.checkin": {
            "state_field": "state",
            "state_phase": {"draft": "draft", "submitted": "submitted", "confirmed": "approved", "cancel": "cancelled"},
            "state_actions": {"draft": ["submit", "cancel"], "submitted": ["complete", "reopen", "cancel"]},
            "method_by_action": {
                "submit": "action_submit",
                "complete": "action_confirm",
                "reopen": "action_reset_draft",
                "cancel": "action_cancel",
            },
            "label_by_action": {"complete": "确认考勤"},
        },
        "sc.edition.release.snapshot": {
            "state_field": "state",
            "state_phase": {"candidate": "draft", "approved": "approved", "released": "done", "superseded": "cancelled"},
            "state_actions": {
                "candidate": ["approve", "complete"],
                "approved": ["complete", "cancel"],
                "released": ["cancel"],
            },
            "method_by_action": {
                "approve": "action_approve",
                "complete": "action_release",
                "cancel": "action_supersede",
            },
            "label_by_action": {"complete": "发布", "cancel": "废弃"},
        },
        "sc.equipment.price": {
            "state_field": "state",
            "state_phase": {"draft": "draft", "active": "effective", "inactive": "cancelled"},
            "state_actions": {"draft": ["submit"], "active": ["complete"], "inactive": ["reopen"]},
            "method_by_action": {
                "submit": "action_activate",
                "complete": "action_deactivate",
                "reopen": "action_reset_draft",
            },
            "label_by_action": {"submit": "生效", "complete": "停用"},
        },
        "sc.labor.price": {
            "state_field": "state",
            "state_phase": {"draft": "draft", "active": "effective", "inactive": "cancelled"},
            "state_actions": {"draft": ["submit"], "active": ["complete"], "inactive": ["reopen"]},
            "method_by_action": {
                "submit": "action_activate",
                "complete": "action_deactivate",
                "reopen": "action_reset_draft",
            },
            "label_by_action": {"submit": "生效", "complete": "停用"},
        },
        "sc.subcontract.price": {
            "state_field": "state",
            "state_phase": {"draft": "draft", "active": "effective", "inactive": "cancelled"},
            "state_actions": {"draft": ["submit"], "active": ["complete"], "inactive": ["reopen"]},
            "method_by_action": {
                "submit": "action_activate",
                "complete": "action_deactivate",
                "reopen": "action_reset_draft",
            },
            "label_by_action": {"submit": "生效", "complete": "停用"},
        },
        "sc.hazard.source": {
            "state_field": "state",
            "state_phase": {"draft": "draft", "reported": "submitted", "controlled": "open", "closed": "closed"},
            "state_actions": {"draft": ["complete"], "reported": ["complete"], "controlled": ["complete"]},
            "method_by_action": {"complete": "action_close"},
            "label_by_action": {"complete": "关闭"},
        },
        "sc.material.acceptance": {
            "state_field": "state",
            "state_phase": {"draft": "draft", "submitted": "submitted", "accepted": "done", "rejected": "rejected", "cancel": "cancelled"},
            "state_actions": {"draft": ["submit", "cancel"], "submitted": ["approve", "reject", "reopen", "cancel"], "rejected": ["reopen", "cancel"]},
            "method_by_action": {
                "submit": "action_submit",
                "approve": "action_accept",
                "reject": "action_reject",
                "reopen": "action_reset_draft",
                "cancel": "action_cancel",
            },
            "label_by_action": {"approve": "验收通过", "reject": "验收不通过"},
        },
        "sc.material.inbound": {
            "state_field": "state",
            "state_phase": {"draft": "draft", "submitted": "submitted", "received": "done", "cancel": "cancelled"},
            "state_actions": {"draft": ["submit", "cancel"], "submitted": ["complete", "reopen", "cancel"]},
            "method_by_action": {
                "submit": "action_submit",
                "complete": "action_receive",
                "reopen": "action_reset_draft",
                "cancel": "action_cancel",
            },
            "label_by_action": {"complete": "确认入库"},
        },
        "sc.material.outbound": {
            "state_field": "state",
            "state_phase": {"draft": "draft", "submitted": "under_review", "issued": "done", "cancel": "cancelled"},
            "state_actions": {"draft": ["submit", "cancel"], "submitted": ["approve", "reject", "complete", "reopen", "cancel"]},
            "approval_actions": ["approve", "reject"],
            "method_by_action": {
                "submit": "action_submit",
                "approve": "validate_tier",
                "reject": "reject_tier",
                "complete": "action_issue",
                "reopen": "action_reset_draft",
                "cancel": "action_cancel",
            },
            "label_by_action": {"complete": "确认出库"},
        },
        "sc.material.rental.order": {
            "state_field": "state",
            "state_phase": {"draft": "draft", "active": "effective", "returned": "open", "settled": "done", "cancel": "cancelled"},
            "state_actions": {"draft": ["submit", "cancel"], "active": ["complete", "cancel"], "returned": ["approve", "cancel"]},
            "method_by_action": {
                "submit": "action_activate",
                "complete": "action_return",
                "approve": "action_settle",
                "cancel": "action_cancel",
            },
            "label_by_action": {"submit": "确认租赁", "complete": "确认退还", "approve": "完成结算"},
        },
        "sc.material.rental.settlement": {
            "state_field": "state",
            "state_phase": {"draft": "draft", "submitted": "submitted", "confirmed": "approved", "paid": "done", "cancel": "cancelled"},
            "state_actions": {"draft": ["submit", "cancel"], "submitted": ["approve", "cancel"], "confirmed": ["complete", "cancel"]},
            "method_by_action": {
                "submit": "action_submit",
                "approve": "action_confirm",
                "complete": "action_paid",
                "cancel": "action_cancel",
            },
            "label_by_action": {"approve": "确认结算", "complete": "确认支付"},
        },
        "sc.material.rfq": {
            "state_field": "state",
            "state_phase": {"draft": "draft", "submitted": "submitted", "selected": "done", "cancel": "cancelled"},
            "state_actions": {"draft": ["submit", "cancel"], "submitted": ["complete", "reopen", "cancel"]},
            "method_by_action": {
                "submit": "action_submit",
                "complete": "action_select",
                "reopen": "action_reset_draft",
                "cancel": "action_cancel",
            },
            "label_by_action": {"submit": "发起询价", "complete": "确定报价"},
        },
        "sc.output.invoice.adjustment": {
            "state_field": "state",
            "state_phase": {"draft": "draft", "confirmed": "approved", "cancel": "cancelled"},
            "state_actions": {"draft": ["submit", "cancel"]},
            "method_by_action": {"submit": "action_confirm", "cancel": "action_cancel"},
            "label_by_action": {"submit": "确认红冲"},
        },
        "sc.project.document": {
            "state_field": "state",
            "state_phase": {"draft": "draft", "review": "under_review", "done": "done", "cancel": "cancelled"},
            "state_actions": {"draft": ["submit", "cancel"], "review": ["approve", "cancel"]},
            "method_by_action": {"submit": "action_submit", "approve": "action_approve", "cancel": "action_cancel"},
            "label_by_action": {"approve": "归档", "cancel": "作废"},
        },
        "sc.safety.patrol.task": {
            "state_field": "state",
            "state_phase": {"draft": "draft", "planned": "submitted", "done": "done", "cancel": "cancelled"},
            "state_actions": {"draft": ["complete", "cancel"], "planned": ["complete", "reopen", "cancel"], "cancel": ["reopen"]},
            "method_by_action": {"complete": "action_done", "reopen": "action_reset_draft", "cancel": "action_cancel"},
        },
        "sc.workflow.instance": {
            "state_field": "state",
            "state_phase": {"draft": "draft", "running": "under_review", "done": "done", "rejected": "rejected", "cancelled": "cancelled"},
            "state_actions": {"draft": ["submit", "cancel"], "running": ["approve", "reject", "cancel"]},
            "method_by_action": {"submit": "action_submit", "approve": "action_approve", "reject": "action_reject", "cancel": "action_cancel"},
        },
        "tender.doc.purchase": {
            "state_field": "state",
            "state_phase": {"draft": "draft", "submitted": "under_review", "approved": "approved", "rejected": "rejected"},
            "state_actions": {"draft": ["submit", "approve"], "submitted": ["approve", "reject", "reopen"], "rejected": ["reopen"]},
            "method_by_action": {"submit": "action_submit", "approve": "action_approve", "reject": "action_reject", "reopen": "action_reset_draft"},
        },
        "tender.guarantee": {
            "state_field": "state",
            "state_phase": {"draft": "draft", "confirmed": "approved", "cancel": "cancelled"},
            "state_actions": {"draft": ["submit", "cancel"], "confirmed": ["cancel", "reopen"], "cancel": ["reopen"]},
            "method_by_action": {"submit": "action_confirm", "reopen": "action_reset_draft", "cancel": "action_cancel"},
            "label_by_action": {"submit": "确认"},
        },
        "sc.legacy.business.entity.map": {
            "state_field": "mapping_state",
            "state_phase": {"candidate": "draft", "confirmed": "done", "conflict": "rejected", "ignored": "cancelled"},
            "state_actions": {"candidate": ["submit", "reject", "cancel"], "conflict": ["submit", "cancel"], "ignored": ["submit", "reject"]},
            "method_by_action": {"submit": "action_confirm", "reject": "action_mark_conflict", "cancel": "action_ignore"},
            "label_by_action": {"submit": "确认映射", "reject": "标记冲突", "cancel": "忽略"},
        },
        "sc.legacy.partner.map": {
            "state_field": "mapping_state",
            "state_phase": {"candidate": "draft", "confirmed": "done", "conflict": "rejected", "ignored": "cancelled"},
            "state_actions": {"candidate": ["submit", "reject", "cancel"], "conflict": ["submit", "cancel"], "ignored": ["submit", "reject"]},
            "method_by_action": {"submit": "action_confirm", "reject": "action_mark_conflict", "cancel": "action_ignore"},
            "label_by_action": {"submit": "确认映射", "reject": "标记冲突", "cancel": "忽略"},
        },
        "sc.legacy.project.map": {
            "state_field": "mapping_state",
            "state_phase": {"candidate": "draft", "confirmed": "done", "conflict": "rejected", "ignored": "cancelled"},
            "state_actions": {"candidate": ["submit", "reject", "cancel"], "conflict": ["submit", "cancel"], "ignored": ["submit", "reject"]},
            "method_by_action": {"submit": "action_confirm", "reject": "action_mark_conflict", "cancel": "action_ignore"},
            "label_by_action": {"submit": "确认映射", "reject": "标记冲突", "cancel": "忽略"},
        },
        "sc.legacy.scbs.material.map": {
            "state_field": "mapping_state",
            "state_phase": {
                "candidate": "draft",
                "confirmed": "done",
                "create_required": "open",
                "conflict": "rejected",
                "ignored": "cancelled",
            },
            "state_actions": {
                "candidate": ["submit", "approve", "reject", "cancel"],
                "create_required": ["submit", "reject", "cancel"],
                "conflict": ["submit", "approve", "cancel"],
                "ignored": ["submit", "approve", "reject"],
            },
            "method_by_action": {
                "submit": "action_confirm",
                "approve": "action_mark_create_required",
                "reject": "action_mark_conflict",
                "cancel": "action_ignore",
            },
            "label_by_action": {
                "submit": "确认映射",
                "approve": "标记需新建",
                "reject": "标记冲突",
                "cancel": "忽略",
            },
        },
        "sc.legacy.purchase.contract.fact": {
            "state_field": "state",
            "state_phase": {
                "draft": "draft",
                "submit": "under_review",
                "approved": "approved",
                "signed": "effective",
                "legacy_confirmed": "legacy_confirmed",
                "cancel": "cancelled",
            },
            "state_actions": {
                "draft": ["submit", "cancel"],
                "submit": ["approve", "reject", "cancel"],
                "approved": ["cancel"],
                "signed": ["cancel"],
            },
            "approval_actions": ["approve", "reject"],
            "method_by_action": {
                "submit": "action_submit",
                "approve": "validate_tier",
                "reject": "reject_tier",
                "cancel": "action_cancel",
            },
        },
        "sc.partner.import.review": {
            "state_field": "review_state",
            "state_phase": {"candidate": "draft", "resolved": "done", "ignored": "cancelled"},
            "state_actions": {"candidate": ["submit", "approve", "complete", "cancel"]},
            "method_by_action": {
                "submit": "action_resolve_customer",
                "approve": "action_resolve_supplier",
                "complete": "action_resolve_customer_supplier",
                "cancel": "action_ignore",
            },
            "label_by_action": {
                "submit": "确认为客户",
                "approve": "确认为供应商",
                "complete": "确认为客户+供应商",
                "cancel": "忽略",
            },
        },
    }

    ACTIONS = {
        "save_draft": {"label": "保存草稿", "intent": "data.write", "method": None, "kind": "save"},
        "submit": {"label": "提交审批", "intent": "server.object", "kind": "transition"},
        "approve": {"label": "审批通过", "intent": "server.object", "kind": "approval"},
        "reject": {"label": "审批驳回", "intent": "server.object", "kind": "approval"},
        "activate": {"label": "开始执行", "intent": "server.object", "kind": "transition"},
        "complete": {"label": "完成", "intent": "server.object", "kind": "transition"},
        "cancel": {"label": "取消", "intent": "server.object", "kind": "transition"},
        "reopen": {"label": "重置为草稿", "intent": "server.object", "kind": "transition"},
    }

    TERMINAL_PHASES = {"done", "cancelled", "legacy_confirmed"}
    STATUSBAR_BASE_STATES = (
        ("draft", "草稿"),
        ("submitted", "已提交"),
        ("under_review", "审批中"),
        ("approved", "已批准"),
        ("effective", "执行中"),
        ("done", "已完成"),
    )
    STATUSBAR_EXTRA_LABELS = {
        "cancelled": "已取消",
        "rejected": "已驳回",
        "legacy_confirmed": "历史确认",
        "closed": "已关闭",
        "open": "处理中",
    }

    @api.model
    def source_authority_contract(self):
        return {
            "kind": self.SOURCE_KIND,
            "authorities": list(self.SOURCE_AUTHORITIES),
            "projection_only": True,
            "rebuildable": True,
            "runtime_carrier": self._name,
        }

    @api.model
    def supported_model_names(self):
        return sorted(self.PROFILE_BY_MODEL)

    @api.model
    def is_model_supported(self, model_name):
        return str(model_name or "").strip() in self.PROFILE_BY_MODEL

    @api.model
    def describe_record(self, record):
        if not record or len(record) != 1:
            return {}
        profile = self.PROFILE_BY_MODEL.get(record._name)
        if not profile:
            return {}
        raw_state = str(getattr(record, profile["state_field"], "") or "").strip()
        business_phase = profile["state_phase"].get(raw_state, raw_state or "unknown")
        approval_phase = self._approval_phase(record, raw_state=raw_state, business_phase=business_phase)
        editability = self._editability(business_phase, approval_phase)
        evidence_gate = self._evidence_gate(record)
        actions = self._available_actions(record, profile, raw_state, business_phase, approval_phase, evidence_gate)
        return {
            "source": self.source_authority_contract(),
            "model": record._name,
            "record_id": record.id,
            "stateField": profile["state_field"],
            "rawState": raw_state,
            "businessPhase": business_phase,
            "approvalPhase": approval_phase,
            "editability": editability,
            "statusbar": self._statusbar_projection(business_phase, approval_phase),
            "evidenceGate": evidence_gate,
            "availableActions": actions,
        }

    @api.model
    def _statusbar_projection(self, business_phase, approval_phase):
        current = str(business_phase or "").strip()
        approval = str(approval_phase or "").strip()
        if current == "submitted" and approval in ("waiting", "pending"):
            current = "under_review"
        states = [{"value": value, "label": label} for value, label in self.STATUSBAR_BASE_STATES]
        if current and current not in {row["value"] for row in states}:
            states.append({"value": current, "label": self.STATUSBAR_EXTRA_LABELS.get(current, current)})
        return {
            "field": "__workflow_phase",
            "current": current,
            "states": states,
            "readonly": True,
            "source": "workflowContract",
        }

    @api.model
    def _approval_phase(self, record, *, raw_state, business_phase):
        status = str(getattr(record, "validation_status", "") or "").strip()
        if status in ("waiting", "pending"):
            return status
        if status in ("validated", "approved"):
            return "approved"
        if status in ("rejected",):
            return "rejected"
        if business_phase in ("under_review",) and raw_state in ("submit", "approve"):
            return "pending"
        if business_phase in ("approved", "done", "legacy_confirmed"):
            return "approved"
        return "none"

    @api.model
    def _editability(self, business_phase, approval_phase):
        if business_phase in self.TERMINAL_PHASES:
            return "locked"
        if business_phase in ("under_review", "approved", "rejected") or approval_phase in ("waiting", "pending", "approved"):
            return "readonly"
        return "editable"

    @api.model
    def _available_actions(self, record, profile, raw_state, business_phase, approval_phase, evidence_gate):
        del business_phase
        keys = list(profile.get("state_actions", {}).get(raw_state, []))
        if approval_phase in ("waiting", "pending"):
            for key in profile.get("approval_actions", []):
                if key not in keys:
                    keys.append(key)
        if approval_phase in ("waiting", "pending") and "approve" in keys:
            if not bool(getattr(record, "can_review", False)):
                keys.remove("approve")
        if approval_phase in ("waiting", "pending") and "reject" in keys:
            if not bool(getattr(record, "can_review", False)):
                keys.remove("reject")
        method_by_action = profile.get("method_by_action", {})
        actions = []
        for key in keys:
            spec = dict(self.ACTIONS.get(key) or {})
            if not spec:
                continue
            method = method_by_action.get(key, spec.get("method"))
            blockers = [
                row for row in evidence_gate
                if row.get("blocking") and key in (row.get("actionKeys") or [])
            ]
            enabled = not blockers
            actions.append(
                {
                    "key": key,
                    "label": profile.get("label_by_action", {}).get(key) or spec.get("label") or key,
                    "intent": spec.get("intent") or "server.object",
                    "kind": spec.get("kind") or "transition",
                    "method": method,
                    "enabled": enabled,
                    "reason_code": blockers[0].get("reasonCode") if blockers else "",
                    "blocked_message": blockers[0].get("message") if blockers else "",
                    "target": {
                        "model": record._name,
                        "id": record.id,
                        "method": method,
                    },
                }
            )
        return actions

    @api.model
    def _evidence_gate(self, record):
        if record._name == "sc.expense.claim":
            return self._expense_claim_evidence_gate(record)
        if record._name == "sc.settlement.order":
            return self._settlement_order_evidence_gate(record)
        if record._name == "payment.request":
            return self._payment_request_evidence_gate(record)
        if record._name in ("construction.contract", "construction.contract.expense", "construction.contract.income"):
            return self._construction_contract_evidence_gate(record)
        if record._name == "sc.payment.execution":
            return self._payment_execution_evidence_gate(record)
        if record._name == "sc.receipt.income":
            return self._receipt_income_evidence_gate(record)
        if record._name == "sc.invoice.registration":
            return self._invoice_registration_evidence_gate(record)
        if record._name == "sc.self.funding.registration":
            return self._self_funding_registration_evidence_gate(record)
        if record._name == "sc.financing.loan":
            return self._financing_loan_evidence_gate(record)
        if record._name == "sc.treasury.reconciliation":
            return self._treasury_reconciliation_evidence_gate(record)
        if record._name == "sc.settlement.adjustment":
            return self._settlement_adjustment_evidence_gate(record)
        return []

    @api.model
    def _gate(self, reason_code, message, *, action_keys=None, blocking=True, severity="block"):
        return {
            "reasonCode": reason_code,
            "message": message,
            "actionKeys": list(action_keys or ["submit", "approve", "complete"]),
            "blocking": bool(blocking),
            "severity": severity,
        }

    @api.model
    def _expense_claim_evidence_gate(self, record):
        if getattr(record, "source_origin", "") == "legacy" and getattr(record, "state", "") == "legacy_confirmed":
            return []
        gates = []
        if not record.project_id:
            gates.append(self._gate("EXPENSE_MISSING_PROJECT", "费用/扣款/保证金单据必须关联项目。"))
        if not record.partner_id:
            gates.append(self._gate("EXPENSE_MISSING_PARTNER", "费用/扣款/保证金单据必须选择往来单位。"))
        if (record.amount or 0.0) <= 0:
            gates.append(self._gate("EXPENSE_INVALID_AMOUNT", "费用/扣款/保证金金额必须大于 0。"))
        if (record.approved_amount or 0.0) < 0:
            gates.append(self._gate("EXPENSE_INVALID_APPROVED_AMOUNT", "批准金额不能为负数。"))
        expected = record.approved_amount or record.amount or 0.0
        if (record.paid_amount or 0.0) < 0:
            gates.append(self._gate("EXPENSE_INVALID_PAID_AMOUNT", "已付款金额不能为负数。"))
        elif (record.paid_amount or 0.0) > expected:
            gates.append(self._gate("EXPENSE_PAID_AMOUNT_OVER_EXPECTED", "已付款金额不能超过批准/申请金额。"))
        if record.payment_anchor_policy in ("pay_request_required", "receive_request_required") and not record.payment_request_id:
            gates.append(self._gate("EXPENSE_MISSING_PAYMENT_REQUEST", "现金办理必须关联付款/收款申请。"))
        try:
            is_noncash_deduction = record._is_noncash_deduction_bill()
        except Exception:
            is_noncash_deduction = False
        if is_noncash_deduction:
            if record.payment_request_id:
                gates.append(self._gate("DEDUCTION_BILL_SHOULD_NOT_LINK_PAYMENT_REQUEST", "扣款单是非现金责任清分事实，不应关联付款/收款申请。"))
            lines = record.deduction_line_ids
            if not lines:
                gates.append(self._gate("DEDUCTION_BILL_MISSING_LINES", "扣款登记必须填写至少一条扣款单明细后才能提交、批准或完成。"))
            else:
                if any(not (line.item_name or "").strip() for line in lines):
                    gates.append(self._gate("DEDUCTION_BILL_LINE_MISSING_ITEM", "扣款单明细必须填写扣款事项。"))
                if any((line.amount or 0.0) <= 0 for line in lines):
                    gates.append(self._gate("DEDUCTION_BILL_LINE_INVALID_AMOUNT", "扣款单明细金额必须大于 0。"))
                total = sum(lines.mapped("amount"))
                rounding = record.currency_id.rounding if record.currency_id else 0.01
                if float_compare(total, expected, precision_rounding=rounding) != 0:
                    gates.append(
                        self._gate(
                            "DEDUCTION_BILL_LINE_TOTAL_MISMATCH",
                            "扣款单明细金额合计必须等于本次扣款金额。当前明细合计：%s，本次扣款金额：%s。" % (total, expected),
                        )
                    )
        category = record.business_category_id
        if category and category.attachment_policy == "required" and not record.attachment_ids:
            gates.append(self._gate("EXPENSE_ATTACHMENT_REQUIRED", "当前业务分类要求上传附件后才能提交、批准或完成。"))
        if record.financial_flow == "cash_out":
            payee_account = record.payee_account or record.receipt_account_name or record.payee
            payer_account = record.payer_account or record.payment_account_name
            if not payee_account:
                gates.append(self._gate("EXPENSE_MISSING_PAYEE_ACCOUNT", "现金流出办理必须填写收款账户信息。"))
            if not payer_account:
                gates.append(self._gate("EXPENSE_MISSING_PAYER_ACCOUNT", "现金流出办理必须填写付款账户信息。"))
        elif record.financial_flow == "cash_in":
            receiving_account = record.payer_account or record.payment_account_name
            if not receiving_account:
                gates.append(self._gate("EXPENSE_MISSING_RECEIVING_ACCOUNT", "现金流入办理必须填写收款账户信息。"))
        return gates

    @api.model
    def _settlement_order_evidence_gate(self, record):
        gates = []
        if not record.project_id:
            gates.append(self._gate("SETTLEMENT_MISSING_PROJECT", "结算单必须关联项目。"))
        if not record.partner_id and not record.legacy_fact_model:
            gates.append(self._gate("SETTLEMENT_MISSING_PARTNER", "结算单必须选择往来单位。"))
        if not record.line_ids:
            gates.append(self._gate("SETTLEMENT_MISSING_LINES", "结算单必须维护结算明细。"))
        if (record.amount_total or 0.0) <= 0:
            gates.append(self._gate("SETTLEMENT_INVALID_AMOUNT", "结算金额必须大于 0。"))
        if any((line.qty or 0.0) <= 0 for line in record.line_ids):
            gates.append(self._gate("SETTLEMENT_INVALID_LINE_QTY", "结算行数量必须大于 0。"))
        if any((line.price_unit or 0.0) < 0 for line in record.line_ids):
            gates.append(self._gate("SETTLEMENT_INVALID_LINE_PRICE", "结算行单价不能为负数。"))
        return gates

    @api.model
    def _payment_request_evidence_gate(self, record):
        gates = []
        if not record.project_id:
            gates.append(self._gate("PAYMENT_MISSING_PROJECT", "付款/收款申请必须关联项目。"))
        if (record.amount or 0.0) <= 0:
            gates.append(self._gate("PAYMENT_INVALID_AMOUNT", "付款/收款申请金额必须大于 0。"))
        try:
            has_basis = record._has_payment_basis()
        except Exception:
            has_basis = bool(record.contract_id or record.settlement_id or record.material_settlement_id)
        if not has_basis:
            gates.append(self._gate("PAYMENT_MISSING_BASIS", "请先选择关联合同、结算单、材料结算单或历史关联依据。"))
        if record.type == "pay" and record.settlement_id:
            try:
                metrics = opm.compute_payment_payable_excluding_self(record)
            except Exception:
                metrics = {}
            payable = metrics.get("payable") if isinstance(metrics, dict) else None
            precision = metrics.get("precision") if isinstance(metrics, dict) else None
            if payable is not None:
                precision = precision or (record.currency_id.rounding if record.currency_id else 0.01)
                if float_compare(payable, 0.0, precision_rounding=precision) <= 0:
                    gates.append(self._gate("PAYMENT_SETTLEMENT_NO_PAYABLE_BALANCE", "结算单剩余额度不足。"))
                elif float_compare(record.amount or 0.0, payable, precision_rounding=precision) == 1:
                    gates.append(self._gate("PAYMENT_OVER_SETTLEMENT_BALANCE", "申请金额 %s 超过结算单剩余额度 %s。" % (record.amount or 0.0, payable)))
        if record.type == "pay" and record.material_settlement_id:
            settlement = record.material_settlement_id
            if getattr(settlement, "state", "") != "confirmed":
                gates.append(self._gate("PAYMENT_MATERIAL_SETTLEMENT_NOT_CONFIRMED", "材料结算单未确认。"))
            try:
                requested = record._material_settlement_requested_amount_excluding_self()
            except Exception:
                requested = 0.0
            payable = (settlement.amount_total or 0.0) - (requested or 0.0)
            precision = record.currency_id.rounding if record.currency_id else 0.01
            if float_compare(record.amount or 0.0, payable, precision_rounding=precision) == 1:
                gates.append(self._gate("PAYMENT_OVER_MATERIAL_SETTLEMENT_BALANCE", "本次申请金额 %s 超过材料结算剩余可申请金额 %s。" % (record.amount or 0.0, payable)))
        return gates

    @api.model
    def _construction_contract_evidence_gate(self, record):
        gates = []
        if not record.project_id:
            gates.append(self._gate("CONTRACT_MISSING_PROJECT", "项目合同必须关联项目。"))
        if not record.partner_id:
            gates.append(self._gate("CONTRACT_MISSING_PARTNER", "项目合同必须选择合同方。"))
        if getattr(record, "validation_status", "") in ("waiting", "pending"):
            gates.append(
                self._gate(
                    "CONTRACT_APPROVAL_IN_PROGRESS",
                    "项目合同已经在统一审批流程中，请等待审批完成后再重复提交。",
                    action_keys=["submit"],
                )
            )
        if getattr(record, "state", "") in ("confirmed", "running") and not record.line_ids:
            gates.append(
                self._gate(
                    "CONTRACT_MISSING_LINES_FOR_CLOSE",
                    "无合同明细的合同不可关闭，请补充明细。",
                    action_keys=["complete"],
                )
            )
        if getattr(record, "is_locked", False):
            gates.append(
                self._gate(
                    "CONTRACT_LOCKED_BY_DOWNSTREAM_FACTS",
                    "合同已被付款申请/结算单引用，禁止取消或重置为草稿。",
                    action_keys=["cancel", "reopen"],
                )
            )
        return gates

    @api.model
    def _payment_execution_evidence_gate(self, record):
        if getattr(record, "source_origin", "") == "legacy" and getattr(record, "state", "") == "legacy_confirmed":
            return []
        gates = []
        if not record.project_id:
            gates.append(self._gate("PAYMENT_EXECUTION_MISSING_PROJECT", "付款执行必须关联项目。"))
        if not record.payment_request_id:
            gates.append(self._gate("PAYMENT_EXECUTION_MISSING_REQUEST", "新系统付款执行必须关联已审批的付款申请。"))
        request = record.payment_request_id
        material_settlement = request.material_settlement_id if request else False
        if not record.contract_id and not material_settlement and not (request and request._has_payment_basis()):
            gates.append(self._gate("PAYMENT_EXECUTION_MISSING_CONTRACT", "新系统付款执行必须关联合同或结算依据。"))
        if not record.partner_id:
            gates.append(self._gate("PAYMENT_EXECUTION_MISSING_PARTNER", "付款执行必须选择往来单位。"))
        if (record.paid_amount or 0.0) <= 0:
            gates.append(self._gate("PAYMENT_EXECUTION_INVALID_AMOUNT", "实付金额必须大于 0。"))
        payer_account = record.payment_account_no or record.bank_account or record.payment_account_name
        payee_account = record.receipt_account_no or record.receipt_account_name
        if not payer_account:
            gates.append(self._gate("PAYMENT_EXECUTION_MISSING_PAYER_ACCOUNT", "新系统付款执行必须填写付款账户信息。"))
        if not payee_account:
            gates.append(self._gate("PAYMENT_EXECUTION_MISSING_PAYEE_ACCOUNT", "新系统付款执行必须填写收款账户信息。"))
        if getattr(record, "validation_status", "") in ("waiting", "pending"):
            gates.append(
                self._gate(
                    "PAYMENT_EXECUTION_APPROVAL_IN_PROGRESS",
                    "付款执行已经在统一审批流程中，请等待审批完成后再重复提交。",
                    action_keys=["submit"],
                )
            )
        return gates

    @api.model
    def _receipt_income_evidence_gate(self, record):
        if getattr(record, "source_origin", "") == "legacy" and getattr(record, "state", "") == "legacy_confirmed":
            return []
        gates = []
        if not record.project_id:
            gates.append(self._gate("RECEIPT_INCOME_MISSING_PROJECT", "收款收入必须关联项目。"))
        if not record.payment_request_id:
            gates.append(self._gate("RECEIPT_INCOME_MISSING_REQUEST", "新系统收款收入必须关联已审批的收款申请。"))
        if not record.contract_id:
            gates.append(self._gate("RECEIPT_INCOME_MISSING_CONTRACT", "新系统收款收入必须关联合同。"))
        if not record.partner_id:
            gates.append(self._gate("RECEIPT_INCOME_MISSING_PARTNER", "收款收入必须选择往来单位。"))
        if (record.amount or 0.0) <= 0:
            gates.append(self._gate("RECEIPT_INCOME_INVALID_AMOUNT", "收款金额必须大于 0。"))
        receiving_account = record.receiving_account_no or record.receiving_account or record.receiving_account_name
        if not receiving_account:
            gates.append(self._gate("RECEIPT_INCOME_MISSING_RECEIVING_ACCOUNT", "新系统收款收入必须填写收款账户信息。"))
        if getattr(record, "validation_status", "") in ("waiting", "pending"):
            gates.append(
                self._gate(
                    "RECEIPT_INCOME_APPROVAL_IN_PROGRESS",
                    "收款收入已经在统一审批流程中，请等待审批完成后再重复提交。",
                    action_keys=["submit"],
                )
            )
        return gates

    @api.model
    def _invoice_registration_evidence_gate(self, record):
        if getattr(record, "source_origin", "") == "legacy" and getattr(record, "state", "") == "legacy_confirmed":
            return []
        gates = []
        if not record.project_id:
            gates.append(self._gate("INVOICE_REGISTRATION_MISSING_PROJECT", "发票登记必须关联项目。"))
        if not record.invoice_date:
            gates.append(self._gate("INVOICE_REGISTRATION_MISSING_DATE", "发票登记必须填写发票日期。"))
        if (record.amount_total or 0.0) <= 0 and (record.tax_amount or 0.0) <= 0 and (record.surcharge_amount or 0.0) <= 0:
            gates.append(self._gate("INVOICE_REGISTRATION_INVALID_AMOUNT", "发票登记必须填写有效金额。"))
        if record.source_kind == "prepaid_tax" or record.direction == "prepaid":
            if not record.tax_certificate_no:
                gates.append(self._gate("INVOICE_REGISTRATION_MISSING_TAX_CERTIFICATE", "预缴税登记必须填写完税凭证号码。"))
        elif not record.invoice_no:
            gates.append(self._gate("INVOICE_REGISTRATION_MISSING_INVOICE_NO", "发票登记必须填写发票号码。"))
        if record.contract_id:
            if record.contract_id.project_id != record.project_id:
                gates.append(self._gate("INVOICE_REGISTRATION_CONTRACT_PROJECT_MISMATCH", "发票登记合同必须属于当前项目。"))
            if record.contract_id.partner_id and record.partner_id and record.contract_id.partner_id != record.partner_id:
                gates.append(self._gate("INVOICE_REGISTRATION_CONTRACT_PARTNER_MISMATCH", "发票登记往来单位必须与合同相对方一致。"))
        if record.settlement_id:
            if record.settlement_id.project_id != record.project_id:
                gates.append(self._gate("INVOICE_REGISTRATION_SETTLEMENT_PROJECT_MISMATCH", "发票登记结算单必须属于当前项目。"))
            if record.settlement_id.contract_id and record.contract_id and record.settlement_id.contract_id != record.contract_id:
                gates.append(self._gate("INVOICE_REGISTRATION_SETTLEMENT_CONTRACT_MISMATCH", "发票登记合同必须与结算单合同一致。"))
            if record.settlement_id.partner_id and record.partner_id and record.settlement_id.partner_id != record.partner_id:
                gates.append(self._gate("INVOICE_REGISTRATION_SETTLEMENT_PARTNER_MISMATCH", "发票登记往来单位必须与结算单往来单位一致。"))
        if getattr(record, "validation_status", "") in ("waiting", "pending"):
            gates.append(
                self._gate(
                    "INVOICE_REGISTRATION_APPROVAL_IN_PROGRESS",
                    "发票登记已经在统一审批流程中，请等待审批完成后再重复提交。",
                    action_keys=["submit"],
                )
            )
        return gates

    @api.model
    def _self_funding_registration_evidence_gate(self, record):
        gates = []
        if not record.project_id:
            gates.append(self._gate("SELF_FUNDING_MISSING_PROJECT", "请先选择项目。"))
        if not record.partner_id:
            gates.append(self._gate("SELF_FUNDING_MISSING_PARTNER", "请先选择承包人。"))
        if not record.document_date:
            gates.append(self._gate("SELF_FUNDING_MISSING_DATE", "请先填写发生日期。"))
        if (record.amount or 0.0) <= 0:
            gates.append(self._gate("SELF_FUNDING_INVALID_AMOUNT", "自筹办理金额必须大于 0。"))
        if getattr(record, "source_origin", "") == "manual":
            if not record.attachment_ids:
                gates.append(self._gate("SELF_FUNDING_ATTACHMENT_REQUIRED", "请上传自筹办理附件，作为公司与承包人资金责任的办理依据。"))
            if not record.payment_account_name:
                gates.append(self._gate("SELF_FUNDING_MISSING_COMPANY_ACCOUNT", "请填写公司账户/户名。"))
            if not record.partner_account_name:
                gates.append(self._gate("SELF_FUNDING_MISSING_PARTNER_ACCOUNT", "请填写承包人账户/户名。"))
        if getattr(record, "validation_status", "") in ("waiting", "pending"):
            gates.append(
                self._gate(
                    "SELF_FUNDING_APPROVAL_IN_PROGRESS",
                    "自筹办理已经在统一审批流程中，请等待审批完成后再重复提交。",
                    action_keys=["submit"],
                )
            )
        return gates

    @api.model
    def _financing_loan_evidence_gate(self, record):
        if getattr(record, "source_origin", "") == "legacy" and getattr(record, "state", "") == "legacy_confirmed":
            return []
        gates = []
        if not record.project_id:
            gates.append(self._gate("FINANCING_LOAN_MISSING_PROJECT", "融资借款必须关联项目。"))
        if not record.partner_id:
            gates.append(self._gate("FINANCING_LOAN_MISSING_PARTNER", "请先选择往来单位后再完成融资借款。"))
        if not record.document_date:
            gates.append(self._gate("FINANCING_LOAN_MISSING_DATE", "请先填写单据日期后再完成融资借款。"))
        if (record.amount or 0.0) <= 0:
            gates.append(self._gate("FINANCING_LOAN_INVALID_AMOUNT", "融资借款金额必须大于 0。"))
        if record.loan_type == "borrowing_request" and record.direction == "borrowed_fund":
            allowed_codes = {
                "finance.loan.contractor_project_borrow",
                "finance.loan.project_borrow_company",
            }
            if record.business_category_id.code not in allowed_codes:
                gates.append(
                    self._gate(
                        "FINANCING_LOAN_INVALID_BORROWING_CATEGORY",
                        "借款办理必须选择“承包人借项目款”或“项目借公司款登记”业务分类后才能完成。",
                    )
                )
        if getattr(record, "validation_status", "") in ("waiting", "pending"):
            gates.append(
                self._gate(
                    "FINANCING_LOAN_APPROVAL_IN_PROGRESS",
                    "融资借款已经在统一审批流程中，请等待审批完成后再重复提交。",
                    action_keys=["submit"],
                )
            )
        return gates

    @api.model
    def _treasury_reconciliation_evidence_gate(self, record):
        if getattr(record, "source_origin", "") == "legacy" and getattr(record, "state", "") == "legacy_confirmed":
            return []
        gates = []
        if not record.project_id:
            gates.append(self._gate("TREASURY_RECONCILIATION_MISSING_PROJECT", "资金对账必须关联项目。"))
        if not record.treasury_ledger_id:
            gates.append(self._gate("TREASURY_RECONCILIATION_MISSING_LEDGER", "请先关联资金台账后再完成对账。"))
        elif record.treasury_ledger_id.state != "posted":
            gates.append(self._gate("TREASURY_RECONCILIATION_LEDGER_NOT_POSTED", "只能对已入账的资金台账完成对账。"))
        elif record.treasury_ledger_id.project_id != record.project_id:
            gates.append(self._gate("TREASURY_RECONCILIATION_LEDGER_PROJECT_MISMATCH", "资金台账项目与对账单项目不一致，不能完成对账。"))
        rounding = record.currency_id.rounding if record.currency_id else 0.01
        if float_compare(record.system_difference or 0.0, 0.0, precision_rounding=rounding) != 0:
            gates.append(self._gate("TREASURY_RECONCILIATION_DIFFERENCE_NOT_ZERO", "银企差额未归零，不能完成资金对账。"))
        if getattr(record, "validation_status", "") in ("waiting", "pending"):
            gates.append(
                self._gate(
                    "TREASURY_RECONCILIATION_APPROVAL_IN_PROGRESS",
                    "资金对账已经在统一审批流程中，请等待审批完成后再重复提交。",
                    action_keys=["submit"],
                )
            )
        return gates

    @api.model
    def _settlement_adjustment_evidence_gate(self, record):
        if getattr(record, "source_origin", "") == "legacy" and getattr(record, "state", "") == "legacy_confirmed":
            return []
        gates = []
        if not record.item_name:
            gates.append(self._gate("SETTLEMENT_ADJUSTMENT_MISSING_ITEM", "结算调整确认前必须维护调整事项。"))
        if (record.amount or 0.0) <= 0:
            gates.append(self._gate("SETTLEMENT_ADJUSTMENT_INVALID_AMOUNT", "结算调整确认前调整金额必须大于 0。"))
        if not record.settlement_id and not record.contract_id:
            gates.append(self._gate("SETTLEMENT_ADJUSTMENT_MISSING_ANCHOR", "结算调整确认前必须关联结算单或合同。"))
        if getattr(record, "validation_status", "") in ("waiting", "pending"):
            gates.append(
                self._gate(
                    "SETTLEMENT_ADJUSTMENT_APPROVAL_IN_PROGRESS",
                    "结算调整已经在统一审批流程中，请等待审批完成后再重复提交。",
                    action_keys=["submit"],
                )
            )
        return gates
