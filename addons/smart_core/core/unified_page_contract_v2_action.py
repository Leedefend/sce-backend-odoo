# -*- coding: utf-8 -*-
from __future__ import annotations

from copy import deepcopy
from hashlib import sha1
from typing import Any

from .source_authority import build_source_authority_contract

CONTRACT_VERSION = "2.1.0"
SOURCE_KIND = "unified_page_contract_v2_action_projection"
SOURCE_AUTHORITIES = ("ui_action_contract", "button_contract", "action_rule_schema")
NO_BUSINESS_FACT_AUTHORITY = True


def source_authority_contract() -> dict[str, Any]:
    return build_source_authority_contract(
        kind=SOURCE_KIND,
        authorities=SOURCE_AUTHORITIES,
        no_business_fact_authority=NO_BUSINESS_FACT_AUTHORITY,
        runtime_carrier="unified_page_contract_v2_action",
    )

TRIGGER_TYPES = {"change", "click", "select", "refresh", "add", "delete", "confirm", "submit", "blur", "focus"}
DISPATCH_MODES = {"local", "server", "serverDebounced", "serverBlocking"}
REFRESH_MODES = {"none", "partial", "full"}


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _text(value: Any, default: str = "") -> str:
    text = str(value or "").strip()
    return text or default


def _stable_id(value: Any, fallback: str) -> str:
    raw = _text(value, fallback)
    out = []
    for char in raw:
        if char.isalnum() or char in "_.:-":
            out.append(char)
        elif char in " /":
            out.append(".")
    normalized = "".join(out).strip(".")
    if not normalized:
        normalized = fallback
    if not normalized[0].isalpha():
        normalized = f"id.{normalized}"
    return normalized


def _fingerprint(value: Any) -> str:
    import json

    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    return sha1(payload.encode("utf-8")).hexdigest()[:12]


def _field_widget_id(field_name: Any) -> str:
    return f"field.{_stable_id(field_name, 'field')}"


def _action_id(action_key: Any) -> str:
    raw = _stable_id(action_key, "action")
    return raw if raw.startswith("action.") else f"action.{raw}"


def _normalize_trigger(raw: Any, fallback: str = "click") -> str:
    value = _text(raw, fallback)
    return value if value in TRIGGER_TYPES else fallback


def _normalize_dispatch(raw: Any, fallback: str = "server") -> str:
    value = _text(raw, fallback)
    return value if value in DISPATCH_MODES else fallback


def _normalize_refresh(raw: Any, fallback: str = "partial") -> str:
    value = _text(raw, fallback)
    return value if value in REFRESH_MODES else fallback


def _target_scope_for_intent(intent: str, fallback: str = "page") -> str:
    if intent in {"api.data", "record.search"}:
        return "dataSource"
    if intent in {"api.onchange"}:
        return "widget"
    if intent in {"runtime.patch"}:
        return "runtime"
    return fallback


def build_action_contract_v2(source_contract: dict[str, Any]) -> dict[str, Any]:
    source = _dict(source_contract)
    action_contract = {"actionRuleList": [], "dependencyGraph": {}}
    _append_onchange_rules(action_contract, source)
    _append_action_schema_rules(action_contract, source)
    _append_policy_action_rules(action_contract, source)
    _append_standard_form_rules(action_contract, source)
    _dedupe_rules(action_contract)
    return action_contract


def build_action_partial_update_v2(
    action_result: dict[str, Any],
    *,
    action_id: str,
    request_id: str = "request.upc.v2.action.patch",
) -> dict[str, Any]:
    source = _dict(action_result)
    fp = _fingerprint(source)
    return {
        "updateType": "partial",
        "layoutPatch": deepcopy(_dict(source.get("layoutPatch") or source.get("updateLayout"))),
        "statusPatch": deepcopy(_dict(source.get("statusPatch") or source.get("updateStatus"))),
        "dataPatch": deepcopy(_dict(source.get("dataPatch") or source.get("updateData"))),
        "runtimePatch": deepcopy(_dict(source.get("runtimePatch") or source.get("updateRuntime"))),
        "meta": {
            "contractVersion": CONTRACT_VERSION,
            "etag": f"upc-v2-action-patch-{fp}",
            "snapshotId": f"snapshot.upc.v2.action.patch.{fp}",
            "traceId": f"trace.upc.v2.action.patch.{fp}",
            "requestId": _stable_id(request_id, f"request.upc.v2.action.patch.{fp}"),
            "actionId": _action_id(action_id),
            "sourceType": "api.onchange",
            "sourceKind": SOURCE_KIND,
        },
    }


def _append_rule(
    action_contract: dict[str, Any],
    *,
    action_id: str,
    trigger_type: str,
    source_widget_id: str,
    target_ids: list[str] | None = None,
    dispatch_mode: str = "server",
    target_scope: str = "page",
    refresh_mode: str = "partial",
) -> None:
    normalized_action_id = _action_id(action_id)
    rule = {
        "actionId": normalized_action_id,
        "triggerType": _normalize_trigger(trigger_type),
        "sourceWidgetId": _stable_id(source_widget_id, "page.root"),
        "targetIds": [_stable_id(item, "target") for item in (target_ids or []) if _text(item)],
        "dispatchMode": _normalize_dispatch(dispatch_mode),
        "targetScope": target_scope if target_scope in {"widget", "container", "page", "dataSource", "runtime"} else "page",
        "refreshMode": _normalize_refresh(refresh_mode),
    }
    action_contract["actionRuleList"].append(rule)
    graph = action_contract.setdefault("dependencyGraph", {})
    graph.setdefault(rule["sourceWidgetId"], [])
    if normalized_action_id not in graph[rule["sourceWidgetId"]]:
        graph[rule["sourceWidgetId"]].append(normalized_action_id)


def _append_onchange_rules(action_contract: dict[str, Any], source: dict[str, Any]) -> None:
    onchange = source.get("onchange")
    if isinstance(onchange, dict):
        rows = [{"field": key, **_dict(value)} for key, value in onchange.items()]
    else:
        rows = _list(source.get("onchange_fields") or source.get("changed_fields"))
    for item in rows:
        if isinstance(item, str):
            field_name = item
            targets: list[str] = []
            debounce_ms = 300
        elif isinstance(item, dict):
            field_name = _text(item.get("field") or item.get("fieldCode") or item.get("source"))
            targets = [_field_widget_id(target) for target in _list(item.get("targets") or item.get("target_fields"))]
            raw_debounce = item.get("debounce_ms")
            if raw_debounce is None:
                raw_debounce = item.get("debounceMs")
            debounce_ms = int(300 if raw_debounce is None else raw_debounce)
        else:
            continue
        if not field_name:
            continue
        dispatch = "serverDebounced" if debounce_ms > 0 else "server"
        _append_rule(
            action_contract,
            action_id=f"{field_name}.change",
            trigger_type="change",
            source_widget_id=_field_widget_id(field_name),
            target_ids=targets,
            dispatch_mode=dispatch,
            target_scope="widget",
            refresh_mode="partial",
        )


def _append_action_schema_rules(action_contract: dict[str, Any], source: dict[str, Any]) -> None:
    actions = _dict(_dict(source.get("action_schema")).get("actions"))
    for key, row in actions.items():
        if not isinstance(row, dict):
            row = {}
        intent = _text(row.get("intent"), "ui.contract")
        _append_rule(
            action_contract,
            action_id=key,
            trigger_type=_normalize_trigger(row.get("trigger"), "click"),
            source_widget_id=_text(row.get("sourceWidgetId"), "page.root"),
            target_ids=[_text(row.get("target", {}).get("scene_key"))] if isinstance(row.get("target"), dict) else [],
            dispatch_mode=_normalize_dispatch(row.get("dispatchMode"), "server"),
            target_scope=_target_scope_for_intent(intent),
            refresh_mode=_normalize_refresh(row.get("refreshMode"), "partial"),
        )


def _append_policy_action_rules(action_contract: dict[str, Any], source: dict[str, Any]) -> None:
    for key, policy in _dict(source.get("action_policies")).items():
        row = _dict(policy)
        if row.get("visible") is False:
            continue
        _append_rule(
            action_contract,
            action_id=key,
            trigger_type=_normalize_trigger(row.get("triggerType") or row.get("trigger"), "click"),
            source_widget_id=_text(row.get("sourceWidgetId"), "page.root"),
            target_ids=[_text(item) for item in _list(row.get("targetIds") or row.get("targets"))],
            dispatch_mode=_normalize_dispatch(row.get("dispatchMode"), "serverBlocking" if row.get("enabled") is False else "server"),
            target_scope=_text(row.get("targetScope"), "page"),
            refresh_mode=_normalize_refresh(row.get("refreshMode"), "partial"),
        )


def _append_standard_form_rules(action_contract: dict[str, Any], source: dict[str, Any]) -> None:
    form_actions = _dict(source.get("form_actions"))
    if form_actions.get("save") is True:
        _append_rule(
            action_contract,
            action_id="form.save",
            trigger_type="submit",
            source_widget_id="page.root",
            target_ids=["page.root"],
            dispatch_mode="serverBlocking",
            target_scope="page",
            refresh_mode="partial",
        )
    if form_actions.get("validate") is True:
        _append_rule(
            action_contract,
            action_id="form.validate",
            trigger_type="confirm",
            source_widget_id="page.root",
            target_ids=["page.root"],
            dispatch_mode="server",
            target_scope="page",
            refresh_mode="none",
        )
    delete_policy = _dict(source.get("delete_policy"))
    if delete_policy.get("allowed") is True:
        _append_rule(
            action_contract,
            action_id="record.delete",
            trigger_type="delete",
            source_widget_id="page.root",
            target_ids=["page.root"],
            dispatch_mode="serverBlocking",
            target_scope="page",
            refresh_mode="partial",
        )
    chain_actions = _list(source.get("chain_actions"))
    for chain in chain_actions:
        if not isinstance(chain, dict):
            continue
        source_id = _action_id(chain.get("source") or chain.get("actionId"))
        target_ids = [_action_id(item) for item in _list(chain.get("targets") or chain.get("targetActions"))]
        if not source_id or not target_ids:
            continue
        graph = action_contract.setdefault("dependencyGraph", {})
        graph.setdefault(source_id, [])
        for target_id in target_ids:
            if target_id not in graph[source_id]:
                graph[source_id].append(target_id)


def _dedupe_rules(action_contract: dict[str, Any]) -> None:
    seen: set[str] = set()
    deduped: list[dict[str, Any]] = []
    for rule in action_contract.get("actionRuleList") or []:
        if not isinstance(rule, dict):
            continue
        action_id = _text(rule.get("actionId"))
        if not action_id or action_id in seen:
            continue
        seen.add(action_id)
        deduped.append(rule)
    action_contract["actionRuleList"] = sorted(deduped, key=lambda row: row["actionId"])
    graph = _dict(action_contract.get("dependencyGraph"))
    action_contract["dependencyGraph"] = {
        key: sorted(set(_list(value)))
        for key, value in sorted(graph.items())
    }
