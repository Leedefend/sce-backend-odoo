# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Dict, Iterable, List, Tuple

from odoo.addons.smart_core.core.handler_registry import HANDLER_REGISTRY
from odoo.addons.smart_core.identity.identity_resolver import IdentityResolver


class IntentSurfaceBuilder:
    @staticmethod
    def _safe_aliases(handler_cls) -> list[str]:
        try:
            raw = list(getattr(handler_cls, "ALIASES") or [])
        except Exception:
            raw = []
        aliases: list[str] = []
        for item in raw:
            alias = str(item or "").strip()
            if alias:
                aliases.append(alias)
        return aliases

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
        user_xmlids = IdentityResolver(env).user_group_xmlids(user)
        canonical_rows: dict[str, dict] = {}
        alias_rows: dict[str, set[str]] = {}

        for name, cls in HANDLER_REGISTRY.items():
            primary = str(getattr(cls, "INTENT_TYPE", None) or name).strip()
            if not primary:
                continue
            if primary not in canonical_rows:
                canonical_rows[primary] = {
                    "version": getattr(cls, "VERSION", None),
                    "required_groups_xmlids": self._normalize_required_groups(env, getattr(cls, "REQUIRED_GROUPS", []) or []),
                    "enabled": bool(getattr(cls, "IS_ENABLED", True)),
                }
            alias_set = alias_rows.setdefault(primary, set())
            for alias in self._safe_aliases(cls):
                if alias != primary:
                    alias_set.add(alias)
            if name != primary:
                alias_set.add(str(name))

        intents: List[str] = []
        meta: Dict[str, dict] = {}
        for primary, row in canonical_rows.items():
            if not bool(row.get("enabled")):
                continue
            required = list(row.get("required_groups_xmlids") or [])
            if not self._has_required_groups(user_xmlids, required):
                continue
            intents.append(primary)
            meta[primary] = {
                "version": row.get("version"),
                "aliases": sorted(alias_rows.get(primary) or set()),
                "required_groups_xmlids": required,
                "status": "canonical",
                "canonical": primary,
            }

        intents_sorted = sorted(set(intents))
        meta_sorted = {k: meta[k] for k in intents_sorted if k in meta}
        return intents_sorted, meta_sorted

    def collect_catalog(self, env, user) -> list[dict]:
        intents, intents_meta = self.collect(env, user)
        rows: list[dict] = []
        for canonical in intents:
            row = intents_meta.get(canonical) if isinstance(intents_meta.get(canonical), dict) else {}
            rows.append({
                "name": canonical,
                "status": "canonical",
                "canonical": canonical,
                "version": row.get("version"),
                "required_groups_xmlids": row.get("required_groups_xmlids") or [],
            })
            for alias in row.get("aliases") or []:
                rows.append({
                    "name": str(alias),
                    "status": "alias",
                    "canonical": canonical,
                    "version": row.get("version"),
                    "required_groups_xmlids": row.get("required_groups_xmlids") or [],
                })
        rows.sort(key=lambda item: (str(item.get("name") or ""), str(item.get("status") or "")))
        return rows
