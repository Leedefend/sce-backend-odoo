# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Dict, Iterable, List, Tuple

from odoo.addons.smart_core.core.handler_registry import HANDLER_REGISTRY
from odoo.addons.smart_core.identity.identity_resolver import IdentityResolver


class IntentSurfaceBuilder:
    def _to_group_xmlid(self, env, group_ref) -> str | None:
        if not group_ref:
            return None
        if isinstance(group_ref, str):
            return group_ref if "." in group_ref else None
        if isinstance(group_ref, int):
            imd = env["ir.model.data"].sudo().search([
                ("model", "=", "res.groups"),
                ("res_id", "=", group_ref),
            ], limit=1)
            return f"{imd.module}.{imd.name}" if imd and imd.module and imd.name else None
        if getattr(group_ref, "_name", None) == "res.groups":
            imd = env["ir.model.data"].sudo().search([
                ("model", "=", "res.groups"),
                ("res_id", "=", group_ref.id),
            ], limit=1)
            return f"{imd.module}.{imd.name}" if imd and imd.module and imd.name else None
        return None

    def _normalize_required_groups(self, env, required: Iterable) -> List[str]:
        if not required:
            return []
        out = []
        for item in required:
            xmlid = self._to_group_xmlid(env, item)
            if xmlid:
                out.append(xmlid)
        return out

    def _has_required_groups(self, user_xmlids: set, required_xmlids: Iterable[str]) -> bool:
        req = set(required_xmlids or [])
        return (not req) or req.issubset(user_xmlids)

    def collect(self, env, user) -> Tuple[List[str], Dict[str, dict]]:
        user_xmlids = IdentityResolver().user_group_xmlids(user)
        intents: List[str] = []
        meta: Dict[str, dict] = {}

        for name, cls in HANDLER_REGISTRY.items():
            primary = getattr(cls, "INTENT_TYPE", None) or name
            version = getattr(cls, "VERSION", None)
            required = self._normalize_required_groups(env, getattr(cls, "REQUIRED_GROUPS", []) or [])
            enabled = getattr(cls, "IS_ENABLED", True)
            aliases = []
            try:
                aliases = list(getattr(cls, "ALIASES") or [])
            except Exception:
                aliases = []

            if not enabled:
                continue
            if not self._has_required_groups(user_xmlids, required):
                continue
            if primary in intents:
                if primary in meta:
                    meta[primary].setdefault("aliases", [])
                    meta[primary]["aliases"] = sorted(set(meta[primary]["aliases"] + aliases))
                continue

            intents.append(primary)
            meta[primary] = {
                "version": version,
                "aliases": aliases,
                "required_groups_xmlids": required,
            }

        intents_sorted = sorted(intents)
        meta_sorted = {k: meta[k] for k in intents_sorted}
        return intents_sorted, meta_sorted
