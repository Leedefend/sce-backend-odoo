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
from . import test_odoo_native_alignment_boundaries
from . import test_release_gate_category_options
from . import test_usage_backend
from . import test_business_config_change_set
