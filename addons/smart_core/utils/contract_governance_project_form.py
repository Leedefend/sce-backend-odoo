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


def build_project_lifecycle_summary(data: dict) -> None:
    workflow = _as_dict(data.get("workflow"))
    states = workflow.get("states")
    transitions = workflow.get("transitions")
    if not isinstance(states, list):
        states = []
    if not isinstance(transitions, list):
        transitions = []

    state_keys = []
    for row in states:
        if not isinstance(row, dict):
            continue
        key = _safe_text(row.get("key"))
        label = _safe_text(row.get("label"), key)
        if not key:
            continue
        state_keys.append({"key": key, "label": label})

    transition_rows = []
    for row in transitions:
        if not isinstance(row, dict):
            continue
        trigger = _as_dict(row.get("trigger"))
        label = _safe_text(trigger.get("label") or trigger.get("name"))
        if not label:
            continue
        transition_rows.append({
            "label": label,
            "kind": _safe_text(trigger.get("kind")),
        })

    data["lifecycle"] = {
        "state_field": _safe_text(workflow.get("state_field"), "stage_id"),
        "current_state": "",
        "steps": state_keys,
        "allowed_transitions": transition_rows[:8],
        "blockers": [],
        "progress_percent": 0 if state_keys else None,
    }
    data["workflow_surface"] = {
        "owner_layer": "business_fact",
        "source": "contract_governance.workflow_facts",
        "state_field": _safe_text(workflow.get("state_field"), "stage_id"),
        "states": state_keys,
        "transitions": transitions[:8],
        "highlight_states": workflow.get("highlight_states") if isinstance(workflow.get("highlight_states"), list) else [],
    }
