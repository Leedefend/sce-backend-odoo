# -*- coding: utf-8 -*-
from __future__ import annotations

from urllib.parse import urlparse


class SystemInitPayloadBuilder:
    BUILD_MODE_BOOT = "boot"
    BUILD_MODE_PRELOAD = "preload"
    BUILD_MODE_DEBUG = "debug"
    MINIMAL_ALLOWED_KEYS = {
        "user",
        "nav",
        "nav_meta",
        "default_route",
        "intents",
        "feature_flags",
        "role_surface",
        "version",
        "init_meta",
    }
    MINIMAL_NAV_META_KEYS = {
        "nav_source",
        "platform_minimum_surface",
        "platform_minimum_reason",
        "role_surface_pruned",
        "role_surface_code",
    }

    @staticmethod
    def _extract_scene_keys_from_nav(nav: list) -> list[str]:
        keys: list[str] = []

        def _walk(nodes):
            if not isinstance(nodes, list):
                return
            for node in nodes:
                if not isinstance(node, dict):
                    continue
                scene_key = ""
                if isinstance(node.get("meta"), dict):
                    scene_key = str((node.get("meta") or {}).get("scene_key") or "").strip()
                if not scene_key:
                    scene_key = str(node.get("scene_key") or "").strip()
                if scene_key and scene_key not in keys:
                    keys.append(scene_key)
                children = node.get("children") if isinstance(node.get("children"), list) else []
                _walk(children)

        _walk(nav)
        return keys

    @staticmethod
    def _extract_scene_key_from_route(route: str) -> str:
        raw = str(route or "").strip()
        if not raw:
            return ""
        try:
            parsed = urlparse(raw)
            path = str(parsed.path or "").strip()
            if path.startswith("/s/"):
                return path.replace("/s/", "", 1).strip("/")
        except Exception:
            return ""
        return ""

    @classmethod
    def resolve_build_mode(cls, params: dict | None = None) -> str:
        params = params if isinstance(params, dict) else {}
        explicit = str(
            params.get("_build_mode")
            or params.get("build_mode")
            or params.get("startup_build_mode")
            or ""
        ).strip().lower()
        if explicit in {cls.BUILD_MODE_BOOT, cls.BUILD_MODE_PRELOAD, cls.BUILD_MODE_DEBUG}:
            return explicit
        if bool(params.get("with_preload", False)):
            return cls.BUILD_MODE_PRELOAD
        return cls.BUILD_MODE_BOOT

    @classmethod
    def _build_minimal_nav_meta(cls, row: dict) -> dict:
        raw = row.get("nav_meta") if isinstance(row.get("nav_meta"), dict) else {}
        minimal: dict = {}
        for key in cls.MINIMAL_NAV_META_KEYS:
            if key in raw:
                minimal[key] = raw.get(key)
        return minimal

    @classmethod
    def _build_minimal_init_meta(cls, row: dict, *, params: dict | None = None) -> dict:
        params = params if isinstance(params, dict) else {}
        preload_requested = bool(params.get("with_preload", False))
        nav = row.get("nav") if isinstance(row.get("nav"), list) else []
        default_route = row.get("default_route") if isinstance(row.get("default_route"), dict) else {}
        role_surface = row.get("role_surface") if isinstance(row.get("role_surface"), dict) else {}

        scene_subset: list[str] = []
        landing_scene_key = str(default_route.get("scene_key") or role_surface.get("landing_scene_key") or "workspace.home").strip()
        if landing_scene_key:
            scene_subset.append(landing_scene_key)

        fallback_scene_key = "workspace.home"
        if fallback_scene_key not in scene_subset:
            scene_subset.append(fallback_scene_key)

        nav_scene_keys = cls._extract_scene_keys_from_nav(nav)
        for key in nav_scene_keys:
            if key not in scene_subset:
                scene_subset.append(key)

        deep_scene_key = str(params.get("scene_key") or "").strip()
        if not deep_scene_key:
            deep_scene_key = cls._extract_scene_key_from_route(str(params.get("route") or ""))
        if deep_scene_key and deep_scene_key not in scene_subset:
            scene_subset.append(deep_scene_key)

        return {
            "contract_mode": str(row.get("contract_mode") or "default"),
            "preload_requested": preload_requested,
            "scene_subset": scene_subset,
            "scene_subset_count": len(scene_subset),
            "page_contract_meta": {
                "intent": "scene.page_contract",
            },
            "workspace_home_preload_hint": {
                "intent": "ui.contract",
                "scene_key": landing_scene_key or "workspace.home",
            },
        }

    @classmethod
    def build_startup_surface(
        cls,
        data: dict,
        *,
        params: dict | None = None,
        build_mode: str | None = None,
        inspect_payload: dict | None = None,
    ) -> dict:
        row = data if isinstance(data, dict) else {}
        params = params if isinstance(params, dict) else {}
        resolved_build_mode = build_mode or cls.resolve_build_mode(params)

        nav = row.get("nav") if isinstance(row.get("nav"), list) else []
        default_route = row.get("default_route") if isinstance(row.get("default_route"), dict) else {}
        intents = row.get("intents") if isinstance(row.get("intents"), list) else []
        feature_flags = row.get("feature_flags") if isinstance(row.get("feature_flags"), dict) else {}
        role_surface = row.get("role_surface") if isinstance(row.get("role_surface"), dict) else {}

        version = {
            "contract_version": str(row.get("contract_version") or "1.0.0"),
            "schema_version": str(row.get("schema_version") or "1.0.0"),
            "scene_version": str(row.get("scene_version") or "v1"),
        }
        init_meta = cls._build_minimal_init_meta(row, params=params)

        minimal = {
            "user": row.get("user") if isinstance(row.get("user"), dict) else {},
            "nav": nav,
            "nav_meta": cls._build_minimal_nav_meta(row),
            "default_route": default_route,
            "intents": intents,
            "feature_flags": feature_flags,
            "role_surface": role_surface,
            "version": version,
            "init_meta": init_meta,
        }
        if bool(params.get("with_preload", False)):
            if isinstance(row.get("workspace_home"), dict):
                minimal["workspace_home"] = row.get("workspace_home")
            if isinstance(row.get("scene_ready_contract_v1"), dict):
                minimal["scene_ready_contract_v1"] = row.get("scene_ready_contract_v1")
        if resolved_build_mode == cls.BUILD_MODE_DEBUG:
            minimal["startup_inspect"] = inspect_payload if isinstance(inspect_payload, dict) else {}
        return minimal

    @classmethod
    def slim_to_minimal_surface(cls, data: dict, *, params: dict | None = None) -> dict:
        return cls.build_startup_surface(data, params=params)
    @staticmethod
    def build_base(
        *,
        user_dict: dict,
        nav_tree: list,
        nav_meta: dict,
        default_route: dict,
        intents,
        feature_flags: dict,
        capabilities: list,
        scene_channel: str,
        channel_selector: str,
        channel_source_ref: str,
        contract_mode: str,
        contract_version: str,
    ) -> dict:
        return {
            "user": user_dict,
            "nav": nav_tree,
            "nav_meta": nav_meta,
            "default_route": default_route,
            "intents": intents,
            "feature_flags": feature_flags,
            "capabilities": capabilities,
            "capability_groups": [],
            "preload": [],
            "scenes": [],
            "scene_version": "v1",
            "schema_version": "1.0.0",
            "contract_version": contract_version,
            "scene_channel": scene_channel,
            "scene_channel_selector": channel_selector,
            "scene_channel_source_ref": channel_source_ref,
            "scene_contract_ref": None,
            "contract_mode": contract_mode,
            "ext_facts": {},
        }

    @staticmethod
    def attach_hud(data: dict, trace_id: str, elapsed_ms: int, contract_version: str, scene_trace_meta: dict) -> None:
        data["hud"] = {
            "trace_id": trace_id,
            "latency_ms": elapsed_ms,
            "contract_version": contract_version,
            "role_key": data.get("role_surface", {}).get("role_code"),
            **scene_trace_meta,
        }

    @staticmethod
    def attach_diagnostic(data: dict, diagnostic_info: dict) -> None:
        data["diagnostic"] = diagnostic_info

    @staticmethod
    def attach_preload(data: dict, home_contract, etags: dict, preload_items: list) -> None:
        if home_contract:
            data["preload"].append({"key": "home", "etag": etags.get("home")})
        if preload_items:
            data["preload"].extend(preload_items)

    @staticmethod
    def attach_layered_contract(data: dict) -> None:
        role_surface = data.get("role_surface") if isinstance(data.get("role_surface"), dict) else {}
        landing_scene_key = str(role_surface.get("landing_scene_key") or "").strip() or "workspace.home"
        contract_version = str(data.get("contract_version") or "1.0.0")
        schema_version = str(data.get("schema_version") or "1.0.0")
        sections_payload = {
            "contract_version": contract_version,
            "schema_version": schema_version,
            "session": {
                "user": data.get("user"),
                "contract_mode": data.get("contract_mode"),
                "scene_channel": data.get("scene_channel"),
            },
            "nav": {
                "nav": data.get("nav"),
                "default_route": data.get("default_route"),
                "nav_meta": data.get("nav_meta"),
            },
            "surface": {
                "role_surface": data.get("role_surface"),
                "role_surface_map": data.get("role_surface_map"),
                "capabilities": data.get("capabilities"),
                "capability_groups": data.get("capability_groups"),
                "feature_flags": data.get("feature_flags"),
            },
            "bootstrap_refs": {
                "workspace_home_ref": {
                    "intent": "ui.contract",
                    "scene_key": landing_scene_key,
                }
            },
        }
        data["system_init_sections_v1"] = sections_payload
        data["init_contract_v1"] = sections_payload
