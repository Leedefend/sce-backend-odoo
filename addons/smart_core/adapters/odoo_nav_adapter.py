# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Dict

from odoo.addons.smart_core.utils.extension_hooks import call_extension_hook_first


class OdooNavAdapter:
    MENU_SCENE_MAP = {}

    ACTION_XMLID_SCENE_MAP = {}

    MODEL_VIEW_SCENE_MAP = {}

    def __init__(self):
        self.menu_scene_map = dict(self.MENU_SCENE_MAP)
        self.action_xmlid_scene_map = dict(self.ACTION_XMLID_SCENE_MAP)
        self.model_view_scene_map = dict(self.MODEL_VIEW_SCENE_MAP)
        self._extension_loaded = False

    def _load_extension_scene_maps(self, env):
        if self._extension_loaded:
            return
        self._extension_loaded = True
        payload = call_extension_hook_first(env, "smart_core_nav_scene_maps", env)
        if not isinstance(payload, dict):
            return
        menu_scene_map = payload.get("menu_scene_map")
        if isinstance(menu_scene_map, dict):
            self.menu_scene_map.update({str(k): str(v) for k, v in menu_scene_map.items() if str(k).strip() and str(v).strip()})
        action_scene_map = payload.get("action_xmlid_scene_map")
        if isinstance(action_scene_map, dict):
            self.action_xmlid_scene_map.update(
                {str(k): str(v) for k, v in action_scene_map.items() if str(k).strip() and str(v).strip()}
            )
        model_view_scene_map = payload.get("model_view_scene_map")
        if isinstance(model_view_scene_map, dict):
            normalized = {}
            for key, value in model_view_scene_map.items():
                if not (isinstance(key, (list, tuple)) and len(key) == 2):
                    continue
                model_name = str(key[0] or "").strip()
                view_mode = str(key[1] or "").strip()
                scene_key = str(value or "").strip()
                if not model_name or not view_mode or not scene_key:
                    continue
                normalized[(model_name, view_mode)] = scene_key
            self.model_view_scene_map.update(normalized)

    def enrich(self, env, nav_tree):
        self._load_extension_scene_maps(env)
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
        action_id_map = self._resolve_action_ids(env, self.action_xmlid_scene_map)

        for node in nodes or []:
            meta = node.get("meta") or {}
            menu_xmlid = meta.get("menu_xmlid") or node.get("xmlid")
            if menu_xmlid:
                node["xmlid"] = menu_xmlid
            scene_key = None
            if menu_xmlid and menu_xmlid in self.menu_scene_map:
                scene_key = self.menu_scene_map[menu_xmlid]
            if not scene_key:
                action_id = meta.get("action_id")
                if isinstance(action_id, str) and action_id.isdigit():
                    action_id = int(action_id)
                if action_id in action_id_map:
                    scene_key = action_id_map[action_id]
            if not scene_key:
                action_xmlid = meta.get("action_xmlid")
                if action_xmlid and action_xmlid in self.action_xmlid_scene_map:
                    scene_key = self.action_xmlid_scene_map[action_xmlid]
                    meta["scene_key_inferred_from"] = "action_xmlid"
            if not scene_key:
                model = meta.get("model")
                view_mode = meta.get("view_mode") or meta.get("view_type")
                if not view_mode:
                    view_modes = meta.get("view_modes")
                    if isinstance(view_modes, list) and view_modes:
                        view_mode = view_modes[0]
                key = (model, self._normalize_view_mode(view_mode)) if model else None
                if key in self.model_view_scene_map:
                    scene_key = self.model_view_scene_map[key]
            if scene_key:
                node["scene_key"] = scene_key
                meta["scene_key"] = scene_key
                node["meta"] = meta
            if node.get("children"):
                self._apply_scene_keys(env, node["children"])
