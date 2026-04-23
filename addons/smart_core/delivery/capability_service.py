# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo.addons.smart_core.core.delivery_capability_entry_defaults import (
    build_delivery_capability_entry,
)


class CapabilityService:
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
            entries.append(build_delivery_capability_entry(row, runtime))
        return entries
