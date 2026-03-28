from __future__ import annotations

from .native_view_contract_builder import build_native_view_contract

def build_native_view_pipeline_payload(*, raw_layout, model, view_type, view_id, permissions, fields, menus, actions):
    return build_native_view_contract(
        raw_layout=raw_layout,
        model=model,
        view_type=view_type,
        view_id=view_id,
        permissions=permissions,
        fields=fields,
        menus=menus,
        actions=actions,
    )
