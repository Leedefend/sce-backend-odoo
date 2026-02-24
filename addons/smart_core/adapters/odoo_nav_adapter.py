# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Dict


class OdooNavAdapter:
    MENU_SCENE_MAP = {
        "smart_construction_demo.menu_sc_project_list_showcase": "projects.list",
        "smart_construction_core.menu_sc_project_initiation": "projects.intake",
        "smart_construction_core.menu_sc_project_project": "projects.ledger",
        "smart_construction_core.menu_sc_root": "projects.list",
        "smart_construction_core.menu_sc_project_dashboard": "projects.dashboard",
        "smart_construction_demo.menu_sc_project_dashboard_showcase": "projects.dashboard_showcase",
        "smart_construction_core.menu_sc_dictionary": "data.dictionary",
        "smart_construction_core.menu_payment_request": "finance.payment_requests",
        "smart_construction_portal.menu_sc_portal_lifecycle": "portal.lifecycle",
        "smart_construction_portal.menu_sc_portal_capability_matrix": "portal.capability_matrix",
        "smart_construction_portal.menu_sc_portal_dashboard": "portal.dashboard",
    }

    ACTION_XMLID_SCENE_MAP = {
        "smart_construction_demo.action_sc_project_list_showcase": "projects.list",
        "smart_construction_core.action_project_initiation": "projects.intake",
        "smart_construction_core.action_sc_project_kanban_lifecycle": "projects.ledger",
        "smart_construction_core.action_sc_project_list": "projects.list",
        "smart_construction_core.action_project_dashboard": "projects.dashboard",
        "smart_construction_demo.action_project_dashboard_showcase": "projects.dashboard_showcase",
        "smart_construction_core.action_project_dictionary": "data.dictionary",
        "smart_construction_core.action_payment_request": "finance.payment_requests",
        "smart_construction_core.action_payment_request_my": "finance.payment_requests",
        "smart_construction_portal.action_sc_portal_lifecycle": "portal.lifecycle",
        "smart_construction_portal.action_sc_portal_capability_matrix": "portal.capability_matrix",
        "smart_construction_portal.action_sc_portal_dashboard": "portal.dashboard",
    }

    MODEL_VIEW_SCENE_MAP = {
        ("project.project", "list"): "projects.list",
        ("project.project", "form"): "projects.intake",
        ("payment.request", "list"): "finance.payment_requests",
        ("payment.request", "form"): "finance.payment_requests",
    }

    def enrich(self, env, nav_tree):
        self._normalize_nav_groups(env, nav_tree)
        self._apply_scene_keys(env, nav_tree)
        return nav_tree

    def _to_xmlid_list(self, env, maybe_ids_or_xmlids):
        if not maybe_ids_or_xmlids:
            return []
        out = []
        int_ids = []
        for group_value in maybe_ids_or_xmlids:
            if isinstance(group_value, str) and "." in group_value:
                out.append(group_value)
            elif isinstance(group_value, int):
                int_ids.append(group_value)
        if int_ids:
            imds = env["ir.model.data"].sudo().search([
                ("model", "=", "res.groups"),
                ("res_id", "in", int_ids),
            ])
            id2xml = {imd.res_id: f"{imd.module}.{imd.name}" for imd in imds if imd.module and imd.name}
            for gid in int_ids:
                if gid in id2xml:
                    out.append(id2xml[gid])
        return sorted(set(out))

    def _normalize_nav_groups(self, env, nodes):
        for node in nodes or []:
            meta = node.get("meta") or {}
            if "groups_xmlids" in meta and meta["groups_xmlids"]:
                meta["groups_xmlids"] = self._to_xmlid_list(env, meta["groups_xmlids"])
                node["meta"] = meta
            if node.get("children"):
                self._normalize_nav_groups(env, node["children"])

    def _resolve_action_ids(self, env, action_xmlids: Dict[str, str]) -> Dict[int, str]:
        resolved = {}
        for xmlid, scene_key in action_xmlids.items():
            try:
                rec = env.ref(xmlid, raise_if_not_found=False)
                if rec and rec.id:
                    resolved[rec.id] = scene_key
            except Exception:
                continue
        return resolved

    def _normalize_view_mode(self, raw: str | None) -> str | None:
        if not raw:
            return None
        value = str(raw).strip().lower()
        if value in {"tree", "list", "kanban"}:
            return "list"
        if value in {"form"}:
            return "form"
        return value

    def _apply_scene_keys(self, env, nodes):
        action_id_map = self._resolve_action_ids(env, self.ACTION_XMLID_SCENE_MAP)

        for node in nodes or []:
            meta = node.get("meta") or {}
            menu_xmlid = meta.get("menu_xmlid") or node.get("xmlid")
            if menu_xmlid:
                node["xmlid"] = menu_xmlid
            scene_key = None
            if menu_xmlid and menu_xmlid in self.MENU_SCENE_MAP:
                scene_key = self.MENU_SCENE_MAP[menu_xmlid]
            if not scene_key:
                action_id = meta.get("action_id")
                if isinstance(action_id, str) and action_id.isdigit():
                    action_id = int(action_id)
                if action_id in action_id_map:
                    scene_key = action_id_map[action_id]
            if not scene_key:
                action_xmlid = meta.get("action_xmlid")
                if action_xmlid and action_xmlid in self.ACTION_XMLID_SCENE_MAP:
                    scene_key = self.ACTION_XMLID_SCENE_MAP[action_xmlid]
                    meta["scene_key_inferred_from"] = "action_xmlid"
            if not scene_key:
                model = meta.get("model")
                view_mode = meta.get("view_mode") or meta.get("view_type")
                if not view_mode:
                    view_modes = meta.get("view_modes")
                    if isinstance(view_modes, list) and view_modes:
                        view_mode = view_modes[0]
                key = (model, self._normalize_view_mode(view_mode)) if model else None
                if key in self.MODEL_VIEW_SCENE_MAP:
                    scene_key = self.MODEL_VIEW_SCENE_MAP[key]
            if scene_key:
                node["scene_key"] = scene_key
                meta["scene_key"] = scene_key
                node["meta"] = meta
            if node.get("children"):
                self._apply_scene_keys(env, node["children"])
