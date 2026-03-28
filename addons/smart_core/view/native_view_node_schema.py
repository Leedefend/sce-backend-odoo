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
):
    return {
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
):
    return {
        "name": name,
        "string": string,
        "type": action_type,
        "context": context if context is not None else {},
        "icon": icon,
        "groups": groups if groups is not None else [],
        "hotkey": hotkey,
        "invisible": invisible,
        "visible": visible,
    }


def build_filter_node(*, name, string=None, domain=None, context=None):
    return {
        "name": name,
        "string": string,
        "domain": domain,
        "context": context if context is not None else {},
    }


def build_group_by_node(*, name, string=None, group_by=None, context=None):
    return {
        "name": name,
        "string": string,
        "group_by": group_by,
        "context": context if context is not None else {},
    }


def build_searchpanel_node(*, name, string=None, select=None, icon=None):
    return {
        "name": name,
        "string": string,
        "select": select,
        "icon": icon,
    }
