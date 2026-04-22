# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Dict, List

from odoo.addons.smart_core.utils.extension_hooks import call_extension_hook_first

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
    "executive": set(),
    "pm": set(),
    "finance": set(),
}

ROLE_GROUPS_CAPABILITY_FALLBACK = {
    "pm": set(),
    "finance": set(),
}

ROLE_PRECEDENCE = ("executive", "pm", "finance")


class IdentityResolver:
    def __init__(self, env=None):
        self._env = env
        self._role_surface_map = ROLE_SURFACE_MAP
        self._role_groups_explicit = ROLE_GROUPS_EXPLICIT
        self._role_groups_capability_fallback = ROLE_GROUPS_CAPABILITY_FALLBACK
        self._role_precedence = ROLE_PRECEDENCE
        profile = self._load_extension_identity_profile()
        if not isinstance(profile, dict):
            return
        role_surface_map = profile.get("role_surface_map")
        if isinstance(role_surface_map, dict) and role_surface_map:
            self._role_surface_map = role_surface_map
        role_groups_explicit = profile.get("role_groups_explicit")
        if isinstance(role_groups_explicit, dict):
            self._role_groups_explicit = {
                str(role): {str(group) for group in (groups or []) if str(group).strip()}
                for role, groups in role_groups_explicit.items()
                if str(role).strip()
            }
        role_groups_capability_fallback = profile.get("role_groups_capability_fallback")
        if isinstance(role_groups_capability_fallback, dict):
            self._role_groups_capability_fallback = {
                str(role): {str(group) for group in (groups or []) if str(group).strip()}
                for role, groups in role_groups_capability_fallback.items()
                if str(role).strip()
            }
        role_precedence = profile.get("role_precedence")
        if isinstance(role_precedence, (tuple, list)) and role_precedence:
            normalized = tuple(str(item).strip() for item in role_precedence if str(item).strip())
            if normalized:
                self._role_precedence = normalized

    def _load_extension_identity_profile(self):
        if self._env is None:
            return None
        return call_extension_hook_first(self._env, "smart_core_identity_profile", self._env)

    def user_group_xmlids(self, user) -> set:
        ext_map = user.groups_id.sudo().get_external_id()
        return {xml for xml in ext_map.values() if xml}

    def resolve_role_code_with_evidence(self, user_xmlids: set) -> tuple[str, dict]:
        explicit_hits: Dict[str, List[str]] = {}
        for role in self._role_precedence:
            hits = sorted((self._role_groups_explicit.get(role) or set()) & user_xmlids)
            if hits:
                explicit_hits[role] = hits
        for role in self._role_precedence:
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
            hits = sorted((self._role_groups_capability_fallback.get(role) or set()) & user_xmlids)
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

    def _extract_scene_key_from_route(self, route: str) -> str:
        normalized_route = str(route or "").strip()
        if not normalized_route.startswith("/s/"):
            return ""
        candidate = normalized_route.split("?", 1)[0].strip()
        return candidate.replace("/s/", "", 1).strip()

    def _collect_nav_scene_candidates(self, nodes, scene_keys: set) -> List[str]:
        available_scene_keys = {str(item or "").strip() for item in (scene_keys or set()) if str(item or "").strip()}
        collected: List[str] = []
        seen = set()

        def _push(scene_key: str):
            normalized = str(scene_key or "").strip()
            if not normalized or normalized in seen:
                return
            if available_scene_keys and normalized not in available_scene_keys:
                return
            seen.add(normalized)
            collected.append(normalized)

        for node in self._walk_nav_nodes(nodes):
            meta = node.get("meta") if isinstance(node.get("meta"), dict) else {}
            target = node.get("target") if isinstance(node.get("target"), dict) else {}
            entry_target = node.get("entry_target") if isinstance(node.get("entry_target"), dict) else {}
            for candidate in (
                meta.get("scene_key"),
                target.get("scene_key"),
                entry_target.get("scene_key"),
                self._extract_scene_key_from_route(meta.get("route") or ""),
                self._extract_scene_key_from_route(target.get("route") or ""),
                self._extract_scene_key_from_route(entry_target.get("route") or ""),
            ):
                _push(candidate)
        return collected

    def _merge_scene_candidates(self, base_candidates: List[str], nav_tree: list, scene_keys: set) -> List[str]:
        merged: List[str] = []
        seen = set()

        def _push(scene_key: str):
            normalized = str(scene_key or "").strip()
            if not normalized or normalized in seen:
                return
            seen.add(normalized)
            merged.append(normalized)

        available_scene_keys = sorted({str(item or "").strip() for item in (scene_keys or set()) if str(item or "").strip()})
        for scene_key in base_candidates or []:
            _push(scene_key)
        for scene_key in self._collect_nav_scene_candidates(nav_tree, scene_keys):
            _push(scene_key)
        for scene_key in available_scene_keys:
            _push(scene_key)
        return merged

    def _build_entry_target(self, *, scene_key: str = "", route: str = "", menu_id=None, action_id=None, model: str = "", record_id=None) -> dict:
        normalized_scene_key = str(scene_key or "").strip()
        normalized_route = str(route or "").strip()
        if not normalized_scene_key and normalized_route.startswith("/s/"):
            normalized_scene_key = normalized_route.replace("/s/", "", 1).strip("/")
        if not normalized_scene_key:
            return {}
        target = {
            "type": "scene",
            "scene_key": normalized_scene_key,
        }
        if normalized_route:
            target["route"] = normalized_route
        compatibility = {}
        if isinstance(menu_id, int) and menu_id > 0:
            compatibility["menu_id"] = menu_id
        if isinstance(action_id, int) and action_id > 0:
            compatibility["action_id"] = action_id
        normalized_model = str(model or "").strip()
        if normalized_model:
            compatibility["model"] = normalized_model
        if isinstance(record_id, int) and record_id > 0:
            compatibility["record_id"] = record_id
        if normalized_model and isinstance(record_id, int) and record_id > 0:
            record_entry = {
                "model": normalized_model,
                "record_id": record_id,
            }
            if isinstance(action_id, int) and action_id > 0:
                record_entry["action_id"] = action_id
            if isinstance(menu_id, int) and menu_id > 0:
                record_entry["menu_id"] = menu_id
            target["record_entry"] = record_entry
        if compatibility:
            target["compatibility_refs"] = compatibility
        return target

    def build_role_surface(
        self,
        user_xmlids: set,
        nav_tree: list,
        scene_keys: set,
        role_surface_overrides: dict | None = None,
    ) -> dict:
        role_code, role_evidence = self.resolve_role_code_with_evidence(user_xmlids)
        role_meta = self._role_surface_map.get(role_code) or self._role_surface_map.get("owner") or {}
        role_meta = self._merge_role_meta(role_code, role_meta, role_surface_overrides)
        scene_candidates = self._merge_scene_candidates(
            list(role_meta.get("landing_scene_candidates") or []),
            nav_tree,
            scene_keys,
        )
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
        landing_path = f"/s/{landing_scene_key}"
        role_surface = {
            "role_code": role_code,
            "role_label": role_meta.get("label") or role_code,
            "role_evidence": role_evidence,
            "landing_scene_key": landing_scene_key,
            "landing_menu_xmlid": landing_menu_xmlid,
            "landing_menu_id": landing_menu_id,
            "landing_path": landing_path,
            "scene_candidates": scene_candidates,
            "menu_xmlids": menu_candidates,
            "menu_blocklist_xmlids": menu_blocklist_xmlids,
        }
        landing_entry_target = self._build_entry_target(
            scene_key=landing_scene_key,
            route=landing_path,
            menu_id=landing_menu_id if isinstance(landing_menu_id, int) else None,
        )
        if landing_entry_target:
            role_surface["landing_entry_target"] = landing_entry_target
        return role_surface

    def build_role_surface_map_payload(self) -> Dict[str, dict]:
        payload = {}
        for role_code, role_meta in self._role_surface_map.items():
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
                    model = ""
                    record_id = None
                    action_id = None
                    if isinstance(node.get("meta"), dict):
                        meta = node.get("meta") or {}
                        scene_key = str(meta.get("scene_key") or "").strip()
                        model = str(meta.get("model") or "").strip()
                        record_id = meta.get("record_id") if isinstance(meta.get("record_id"), int) else None
                        action_id = meta.get("action_id") if isinstance(meta.get("action_id"), int) else None
                    if not scene_key:
                        scene_key = str(node.get("scene_key") or "").strip()
                    route = f"/s/{scene_key}" if scene_key else "/workbench"
                    default_route = {
                        "menu_id": menu_id,
                        "scene_key": scene_key or None,
                        "route": route,
                        "reason": "menu_fallback",
                    }
                    entry_target = self._build_entry_target(
                        scene_key=scene_key,
                        route=route,
                        menu_id=menu_id if isinstance(menu_id, int) else None,
                        action_id=action_id,
                        model=model,
                        record_id=record_id,
                    )
                    if entry_target:
                        default_route["entry_target"] = entry_target
                    return default_route
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
