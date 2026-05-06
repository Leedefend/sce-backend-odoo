# -*- coding: utf-8 -*-
from __future__ import annotations

from copy import deepcopy
from typing import Any

from .source_authority import build_source_authority_contract

PATCH_OPERATIONS = ("replace", "merge", "append", "remove", "reorder", "invalidate")
SOURCE_KIND = "unified_page_contract_v2_runtime_projection"
SOURCE_AUTHORITIES = ("unified_page_contract_v2", "runtime_contract_schema")
NO_BUSINESS_FACT_AUTHORITY = True


def source_authority_contract() -> dict[str, Any]:
    return build_source_authority_contract(
        kind=SOURCE_KIND,
        authorities=SOURCE_AUTHORITIES,
        no_business_fact_authority=NO_BUSINESS_FACT_AUTHORITY,
        runtime_carrier="unified_page_contract_v2_runtime",
    )

FORBIDDEN_RUNTIME_KEYS = {
    "script",
    "scripts",
    "function",
    "functions",
    "eval",
    "expression",
    "expressions",
    "jsonLogic",
    "workflowDsl",
    "bpmn",
    "loop",
    "loops",
    "componentCode",
}


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _text(value: Any, default: str = "") -> str:
    text = str(value or "").strip()
    return text or default


def _count_containers(rows: Any) -> int:
    total = 0
    for row in _list(rows):
        if not isinstance(row, dict):
            continue
        total += 1
        total += _count_containers(row.get("children"))
    return total


def _count_widgets(rows: Any) -> int:
    total = 0
    for row in _list(rows):
        if not isinstance(row, dict):
            continue
        total += len(_list(row.get("widgetList")))
        total += _count_widgets(row.get("children"))
    return total


def _complexity_budget(contract: dict[str, Any]) -> dict[str, Any]:
    layout = _dict(contract.get("layoutContract"))
    status = _dict(contract.get("statusContract"))
    action = _dict(contract.get("actionContract"))
    data = _dict(contract.get("dataContract"))
    containers = _count_containers(layout.get("containerTree"))
    widgets = _count_widgets(layout.get("containerTree"))
    actions = len(_list(action.get("actionRuleList")))
    selector_status = len(_list(status.get("selectorStatus")))
    data_sources = len(_dict(data.get("dataSource")))
    score = containers + widgets + (actions * 2) + selector_status + data_sources
    return {
        "containers": containers,
        "widgets": widgets,
        "actions": actions,
        "selectorStatus": selector_status,
        "dataSources": data_sources,
        "score": score,
        "level": "high" if score >= 120 else "medium" if score >= 40 else "low",
        "maxScore": 200,
    }


def build_runtime_contract_v2(contract: dict[str, Any], *, overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    source = _dict(contract)
    current = _dict(source.get("runtimeContract"))
    override = _dict(overrides)
    patch_ops = override.get("patchOperations") or current.get("patchOperations") or list(PATCH_OPERATIONS)
    normalized_ops = [op for op in patch_ops if op in PATCH_OPERATIONS]
    runtime = {
        "patchStrategy": _text(override.get("patchStrategy") or current.get("patchStrategy"), "incremental"),
        "cachePolicy": _text(override.get("cachePolicy") or current.get("cachePolicy"), "etag"),
        "optimistic": bool(override.get("optimistic") if "optimistic" in override else current.get("optimistic", False)),
        "lazyContainer": deepcopy(_list(override.get("lazyContainer") or current.get("lazyContainer"))),
        "virtualization": deepcopy(_dict(override.get("virtualization") or current.get("virtualization"))),
        "retryPolicy": deepcopy(_dict(override.get("retryPolicy") or current.get("retryPolicy") or {"maxRetries": 1})),
        "renderStrategy": _text(override.get("renderStrategy") or current.get("renderStrategy"), "sync"),
        "hydration": deepcopy(_dict(override.get("hydration") or current.get("hydration") or {"mode": "eager"})),
        "patchOperations": normalized_ops,
        "tracePolicy": deepcopy(_dict(override.get("tracePolicy") or current.get("tracePolicy") or {"required": True})),
        "complexityBudget": _complexity_budget(source),
        "aiEnvelope": _normalize_ai_envelope(override.get("aiEnvelope") or current.get("aiEnvelope")),
    }
    if runtime["patchStrategy"] not in {"incremental", "full"}:
        runtime["patchStrategy"] = "incremental"
    if runtime["cachePolicy"] not in {"none", "etag", "snapshot"}:
        runtime["cachePolicy"] = "etag"
    if runtime["renderStrategy"] not in {"sync", "scheduled", "virtualized"}:
        runtime["renderStrategy"] = "sync"
    return runtime


def _normalize_ai_envelope(value: Any) -> dict[str, Any]:
    row = _dict(value)
    if not row:
        return {"mode": "suggestion", "executable": False, "allowed": False}
    return {
        "mode": "suggestion",
        "executable": False,
        "allowed": bool(row.get("allowed") is True),
        "capabilities": [str(item) for item in _list(row.get("capabilities")) if str(item).strip()],
    }


def find_runtime_guard_issues(contract: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    runtime = _dict(contract.get("runtimeContract"))
    meta = _dict(contract.get("meta"))
    action = _dict(contract.get("actionContract"))
    layout = _dict(contract.get("layoutContract"))
    status = _dict(contract.get("statusContract"))
    if not runtime:
        issues.append("runtimeContract is required")
    for key in ("etag", "snapshotId", "traceId", "requestId"):
        if not _text(meta.get(key)):
            issues.append(f"meta.{key} is required")
    ops = _list(runtime.get("patchOperations"))
    unknown_ops = [op for op in ops if op not in PATCH_OPERATIONS]
    if unknown_ops:
        issues.append(f"unknown patch operations: {unknown_ops}")
    ai = _dict(runtime.get("aiEnvelope"))
    if ai.get("executable") is True or _text(ai.get("mode")) not in {"", "suggestion"}:
        issues.append("aiEnvelope must be suggestion-only and non-executable")
    for path, node in _walk(runtime):
        if isinstance(node, dict):
            for key in node:
                if key in FORBIDDEN_RUNTIME_KEYS:
                    issues.append(f"forbidden runtime key at {path}.{key}")
    graph = _dict(action.get("dependencyGraph"))
    for source, targets in graph.items():
        if not isinstance(targets, list):
            issues.append(f"dependencyGraph.{source} must be a list")
        for target in _list(targets):
            if isinstance(target, dict):
                issues.append(f"dependencyGraph.{source} contains executable object edge")
    registry = _dict(layout.get("componentRegistry"))
    if not registry:
        issues.append("layoutContract.componentRegistry is required for runtime adapter resolution")
    for row in _list(status.get("selectorStatus")):
        if isinstance(row, dict) and not _text(row.get("selector")):
            issues.append("selectorStatus row missing selector")
    return issues


def _walk(value: Any, path: str = "$"):
    yield path, value
    if isinstance(value, dict):
        for key, child in value.items():
            yield from _walk(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk(child, f"{path}[{index}]")
