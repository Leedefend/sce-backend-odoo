from __future__ import annotations


def build_native_view_pipeline_payload(*, raw_layout, model, view_type, view_id, permissions, fields, menus, actions):
    return {
        "model": model,
        "view_type": view_type,
        "view_id": view_id,
        "permissions": permissions,
        "layout": raw_layout,
        "fields": fields,
        "menus": menus,
        "actions": actions,
    }
