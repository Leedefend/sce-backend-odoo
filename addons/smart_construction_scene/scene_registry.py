# -*- coding: utf-8 -*-

SCENE_VERSION = "v2"


def get_scene_version():
    return SCENE_VERSION


def _tile(
    key,
    title,
    subtitle,
    icon,
    *,
    action_xmlid=None,
    menu_xmlid=None,
    required_caps=None,
    scene_key=None,
):
    payload = {}
    if action_xmlid:
        payload["action_xmlid"] = action_xmlid
    if menu_xmlid:
        payload["menu_xmlid"] = menu_xmlid
    if scene_key:
        payload["scene_key"] = scene_key
    return {
        "key": key,
        "title": title,
        "subtitle": subtitle,
        "icon": icon,
        "payload": payload,
        "scene_key": scene_key,
        "required_capabilities": required_caps or [],
    }


def _normalize_layout(layout):
    if isinstance(layout, dict):
        return layout
    return {"kind": "workspace", "sidebar": "fixed", "header": "full"}


def _normalize_scene(scene):
    if not isinstance(scene, dict):
        return None
    if not scene.get("code") and scene.get("key"):
        scene["code"] = scene.get("key")
    scene["layout"] = _normalize_layout(scene.get("layout"))
    if scene.get("code") == "default":
        tiles = scene.get("tiles") if isinstance(scene.get("tiles"), list) else []
        for tile in tiles:
            if not isinstance(tile, dict):
                continue
            if tile.get("key") == "project.work":
                if not tile.get("scene_key") and not (tile.get("payload") or {}).get("scene_key"):
                    tile["scene_key"] = "projects.ledger"
                    payload = tile.get("payload") if isinstance(tile.get("payload"), dict) else {}
                    payload.setdefault("scene_key", "projects.ledger")
                    tile["payload"] = payload
    return scene


def _load_from_db(env):
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
        normalized = _normalize_scene(payload)
        if normalized:
            out.append(normalized)
    return out


def load_scene_configs(env):
    # Prefer DB scenes if present; fallback to code-defined scenes.
    db_scenes = _load_from_db(env)
    # Note: keep configs data-only; target IDs are resolved by system_init.
    fallback = [
        {
            "code": "default",
            "name": "默认场景",
            "layout": {"kind": "workspace", "sidebar": "fixed", "header": "full"},
            "target": {"route": "/workbench?scene=default"},
            "tiles": [
                _tile(
                    "project.work",
                    "项目工作",
                    "项目看板与概览入口",
                    "P",
                    action_xmlid="smart_construction_core.action_sc_project_kanban_lifecycle",
                    menu_xmlid="smart_construction_core.menu_sc_project_project",
                    required_caps=["project.work"],
                    scene_key="projects.ledger",
                ),
                _tile(
                    "capability.matrix",
                    "能力矩阵",
                    "查看角色可用能力",
                    "M",
                    action_xmlid="smart_construction_portal.action_sc_portal_capability_matrix",
                    menu_xmlid="smart_construction_portal.menu_sc_portal_capability_matrix",
                    required_caps=["capability.matrix"],
                ),
                _tile(
                    "contract.work",
                    "合同工作",
                    "合同台账与合同清单",
                    "C",
                    action_xmlid="smart_construction_core.action_construction_contract_my",
                    menu_xmlid="smart_construction_core.menu_sc_contract_income",
                    required_caps=["contract.work"],
                ),
                _tile(
                    "cost.work",
                    "成本工作",
                    "成本台账与预算入口",
                    "K",
                    action_xmlid="smart_construction_core.action_project_cost_ledger_my",
                    menu_xmlid="smart_construction_core.menu_sc_project_cost_ledger",
                    required_caps=["cost.work"],
                ),
                _tile(
                    "finance.work",
                    "财务工作",
                    "付款申请与财务台账",
                    "F",
                    action_xmlid="smart_construction_core.action_payment_request_my",
                    menu_xmlid="smart_construction_core.menu_payment_request",
                    required_caps=["finance.work"],
                ),
            ],
        },
        {
            "code": "scene_smoke_default",
            "name": "Scene Smoke Default",
            "layout": {"kind": "workspace", "sidebar": "fixed", "header": "full"},
            "target": {"route": "/workbench?scene=scene_smoke_default"},
            "tiles": [],
        },
        {
            "code": "projects.list",
            "name": "项目列表",
            "layout": {"kind": "list", "sidebar": "fixed", "header": "full"},
            "target": {
                "menu_xmlid": "smart_construction_demo.menu_sc_project_list_showcase",
                "action_xmlid": "smart_construction_demo.action_sc_project_list_showcase",
            },
        },
        {
            "code": "projects.intake",
            "name": "项目立项",
            "layout": {"kind": "record", "sidebar": "fixed", "header": "full"},
            "target": {
                "menu_xmlid": "smart_construction_core.menu_sc_project_initiation",
            },
        },
        {
            "code": "projects.ledger",
            "name": "项目台账（试点）",
            "layout": {"kind": "ledger", "sidebar": "fixed", "header": "full"},
            "target": {
                "menu_xmlid": "smart_construction_core.menu_sc_project_project",
                "action_xmlid": "smart_construction_core.action_sc_project_kanban_lifecycle",
            },
            "list_profile": {
                "columns": [
                    "name",
                    "project_code",
                    "partner_id",
                    "user_id",
                    "stage_id",
                    "write_date",
                ],
                "hidden_columns": [
                    "message_needaction",
                    "message_unread",
                    "is_favorite",
                    "display_name",
                    "__last_update",
                ],
                "column_labels": {
                    "name": "项目名称",
                    "project_code": "项目编号",
                    "partner_id": "客户",
                    "user_id": "负责人",
                    "stage_id": "状态",
                    "write_date": "更新时间",
                },
                "row_primary": "name",
                "row_secondary": "partner_id",
            },
            "filters": [],
            "default_sort": "write_date desc",
        },
    ]
    if not db_scenes:
        return fallback

    fallback_map = {scene.get("code"): scene for scene in fallback}
    seen = {scene.get("code") for scene in db_scenes if scene.get("code")}
    for code, scene in fallback_map.items():
        if code not in seen:
            db_scenes.append(scene)
    return db_scenes
