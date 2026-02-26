# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Dict, List

ROLE_SURFACE_MAP = {
    "owner": {
        "label": "Owner",
        "landing_scene_candidates": ["projects.list", "projects.intake"],
        "menu_xmlids": [
            "smart_construction_core.menu_sc_project_center",
            "smart_construction_core.menu_sc_contract_center",
        ],
    },
    "pm": {
        "label": "Project Manager",
        "landing_scene_candidates": ["projects.ledger", "projects.list", "projects.intake"],
        "menu_xmlids": [
            "smart_construction_core.menu_sc_project_center",
            "smart_construction_core.menu_sc_contract_center",
            "smart_construction_core.menu_sc_cost_center",
        ],
    },
    "finance": {
        "label": "Finance",
        "landing_scene_candidates": ["finance.payment_requests", "projects.ledger", "projects.list"],
        "menu_xmlids": [
            "smart_construction_core.menu_sc_finance_center",
            "smart_construction_core.menu_sc_settlement_center",
            "smart_construction_core.menu_payment_request",
        ],
    },
    "executive": {
        "label": "Executive",
        "landing_scene_candidates": ["projects.intake", "projects.list", "projects.ledger"],
        "menu_xmlids": [
            "smart_construction_core.menu_sc_root",
            "smart_construction_core.menu_sc_projection_root",
            "smart_construction_core.menu_sc_project_center",
        ],
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
        return "projects.list"

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

    def build_role_surface(self, user_xmlids: set, nav_tree: list, scene_keys: set) -> dict:
        role_code, role_evidence = self.resolve_role_code_with_evidence(user_xmlids)
        role_meta = ROLE_SURFACE_MAP.get(role_code) or ROLE_SURFACE_MAP["owner"]
        scene_candidates = list(role_meta.get("landing_scene_candidates") or [])
        menu_candidates = list(role_meta.get("menu_xmlids") or [])
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
        }

    def build_role_surface_map_payload(self) -> Dict[str, dict]:
        payload = {}
        for role_code, role_meta in ROLE_SURFACE_MAP.items():
            payload[role_code] = {
                "role_code": role_code,
                "role_label": role_meta.get("label") or role_code,
                "scene_candidates": list(role_meta.get("landing_scene_candidates") or []),
                "menu_xmlids": list(role_meta.get("menu_xmlids") or []),
            }
        return payload

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
