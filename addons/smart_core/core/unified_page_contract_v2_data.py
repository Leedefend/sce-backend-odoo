# -*- coding: utf-8 -*-
from __future__ import annotations

from copy import deepcopy
from typing import Any

from .source_authority import build_source_authority_contract

ALLOWED_CACHE_POLICIES = {"none", "etag", "snapshot"}
SOURCE_KIND = "unified_page_contract_v2_data_projection"
SOURCE_AUTHORITIES = ("record_payload", "list_payload", "relation_payload", "data_source_schema")
NO_BUSINESS_FACT_AUTHORITY = True


def source_authority_contract() -> dict[str, Any]:
    return build_source_authority_contract(
        kind=SOURCE_KIND,
        authorities=SOURCE_AUTHORITIES,
        no_business_fact_authority=NO_BUSINESS_FACT_AUTHORITY,
        runtime_carrier="unified_page_contract_v2_data",
    )

ALLOWED_CONSISTENCY = {"strong", "eventual"}
FORBIDDEN_DATASOURCE_KEYS = {
    "sql",
    "raw_sql",
    "domain",
    "permission",
    "permissions",
    "acl",
    "record_rule",
    "recordRules",
    "sudo",
}


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _text(value: Any, default: str = "") -> str:
    text = str(value or "").strip()
    return text or default


def _stable_key(value: Any, fallback: str) -> str:
    raw = _text(value, fallback)
    out = []
    for char in raw:
        if char.isalnum() or char in "_.:-":
            out.append(char)
        elif char in " /":
            out.append("_")
    normalized = "".join(out).strip("._:-")
    if not normalized:
        normalized = fallback
    if not normalized[0].isalpha():
        normalized = f"data_{normalized}"
    return normalized


def build_data_contract_v2(source_payload: dict[str, Any]) -> dict[str, Any]:
    source = _dict(source_payload)
    data_contract = {
        "mainData": _resolve_main_data(source),
        "tableRows": _resolve_table_rows(source),
        "relationRows": _resolve_relation_rows(source),
        "treeData": _resolve_tree_data(source),
        "ganttData": _resolve_gantt_data(source),
        "dictData": _resolve_dict_data(source),
        "pagination": _normalize_mapping(source.get("pagination")),
        "dataSource": _resolve_data_source(source),
        "dataMeta": _resolve_data_meta(source),
    }
    return data_contract


def _resolve_main_data(source: dict[str, Any]) -> dict[str, Any]:
    for key in ("mainData", "main_data", "record", "values", "formData"):
        row = source.get(key)
        if isinstance(row, dict):
            return deepcopy(row)
    return {}


def _resolve_table_rows(source: dict[str, Any]) -> dict[str, list[Any]]:
    rows = source.get("tableRows")
    if isinstance(rows, dict):
        return {str(_stable_key(key, "table_rows")): deepcopy(_list(value)) for key, value in rows.items()}
    for key in ("rows", "list_rows", "table_rows", "records"):
        value = source.get(key)
        if isinstance(value, list):
            data_key = _stable_key(source.get("data_key") or source.get("dataKey"), "rows")
            return {data_key: deepcopy(value)}
    return {}


def _resolve_relation_rows(source: dict[str, Any]) -> dict[str, list[Any]]:
    rows = source.get("relationRows") or source.get("relation_rows")
    if isinstance(rows, dict):
        return {str(_stable_key(key, "relation_rows")): deepcopy(_list(value)) for key, value in rows.items()}
    line_patches = source.get("line_patches")
    if isinstance(line_patches, list):
        return {"line_patches": deepcopy(line_patches)}
    return {}


def _resolve_tree_data(source: dict[str, Any]) -> dict[str, Any]:
    rows = source.get("treeData") or source.get("tree_data")
    if isinstance(rows, dict):
        return deepcopy(rows)
    if isinstance(rows, list):
        return {"tree_rows": deepcopy(rows)}
    return {}


def _resolve_gantt_data(source: dict[str, Any]) -> dict[str, Any]:
    rows = source.get("ganttData") or source.get("gantt_data")
    if isinstance(rows, dict):
        return deepcopy(rows)
    if isinstance(rows, list):
        return {"gantt_rows": deepcopy(rows)}
    return {}


def _resolve_dict_data(source: dict[str, Any]) -> dict[str, Any]:
    dict_data = source.get("dictData") or source.get("dict_data") or source.get("options")
    if isinstance(dict_data, dict):
        return deepcopy(dict_data)
    return {}


def _normalize_mapping(value: Any) -> dict[str, Any]:
    return deepcopy(value) if isinstance(value, dict) else {}


def _resolve_data_source(source: dict[str, Any]) -> dict[str, dict[str, Any]]:
    raw = source.get("dataSource") or source.get("data_source") or source.get("data_sources")
    if not isinstance(raw, dict):
        return {}
    out: dict[str, dict[str, Any]] = {}
    for key, row in raw.items():
        if not isinstance(row, dict):
            continue
        data_key = _stable_key(key, "data_source")
        query = _text(row.get("query") or row.get("provider") or row.get("intent"), data_key)
        cache_policy = _text(row.get("cachePolicy") or row.get("cache_policy"), "etag")
        if cache_policy not in ALLOWED_CACHE_POLICIES:
            cache_policy = "etag"
        consistency = _text(row.get("consistency"), "eventual")
        if consistency not in ALLOWED_CONSISTENCY:
            consistency = "eventual"
        out[data_key] = {
            "query": query,
            "cachePolicy": cache_policy,
            "consistency": consistency,
            "subscription": bool(row.get("subscription") is True),
        }
    return out


def _resolve_data_meta(source: dict[str, Any]) -> dict[str, Any]:
    meta = source.get("dataMeta") or source.get("data_meta")
    if isinstance(meta, dict):
        return deepcopy(meta)
    out: dict[str, Any] = {}
    for key, bucket in (
        ("mainData", _resolve_main_data(source)),
        ("tableRows", _resolve_table_rows(source)),
        ("relationRows", _resolve_relation_rows(source)),
        ("treeData", _resolve_tree_data(source)),
        ("dictData", _resolve_dict_data(source)),
    ):
        if bucket:
            out[key] = {"present": True}
    return out


def find_forbidden_data_source_keys(data_contract: dict[str, Any]) -> list[str]:
    out: list[str] = []
    data_source = _dict(data_contract.get("dataSource"))
    for data_key, row in data_source.items():
        if not isinstance(row, dict):
            continue
        for key in row:
            if str(key) in FORBIDDEN_DATASOURCE_KEYS:
                out.append(f"{data_key}.{key}")
    return out
