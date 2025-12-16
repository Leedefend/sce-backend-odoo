# -*- coding: utf-8 -*-
from . import project_core
from . import project_contract
from . import purchase_extend
from . import cost_domain
from ..support import budget_compat  # 兼容旧 project.budget.line 名称，需在主模型前加载
from . import project_project_financial
from . import project_budget
from . import boq
from . import material_plan
from . import settlement_order
from . import settlement
from . import payment_request
