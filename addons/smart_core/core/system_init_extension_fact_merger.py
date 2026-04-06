# -*- coding: utf-8 -*-
from __future__ import annotations

import importlib
from typing import Any

from odoo.addons.smart_core.utils.extension_hooks import iter_extension_modules


def apply_extension_fact_contributions(
    data: dict[str, Any],
    env,
    user,
    context: dict[str, Any] | None = None,
) -> None:
    ext_facts = data.get("ext_facts")
    if not isinstance(ext_facts, dict):
        ext_facts = {}

    for module_name in iter_extension_modules(env):
        try:
            module = importlib.import_module(f"odoo.addons.{module_name}")
        except Exception:
            continue

        hook = getattr(module, "get_system_init_fact_contributions", None)
        if not callable(hook):
            continue

        try:
            payload = hook(env, user, context=context or {})
        except Exception:
            continue

        if isinstance(payload, dict):
            module_key = str(payload.get("module") or module_name or "").strip()
            facts = payload.get("facts")
            if module_key and isinstance(facts, dict):
                module_facts = ext_facts.get(module_key)
                if not isinstance(module_facts, dict):
                    module_facts = {}
                module_facts.update(facts)
                ext_facts[module_key] = module_facts
            continue

        if isinstance(payload, list):
            for row in payload:
                if not isinstance(row, dict):
                    continue
                module_key = str(row.get("module") or module_name or "").strip()
                facts = row.get("facts")
                if not module_key or not isinstance(facts, dict):
                    continue
                module_facts = ext_facts.get(module_key)
                if not isinstance(module_facts, dict):
                    module_facts = {}
                module_facts.update(facts)
                ext_facts[module_key] = module_facts

    if ext_facts:
        data["ext_facts"] = ext_facts


def merge_extension_facts(data: dict[str, Any], *, include_workspace_collections: bool = True) -> None:
    ext_facts = data.get("ext_facts")
    if not isinstance(ext_facts, dict):
        return

    for ext_module, module_facts in ext_facts.items():
        if not isinstance(module_facts, dict):
            continue

        for key in ("entitlements", "usage"):
            if key in module_facts and key not in data:
                data[key] = module_facts.get(key)

        if include_workspace_collections:
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
