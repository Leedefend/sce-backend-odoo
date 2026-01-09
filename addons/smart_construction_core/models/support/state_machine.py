# -*- coding: utf-8 -*-
"""Unified state definitions for core business objects.

Keep these constants in sync with docs/phase_p0/state_machine.md.
"""

# Project lifecycle (project.project.lifecycle_state)
PROJECT_LIFECYCLE_STATES = [
    ("draft", "立项"),
    ("in_progress", "在建"),
    ("paused", "停工"),
    ("done", "竣工"),
    ("closing", "结算中"),
    ("warranty", "保修期"),
    ("closed", "关闭"),
]

PROJECT_LIFECYCLE_TRANSITIONS = {
    "draft": ["in_progress", "paused", "closed"],
    "in_progress": ["paused", "done", "closing", "closed"],
    "paused": ["in_progress", "closed"],
    "done": ["closing", "warranty", "closed"],
    "closing": ["warranty", "closed"],
    "warranty": ["closed"],
    "closed": [],
}

# Contract (construction.contract.state)
CONTRACT_STATES = [
    ("draft", "草稿"),
    ("confirmed", "已生效"),
    ("running", "执行中"),
    ("closed", "已关闭"),
    ("cancel", "已取消"),
]

CONTRACT_TRANSITIONS = {
    "draft": ["confirmed", "cancel"],
    "confirmed": ["running", "closed", "cancel"],
    "running": ["closed", "cancel"],
    "closed": [],
    "cancel": [],
}

# Settlement order (sc.settlement.order.state)
SETTLEMENT_ORDER_STATES = [
    ("draft", "草稿"),
    ("submit", "提交"),
    ("approve", "批准"),
    ("done", "完成"),
    ("cancel", "取消"),
]

SETTLEMENT_ORDER_TRANSITIONS = {
    "draft": ["submit", "cancel"],
    "submit": ["approve", "cancel"],
    "approve": ["done", "cancel"],
    "done": [],
    "cancel": [],
}

# Settlement (project.settlement.state)
SETTLEMENT_STATES = [
    ("draft", "草稿"),
    ("confirmed", "已确认"),
    ("done", "完成"),
    ("cancel", "取消"),
]

SETTLEMENT_TRANSITIONS = {
    "draft": ["confirmed", "cancel"],
    "confirmed": ["done", "cancel"],
    "done": [],
    "cancel": [],
}

# Payment request (payment.request.state)
PAYMENT_REQUEST_STATES = [
    ("draft", "草稿"),
    ("submit", "提交"),
    ("approve", "审批中"),
    ("approved", "已批准"),
    ("rejected", "已驳回"),
    ("done", "已完成"),
    ("cancel", "已取消"),
]

PAYMENT_REQUEST_TRANSITIONS = {
    "draft": ["submit", "cancel"],
    "submit": ["approve", "rejected", "cancel"],
    "approve": ["approved", "rejected", "cancel"],
    "approved": ["done", "cancel"],
    "rejected": ["draft", "cancel"],
    "done": [],
    "cancel": [],
}

# BOQ source types (project.boq.line.source_type)
BOQ_SOURCE_TYPES = [
    ("tender", "招标清单"),
    ("contract", "合同清单"),
    ("settlement", "结算清单"),
]
