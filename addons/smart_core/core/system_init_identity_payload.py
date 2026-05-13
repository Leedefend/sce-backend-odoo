# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo.addons.smart_core.core.source_authority import build_source_authority_contract
from odoo.addons.smart_core.security.platform_admin import user_is_platform_admin


class SystemInitIdentityPayload:
    SOURCE_KIND = "system_init_identity_payload_projection"
    SOURCE_AUTHORITIES = ("res.users", "res.company", "res.groups")
    NO_BUSINESS_FACT_AUTHORITY = True

    @classmethod
    def source_authority_contract(cls) -> dict:
        return build_source_authority_contract(
            kind=cls.SOURCE_KIND,
            authorities=cls.SOURCE_AUTHORITIES,
            no_business_fact_authority=cls.NO_BUSINESS_FACT_AUTHORITY,
            identity_surface_only=True,
        )

    @staticmethod
    def build(user, user_groups_xmlids: list) -> dict:
        company = user.company_id if user.company_id else None
        company_id = company.id if company else None
        company_name = (company.name or "").strip() if company else ""
        return {
            "id": user.id,
            "name": user.name,
            "groups_xmlids": list(user_groups_xmlids),
            "is_platform_admin": user_is_platform_admin(user),
            "lang": user.lang,
            "tz": user.tz,
            "company_id": company_id,
            "company_name": company_name,
            "company": {
                "id": company_id,
                "name": company_name,
                "display_name": company_name,
            } if company_id else None,
        }
