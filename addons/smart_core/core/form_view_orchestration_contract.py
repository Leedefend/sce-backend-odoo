# -*- coding: utf-8 -*-
"""Boundary contract for business form-view orchestration.

This module is intentionally declarative for now.  It names the layer that must
own business layout composition before we introduce runtime models/services for
industry templates and customer view profiles.
"""

from __future__ import annotations

from typing import Any

from .source_authority import build_source_authority_contract


SOURCE_KIND = "business_form_view_orchestration_boundary"
SOURCE_AUTHORITIES = (
    "odoo_native_view_parse_snapshot",
    "ir.model.fields",
    "ir.actions.act_window",
    "industry_form_view_template",
    "customer_form_view_profile",
    "ui.form.field.policy",
)
NO_BUSINESS_FACT_AUTHORITY = True

FORM_VIEW_ORCHESTRATION_LAYERS = (
    "model_capability",
    "native_view_parse_snapshot",
    "business_form_orchestration",
    "contract_projection",
    "user_preference",
)

FORM_VIEW_ORCHESTRATOR_INPUTS = (
    "model_capabilities",
    "native_view_parse_snapshot",
    "action_scope",
    "source_view_scope",
    "industry_template",
    "customer_profile",
    "company_overlay",
    "role_profile",
    "field_policy_overlay",
)

FORM_VIEW_ORCHESTRATOR_OUTPUTS = (
    "container_tree",
    "field_order",
    "visible_field_policy",
    "business_action_slots",
    "relation_entry_slots",
    "collaboration_slots",
    "source_trace",
)

PARSER_ALLOWED_OUTPUTS = (
    "native_layout_snapshot",
    "native_field_nodes",
    "native_container_nodes",
    "native_buttons",
    "native_modifiers",
    "native_subviews",
    "native_chatter",
)

PARSER_FORBIDDEN_RESPONSIBILITIES = (
    "industry_template_selection",
    "customer_profile_selection",
    "business_group_renaming",
    "business_field_reordering",
    "business_action_repositioning",
    "user_specific_structure",
)


def source_authority_contract() -> dict[str, Any]:
    return build_source_authority_contract(
        kind=SOURCE_KIND,
        authorities=list(SOURCE_AUTHORITIES),
        no_business_fact_authority=NO_BUSINESS_FACT_AUTHORITY,
        runtime_carrier="form_view_orchestration_contract",
    )
