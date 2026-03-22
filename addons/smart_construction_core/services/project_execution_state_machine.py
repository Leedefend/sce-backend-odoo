# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Dict, Tuple


class ProjectExecutionStateMachine:
    STATES: Tuple[str, ...] = ("ready", "in_progress", "blocked", "done")
    ALLOWED_TRANSITIONS: Dict[str, Tuple[str, ...]] = {
        "ready": ("in_progress",),
        "in_progress": ("done",),
        "blocked": ("ready",),
        "done": (),
    }

    ACTION_REASON = {
        "ready": "EXECUTION_READY_TO_START",
        "in_progress": "EXECUTION_READY_TO_COMPLETE",
        "blocked": "EXECUTION_BLOCKED_REQUIRES_UNBLOCK",
        "done": "EXECUTION_ALREADY_DONE",
    }
    ACTION_LABEL = {
        "ready": "开始执行",
        "in_progress": "完成执行",
        "blocked": "解除阻塞并回到就绪",
        "done": "执行已完成",
    }
    ACTION_HINT = {
        "ready": "当前执行状态为 ready，可推进到 in_progress。",
        "in_progress": "当前执行状态为 in_progress，可推进到 done。",
        "blocked": "当前执行状态为 blocked，仅允许回到 ready。",
        "done": "当前执行状态已为 done，不再允许继续推进。",
    }
    TRANSITION_REASON = {
        ("ready", "in_progress"): "EXECUTION_TRANSITION_READY_TO_IN_PROGRESS",
        ("in_progress", "done"): "EXECUTION_TRANSITION_IN_PROGRESS_TO_DONE",
        ("blocked", "ready"): "EXECUTION_TRANSITION_BLOCKED_TO_READY",
    }

    @classmethod
    def normalize_state(cls, raw) -> str:
        state = str(raw or "").strip().lower()
        return state if state in cls.STATES else "ready"

    @classmethod
    def allowed_targets(cls, state: str) -> Tuple[str, ...]:
        return cls.ALLOWED_TRANSITIONS.get(cls.normalize_state(state), ())

    @classmethod
    def default_target(cls, state: str) -> str:
        allowed = cls.allowed_targets(state)
        return allowed[0] if allowed else cls.normalize_state(state)

    @classmethod
    def can_transition(cls, from_state: str, to_state: str) -> bool:
        return cls.normalize_state(to_state) in cls.allowed_targets(from_state)

    @classmethod
    def transition_reason_code(cls, from_state: str, to_state: str) -> str:
        pair = (cls.normalize_state(from_state), cls.normalize_state(to_state))
        if pair in cls.TRANSITION_REASON:
            return cls.TRANSITION_REASON[pair]
        if cls.normalize_state(from_state) == "done":
            return "EXECUTION_ALREADY_DONE"
        return "EXECUTION_TRANSITION_NOT_ALLOWED"

    @classmethod
    def action_payload(cls, project_id: int, current_state: str) -> dict:
        state = cls.normalize_state(current_state)
        target_state = cls.default_target(state)
        allowed = cls.allowed_targets(state)
        blocked = not bool(allowed)
        return {
            "key": "execution_advance",
            "label": cls.ACTION_LABEL[state],
            "hint": cls.ACTION_HINT[state],
            "intent": "project.execution.advance",
            "params": {
                "project_id": int(project_id or 0),
                "target_state": target_state,
                "source": "project.execution.next_actions",
            },
            "state": "blocked" if blocked else "ready",
            "reason_code": cls.ACTION_REASON[state],
            "current_state": state,
            "target_state": target_state,
            "source": "phase_13_c2",
        }
