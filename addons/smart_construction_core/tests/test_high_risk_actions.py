# -*- coding: utf-8 -*-
import logging

from odoo.tests.common import TransactionCase, tagged

from .risk_actions import RISK_ACTION_XMLIDS

_logger = logging.getLogger(__name__)


@tagged("post_install", "-at_install", "sc_gate", "sc_perm")
class TestHighRiskActions(TransactionCase):
    """高风险动作必须显式绑定 groups_id，避免越权。"""

    def test_high_risk_actions_have_groups(self):
        missing_groups = []
        missing_xmlid = []
        for xid in RISK_ACTION_XMLIDS:
            rec = self.env.ref(xid, raise_if_not_found=False)
            if not rec:
                missing_xmlid.append(xid)
                continue
            if hasattr(rec, "groups_id") and not rec.groups_id:
                missing_groups.append(xid)
        if missing_xmlid:
            _logger.info("高风险动作未找到（模块未安装可忽略）：%s", missing_xmlid)
        self.assertFalse(
            missing_groups,
            "高风险动作缺少 groups_id: %s" % ", ".join(missing_groups),
        )
