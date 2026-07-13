# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any


def _safe_text(value: Any, fallback: str = "") -> str:
    text = str(value or "").strip()
    if text.lower() in {"undefined", "null"}:
        text = ""
    return text or fallback


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
