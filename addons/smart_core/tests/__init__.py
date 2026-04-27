# -*- coding: utf-8 -*-
"""
smart_core tests package

Keep package import side effects minimal so isolated pure-Python unittest
modules can be executed without a live Odoo runtime. Odoo transaction-style
tests remain discoverable by explicit module import in Odoo test execution.
"""

from . import test_permission_contract_runtime_uid
from . import test_native_action_selection_alignment
from . import test_action_dispatcher_server_mapping
from . import test_menu_delivery_convergence_service
