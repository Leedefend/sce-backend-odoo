# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Dict, List

ROLE_SURFACE_MAP = {
    "owner": {
        "label": "Owner",
        "landing_scene_candidates": ["portal.dashboard", "workspace.home"],
        "menu_xmlids": [],
    },
    "pm": {
        "label": "Project Manager",
        "landing_scene_candidates": ["portal.dashboard", "workspace.home"],
        "menu_xmlids": [],
        "menu_blocklist_xmlids": [],
    },
    "finance": {
        "label": "Finance",
        "landing_scene_candidates": ["portal.dashboard", "workspace.home"],
        "menu_xmlids": [],
    },
    "executive": {
        "label": "Executive",
        "landing_scene_candidates": ["portal.dashboard", "workspace.home"],
        "menu_xmlids": [],
    },
}

ROLE_GROUPS_EXPLICIT = {
    "executive": {
        "smart_construction_custom.group_sc_role_executive",
        "smart_construction_core.group_sc_super_admin",
        "smart_construction_core.group_sc_cap_config_admin",
        "base.group_system",
    },
    "pm": {
        "smart_construction_custom.group_sc_role_pm",
        "smart_construction_custom.group_sc_role_project_manager",
        "smart_construction_custom.group_sc_role_project_user",
        "smart_construction_core.group_sc_role_project_manager",
    },
    "finance": {
        "smart_construction_custom.group_sc_role_finance",
        "smart_construction_custom.group_sc_role_payment_manager",
        "smart_construction_custom.group_sc_role_payment_user",
        "smart_construction_custom.group_sc_role_payment_read",
        "smart_construction_core.group_sc_role_finance_manager",
        "smart_construction_core.group_sc_role_finance_user",
    },
}

ROLE_GROUPS_CAPABILITY_FALLBACK = {
    "pm": {
        "smart_construction_core.group_sc_cap_project_manager",
        "smart_construction_core.group_sc_cap_project_user",
    },
    "finance": {
        "smart_construction_core.group_sc_cap_finance_user",
        "smart_construction_core.group_sc_cap_finance_manager",
    },
}

ROLE_PRECEDENCE = ("executive", "pm", "finance")


class IdentityResolver:
    def user_group_xmlids(self, user) -> set:
        ext_map = user.groups_id.sudo().get_external_id()
        return {xml for xml in ext_map.values() if xml}

    def resolve_role_code_with_evidence(self, user_xmlids: set) -> tuple[str, dict]:
        explicit_hits: Dict[str, List[str]] = {}
        for role in ROLE_PRECEDENCE:
            hits = sorted((ROLE_GROUPS_EXPLICIT.get(role) or set()) & user_xmlids)
            if hits:
                explicit_hits[role] = hits
        for role in ROLE_PRECEDENCE:
            hits = explicit_hits.get(role) or []
            if hits:
                evidence = {
                    "source": "explicit",
                    "matched_groups": hits,
                }
                if len(explicit_hits) > 1:
                    evidence["candidate_roles"] = sorted(explicit_hits.keys())
                return role, evidence

        capability_hits: Dict[str, List[str]] = {}
        for role in ("pm", "finance"):
            hits = sorted((ROLE_GROUPS_CAPABILITY_FALLBACK.get(role) or set()) & user_xmlids)
            if hits:
                capability_hits[role] = hits
        for role in ("pm", "finance"):
            hits = capability_hits.get(role) or []
            if hits:
                evidence = {
                    "source": "capability_fallback",
                    "matched_groups": hits,
                }
                if len(capability_hits) > 1:
                    evidence["candidate_roles"] = sorted(capability_hits.keys())
                return role, evidence

        return "owner", {"source": "default_owner", "matched_groups": []}

    def resolve_role_code(self, user_xmlids: set) -> str:
        role_code, _ = self.resolve_role_code_with_evidence(user_xmlids)
        return role_code

    def _pick_landing_scene(self, scene_candidates: List[str], scene_keys: set) -> str:
        for candidate in scene_candidates:
            if candidate in scene_keys:
                return candidate
        if "portal.dashboard" in scene_keys:
            return "portal.dashboard"
        if "workspace.home" in scene_keys:
            return "workspace.home"
        return "portal.dashboard"

    def _merge_role_meta(self, role_code: str, role_meta: dict, role_surface_overrides: dict | None) -> dict:
        merged = dict(role_meta or {})
        if not isinstance(role_surface_overrides, dict):
            return merged
        role_override = role_surface_overrides.get(role_code)
        if not isinstance(role_override, dict):
            return merged
        for field in ("landing_scene_candidates", "menu_xmlids", "menu_blocklist_xmlids"):
            value = role_override.get(field)
            if isinstance(value, list):
                merged[field] = value
        label = role_override.get("label")
        if isinstance(label, str) and label.strip():
            merged["label"] = label.strip()
        return merged

    def _walk_nav_nodes(self, nodes):
        for node in nodes or []:
            if isinstance(node, dict):
                yield node
                children = node.get("children")
                if isinstance(children, list):
                    for child in self._walk_nav_nodes(children):
                        yield child

    def _index_nav_by_xmlid(self, nodes) -> Dict[str, dict]:
        indexed = {}
        for node in self._walk_nav_nodes(nodes):
            xmlid = node.get("xmlid") or (node.get("meta") or {}).get("menu_xmlid")
            if xmlid and xmlid not in indexed:
                indexed[xmlid] = node
        return indexed

    def build_role_surface(
        self,
        user_xmlids: set,
        nav_tree: list,
        scene_keys: set,
        role_surface_overrides: dict | None = None,
    ) -> dict:
        role_code, role_evidence = self.resolve_role_code_with_evidence(user_xmlids)
        role_meta = ROLE_SURFACE_MAP.get(role_code) or ROLE_SURFACE_MAP["owner"]
        role_meta = self._merge_role_meta(role_code, role_meta, role_surface_overrides)
        scene_candidates = list(role_meta.get("landing_scene_candidates") or [])
        menu_candidates = list(role_meta.get("menu_xmlids") or [])
        menu_blocklist_xmlids = list(role_meta.get("menu_blocklist_xmlids") or [])
        landing_scene_key = self._pick_landing_scene(scene_candidates, scene_keys)
        nav_index = self._index_nav_by_xmlid(nav_tree)
        landing_menu_xmlid = ""
        landing_menu_id = None
        for xmlid in menu_candidates:
            node = nav_index.get(xmlid)
            if not node:
                continue
            landing_menu_xmlid = xmlid
            landing_menu_id = node.get("menu_id") or node.get("id")
            break
        return {
            "role_code": role_code,
            "role_label": role_meta.get("label") or role_code,
            "role_evidence": role_evidence,
            "landing_scene_key": landing_scene_key,
            "landing_menu_xmlid": landing_menu_xmlid,
            "landing_menu_id": landing_menu_id,
            "landing_path": f"/s/{landing_scene_key}",
            "scene_candidates": scene_candidates,
            "menu_xmlids": menu_candidates,
            "menu_blocklist_xmlids": menu_blocklist_xmlids,
        }

    def build_role_surface_map_payload(self) -> Dict[str, dict]:
        payload = {}
        for role_code, role_meta in ROLE_SURFACE_MAP.items():
            payload[role_code] = {
                "role_code": role_code,
                "role_label": role_meta.get("label") or role_code,
                "scene_candidates": list(role_meta.get("landing_scene_candidates") or []),
                "menu_xmlids": list(role_meta.get("menu_xmlids") or []),
                "menu_blocklist_xmlids": list(role_meta.get("menu_blocklist_xmlids") or []),
            }
        return payload

    def _node_xmlid(self, node: dict) -> str:
        if not isinstance(node, dict):
            return ""
        xmlid = node.get("xmlid")
        if isinstance(xmlid, str) and xmlid:
            return xmlid
        meta = node.get("meta") or {}
        meta_xmlid = meta.get("menu_xmlid")
        if isinstance(meta_xmlid, str) and meta_xmlid:
            return meta_xmlid
        return ""

    def filter_nav_for_role_surface(self, nav_tree: list, role_surface: dict) -> list:
        if not isinstance(nav_tree, list) or not isinstance(role_surface, dict):
            return nav_tree if isinstance(nav_tree, list) else []

        allow_xmlids = {x for x in (role_surface.get("menu_xmlids") or []) if isinstance(x, str) and x}
        block_xmlids = {x for x in (role_surface.get("menu_blocklist_xmlids") or []) if isinstance(x, str) and x}

        def walk(node: dict, in_allowed_branch: bool):
            if not isinstance(node, dict):
                return None, False
            xmlid = self._node_xmlid(node)
            if xmlid and xmlid in block_xmlids:
                return None, False

            current_allowed = in_allowed_branch or (bool(xmlid) and xmlid in allow_xmlids)
            has_explicit_allow = bool(xmlid) and xmlid in allow_xmlids
            kept_children = []
            has_allowed_descendant = False
            for child in node.get("children") or []:
                kept, child_allowed = walk(child, current_allowed)
                if kept:
                    kept_children.append(kept)
                has_allowed_descendant = has_allowed_descendant or child_allowed

            keep_node = True
            if allow_xmlids:
                keep_node = current_allowed or has_allowed_descendant
            if not keep_node:
                return None, has_allowed_descendant or has_explicit_allow

            out = dict(node)
            out["children"] = kept_children
            return out, (has_explicit_allow or has_allowed_descendant or current_allowed)

        filtered = []
        for node in nav_tree:
            kept, _ = walk(node, False)
            if kept:
                filtered.append(kept)
        return filtered

    def infer_default_route_from_nav(self, nav_tree: list) -> dict:
        if not isinstance(nav_tree, list):
            return {"menu_id": None, "scene_key": None, "route": "/workbench", "reason": "menu_fallback"}

        def dfs(nodes):
            for node in nodes or []:
                if not isinstance(node, dict):
                    continue
                children = node.get("children") or []
                if children:
                    found = dfs(children)
                    if found:
                        return found
                menu_id = node.get("menu_id") or node.get("id")
                if menu_id:
                    scene_key = ""
                    if isinstance(node.get("meta"), dict):
                        scene_key = str((node.get("meta") or {}).get("scene_key") or "").strip()
                    if not scene_key:
                        scene_key = str(node.get("scene_key") or "").strip()
                    return {
                        "menu_id": menu_id,
                        "scene_key": scene_key or None,
                        "route": f"/workbench?scene={scene_key}" if scene_key else "/workbench",
                        "reason": "menu_fallback",
                    }
            return None

        default_route = dfs(nav_tree)
        if isinstance(default_route, dict):
            return default_route
        return {"menu_id": default_route, "scene_key": None, "route": "/workbench", "reason": "menu_fallback"}

    def resolve(self, env):
        user = env.user
        groups = self.user_group_xmlids(user)
        role_code, role_evidence = self.resolve_role_code_with_evidence(groups)
        return {
            "user_id": user.id,
            "groups_xmlids": sorted(groups),
            "role_code": role_code,
            "role_evidence": role_evidence,
        }
