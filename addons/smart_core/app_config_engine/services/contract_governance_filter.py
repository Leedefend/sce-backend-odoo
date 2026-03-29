# -*- coding: utf-8 -*-
"""View-runtime filter service.

This service performs view-level runtime filtering on already parsed/governed
view contracts. It is distinct from delivery-surface governance in
``utils.contract_governance`` and must not parse XML, assemble page contracts,
or decide delivery surfaces.
"""

from __future__ import annotations

import json


class ContractGovernanceFilterService:
    """Apply view-level runtime filtering to already parsed contracts."""

    def __init__(self, owner):
        self.owner = owner

    def apply_runtime_filter(self, parsed, model_name, check_model_acl=False):
        """Backward-compatible alias for view-level runtime filtering."""
        return self.apply_view_runtime_filter(parsed, model_name, check_model_acl=check_model_acl)

    def apply_view_runtime_filter(self, parsed, model_name, check_model_acl=False):
        user_groups = set(self.owner.env.user.groups_id.ids)

        # Contract-level group guard.
        if self.owner.groups_id and not (user_groups & set(self.owner.groups_id.ids)):
            return {
                "modifiers": {},
                "toolbar": {"header": [], "sidebar": [], "footer": []},
                "search": {"filters": [], "group_by": [], "facets": {"enabled": True}},
            }

        vp = json.loads(json.dumps(parsed or {}, ensure_ascii=False))

        def _resolve_groups_xmlids(xmlids):
            ids = set()
            for xid in (xmlids or []):
                try:
                    rec = self.owner.env.ref(xid, raise_if_not_found=False)
                    if rec and rec._name == "res.groups":
                        ids.add(rec.id)
                except Exception:
                    continue
            return ids

        def _keep_item(item):
            gids = set(item.get("groups") or [])
            gids |= _resolve_groups_xmlids(item.get("groups_xmlids"))
            return (not gids) or bool(gids & user_groups)

        def _filter_list(items):
            return [x for x in (items or []) if _keep_item(x)]

        tb = vp.get("toolbar") or {}
        tb["header"] = _filter_list(tb.get("header"))
        tb["sidebar"] = _filter_list(tb.get("sidebar"))
        tb["footer"] = _filter_list(tb.get("footer"))
        vp["toolbar"] = tb

        if "row_actions" in vp:
            vp["row_actions"] = _filter_list(vp.get("row_actions"))

        if isinstance(vp.get("kanban"), dict) and "quick_actions" in vp["kanban"]:
            vp["kanban"]["quick_actions"] = _filter_list(vp["kanban"].get("quick_actions"))

        def _filter_layout(nodes):
            kept = []
            for node in (nodes or []):
                if not isinstance(node, dict):
                    continue
                if not _keep_item(node):
                    continue
                if node.get("children"):
                    node["children"] = _filter_layout(node["children"])
                kept.append(node)
            return kept

        if isinstance(vp.get("layout"), list):
            vp["layout"] = _filter_layout(vp["layout"])

        fmods = vp.get("field_modifiers") or {}
        clean = {}
        for fname, mods in fmods.items():
            if not isinstance(mods, dict):
                continue
            gids = set(mods.get("groups") or [])
            gids |= _resolve_groups_xmlids(mods.get("groups_xmlids"))
            if gids and not (gids & user_groups):
                continue
            clean[fname] = mods
        vp["field_modifiers"] = clean

        if check_model_acl and model_name in self.owner.env:
            try:
                ok = bool(self.owner.env[model_name].check_access_rights("read", raise_exception=False))
                if not ok:
                    return {
                        "modifiers": {},
                        "toolbar": {"header": [], "sidebar": [], "footer": []},
                        "search": {"filters": [], "group_by": [], "facets": {"enabled": True}},
                    }
            except Exception:
                pass
        return vp
