# -*- coding: utf-8 -*-
from __future__ import annotations


class ProjectTaskStateSupport:
    BUSINESS_STATES = ("draft", "ready", "in_progress", "done", "cancelled")
    OPEN_STATES = ("draft", "ready", "in_progress")
    ACTIVE_STATES = ("ready", "in_progress")
    CLOSED_STATES = ("done", "cancelled")

    @classmethod
    def normalize(cls, raw) -> str:
        state = str(raw or "").strip().lower()
        return state if state in cls.BUSINESS_STATES else "draft"

    @classmethod
    def is_open(cls, raw) -> bool:
        return cls.normalize(raw) in cls.OPEN_STATES

    @classmethod
    def is_active(cls, raw) -> bool:
        return cls.normalize(raw) in cls.ACTIVE_STATES

    @classmethod
    def is_done(cls, raw) -> bool:
        return cls.normalize(raw) == "done"

    @classmethod
    def open_domain(cls):
        return [("sc_state", "not in", list(cls.CLOSED_STATES))]

    @classmethod
    def active_domain(cls):
        return [("sc_state", "in", list(cls.ACTIVE_STATES))]

    @classmethod
    def done_domain(cls):
        return [("sc_state", "=", "done")]

    @classmethod
    def sync_kanban_state(cls, task) -> None:
        if "kanban_state" not in getattr(task, "_fields", {}):
            return
        task_state = cls.normalize(getattr(task, "sc_state", "draft"))
        kanban_state = "done" if task_state == "done" else "normal"
        task.sudo().write({"kanban_state": kanban_state})
