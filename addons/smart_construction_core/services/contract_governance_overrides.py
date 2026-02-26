# -*- coding: utf-8 -*-
from odoo.addons.smart_core.utils.contract_governance import (
    apply_project_form_domain_override,
    register_contract_domain_override,
)


register_contract_domain_override(
    "smart_construction_core.project_form",
    apply_project_form_domain_override,
    priority=10,
)
