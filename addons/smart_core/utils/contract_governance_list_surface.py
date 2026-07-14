# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any


def _safe_text(value: Any, fallback: str = "") -> str:
    text = str(value or "").strip()
    if text.lower() in {"undefined", "null"}:
        text = ""
    return text or fallback


def _safe_lower(value: Any) -> str:
    return _safe_text(value).lower()


def _as_dict(value: Any) -> dict:
    return dict(value) if isinstance(value, dict) else {}


def apply_standard_search_toolbar_labels(data: dict) -> None:
    search = _as_dict(data.get("search"))
    labels = _as_dict(search.get("ui_labels"))
    labels.update({
        "view_switch": "视图",
        "search_placeholder": "搜索关键字",
        "search_submit": "搜索",
        "search_menu_toggle": "展开搜索菜单",
        "filters": "筛选",
        "empty_filters": "暂无筛选",
        "saved_filters": "收藏夹",
        "empty_saved_filters": "暂无收藏",
        "group_by": "分组方式",
        "empty_group_by": "暂无分组",
        "sort": "排序",
        "sort_column_asc": "按 {column} 升序",
        "sort_column_desc": "按 {column} 降序",
        "create": "新建",
        "select_field": "选择字段",
        "select_value": "选择值",
        "boolean_true": "是",
        "boolean_false": "否",
        "input_value": "输入值",
        "custom_filter": "添加自定义筛选",
        "custom_group": "添加自定义分组",
        "favorite_save": "加入收藏",
        "add": "添加",
        "cancel": "取消",
        "save": "保存",
        "default": "默认",
        "shared": "共享",
        "favorite_name": "收藏名称",
        "favorite_use_by_default": "设为默认筛选",
        "favorite_shared": "共享给所有用户",
        "row_open": "打开",
        "loading_list": "正在加载列表...",
        "list_load_failed": "列表加载失败",
        "empty_create_title": "当前还没有数据",
        "empty_create_message": "可以先新建一条业务记录，开始录入和办理。",
        "empty_readonly_title": "当前还没有可查看的数据",
        "empty_readonly_message": "当前账号没有新建权限，可调整筛选条件或联系管理员确认数据与权限。",
        "empty_retry": "刷新",
        "pagination_prev": "上一页",
        "pagination_next": "下一页",
        "pagination_jump": "跳转",
        "pagination_page": "第 {current} / {total} 页",
        "pagination_total_empty": "共 0 条",
        "pagination_summary": "共 {total} 条，当前 {start}-{end} 条",
        "pagination_page_size": "每页",
        "pagination_apply_size": "应用",
        "record_count": "{count} 条记录",
        "row_number": "序号",
        "plain_search_placeholder": "输入关键字搜索",
        "page_footer_title": "页面统计",
        "page_footer_count": "当前页 {count} 条",
        "page_footer_current_total": "当前页合计",
        "page_footer_grand_total": "总计",
        "page_footer_current_count": "{count} 条",
        "page_footer_total_count": "{count} 条",
        "page_footer_summary": "{column} 汇总",
        "page_footer_summary_count": "{count} 项",
        "page_footer_no_numeric": "当前页没有可汇总的数值列",
        "selected_count": "已选 {count} 条",
        "clear": "清空",
        "batch_label_archive": "批量归档",
        "batch_label_activate": "批量激活",
        "batch_msg_archive_done_prefix": "批量归档完成：成功 ",
        "batch_msg_activate_done_prefix": "批量激活完成：成功 ",
        "batch_msg_done_middle": "，失败 ",
        "batch_msg_idempotent_replay": "批量操作已幂等处理（重复请求被忽略）",
        "batch_msg_archive_failed": "批量归档失败",
        "batch_msg_activate_failed": "批量激活失败",
        "batch_msg_model_no_active_field": "当前模型不支持归档/激活语义",
        "batch_msg_action_not_allowed": "当前场景不支持该批量操作",
        "grouped_result": "分组结果",
        "expand_all": "全部展开",
        "collapse_all": "全部收起",
        "group_sample_limit": "每组 {count} 条",
        "group_sort_desc": "按数量降序",
        "group_sort_asc": "按数量升序",
        "group_toggle_expand": "展开",
        "group_toggle_collapse": "收起",
        "group_count": "{count} 条",
        "group_view_all": "查看全部",
        "group_page_info": "第 {current} / {total} 页 · {range}",
        "column_picker": "列",
        "column_resize": "调整列宽",
        "column_reset": "恢复默认",
        "column_saving": "保存中",
        "column_saved": "已保存",
        "column_save_error": "保存失败，请重试",
    })
    search["ui_labels"] = labels
    data["search"] = search

    views = _as_dict(data.get("views"))
    tree = _as_dict(views.get("tree"))
    row_actions = tree.get("row_actions") if isinstance(tree.get("row_actions"), list) else []
    for action in row_actions:
        if not isinstance(action, dict):
            continue
        if _safe_text(action.get("name")) != "open_form" and _safe_text(action.get("intent")) != "open":
            continue
        action["label"] = labels.get("row_open") or action.get("label") or "打开"
        action["trigger"] = action.get("trigger") or "row_click"
        action["display_mode"] = action.get("display_mode") or "row_click"
        action["level"] = action.get("level") or "row"
        action["selection"] = action.get("selection") or "single"
        payload = _as_dict(action.get("payload"))
        payload["view_mode"] = payload.get("view_mode") or "form"
        action["payload"] = payload
    tree["row_actions"] = row_actions
    views["tree"] = tree
    data["views"] = views


def govern_tier_review_list_for_user(
    data: dict,
    *,
    is_model_tree_contract: Any,
    mark_legacy_industry_governance_profile: Any,
    nav_action_prefixes: tuple[str, ...],
) -> None:
    if not is_model_tree_contract(data, "tier.review"):
        return
    mark_legacy_industry_governance_profile(data, "tier.review.list")

    def _keep_action(row: Any) -> bool:
        if not isinstance(row, dict):
            return False
        key = _safe_text(row.get("key"))
        return not any(key.startswith(prefix) for prefix in nav_action_prefixes)

    buttons = data.get("buttons")
    if isinstance(buttons, list):
        data["buttons"] = [dict(row) for row in buttons if _keep_action(row)]

    toolbar = _as_dict(data.get("toolbar"))
    if toolbar:
        for slot in ("header", "sidebar", "footer"):
            rows = toolbar.get(slot)
            if isinstance(rows, list):
                toolbar[slot] = [dict(row) for row in rows if _keep_action(row)]
        data["toolbar"] = toolbar

    groups = data.get("action_groups")
    if isinstance(groups, list):
        normalized = []
        for group in groups:
            if not isinstance(group, dict):
                continue
            actions = group.get("actions")
            if not isinstance(actions, list):
                continue
            kept = [dict(row) for row in actions if _keep_action(row)]
            if not kept:
                continue
            next_group = dict(group)
            next_group["actions"] = kept
            normalized.append(next_group)
        data["action_groups"] = normalized


def govern_standard_list_for_user(
    data: dict,
    *,
    model_name: str,
    columns_order: list[str],
    column_labels: dict[str, str],
    row_primary: str,
    row_secondary: str,
    status_field: str,
    strict_columns: bool = False,
    is_model_tree_contract: Any,
    legacy_field_presentation: Any,
    deep_clone_json_like: Any,
    apply_standard_search_toolbar_labels: Any,
) -> None:
    if not is_model_tree_contract(data, model_name):
        return
    fields_map = _as_dict(data.get("fields"))
    selected = [name for name in columns_order if name in fields_map]
    if not selected:
        return

    views = _as_dict(data.get("views"))
    tree = _as_dict(views.get("tree") or views.get("list"))
    tree_governance = _as_dict(tree.get("governance"))
    tree_view_orchestration = _as_dict(tree_governance.get("view_orchestration"))
    tree_source_trace = _as_dict(tree.get("source_trace"))
    tree_trace_orchestration = _as_dict(tree_source_trace.get("view_orchestration"))
    has_orchestrated_tree = bool(
        tree_view_orchestration.get("applied")
        or tree_trace_orchestration.get("business_config_contracts")
    )
    native_schema_rows = tree.get("columns_schema") if isinstance(tree.get("columns_schema"), list) else []
    native_schema_by_name = {
        _safe_text(row.get("name")): dict(row)
        for row in native_schema_rows
        if isinstance(row, dict) and _safe_text(row.get("name"))
    }
    native_columns = []
    for row in tree.get("columns") or []:
        if isinstance(row, dict):
            name = _safe_text(row.get("name"))
        else:
            name = _safe_text(row)
        if name and name not in native_columns:
            native_columns.append(name)
    for name in native_schema_by_name:
        if name not in native_columns:
            native_columns.append(name)
    if has_orchestrated_tree and native_columns:
        selected = [name for name in native_columns if name in fields_map]
        for name in columns_order:
            if name in fields_map and name not in selected:
                selected.append(name)
    elif strict_columns:
        selected = [name for name in columns_order if name in fields_map]
    else:
        for name in native_columns:
            if name in fields_map and name not in selected:
                selected.append(name)

    def _field_label(name: str) -> str:
        schema_label = _safe_text(
            native_schema_by_name.get(name, {}).get("label")
            or native_schema_by_name.get(name, {}).get("string")
        )
        field_label = _safe_text(_as_dict(fields_map.get(name)).get("string"))
        if has_orchestrated_tree and schema_label:
            return schema_label
        return column_labels.get(name) or schema_label or field_label or name

    def _column_schema(name: str) -> dict:
        field = _as_dict(fields_map.get(name))
        schema = dict(native_schema_by_name.get(name) or {})
        schema["name"] = name
        schema["label"] = _field_label(name)
        schema["string"] = schema["label"]
        schema["type"] = schema.get("type") or field.get("type") or "char"
        schema["widget"] = schema.get("widget") or field.get("type") or "char"
        presentation = legacy_field_presentation(model_name, name)
        if presentation:
            if presentation.get("label"):
                schema["label"] = presentation["label"]
                schema["string"] = presentation["label"]
            if presentation.get("widget"):
                schema["widget"] = presentation["widget"]
            if presentation.get("cell_role"):
                schema["cell_role"] = presentation["cell_role"]
            if isinstance(presentation.get("mutation"), dict) and presentation["mutation"]:
                schema["mutation"] = deep_clone_json_like(presentation["mutation"])
        if name == status_field:
            schema["cell_role"] = "status"
            schema["tone_by_value"] = {
                "draft": "neutral",
                "in_progress": "info",
                "paused": "warning",
                "done": "success",
                "closing": "warning",
                "warranty": "info",
                "closed": "neutral",
            }
        if isinstance(field.get("selection"), list) and not isinstance(schema.get("selection"), list):
            schema["selection"] = [
                {"value": item[0], "label": item[1]}
                for item in field.get("selection")
                if isinstance(item, (list, tuple)) and len(item) >= 2
            ]
        return schema

    tree["columns"] = selected
    tree["columns_schema"] = [_column_schema(name) for name in selected]
    views["tree"] = tree
    data["views"] = views

    metric_fields = [
        name
        for name in (
            "contract_income_total",
            "contract_amount",
            "dashboard_invoice_amount",
            "amount_total",
            "total_amount",
            "planned_revenue",
            "budget_total",
        )
        if name in fields_map
    ]
    active_field = "active" if "active" in fields_map else ""
    assignee_field = "user_id" if "user_id" in fields_map else ""
    surface_policies = _as_dict(data.get("surface_policies"))
    surface_batch_policy = _as_dict(surface_policies.get("batch_policy"))
    delete_policy = _as_dict(data.get("delete_policy"))
    permissions = _as_dict(data.get("permissions"))
    effective = _as_dict(permissions.get("effective"))
    rights = _as_dict(effective.get("rights"))
    write_allowed = bool(rights.get("write"))
    unlink_right_allowed = bool(rights.get("unlink"))
    raw_available_actions = (
        surface_batch_policy.get("available_actions")
        if isinstance(surface_batch_policy.get("available_actions"), list)
        else []
    )
    if rights and not (write_allowed or unlink_right_allowed):
        raw_available_actions = []
    delete_mode = _safe_text(
        surface_policies.get("delete_mode")
        or delete_policy.get("delete_mode")
        or data.get("delete_mode"),
        "none",
    )
    available_actions = []
    if (write_allowed or unlink_right_allowed) and not raw_available_actions:
        raw_available_actions = []
        if active_field:
            raw_available_actions.extend(["archive", "activate"])
        if delete_mode == "unlink":
            raw_available_actions.append("delete")
    for raw_action in raw_available_actions:
        action = _safe_lower(raw_action)
        if action in {"archive", "activate"}:
            if active_field and write_allowed and action not in available_actions:
                available_actions.append(action)
            continue
        if action == "delete":
            if unlink_right_allowed and delete_mode == "unlink" and action not in available_actions:
                available_actions.append(action)
    batch_policy = {
        "enabled": bool(available_actions),
        "active_field": active_field,
        "assignee_field": assignee_field,
        "archive_value": False if active_field else None,
        "activate_value": True if active_field else None,
        "assignee_options": {
            "model": "res.users",
            "fields": ["id", "name"],
            "domain": [["active", "=", True]],
            "order": "name asc",
            "limit": 80,
        }
        if assignee_field
        else None,
        "delete_mode": delete_mode if "delete" in available_actions else "none",
        "available_actions": available_actions,
    }

    list_profile = _as_dict(data.get("list_profile"))
    list_profile.update(
        {
            "source": "contract_governance.curated_list_facts",
            "columns": selected,
            "fact_columns": selected,
            "hidden_columns": [],
            "column_labels": {name: _field_label(name) for name in selected},
            "row_primary": row_primary,
            "row_secondary": row_secondary,
            "primary_field": row_primary,
            "status_field": status_field,
            "metric_fields": metric_fields,
            "preference_policy": {
                "scope": "ui_only",
                "allow_visibility": True,
                "allow_order": True,
                "allow_width": True,
                "locked_columns": [],
                "must_request_columns": selected,
            },
            "batch_policy": batch_policy,
            "grouping": {
                "sample_limits": [3, 5, 8],
                "default_sample_limit": 3,
                "sort": {
                    "key": "count",
                    "default_direction": "desc",
                    "directions": ["desc", "asc"],
                },
            },
        }
    )
    if strict_columns:
        list_profile["column_policy"] = {
            "mode": "strict",
            "reason": "native_tree_columns_are_the_user_visible_business_surface",
        }
        list_profile["preference_policy"]["allow_visibility"] = True
        list_profile["preference_policy"]["allow_order"] = True
        list_profile["preference_policy"]["locked_columns"] = []
    data["list_profile"] = list_profile
    views = _as_dict(data.get("views"))
    tree_view = _as_dict(views.get("tree") or views.get("list"))
    if tree_view:
        tree_view.setdefault("order", "write_date desc, id desc")
        tree_view.setdefault("default_order", "write_date desc, id desc")
        if "tree" in views:
            views["tree"] = tree_view
        else:
            views["list"] = tree_view
        data["views"] = views
    surface_policies["batch_policy"] = batch_policy
    surface_policies["delete_mode"] = batch_policy.get("delete_mode") or surface_policies.get("delete_mode") or "none"
    data["surface_policies"] = surface_policies

    semantic_page = _as_dict(data.get("semantic_page"))
    list_semantics = _as_dict(semantic_page.get("list_semantics"))
    list_semantics["owner_layer"] = "scene_orchestration"
    list_semantics["source"] = "contract_governance.curated_list_facts"
    list_semantics["columns"] = [
        {
            "name": name,
            "label": _field_label(name),
            "widget": _column_schema(name).get("widget"),
            "cell_role": _column_schema(name).get("cell_role") or "text",
        }
        for name in selected
    ]
    list_semantics["row_primary"] = row_primary
    list_semantics["row_secondary"] = row_secondary
    list_semantics["status_field"] = status_field
    list_semantics["metric_fields"] = metric_fields
    list_semantics["batch_policy"] = batch_policy
    semantic_page["list_semantics"] = list_semantics
    data["semantic_page"] = semantic_page
    apply_standard_search_toolbar_labels(data)
