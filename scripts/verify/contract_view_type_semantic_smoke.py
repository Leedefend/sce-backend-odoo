#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import os
from typing import Any

from intent_smoke_utils import require_ok
from python_http_smoke_utils import get_base_url, http_post_json

DEFAULT_REQUIRED_VIEW_TYPES = ("pivot", "graph", "calendar", "gantt", "activity", "dashboard")
DEFAULT_OPTIONAL_VIEW_TYPES: tuple[str, ...] = ()


def _extract_data(payload: dict) -> dict:
    if not isinstance(payload, dict):
        return {}
    data = payload.get("data")
    if isinstance(data, dict):
        return data
    return {}


def _is_list_like(value: Any) -> bool:
    return isinstance(value, (list, tuple))


def _validate_view_block(view_type: str, block: dict) -> str | None:
    if not isinstance(block, dict):
        return "view block missing"
    semantic = block.get(view_type)
    if isinstance(semantic, dict):
        merged = dict(semantic)
        merged.update(block)
        block = merged
    if view_type == "pivot":
        if not _is_list_like(block.get("measures")):
            return "pivot.measures missing"
        if not _is_list_like(block.get("dimensions")):
            return "pivot.dimensions missing"
        return None
    if view_type == "graph":
        graph_type = str(block.get("type") or block.get("type_default") or "").strip()
        if not graph_type:
            return "graph.type missing"
        if (
            "measure" not in block
            and "dimension" not in block
            and not _is_list_like(block.get("measures"))
            and not _is_list_like(block.get("dimensions"))
        ):
            return "graph measure/dimension missing"
        return None
    if view_type in ("calendar", "gantt"):
        if not str(block.get("date_start") or "").strip():
            return f"{view_type}.date_start missing"
        if not str(block.get("date_stop") or "").strip():
            return f"{view_type}.date_stop missing"
        return None
    if view_type == "activity":
        if not str(block.get("field") or "").strip():
            return "activity.field missing"
        return None
    if view_type == "dashboard":
        cards = block.get("cards")
        kpis = block.get("kpis")
        if not _is_list_like(cards):
            return "dashboard.cards missing"
        if not _is_list_like(kpis):
            return "dashboard.kpis missing"
        return None
    return f"{view_type} unsupported"


def _post_intent(intent_url: str, token: str, params: dict) -> tuple[int, dict]:
    return http_post_json(
        intent_url,
        {"intent": "ui.contract", "params": params},
        headers={"Authorization": f"Bearer {token}"},
    )


def _pick_models() -> list[str]:
    raw = os.getenv("VIEW_TYPE_SMOKE_MODELS", "").strip()
    if raw:
        values = [item.strip() for item in raw.split(",")]
        return [item for item in values if item]
    return ["project.task", "project.project", "res.partner", "crm.lead"]


def _pick_view_types() -> tuple[list[str], list[str]]:
    required_raw = os.getenv("VIEW_TYPE_SMOKE_REQUIRED", "").strip()
    optional_raw = os.getenv("VIEW_TYPE_SMOKE_OPTIONAL", "").strip()
    if required_raw:
        required = [item.strip() for item in required_raw.split(",") if item.strip()]
    else:
        required = list(DEFAULT_REQUIRED_VIEW_TYPES)
    if optional_raw:
        optional = [item.strip() for item in optional_raw.split(",") if item.strip()]
    else:
        optional = list(DEFAULT_OPTIONAL_VIEW_TYPES)
    optional = [item for item in optional if item not in required]
    return required, optional


def _pick_min_models() -> int:
    raw = os.getenv("VIEW_TYPE_SMOKE_MIN_MODELS", "").strip()
    if not raw:
        return 1
    try:
        value = int(raw)
    except Exception:
        return 1
    return value if value > 0 else 1


def main() -> None:
    base_url = get_base_url().rstrip("/")
    intent_url = f"{base_url}/api/v1/intent"
    db_name = os.getenv("E2E_DB") or os.getenv("DB_NAME") or ""
    login = os.getenv("E2E_LOGIN") or "admin"
    password = os.getenv("E2E_PASSWORD") or os.getenv("ADMIN_PASSWD") or "admin"

    status, login_resp = http_post_json(
        intent_url,
        {"intent": "login", "params": {"db": db_name, "login": login, "password": password}},
        headers={"X-Anonymous-Intent": "1"},
    )
    require_ok(status, login_resp, "login")
    token = (_extract_data(login_resp)).get("token")
    if not token:
        raise RuntimeError("login response missing token")

    models = _pick_models()
    min_models = _pick_min_models()
    required_view_types, optional_view_types = _pick_view_types()
    all_view_types = [*required_view_types, *optional_view_types]
    debug = os.getenv("VIEW_TYPE_SMOKE_DEBUG", "").strip().lower() in {"1", "true", "yes", "on"}
    resolved: dict[str, list[str]] = {}
    failures: list[str] = []
    warnings: list[str] = []
    for view_type in all_view_types:
        matched_models: list[str] = []
        attempts: list[str] = []
        for model in models:
            status, payload = _post_intent(
                intent_url,
                token,
                {"op": "model", "model": model, "view_type": view_type, "contract_mode": "user"},
            )
            if status >= 400 or not payload.get("ok"):
                attempts.append(f"{model}: status={status}")
                continue
            data = _extract_data(payload)
            views = data.get("views") if isinstance(data.get("views"), dict) else {}
            block = views.get(view_type)
            if not isinstance(block, dict):
                root_block = data.get(view_type)
                block = root_block if isinstance(root_block, dict) else {}
            if debug:
                nested = block.get(view_type) if isinstance(block, dict) else None
                nested_keys = list(nested.keys())[:12] if isinstance(nested, dict) else []
                print(
                    f"[debug] vt={view_type} model={model} views_keys={list(views.keys())[:10]} "
                    f"block_keys={list(block.keys())[:12] if isinstance(block, dict) else []} nested_keys={nested_keys}"
                )
            reason = _validate_view_block(view_type, block if isinstance(block, dict) else {})
            if reason:
                attempts.append(f"{model}: {reason}")
                continue
            matched_models.append(model)
            if len(matched_models) >= min_models:
                break
        resolved[view_type] = matched_models
        if len(matched_models) < min_models:
            detail = f"{view_type} -> matched={len(matched_models)}/{min_models}; {'; '.join(attempts[:4])}"
            if view_type in required_view_types:
                failures.append(detail)
            else:
                warnings.append(detail)

    if failures:
        raise RuntimeError("[contract_view_type_semantic_smoke] FAIL: " + " | ".join(failures))

    print("[contract_view_type_semantic_smoke] PASS")
    print(f"- min_models_per_view: {min_models}")
    print("- required: " + ", ".join(required_view_types))
    print("- optional: " + ", ".join(optional_view_types))
    print("- coverage: " + ", ".join(f"{vt}:{'|'.join(resolved.get(vt, [])) or '-'}" for vt in all_view_types))
    if warnings:
        print("- warnings:")
        for item in warnings:
            print(f"  * {item}")


if __name__ == "__main__":
    main()
