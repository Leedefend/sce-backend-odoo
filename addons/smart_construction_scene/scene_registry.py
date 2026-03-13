# -*- coding: utf-8 -*-
import json
import os
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

SCENE_VERSION = "v2"
SCHEMA_VERSION = "v2"
IMPORTED_SCENES_PARAM = "sc.scene.package.imported_scenes"


_SCENE_REGISTRY_CONTENT_MODULE = None
_SCENE_REGISTRY_ENGINE_MODULE = None


def _load_scene_registry_engine_module():
    global _SCENE_REGISTRY_ENGINE_MODULE
    if _SCENE_REGISTRY_ENGINE_MODULE is not None:
        return _SCENE_REGISTRY_ENGINE_MODULE
    engine_path = Path(__file__).resolve().parents[1] / "smart_scene" / "core" / "scene_registry_engine.py"
    try:
        spec = spec_from_file_location("smart_scene_scene_registry_engine", engine_path)
        if spec is None or spec.loader is None:
            raise RuntimeError("spec unavailable")
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
        _SCENE_REGISTRY_ENGINE_MODULE = module
        return module
    except Exception:
        _SCENE_REGISTRY_ENGINE_MODULE = False
        return None


def _load_scene_registry_content_module():
    global _SCENE_REGISTRY_CONTENT_MODULE
    if _SCENE_REGISTRY_CONTENT_MODULE is not None:
        return _SCENE_REGISTRY_CONTENT_MODULE
    engine = _load_scene_registry_engine_module()
    loader = getattr(engine, "load_scene_registry_content_module", None) if engine else None
    if not callable(loader):
        _SCENE_REGISTRY_CONTENT_MODULE = False
        return None
    module = loader(Path(__file__))
    _SCENE_REGISTRY_CONTENT_MODULE = module if module is not None else False
    return module


def _load_scene_registry_content_entries():
    engine = _load_scene_registry_engine_module()
    loader = getattr(engine, "load_scene_registry_content_entries", None) if engine else None
    if callable(loader):
        try:
            rows = loader(Path(__file__))
            return rows if isinstance(rows, list) else []
        except Exception:
            return []
    return []


def _append_drift(drift, *, scene_key, kind, fields, severity="info", source="db->registry"):
    if drift is None:
        return
    drift.append({
        "scene_key": scene_key or "",
        "kind": kind,
        "fields": list(fields or []),
        "severity": severity,
        "source": source,
    })


def get_scene_version():
    return SCENE_VERSION


def get_schema_version():
    return SCHEMA_VERSION


def _to_bool(value, default=False):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        text = value.strip().lower()
        if text in {"1", "true", "yes", "on"}:
            return True
        if text in {"0", "false", "no", "off"}:
            return False
    return default


def _include_test_scenes(env) -> bool:
    try:
        cfg = env["ir.config_parameter"].sudo().get_param("sc.scene.include_tests") if env is not None else ""
    except Exception:
        cfg = ""
    if str(cfg or "").strip():
        return _to_bool(cfg, False)
    runtime_env = str(os.environ.get("ENV") or "").strip().lower()
    if runtime_env in {"prod", "production"}:
        return False
    return runtime_env in {"dev", "test"}


def _filter_test_scenes(scenes, include_tests: bool):
    if include_tests:
        return list(scenes or [])
    out = []
    for scene in scenes or []:
        if not isinstance(scene, dict):
            continue
        if bool(scene.get("is_test")):
            continue
        out.append(scene)
    return out

def has_db_scenes(env):
    if env is None:
        return False
    try:
        Scene = env['sc.scene'].sudo()
    except Exception:
        return False
    try:
        return Scene.search_count([('active', '=', True), ('state', '=', 'published')]) > 0
    except Exception:
        return False



def _normalize_scene(scene, drift=None, source="registry"):
    if not isinstance(scene, dict):
        return None
    if not scene.get("code") and scene.get("key"):
        scene["code"] = scene.get("key")
    tags = scene.get("tags")
    if isinstance(tags, str):
        scene["tags"] = [t.strip() for t in tags.split(",") if t and t.strip()]
    elif isinstance(tags, list):
        scene["tags"] = [str(t).strip() for t in tags if str(t).strip()]
    else:
        scene["tags"] = []
    if scene.get("is_test"):
        if "internal" not in scene["tags"]:
            scene["tags"].append("internal")
        if "smoke" not in scene["tags"]:
            scene["tags"].append("smoke")
    scene = _apply_scene_defaults(scene, drift=drift, source=source)
    return scene


def _apply_scene_defaults(scene, drift=None, source="registry"):
    code = scene.get("code") or scene.get("key") or ""
    if code == "projects.intake":
        required_caps = scene.get("required_capabilities")
        if not isinstance(required_caps, list) or not [str(x).strip() for x in required_caps if str(x).strip()]:
            scene["required_capabilities"] = ["project.board.open"]
            if source == "db":
                _append_drift(
                    drift,
                    scene_key=code,
                    kind="fallback_override",
                    fields=["required_capabilities"],
                    severity="warn",
                )
        target = scene.get("target") if isinstance(scene.get("target"), dict) else {}
        if not str(target.get("model") or "").strip():
            target["model"] = "project.project"
            if source == "db":
                _append_drift(
                    drift,
                    scene_key=code,
                    kind="fallback_override",
                    fields=["target.model"],
                    severity="warn",
                )
        if not str(target.get("view_type") or "").strip():
            target["view_type"] = "form"
            if source == "db":
                _append_drift(
                    drift,
                    scene_key=code,
                    kind="fallback_override",
                    fields=["target.view_type"],
                    severity="warn",
                )
        route = str(target.get("route") or "").strip()
        if "TARGET_MISSING" in route:
            # 历史导出可能遗留 workbench 占位路由，强制收敛到稳定语义路由。
            target["route"] = "/s/projects.intake"
            scene["target"] = target
            if source == "db":
                _append_drift(
                    drift,
                    scene_key=code,
                    kind="fallback_override",
                    fields=["target.route"],
                    severity="warn",
                )
        if not (
            target.get("menu_xmlid")
            or target.get("menu_id")
            or target.get("action_xmlid")
            or target.get("action_id")
            or target.get("model")
            or target.get("route")
        ):
            # Keep intake scene executable without leaking workbench fallback.
            target["route"] = "/s/projects.intake"
            scene["target"] = target
            if source == "db":
                _append_drift(
                    drift,
                    scene_key=code,
                    kind="fallback_override",
                    fields=["target"],
                    severity="warn",
                )
    return scene


def _load_from_db(env, drift=None):
    if env is None:
        return []
    try:
        Scene = env["sc.scene"].sudo()
    except Exception:
        return []
    scenes = Scene.search([("active", "=", True), ("state", "=", "published")], order="sequence, id")
    out = []
    for scene in scenes:
        payload = scene.to_public_dict(env.user)
        normalized = _normalize_scene(payload, drift=drift, source="db")
        if normalized:
            out.append(normalized)
    return out


def _load_imported_scenes(env, drift=None):
    if env is None:
        return []
    try:
        raw = env["ir.config_parameter"].sudo().get_param(IMPORTED_SCENES_PARAM)
    except Exception:
        return []
    if not raw:
        return []
    try:
        payload = json.loads(raw)
    except Exception:
        return []
    if not isinstance(payload, dict):
        return []

    out = []
    for code, scene in payload.items():
        if not isinstance(scene, dict):
            continue
        item = dict(scene)
        if not item.get("code"):
            item["code"] = str(code or "").strip()
        normalized = _normalize_scene(item, drift=drift, source="db")
        if normalized and normalized.get("code"):
            out.append(normalized)
    return out


def load_scene_configs(env, drift=None):
    # Prefer DB scenes if present; fallback to code-defined scenes.
    db_scenes = _load_from_db(env, drift=drift)
    imported_scenes = _load_imported_scenes(env, drift=drift)
    include_tests = _include_test_scenes(env)
    # Note: keep configs data-only; target IDs are resolved by system_init.
    # Complete migration: platform fallback keeps only minimal internal defaults.
    fallback = [
        {
            "code": "default",
            "name": "默认场景",
            "is_test": True,
            "tags": ["internal"],
            "target": {"route": "/workbench?scene=default"},
        },
        {
            "code": "scene_smoke_default",
            "name": "Scene Smoke Default",
            "is_test": True,
            "tags": ["internal", "smoke"],
            "target": {"route": "/workbench?scene=scene_smoke_default"},
        },
    ]
    for scene in _load_scene_registry_content_entries():
        code = str(scene.get("code") or "").strip()
        if not code:
            continue
        fallback = [item for item in fallback if str(item.get("code") or "").strip() != code]
        fallback.append(scene)
    if not db_scenes:
        if not imported_scenes:
            return _filter_test_scenes(fallback, include_tests)
        imported_codes = {scene.get("code") for scene in imported_scenes if scene.get("code")}
        merged = list(imported_scenes)
        for scene in fallback:
            if scene.get("code") not in imported_codes:
                merged.append(scene)
        return _filter_test_scenes(merged, include_tests)

    fallback_map = {scene.get("code"): scene for scene in fallback}
    imported_map = {scene.get("code"): scene for scene in imported_scenes if scene.get("code")}
    seen = {scene.get("code") for scene in db_scenes if scene.get("code")}

    def _merge_missing(scene, defaults):
        for key, value in defaults.items():
            current = scene.get(key)
            if key not in scene or current in (None, "", [], {}):
                scene[key] = value
                continue
            if isinstance(value, dict):
                if not isinstance(current, dict):
                    scene[key] = value
                    continue
                for d_key, d_val in value.items():
                    if d_key not in current or current.get(d_key) in (None, "", [], {}):
                        current[d_key] = d_val
                continue
            if isinstance(value, list) and not isinstance(current, list):
                scene[key] = value

    def _upgrade_fallback_target(scene, defaults):
        current = scene.get("target")
        default_target = defaults.get("target") if isinstance(defaults, dict) else None
        if not isinstance(current, dict) or not isinstance(default_target, dict):
            return
        code = scene.get("code")
        route = current.get("route")
        if not isinstance(route, str) or not code:
            return
        is_scene_fallback = route.startswith(f"/workbench?scene={code}")
        is_missing_reason = "TARGET_MISSING" in route
        if not (is_scene_fallback or is_missing_reason):
            return
        has_resolvable_default = bool(
            default_target.get("action_xmlid")
            or default_target.get("menu_xmlid")
            or default_target.get("action_id")
            or default_target.get("menu_id")
            or default_target.get("model")
        )
        if has_resolvable_default:
            scene["target"] = dict(default_target)

    for scene in db_scenes:
        code = scene.get("code")
        if not code:
            continue
        defaults = fallback_map.get(code)
        if defaults:
            _merge_missing(scene, defaults)
            _upgrade_fallback_target(scene, defaults)
        imported = imported_map.get(code)
        if imported:
            _merge_missing(scene, imported)

    for code, scene in imported_map.items():
        if code not in seen:
            db_scenes.append(scene)
            seen.add(code)

    for code, scene in fallback_map.items():
        if code not in seen:
            db_scenes.append(scene)
    return _filter_test_scenes(db_scenes, include_tests)
