# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo.addons.smart_core.core.delivery_capability_entry_defaults import (
    build_delivery_capability_entry,
)
from odoo.addons.smart_core.core.source_authority import build_source_authority_contract


class CapabilityService:
    SOURCE_KIND = "delivery_capability_projection"
    SOURCE_AUTHORITIES = ("delivery_product_policy_projection", "capability_startup_surface_projection")
    NO_BUSINESS_FACT_AUTHORITY = True

    @classmethod
    def source_authority_contract(cls) -> dict:
        return build_source_authority_contract(
            kind=cls.SOURCE_KIND,
            authorities=cls.SOURCE_AUTHORITIES,
            no_business_fact_authority=cls.NO_BUSINESS_FACT_AUTHORITY,
            runtime_carrier="delivery_engine_v1.capabilities",
        )

    def build_entries(self, *, policy: dict, capabilities: list[dict]) -> list[dict]:
        runtime_index = {}
        for item in capabilities or []:
            if not isinstance(item, dict):
                continue
            key = str(item.get("key") or "").strip()
            if key and key not in runtime_index:
                runtime_index[key] = item

        entries: list[dict] = []
        for row in policy.get("capabilities") or []:
            if not isinstance(row, dict):
                continue
            key = str(row.get("capability_key") or row.get("key") or "").strip()
            if not key:
                continue
            runtime = runtime_index.get(key) or {}
            entry = build_delivery_capability_entry(row, runtime)
            if entry:
                entry["source_authority"] = self.source_authority_contract()
                entries.append(entry)
        return entries
