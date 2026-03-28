from __future__ import annotations

from .native_view_parser_registry import normalize_view_type


NATIVE_VIEW_CONTRACT_VERSION = "native_view.v1"


def build_native_view_contract(
    *,
    raw_layout,
    model,
    view_type,
    view_id,
    permissions,
    fields,
    menus,
    actions,
):
    normalized_view_type = normalize_view_type(view_type)

    parser_contract = {
        "version": NATIVE_VIEW_CONTRACT_VERSION,
        "view_type": normalized_view_type,
        "layout": {
            "kind": normalized_view_type,
            "body": raw_layout,
        },
        "metadata": {
            "model": model,
            "view_id": view_id,
        },
    }

    return {
        "model": model,
        "view_type": view_type,
        "view_id": view_id,
        "permissions": permissions,
        "layout": raw_layout,
        "fields": fields,
        "menus": menus,
        "actions": actions,
        "contract_version": NATIVE_VIEW_CONTRACT_VERSION,
        "parser_contract": parser_contract,
    }
