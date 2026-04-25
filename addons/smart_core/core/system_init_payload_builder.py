# -*- coding: utf-8 -*-
from __future__ import annotations

from urllib.parse import urlparse


class SystemInitPayloadBuilder:
    BUILD_MODE_BOOT = "boot"
    BUILD_MODE_PRELOAD = "preload"
    BUILD_MODE_DEBUG = "debug"
    MINIMAL_ALLOWED_KEYS = {
        "delivery_engine_v1",
        "edition_runtime_v1",
        "user",
        "nav",
        "nav_meta",
        "default_route",
        "scene_ready_contract_v1",
        "intents",
        "feature_flags",
        "role_surface",
        "semantic_runtime",
        "released_scene_semantic_surface",
        "version",
        "init_meta",
    }
    MINIMAL_NAV_META_KEYS = {
        "nav_source",
        "platform_minimum_surface",
        "platform_minimum_reason",
        "role_surface_pruned",
        "role_surface_code",
        "semantic_scene_key",
        "semantic_source_view",
        "semantic_view_type",
    }
    MINIMAL_EXT_FACT_KEYS = {
        "enterprise_enablement",
    }
    DEFAULT_STARTUP_PAGE_KEYS = ("home", "my_work", "workbench")

    @staticmethod
    def _parse_with_tokens(value) -> set[str]:
        if isinstance(value, str):
            raw = [item.strip() for item in value.split(",")]
        elif isinstance(value, (list, tuple, set)):
            raw = [str(item or "").strip() for item in value]
        else:
            raw = []
        return {item for item in raw if item}

    @staticmethod
    def _build_entry_target(*, scene_key: str = "", route: str = "", menu_id=None, action_id=None, model: str = "", record_id=None) -> dict:
        normalized_scene_key = str(scene_key or "").strip()
        if not normalized_scene_key:
            normalized_scene_key = SystemInitPayloadBuilder._extract_scene_key_from_route(route)
        if not normalized_scene_key:
            return {}
        target = {
            "type": "scene",
            "scene_key": normalized_scene_key,
        }
        normalized_route = str(route or "").strip()
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

    @classmethod
    def _normalize_default_route(cls, route_payload: dict | None) -> dict:
        payload = dict(route_payload or {})
        if not payload:
            return payload
        entry_target = cls._build_entry_target(
            scene_key=str(payload.get("scene_key") or "").strip(),
            route=str(payload.get("route") or "").strip(),
            menu_id=payload.get("menu_id") if isinstance(payload.get("menu_id"), int) else None,
            action_id=payload.get("action_id") if isinstance(payload.get("action_id"), int) else None,
            model=str(payload.get("model") or "").strip(),
            record_id=payload.get("record_id") if isinstance(payload.get("record_id"), int) else None,
        )
        if entry_target:
            payload["entry_target"] = entry_target
        return payload

    @classmethod
    def _normalize_role_surface(cls, role_surface: dict | None) -> dict:
        payload = dict(role_surface or {})
        if not payload:
            return payload
        entry_target = cls._build_entry_target(
            scene_key=str(payload.get("landing_scene_key") or "").strip(),
            route=str(payload.get("landing_path") or "").strip(),
            menu_id=payload.get("landing_menu_id") if isinstance(payload.get("landing_menu_id"), int) else None,
        )
        if entry_target:
            payload["landing_entry_target"] = entry_target
        return payload

    @classmethod
    def _normalize_nav_tree(cls, nodes: list | None) -> list:
        normalized = []
        for node in nodes or []:
            if not isinstance(node, dict):
                continue
            row = dict(node)
            row["children"] = cls._normalize_nav_tree(row.get("children") if isinstance(row.get("children"), list) else [])
            meta = dict(row.get("meta") or {})
            entry_target = cls._build_entry_target(
                scene_key=str(row.get("scene_key") or meta.get("scene_key") or "").strip(),
                route=str(meta.get("route") or row.get("route") or "").strip(),
                menu_id=row.get("menu_id") if isinstance(row.get("menu_id"), int) else None,
                action_id=meta.get("action_id") if isinstance(meta.get("action_id"), int) else None,
                model=str(meta.get("model") or row.get("model") or "").strip(),
                record_id=meta.get("record_id") if isinstance(meta.get("record_id"), int) else None,
            )
            if entry_target:
                meta["entry_target"] = entry_target
            row["meta"] = meta
            normalized.append(row)
        return normalized

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
        default_route = row.get("default_route") if isinstance(row.get("default_route"), dict) else {}
        role_surface = row.get("role_surface") if isinstance(row.get("role_surface"), dict) else {}
        role_entries = row.get("role_entries") if isinstance(row.get("role_entries"), list) else []
        home_blocks = row.get("home_blocks") if isinstance(row.get("home_blocks"), list) else []

        scene_subset: list[str] = []
        landing_scene_key = str(default_route.get("scene_key") or role_surface.get("landing_scene_key") or "workspace.home").strip()
        if landing_scene_key:
            scene_subset.append(landing_scene_key)

        fallback_scene_key = "workspace.home"
        if fallback_scene_key not in scene_subset:
            scene_subset.append(fallback_scene_key)

        deep_scene_key = str(params.get("scene_key") or "").strip()
        if not deep_scene_key:
            deep_scene_key = cls._extract_scene_key_from_route(str(params.get("route") or ""))
        if deep_scene_key and deep_scene_key not in scene_subset:
            scene_subset.append(deep_scene_key)

        role_scene_candidates = role_surface.get("scene_candidates") if isinstance(role_surface.get("scene_candidates"), list) else []
        for candidate in role_scene_candidates:
            scene_key = str(candidate or "").strip()
            if not scene_key or scene_key in scene_subset:
                continue
            scene_subset.append(scene_key)

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
    def _build_minimal_ext_facts(cls, row: dict) -> dict:
        ext_facts = row.get("ext_facts") if isinstance(row.get("ext_facts"), dict) else {}
        minimal: dict = {}
        for key in cls.MINIMAL_EXT_FACT_KEYS:
            value = ext_facts.get(key)
            if isinstance(value, dict) and value:
                minimal[key] = value
        return minimal

    @classmethod
    def _build_minimal_page_contracts(cls, row: dict) -> dict:
        payload = row.get("page_contracts") if isinstance(row.get("page_contracts"), dict) else {}
        pages = payload.get("pages") if isinstance(payload.get("pages"), dict) else {}
        selected_pages: dict = {}
        for page_key in cls.DEFAULT_STARTUP_PAGE_KEYS:
            page = pages.get(page_key)
            if isinstance(page, dict):
                selected_pages[page_key] = page
        if not selected_pages:
            return {}
        out = {"pages": selected_pages}
        for key in ("schema_version", "contract_version", "meta"):
            value = payload.get(key)
            if value is not None:
                out[key] = value
        return out

    @classmethod
    def _build_workspace_home_default_route(cls) -> dict:
        route = {
            "menu_id": None,
            "scene_key": "workspace.home",
            "route": "/",
            "reason": "workspace_home_default",
        }
        entry_target = cls._build_entry_target(scene_key="workspace.home", route="/")
        if entry_target:
            route["entry_target"] = entry_target
        return route

    @classmethod
    def _build_workspace_home_ref(cls, row: dict) -> dict:
        payload = row.get("workspace_home_ref") if isinstance(row.get("workspace_home_ref"), dict) else {}
        out = dict(payload)
        out["intent"] = str(out.get("intent") or "ui.contract")
        out["scene_key"] = "workspace.home"
        out["loaded"] = bool(out.get("loaded"))
        return out

    @classmethod
    def resolve_startup_scene_subset(cls, row: dict, *, params: dict | None = None) -> list[str]:
        init_meta = cls._build_minimal_init_meta(row if isinstance(row, dict) else {}, params=params)
        scene_subset = init_meta.get("scene_subset") if isinstance(init_meta.get("scene_subset"), list) else []
        unique_subset: list[str] = []
        for item in scene_subset:
            key = str(item or "").strip()
            if key and key not in unique_subset:
                unique_subset.append(key)
        return unique_subset

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
        with_tokens = cls._parse_with_tokens(params.get("with"))
        include_workspace_home = bool(params.get("with_preload", False)) or "workspace_home" in with_tokens

        nav = cls._normalize_nav_tree(row.get("nav") if isinstance(row.get("nav"), list) else [])
        default_route = cls._normalize_default_route(row.get("default_route") if isinstance(row.get("default_route"), dict) else {})
        intents = row.get("intents") if isinstance(row.get("intents"), list) else []
        feature_flags = row.get("feature_flags") if isinstance(row.get("feature_flags"), dict) else {}
        role_surface = cls._normalize_role_surface(row.get("role_surface") if isinstance(row.get("role_surface"), dict) else {})
        role_entries = row.get("role_entries") if isinstance(row.get("role_entries"), list) else []
        home_blocks = row.get("home_blocks") if isinstance(row.get("home_blocks"), list) else []

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
            "scene_channel": str(row.get("scene_channel") or ""),
            "scene_channel_selector": str(row.get("scene_channel_selector") or ""),
            "scene_channel_source_ref": str(row.get("scene_channel_source_ref") or ""),
            "scene_contract_ref": row.get("scene_contract_ref"),
            "version": version,
            "init_meta": init_meta,
        }
        pinned_param = str(params.get("scene_use_pinned") or "").strip().lower()
        rollback_param = str(params.get("scene_rollback") or "").strip().lower()
        pinned_requested = pinned_param in {"1", "true", "yes", "on"}
        rollback_requested = rollback_param in {"1", "true", "yes", "on"}
        rollback_ref = str(row.get("scene_contract_ref") or "").strip()
        rollback_active = pinned_requested or rollback_requested or ("PINNED.json" in rollback_ref)
        if rollback_active:
            minimal["scene_diagnostics"] = {
                "rollback_active": True,
                "rollback_ref": rollback_ref or "stable/PINNED.json",
                "schema_version": str(row.get("schema_version") or "1.0.0"),
                "scene_version": str(row.get("scene_version") or "v1"),
                "loaded_from": "contract",
                "resolve_errors": [],
                "drift": [],
                "normalize_warnings": [],
            }
        minimal_ext_facts = cls._build_minimal_ext_facts(row)
        if minimal_ext_facts:
            minimal["ext_facts"] = minimal_ext_facts
        if isinstance(row.get("delivery_engine_v1"), dict):
            minimal["delivery_engine_v1"] = row.get("delivery_engine_v1")
        if isinstance(row.get("edition_runtime_v1"), dict):
            minimal["edition_runtime_v1"] = row.get("edition_runtime_v1")
        if isinstance(row.get("release_navigation_v1"), dict):
            minimal["release_navigation_v1"] = row.get("release_navigation_v1")
        if isinstance(row.get("semantic_runtime"), dict):
            minimal["semantic_runtime"] = cls._build_minimal_semantic_runtime(
                row.get("semantic_runtime")
            )
        if isinstance(row.get("released_scene_semantic_surface"), dict):
            minimal["released_scene_semantic_surface"] = cls._build_minimal_released_scene_semantic_surface(
                row.get("released_scene_semantic_surface")
            )
        if isinstance(row.get("scene_ready_contract_v1"), dict):
            if bool(params.get("with_preload", False)):
                minimal["scene_ready_contract_v1"] = row.get("scene_ready_contract_v1")
            else:
                minimal["scene_ready_contract_v1"] = cls._build_minimal_scene_ready_contract(
                    row.get("scene_ready_contract_v1")
                )
        minimal_page_contracts = cls._build_minimal_page_contracts(row)
        if minimal_page_contracts:
            minimal["page_contracts"] = minimal_page_contracts
        if isinstance((minimal.get("page_contracts") or {}).get("pages"), dict) and "home" in (minimal.get("page_contracts") or {}).get("pages", {}):
            minimal["default_route"] = cls._build_workspace_home_default_route()
            minimal["workspace_home_ref"] = cls._build_workspace_home_ref(row)
        else:
            workspace_home_ref = row.get("workspace_home_ref") if isinstance(row.get("workspace_home_ref"), dict) else {}
            if workspace_home_ref:
                minimal["workspace_home_ref"] = workspace_home_ref
        if include_workspace_home:
            if isinstance(row.get("workspace_home"), dict):
                minimal["workspace_home"] = row.get("workspace_home")
        if role_entries:
            minimal["role_entries"] = role_entries
        if home_blocks:
            minimal["home_blocks"] = home_blocks
        if resolved_build_mode == cls.BUILD_MODE_DEBUG:
            minimal["startup_inspect"] = inspect_payload if isinstance(inspect_payload, dict) else {}
        return minimal

    @classmethod
    def _build_minimal_scene_ready_contract(cls, payload: dict | None) -> dict:
        raw = payload if isinstance(payload, dict) else {}
        scenes = raw.get("scenes") if isinstance(raw.get("scenes"), list) else []
        compact_scenes: list[dict] = []
        for item in scenes:
            if not isinstance(item, dict):
                continue
            compact: dict = {}
            for key in (
                "scene",
                "page",
                "parser_semantic_surface",
                "semantic_view",
                "semantic_page",
                "view_type",
                "guidance",
                "primary_action",
                "next_action",
                "fallback_strategy",
                "delivery_handoff_v1",
                "runtime_handoff_surface",
                "product_delivery_surface",
                "permission_surface",
                "workflow_surface",
                "actions",
                "next_scene",
                "next_scene_route",
            ):
                value = item.get(key)
                if value not in (None, {}, []):
                    compact[key] = value
            compact_search = cls._compact_search_surface(item.get("search_surface"))
            if compact_search:
                compact["search_surface"] = compact_search
            list_surface = item.get("list_surface") if isinstance(item.get("list_surface"), dict) else {}
            if list_surface:
                compact_list_surface = {}
                for key in ("columns", "hidden_columns", "default_sort", "available_view_modes", "default_mode"):
                    value = list_surface.get(key)
                    if value not in (None, {}, []):
                        compact_list_surface[key] = value
                if compact_list_surface:
                    compact["list_surface"] = compact_list_surface
            form_surface = item.get("form_surface") if isinstance(item.get("form_surface"), dict) else {}
            if form_surface:
                compact_form_surface = {}
                for key in ("layout", "header_actions", "stat_actions", "relation_fields", "field_behavior_map", "flags"):
                    value = form_surface.get(key)
                    if value not in (None, {}, []):
                        compact_form_surface[key] = value
                if compact_form_surface:
                    compact["form_surface"] = compact_form_surface
            optimization_composition = item.get("optimization_composition") if isinstance(item.get("optimization_composition"), dict) else {}
            if optimization_composition:
                compact_optimization_composition = {}
                for key in ("toolbar_sections", "active_conditions", "high_frequency_filters", "advanced_filters"):
                    value = optimization_composition.get(key)
                    if value not in (None, {}, []):
                        compact_optimization_composition[key] = value
                if compact_optimization_composition:
                    compact["optimization_composition"] = compact_optimization_composition
            action_surface = item.get("action_surface") if isinstance(item.get("action_surface"), dict) else {}
            if action_surface:
                compact_action_surface = {}
                for key in ("primary_actions", "groups", "selection_mode", "counts", "batch_capabilities"):
                    value = action_surface.get(key)
                    if value not in (None, {}, []):
                        compact_action_surface[key] = value
                if compact_action_surface:
                    compact["action_surface"] = compact_action_surface
            compact_validation_surface = cls._compact_validation_surface(item.get("validation_surface"))
            if compact_validation_surface:
                compact["validation_surface"] = compact_validation_surface
            compact_permission_surface = cls._compact_permission_surface(item.get("permission_surface"))
            if compact_permission_surface:
                compact["permission_surface"] = compact_permission_surface
            compact_workflow_surface = cls._compact_workflow_surface(item.get("workflow_surface"))
            if compact_workflow_surface:
                compact["workflow_surface"] = compact_workflow_surface
            meta = item.get("meta") if isinstance(item.get("meta"), dict) else {}
            compact_meta = {}
            for key in ("target", "next_scene", "ui_base_contract_source", "parser_semantic_surface", "compile_verdict"):
                value = meta.get(key)
                if value not in (None, {}, []):
                    compact_meta[key] = value
            if compact_meta:
                compact["meta"] = compact_meta
            if compact:
                compact_scenes.append(compact)

        meta = raw.get("meta") if isinstance(raw.get("meta"), dict) else {}
        compact_meta = {}
        for key in (
            "generated_by",
            "scene_count",
            "mode",
            "base_contract_bound_scene_count",
            "compile_issue_scene_count",
        ):
            value = meta.get(key)
            if value not in (None, {}, []):
                compact_meta[key] = value
        return {
            "contract_version": str(raw.get("contract_version") or "v1"),
            "schema_version": str(raw.get("schema_version") or "scene_ready_contract_v1"),
            "scene_version": str(raw.get("scene_version") or ""),
            "source_schema_version": str(raw.get("source_schema_version") or ""),
            "scene_channel": str(raw.get("scene_channel") or ""),
            "active_scene_key": str(raw.get("active_scene_key") or ""),
            "scenes": compact_scenes,
            "meta": compact_meta,
        }

    @staticmethod
    def _compact_search_surface(payload: dict | None) -> dict:
        raw = payload if isinstance(payload, dict) else {}
        compact = {}
        for key in ("default_sort", "filters", "fields", "group_by", "searchpanel", "default_state", "mode"):
            value = raw.get(key)
            if value not in (None, {}, []):
                compact[key] = value
        return compact

    @staticmethod
    def _compact_permission_surface(payload: dict | None) -> dict:
        raw = payload if isinstance(payload, dict) else {}
        compact = {}
        for key in ("visible", "allowed", "reason_code", "required_capabilities"):
            value = raw.get(key)
            if value not in (None, {}, []):
                compact[key] = value
        return compact

    @staticmethod
    def _compact_workflow_surface(payload: dict | None) -> dict:
        raw = payload if isinstance(payload, dict) else {}
        compact = {}
        for key in ("state_field", "states", "transitions", "highlight_states"):
            value = raw.get(key)
            if value not in (None, {}, []):
                compact[key] = value
        return compact

    @staticmethod
    def _compact_validation_surface(payload: dict | None) -> dict:
        raw = payload if isinstance(payload, dict) else {}
        compact = {}
        for key in ("required_fields", "field_rules"):
            value = raw.get(key)
            if value not in (None, {}, []):
                compact[key] = value
        return compact

    @classmethod
    def _build_minimal_semantic_runtime(cls, payload: dict | None) -> dict:
        raw = payload if isinstance(payload, dict) else {}
        compact = {}
        for key in ("scene_key", "view_type", "semantic_view", "semantic_page", "parser_semantic_surface"):
            value = raw.get(key)
            if value not in (None, {}, []):
                compact[key] = value
        compact_search = cls._compact_search_surface(raw.get("search_surface"))
        if compact_search:
            compact["search_surface"] = compact_search
        compact_permission = cls._compact_permission_surface(raw.get("permission_surface"))
        if compact_permission:
            compact["permission_surface"] = compact_permission
        compact_workflow = cls._compact_workflow_surface(raw.get("workflow_surface"))
        if compact_workflow:
            compact["workflow_surface"] = compact_workflow
        compact_validation = cls._compact_validation_surface(raw.get("validation_surface"))
        if compact_validation:
            compact["validation_surface"] = compact_validation
        return compact

    @classmethod
    def _build_minimal_released_scene_semantic_surface(cls, payload: dict | None) -> dict:
        raw = payload if isinstance(payload, dict) else {}
        compact = {}
        for key in ("scene_key", "parser_semantic_surface", "page_surface"):
            value = raw.get(key)
            if value not in (None, {}, []):
                compact[key] = value
        compact_search = cls._compact_search_surface(raw.get("search_surface"))
        if compact_search:
            compact["search_surface"] = compact_search
        compact_permission = cls._compact_permission_surface(raw.get("permission_surface"))
        if compact_permission:
            compact["permission_surface"] = compact_permission
        compact_workflow = cls._compact_workflow_surface(raw.get("workflow_surface"))
        if compact_workflow:
            compact["workflow_surface"] = compact_workflow
        compact_validation = cls._compact_validation_surface(raw.get("validation_surface"))
        if compact_validation:
            compact["validation_surface"] = compact_validation
        return compact

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
            "nav": SystemInitPayloadBuilder._normalize_nav_tree(nav_tree),
            "nav_meta": nav_meta,
            "default_route": SystemInitPayloadBuilder._normalize_default_route(default_route),
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
