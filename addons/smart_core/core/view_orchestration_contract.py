# -*- coding: utf-8 -*-
"""Boundary contract for business view orchestration.

The boundary covers every Odoo view surface.  Form layout is only one
specialized consumer; it must not define the platform-wide orchestration model.
"""

from __future__ import annotations

from typing import Any

from .source_authority import build_source_authority_contract


SOURCE_KIND = "business_view_orchestration_boundary"
SOURCE_AUTHORITIES = (
    "odoo_native_view_parse_snapshot",
    "ir.model.fields",
    "ir.actions.act_window",
    "ir.ui.view",
    "ui.business.config.contract",
    "ui.business.config.contract.version",
    "ui.form.field.policy",
)
NO_BUSINESS_FACT_AUTHORITY = True

VIEW_ORCHESTRATION_LAYERS = (
    "model_capability",
    "native_view_parse_snapshot",
    "business_view_orchestration",
    "contract_projection",
    "user_preference",
)

SUPPORTED_VIEW_TYPES = (
    "form",
    "tree",
    "list",
    "kanban",
    "search",
    "pivot",
    "graph",
    "calendar",
    "gantt",
    "activity",
    "dashboard",
)

VIEW_ORCHESTRATOR_INPUTS = (
    "model_capabilities",
    "native_view_parse_snapshot",
    "view_type",
    "action_scope",
    "source_view_scope",
    "business_config_contract",
    "business_config_version",
    "business_config_rules",
    "legacy_field_policy_overlay",
)

VIEW_ORCHESTRATOR_OUTPUTS = (
    "view_type",
    "layout_slots",
    "field_order",
    "visible_field_policy",
    "business_action_slots",
    "relation_entry_slots",
    "aggregation_slots",
    "search_filter_slots",
    "grouping_slots",
    "collaboration_slots",
    "source_trace",
)

VIEW_TYPE_OUTPUT_SURFACES = {
    "form": ("container_tree", "field_order", "business_action_slots", "relation_entry_slots", "collaboration_slots"),
    "tree": ("columns", "column_order", "row_actions", "aggregation_slots"),
    "list": ("columns", "column_order", "row_actions", "aggregation_slots"),
    "kanban": ("card_layout", "grouping_slots", "quick_actions"),
    "search": ("filter_slots", "group_by_slots", "favorite_slots"),
    "pivot": ("measure_slots", "row_dimension_slots", "column_dimension_slots"),
    "graph": ("measure_slots", "dimension_slots", "chart_policy"),
    "calendar": ("date_slots", "resource_slots", "color_slots"),
    "gantt": ("date_slots", "dependency_slots", "resource_slots"),
    "activity": ("activity_type_slots", "deadline_slots", "assignee_slots"),
    "dashboard": ("metric_slots", "chart_slots", "navigation_slots"),
}

PARSER_ALLOWED_OUTPUTS = (
    "native_view_type",
    "native_arch_snapshot",
    "native_field_nodes",
    "native_container_nodes",
    "native_buttons",
    "native_modifiers",
    "native_columns",
    "native_filters",
    "native_group_bys",
    "native_measures",
    "native_templates",
    "native_subviews",
    "native_chatter",
)

PARSER_FORBIDDEN_RESPONSIBILITIES = (
    "business_config_selection",
    "business_config_rule_evaluation",
    "business_section_naming",
    "business_field_reordering",
    "business_column_reordering",
    "business_filter_prioritization",
    "business_measure_selection",
    "business_action_repositioning",
    "user_specific_structure",
)


def source_authority_contract() -> dict[str, Any]:
    return build_source_authority_contract(
        kind=SOURCE_KIND,
        authorities=list(SOURCE_AUTHORITIES),
        no_business_fact_authority=NO_BUSINESS_FACT_AUTHORITY,
        runtime_carrier="view_orchestration_contract",
    )
