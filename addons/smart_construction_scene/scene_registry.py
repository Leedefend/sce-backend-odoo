# -*- coding: utf-8 -*-
import json

SCENE_VERSION = "v2"
SCHEMA_VERSION = "v2"
IMPORTED_SCENES_PARAM = "sc.scene.package.imported_scenes"


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
    scene = _apply_scene_defaults(scene, drift=drift, source=source)
    return scene


def _apply_scene_defaults(scene, drift=None, source="registry"):
    code = scene.get("code") or scene.get("key") or ""
    if code == "projects.intake":
        target = scene.get("target") if isinstance(scene.get("target"), dict) else {}
        if not (
            target.get("menu_xmlid")
            or target.get("menu_id")
            or target.get("action_xmlid")
            or target.get("action_id")
            or target.get("model")
            or target.get("route")
        ):
            target["route"] = "/workbench?scene=projects.intake&reason=TARGET_MISSING"
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
    # Note: keep configs data-only; target IDs are resolved by system_init.
    fallback = [
        {
            "code": "default",
            "name": "默认场景",
            "target": {"route": "/workbench?scene=default"},
        },
        {
            "code": "scene_smoke_default",
            "name": "Scene Smoke Default",
            "target": {"route": "/workbench?scene=scene_smoke_default"},
        },
        {
            "code": "projects.list",
            "name": "项目列表",
            "target": {
                "menu_xmlid": "smart_construction_demo.menu_sc_project_list_showcase",
                "action_xmlid": "smart_construction_demo.action_sc_project_list_showcase",
            },
        },
        {
            "code": "projects.intake",
            "name": "项目立项",
            "target": {
                "menu_xmlid": "smart_construction_core.menu_sc_project_initiation",
                "action_xmlid": "smart_construction_core.action_project_initiation",
            },
        },
        {
            "code": "projects.ledger",
            "name": "项目台账（试点）",
            "target": {
                "menu_xmlid": "smart_construction_core.menu_sc_project_project",
                "action_xmlid": "smart_construction_core.action_sc_project_kanban_lifecycle",
            },
        },
        {
            "code": "portal.lifecycle",
            "name": "生命周期驾驶舱",
            "target": {"route": "/portal/lifecycle"},
        },
        {
            "code": "portal.capability_matrix",
            "name": "能力矩阵",
            "target": {"route": "/portal/capability-matrix"},
        },
        {
            "code": "portal.dashboard",
            "name": "工作台",
            "target": {"route": "/portal/dashboard"},
        },
    ]
    if not db_scenes:
        if not imported_scenes:
            return fallback
        imported_codes = {scene.get("code") for scene in imported_scenes if scene.get("code")}
        merged = list(imported_scenes)
        for scene in fallback:
            if scene.get("code") not in imported_codes:
                merged.append(scene)
        return merged

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
    return db_scenes
