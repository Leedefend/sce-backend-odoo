# -*- coding: utf-8 -*-
from odoo import _
from odoo.exceptions import UserError


def raise_guard(code, obj, action, reasons=None, hints=None):
    """Raise standardized guard error.

    code: short identifier for tests/logs, e.g. P0_STATE_ILLEGAL_TRANSITION
    obj: object label, e.g. 项目[Demo]
    action: action label, e.g. 状态变更
    reasons/hints: list of strings
    """
    reasons = reasons or []
    hints = hints or []
    lines = [_(f"[SC_GUARD:{code}] {obj}：{action} 被拒绝")]
    if reasons:
        lines.append(_("原因："))
        lines.extend([f"- {r}" for r in reasons])
    if hints:
        lines.append(_("建议："))
        lines.extend([f"- {h}" for h in hints])
    raise UserError("\n".join(lines))
