# -*- coding: utf-8 -*-
"""Unified state definitions for core business objects.

Keep these constants in sync with docs/phase_p0/state_machine.md.
"""

from odoo import _
from odoo.exceptions import UserError


class ScStateMachine:
    """Single source of truth for lifecycle states + legal transitions."""

    PROJECT = "project.project"
    CONTRACT = "construction.contract"
    SETTLEMENT_ORDER = "sc.settlement.order"
    SETTLEMENT = "project.settlement"
    PAYMENT_REQUEST = "payment.request"

    PROJECT_STATES = [
        ("draft", _("立项")),
        ("in_progress", _("在建")),
        ("paused", _("停工")),
        ("done", _("竣工")),
        ("closing", _("结算中")),
        ("warranty", _("保修期")),
        ("closed", _("关闭")),
    ]
    PROJECT_TRANSITIONS = {
        "draft": {"in_progress", "paused", "closed"},
        "in_progress": {"paused", "done", "closing", "closed"},
        "paused": {"in_progress", "closed"},
        "done": {"closing", "warranty", "closed"},
        "closing": {"warranty", "closed"},
        "warranty": {"closed"},
        "closed": set(),
    }

    CONTRACT_STATES = [
        ("draft", _("草稿")),
        ("confirmed", _("已生效")),
        ("running", _("执行中")),
        ("closed", _("已关闭")),
        ("cancel", _("已取消")),
    ]
    CONTRACT_TRANSITIONS = {
        "draft": {"confirmed", "cancel"},
        "confirmed": {"running", "closed", "cancel"},
        "running": {"closed", "cancel"},
        "closed": set(),
        "cancel": set(),
    }

    SETTLEMENT_ORDER_STATES = [
        ("draft", _("草稿")),
        ("submit", _("提交")),
        ("approve", _("批准")),
        ("done", _("完成")),
        ("cancel", _("取消")),
    ]
    SETTLEMENT_ORDER_TRANSITIONS = {
        "draft": {"submit", "cancel"},
        "submit": {"approve", "cancel"},
        "approve": {"done", "cancel"},
        "done": set(),
        "cancel": set(),
    }

    SETTLEMENT_STATES = [
        ("draft", _("草稿")),
        ("confirmed", _("已确认")),
        ("done", _("完成")),
        ("cancel", _("取消")),
    ]
    SETTLEMENT_TRANSITIONS = {
        "draft": {"confirmed", "cancel"},
        "confirmed": {"done", "cancel"},
        "done": set(),
        "cancel": set(),
    }

    PAYMENT_REQUEST_STATES = [
        ("draft", _("草稿")),
        ("submit", _("提交")),
        ("approve", _("审批中")),
        ("approved", _("已批准")),
        ("rejected", _("已驳回")),
        ("done", _("已完成")),
        ("cancel", _("已取消")),
    ]
    PAYMENT_REQUEST_TRANSITIONS = {
        "draft": {"submit", "cancel"},
        "submit": {"approve", "rejected", "cancel"},
        "approve": {"approved", "rejected", "cancel"},
        "approved": {"done", "cancel"},
        "rejected": {"draft", "cancel"},
        "done": set(),
        "cancel": set(),
    }

    BOQ_SOURCE_TYPES = [
        ("tender", _("招标清单")),
        ("contract", _("合同清单")),
        ("settlement", _("结算清单")),
    ]

    _REGISTRY = {
        PROJECT: (PROJECT_STATES, PROJECT_TRANSITIONS),
        CONTRACT: (CONTRACT_STATES, CONTRACT_TRANSITIONS),
        SETTLEMENT_ORDER: (SETTLEMENT_ORDER_STATES, SETTLEMENT_ORDER_TRANSITIONS),
        SETTLEMENT: (SETTLEMENT_STATES, SETTLEMENT_TRANSITIONS),
        PAYMENT_REQUEST: (PAYMENT_REQUEST_STATES, PAYMENT_REQUEST_TRANSITIONS),
    }

    @classmethod
    def is_registered(cls, model_name):
        return model_name in cls._REGISTRY

    @classmethod
    def _get_registry(cls, model_name):
        if model_name not in cls._REGISTRY:
            raise KeyError(f"ScStateMachine: model not registered: {model_name}")
        return cls._REGISTRY[model_name]

    @classmethod
    def selection(cls, model_name):
        return cls._get_registry(model_name)[0]

    @classmethod
    def transitions(cls, model_name):
        return cls._get_registry(model_name)[1]

    @classmethod
    def label(cls, model_name, key):
        states, _ = cls._get_registry(model_name)
        return dict(states).get(key, key)

    @classmethod
    def assert_transition(cls, model_name, old, new, obj_display=""):
        if not old or not new or old == new:
            return
        allowed = cls.transitions(model_name).get(old, set())
        if new not in allowed:
            hint = _("合法跃迁：%s") % (", ".join(sorted(allowed)) or "-")
            title = _("状态跃迁被拒绝")
            who = obj_display or model_name
            raise UserError(
                _("%(title)s：%(who)s %(old)s(%(old_l)s) -> %(new)s(%(new_l)s)\n%(hint)s")
                % {
                    "title": title,
                    "who": who,
                    "old": old,
                    "old_l": cls.label(model_name, old),
                    "new": new,
                    "new_l": cls.label(model_name, new),
                    "hint": hint,
                }
            )


# Legacy exports for backward compatibility. Prefer ScStateMachine.* in new code.
PROJECT_LIFECYCLE_STATES = ScStateMachine.PROJECT_STATES
PROJECT_LIFECYCLE_TRANSITIONS = ScStateMachine.PROJECT_TRANSITIONS
CONTRACT_STATES = ScStateMachine.CONTRACT_STATES
CONTRACT_TRANSITIONS = ScStateMachine.CONTRACT_TRANSITIONS
SETTLEMENT_ORDER_STATES = ScStateMachine.SETTLEMENT_ORDER_STATES
SETTLEMENT_ORDER_TRANSITIONS = ScStateMachine.SETTLEMENT_ORDER_TRANSITIONS
SETTLEMENT_STATES = ScStateMachine.SETTLEMENT_STATES
SETTLEMENT_TRANSITIONS = ScStateMachine.SETTLEMENT_TRANSITIONS
PAYMENT_REQUEST_STATES = ScStateMachine.PAYMENT_REQUEST_STATES
PAYMENT_REQUEST_TRANSITIONS = ScStateMachine.PAYMENT_REQUEST_TRANSITIONS
BOQ_SOURCE_TYPES = ScStateMachine.BOQ_SOURCE_TYPES
