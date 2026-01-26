# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo.addons.smart_construction_core.services.lifecycle_capability_service import (
    LifecycleCapabilityService,
)


class PortalContractService:
    def __init__(self, env):
        self.env = env

    def build_lifecycle_dashboard(self, route="/portal/lifecycle"):
        matrix, meta = LifecycleCapabilityService(self.env)._load_matrix()
        lifecycle_states = list(matrix.keys())
        capability_codes = sorted({cap for caps in matrix.values() for cap in caps.keys()})
        return {
            "subject": "ui.contract",
            "route": route,
            "schema_version": "portal-lifecycle-v1",
            "layout": {
                "title": "项目生命周期驾驶舱",
                "columns": [
                    {"key": "lifecycle", "title": "生命周期看板"},
                    {"key": "detail", "title": "项目详情"},
                    {"key": "capabilities", "title": "能力矩阵"},
                ],
            },
            "lifecycle_states": lifecycle_states,
            "capability_codes": capability_codes,
            "matrix_meta": meta,
        }
