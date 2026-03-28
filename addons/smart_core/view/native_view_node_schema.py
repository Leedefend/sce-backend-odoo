from __future__ import annotations


def build_field_node(
    *,
    name,
    string=None,
    widget=None,
    optional=None,
    operator=None,
    filter_domain=None,
    options=None,
    invisible=None,
    required=None,
    readonly=None,
    placeholder=None,
    visible=True,
    editable=True,
    semantic_role=None,
    source_view=None,
    semantic_meta=None,
):
    return {
        "kind": "field",
        "name": name,
        "string": string,
        "widget": widget,
        "optional": optional,
        "operator": operator,
        "filter_domain": filter_domain,
        "options": options,
        "invisible": invisible,
        "required": required,
        "readonly": readonly,
        "placeholder": placeholder,
        "visible": visible,
        "editable": editable,
        "semantic_role": semantic_role,
        "source_view": source_view,
        "semantic_meta": semantic_meta if semantic_meta is not None else {},
    }


def build_action_node(
    *,
    name,
    string=None,
    action_type=None,
    context=None,
    icon=None,
    groups=None,
    hotkey=None,
    invisible=None,
    visible=True,
    semantic_role=None,
    source_view=None,
    semantic_meta=None,
):
    return {
        "kind": "action",
        "name": name,
        "string": string,
        "type": action_type,
        "context": context if context is not None else {},
        "icon": icon,
        "groups": groups if groups is not None else [],
        "hotkey": hotkey,
        "invisible": invisible,
        "visible": visible,
        "semantic_role": semantic_role,
        "source_view": source_view,
        "semantic_meta": semantic_meta if semantic_meta is not None else {},
    }


def build_filter_node(*, name, string=None, domain=None, context=None, semantic_role=None, source_view=None, semantic_meta=None):
    return {
        "kind": "filter",
        "name": name,
        "string": string,
        "domain": domain,
        "context": context if context is not None else {},
        "semantic_role": semantic_role,
        "source_view": source_view,
        "semantic_meta": semantic_meta if semantic_meta is not None else {},
    }


def build_group_by_node(*, name, string=None, group_by=None, context=None, semantic_role=None, source_view=None, semantic_meta=None):
    return {
        "kind": "group_by",
        "name": name,
        "string": string,
        "group_by": group_by,
        "context": context if context is not None else {},
        "semantic_role": semantic_role,
        "source_view": source_view,
        "semantic_meta": semantic_meta if semantic_meta is not None else {},
    }


def build_searchpanel_node(*, name, string=None, select=None, icon=None, semantic_role=None, source_view=None, semantic_meta=None):
    return {
        "kind": "searchpanel",
        "name": name,
        "string": string,
        "select": select,
        "icon": icon,
        "semantic_role": semantic_role,
        "source_view": source_view,
        "semantic_meta": semantic_meta if semantic_meta is not None else {},
    }


def build_group_node(*, fields=None, sub_groups=None, attributes=None, semantic_role=None, source_view=None, semantic_meta=None):
    return {
        "kind": "group",
        "fields": fields if fields is not None else [],
        "sub_groups": sub_groups if sub_groups is not None else [],
        "attributes": attributes if attributes is not None else {},
        "semantic_role": semantic_role,
        "source_view": source_view,
        "semantic_meta": semantic_meta if semantic_meta is not None else {},
    }


def build_page_node(*, title=None, groups=None, visible=True, semantic_role=None, source_view=None, semantic_meta=None):
    return {
        "kind": "page",
        "title": title,
        "groups": groups if groups is not None else [],
        "visible": visible,
        "semantic_role": semantic_role,
        "source_view": source_view,
        "semantic_meta": semantic_meta if semantic_meta is not None else {},
    }


def build_notebook_node(*, pages=None, semantic_role=None, source_view=None, semantic_meta=None):
    return {
        "kind": "notebook",
        "pages": pages if pages is not None else [],
        "semantic_role": semantic_role,
        "source_view": source_view,
        "semantic_meta": semantic_meta if semantic_meta is not None else {},
    }


def build_ribbon_node(*, title=None, bg_color=None, invisible=None, semantic_role=None, source_view=None, semantic_meta=None):
    return {
        "kind": "ribbon",
        "title": title,
        "bg_color": bg_color,
        "invisible": invisible,
        "semantic_role": semantic_role,
        "source_view": source_view,
        "semantic_meta": semantic_meta if semantic_meta is not None else {},
    }


def build_chatter_node(*, followers=None, activities=None, messages=None, semantic_role=None, source_view=None, semantic_meta=None):
    return {
        "kind": "chatter",
        "followers": followers,
        "activities": activities,
        "messages": messages,
        "semantic_role": semantic_role,
        "source_view": source_view,
        "semantic_meta": semantic_meta if semantic_meta is not None else {},
    }


def build_view_semantics(*, source_view, capability_flags=None, semantic_meta=None):
    return {
        "kind": "view_semantics",
        "source_view": source_view,
        "capability_flags": capability_flags if capability_flags is not None else {},
        "semantic_meta": semantic_meta if semantic_meta is not None else {},
    }
