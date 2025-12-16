# -*- coding: utf-8 -*-
from .rules import get_registered_rules

# 注册规则（导入以触发装饰器）
from . import rule_company_consistency  # noqa: F401
from . import rule_project_required  # noqa: F401
from . import rule_3way_link_integrity  # noqa: F401
from . import rule_amount_qty_sanity  # noqa: F401
from . import rule_payment_not_overpay  # noqa: F401
