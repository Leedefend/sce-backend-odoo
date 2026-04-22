# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo.addons.smart_construction_core.services.project_state_explain_service import lifecycle_state_label


def build_project_context(project):
    if not project:
        return {
            "project_id": 0,
            "project_name": "",
            "execution_stage": "",
            "execution_stage_label": "",
            "stage": "",
            "stage_label": "",
            "milestone": "",
            "milestone_label": "",
            "project_condition": "",
            "status": "",
        }
    execution_stage = str(getattr(project, "lifecycle_state", "") or "").strip()
    execution_stage_label = lifecycle_state_label(execution_stage, default="")
    milestone = str(getattr(project, "sc_execution_state", "") or "").strip()
    milestone_label = str(getattr(project, "sc_execution_state_label", "") or "").strip()
    project_condition = str(getattr(project, "health_state", "") or getattr(project, "state", "") or "").strip()
    return {
        "project_id": int(getattr(project, "id", 0) or 0),
        "project_name": str(getattr(project, "display_name", "") or getattr(project, "name", "") or "").strip(),
        "execution_stage": execution_stage,
        "execution_stage_label": execution_stage_label or execution_stage,
        "stage": execution_stage,
        "stage_label": execution_stage_label or execution_stage,
        "milestone": milestone,
        "milestone_label": milestone_label or milestone,
        "project_condition": project_condition,
        "status": project_condition,
    }


def attach_project_context_to_scene_payload(data, project):
    payload = dict(data or {})
    project_context = build_project_context(project)
    payload["project_context"] = project_context
    runtime_fetch_hints = payload.get("runtime_fetch_hints")
    blocks = runtime_fetch_hints.get("blocks") if isinstance(runtime_fetch_hints, dict) else None
    if isinstance(blocks, dict):
        for row in blocks.values():
            if not isinstance(row, dict):
                continue
            params = dict(row.get("params") or {})
            params.setdefault("project_id", project_context.get("project_id") or 0)
            params["project_context"] = project_context
            row["params"] = params
    return payload


def attach_project_context_to_runtime_payload(data, project):
    payload = dict(data or {})
    payload["project_context"] = build_project_context(project)
    return payload
