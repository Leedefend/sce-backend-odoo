# -*- coding: utf-8 -*-
from __future__ import annotations

from uuid import uuid4

from odoo.addons.smart_construction_core.services.lifecycle_capability_service import (
    LifecycleCapabilityService,
)


class PortalContractService:
    def __init__(self, env):
        self.env = env

    def build_lifecycle_dashboard(self, route="/portal/lifecycle", trace_id=None):
        matrix, meta = LifecycleCapabilityService(self.env)._load_matrix()
        lifecycle_states = list(matrix.keys())
        capability_codes = sorted({cap for caps in matrix.values() for cap in caps.keys()})
        user = self.env.user
        profile = self._build_profile(user)
        return {
            "contract_version": "v1",
            "profile": profile,
            "trace_id": trace_id or uuid4().hex,
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

    def _build_profile(self, user):
        profile = {
            "name": "portal.lifecycle_dashboard",
            "company_id": self.env.company.id,
            "lang": self.env.lang,
            "tz": user.tz or self.env.context.get("tz"),
        }
        if self._allow_sensitive_profile(user):
            profile.update(
                {
                    "db": self.env.cr.dbname,
                    "user_id": user.id,
                    "login": user.login,
                    "role": self._resolve_role(user),
                }
            )
        return profile

    def _allow_sensitive_profile(self, user):
        value = self.env["ir.config_parameter"].sudo().get_param("sc.portal.debug_profile", "0")
        enabled = str(value).strip().lower() in {"1", "true", "yes", "on"}
        return enabled and user.has_group("smart_construction_core.group_sc_internal_user")

    def _resolve_role(self, user):
        if user.has_group("base.group_system"):
            return "admin"
        if user.has_group("smart_construction_core.group_sc_cap_project_manager"):
            return "pm"
        return "user"
