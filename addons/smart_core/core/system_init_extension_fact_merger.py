# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any


def merge_extension_facts(data: dict[str, Any]) -> None:
    ext_facts = data.get("ext_facts")
    if not isinstance(ext_facts, dict):
        return

    for ext_module, module_facts in ext_facts.items():
        if not isinstance(module_facts, dict):
            continue

        for key in ("entitlements", "usage"):
            if key in module_facts and key not in data:
                data[key] = module_facts.get(key)

        workspace_collections = module_facts.get("workspace_collections")
        if isinstance(workspace_collections, dict):
            for key in ("task_items", "payment_requests", "risk_actions", "project_actions"):
                rows = workspace_collections.get(key)
                if key not in data and isinstance(rows, list):
                    data[key] = rows

        provider_payload = module_facts.get("role_surface_override_provider")
        if isinstance(provider_payload, dict):
            provider_key = str(provider_payload.get("key") or "").strip() or str(ext_module or "").strip()
            if not provider_key:
                continue
            providers = data.get("role_surface_override_providers")
            if not isinstance(providers, dict):
                providers = {}
            merged = dict(provider_payload)
            merged.pop("key", None)
            providers[provider_key] = merged
            data["role_surface_override_providers"] = providers
