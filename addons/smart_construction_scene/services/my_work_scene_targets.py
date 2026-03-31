# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, Iterable, List


DEFAULT_MY_WORK_SCENE_KEY = "projects.list"


def resolve_my_work_scene_key(
    *,
    explicit_scene_key: str = "",
    model_name: str = "",
    source_key: str = "",
    section_key: str = "",
) -> str:
    explicit = str(explicit_scene_key or "").strip()
    if explicit:
        return explicit

    normalized_model = str(model_name or "").strip()
    normalized_source = str(source_key or "").strip()
    normalized_section = str(section_key or "").strip().lower()

    model_map = {
        "project.project": "projects.list",
        "project.task": "projects.list",
        "payment.request": "finance.payment_requests",
        "construction.contract": "contracts.list",
        "sc.settlement.order": "settlement",
        "sc.workflow.instance": "projects.list",
        "sale.order": "contracts.list",
        "account.move": "finance.vouchers.list",
    }
    if normalized_model in model_map:
        return model_map[normalized_model]

    source_map = {
        "project.task": "projects.list",
        "project.project": "projects.list",
        "project.risk": "projects.list",
        "mail.activity": "projects.list",
        "mail.message": "projects.list",
        "mail.followers": "projects.list",
        "tier.review": "projects.list",
        "sc.workflow.workitem": "projects.list",
    }
    if normalized_source in source_map:
        return source_map[normalized_source]

    if normalized_section in {"todo", "owned", "mentions", "following"}:
        return DEFAULT_MY_WORK_SCENE_KEY
    return DEFAULT_MY_WORK_SCENE_KEY


def build_my_work_target(
    *,
    model_name: str = "",
    record_id: int = 0,
    action_id: int = 0,
    menu_id: int = 0,
    explicit_scene_key: str = "",
    source_key: str = "",
    section_key: str = "",
) -> Dict[str, Any]:
    model = str(model_name or "").strip()
    rid = int(record_id or 0)
    scene_key = resolve_my_work_scene_key(
        explicit_scene_key=explicit_scene_key,
        model_name=model,
        source_key=source_key,
        section_key=section_key,
    )
    target = {
        "kind": "record" if model and rid else "scene",
        "scene_key": scene_key,
    }
    if model:
        target["model"] = model
    if rid:
        target["record_id"] = rid
    if int(action_id or 0) > 0:
        target["action_id"] = int(action_id)
    if int(menu_id or 0) > 0:
        target["menu_id"] = int(menu_id)
    return target


def build_my_work_section_rows(section_labels: Dict[str, str]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for key in ("todo", "owned", "mentions", "following"):
        rows.append(
            {
                "key": key,
                "label": str((section_labels or {}).get(key) or key),
                "scene_key": resolve_my_work_scene_key(section_key=key),
            }
        )
    return rows


def build_my_work_summary_rows(summary_items: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for item in list(summary_items or []):
        if not isinstance(item, dict):
            continue
        row = dict(item)
        row["scene_key"] = resolve_my_work_scene_key(
            explicit_scene_key=str(row.get("scene_key") or ""),
            source_key=str(row.get("source") or ""),
            section_key=str(row.get("key") or ""),
        )
        rows.append(row)
    return rows
