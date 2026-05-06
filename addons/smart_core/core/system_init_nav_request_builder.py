# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo.addons.smart_core.core.source_authority import build_source_authority_contract


class SystemInitNavRequestBuilder:
    SOURCE_KIND = "system_init_nav_request_projection"
    SOURCE_AUTHORITIES = ("system_init_params", "scene_channel")
    NO_BUSINESS_FACT_AUTHORITY = True

    @classmethod
    def source_authority_contract(cls) -> dict:
        return build_source_authority_contract(
            kind=cls.SOURCE_KIND,
            authorities=cls.SOURCE_AUTHORITIES,
            no_business_fact_authority=cls.NO_BUSINESS_FACT_AUTHORITY,
            request_projection_only=True,
        )

    @staticmethod
    def build(params: dict, scene: str) -> dict:
        payload = {"subject": "nav", "scene": scene}
        if params.get("root_xmlid"):
            payload["root_xmlid"] = params.get("root_xmlid")
        if params.get("root_menu_id"):
            payload["root_menu_id"] = params.get("root_menu_id")
        return payload
