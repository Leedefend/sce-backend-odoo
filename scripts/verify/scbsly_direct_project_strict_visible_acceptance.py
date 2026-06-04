#!/usr/bin/env python3
"""Strict browser/API acceptance for 34 SCBSLY direct-project user menus."""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scbsly_direct_project_acceptance_menu_probe import (  # noqa: E402
    BASE_URL as OLD_BASE_URL,
    MENU_ALIASES,
    api_get,
    clean,
    config_id_from_link,
    find_candidates,
    labels_from_manifest,
    list_payload,
    login as old_login,
    route_kind,
)


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "docs/migration_alignment/scbs55_user_acceptance_asset_freeze_v1.json"
OLD_MENU_EVIDENCE = ROOT / "artifacts/migration/scbsly_direct_project_acceptance_menu_probe_v1.json"
OLD_ROW_SUMMARY = ROOT / "artifacts/migration/scbsly_direct_project_old_row_dump_summary_v1.json"
OLD_IDENTITY_LOCK = ROOT / "artifacts/migration/scbsly_direct_project_old_identity_lock_v1.json"
OUTPUT = ROOT / "artifacts/migration/scbsly_direct_project_strict_visible_acceptance_v1.json"
OUTPUT_MD = ROOT / "artifacts/migration/scbsly_direct_project_strict_visible_acceptance_v1.md"

NEW_BASE_URL = os.getenv("FRONTEND_URL") or os.getenv("BASE_URL") or "http://1.95.85.92:18081"
DB_NAME = os.getenv("DB_NAME") or os.getenv("E2E_DB") or "sc_demo"
NEW_LOGIN = os.getenv("E2E_LOGIN") or "wutao"
NEW_PASSWORD = os.getenv("E2E_PASSWORD") or "123456"
NEW_AUTH_TOKEN = os.getenv("AUTH_TOKEN") or ""
OLD_ROWS_DIR = Path(
    os.getenv("SCBSLY_OLD_ROWS_DIR")
    or os.getenv("MIGRATION_SCBSLY_OLD_ROWS_DIR")
    or "/tmp/scbsly_direct_project_old_pages_20260530"
)
PAGE_LIMIT = int(os.getenv("STRICT_ACCEPTANCE_PAGE_LIMIT", "1000"))
TARGET_CATEGORY = os.getenv("STRICT_ACCEPTANCE_CATEGORY", "").strip()
TARGET_LABELS = {
    item.strip()
    for item in os.getenv("STRICT_ACCEPTANCE_LABELS", "").split(",")
    if item.strip()
}

REPORT_LABELS = {"库存统计表（新）", "成本统计表（数据）"}
NO_ROW_OLD_LIST_LABELS: set[str] = set()
RAW_PAYLOAD_MODELS = {"sc.legacy.direct.acceptance.fact"}

MENU_ALIASES.update({
    "入库": ["入库单"],
    "材料结算单": ["材料结算"],
    "机械结算单": ["设备结算", "租赁结算"],
    "租赁结算单": ["租赁结算"],
    "项目费用报销单": ["项目费用报销单", "费用报销单"],
    "管理人员工资表": ["工资登记", "工资统计表"],
    "工程结算单": ["结算单", "收入合同结算"],
    "进项上报": ["进项税额上报", "进项发票明细表"],
    "总包进项上报": ["进项税额上报", "销项发票登记"],
    "施工日志（新）": ["施工日志"],
})

PREFERRED_MENU_IDS = {
    "施工合同": 743,
    "供货合同": 746,
    "供货合同（数据）": 802,
    "库存统计表（新）": 715,
    "支付申请": 769,
    "工程进度收款": 770,
    "往来单位付款": 771,
    "进项上报": 773,
    "成本统计表（数据）": 717,
}

STRICT_SHADOW_LABELS = {
    "施工合同",
    "分包合同",
    "租赁合同",
    "供货合同",
    "劳务合同",
    "机械合同（合同）",
    "租入",
    "还租",
}


def normalize(value: object) -> str:
    if value is None or value is False:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def canonical_hash(payload: Any) -> str:
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


LEGACY_DJZT_DISPLAY = {
    "-1": "否决",
    "0": "草稿",
    "1": "审批中",
    "2": "审核通过",
}

LEGACY_PAYMENT_STATUS_DISPLAY = {
    "0": "未付款",
    "1": "部分付款",
    "2": "已付款",
}

LEGACY_PAYMENT_REQUEST_STATUS_DISPLAY = {
    "0": "未申请",
    "1": "部分申请",
    "2": "已申请",
}


def legacy_number(payload: dict[str, Any], *field_names: str) -> float:
    for field_name in field_names:
        value = payload.get(field_name)
        if value is None or value is False:
            continue
        text = normalize(value).replace(",", "")
        if not text:
            continue
        try:
            return float(text)
        except ValueError:
            continue
    return 0.0


def legacy_number_text(value: object) -> str:
    try:
        return str(float(value))
    except (TypeError, ValueError):
        return normalize(value)


def legacy_tax_rate_text(value: object) -> str:
    if value is None or value is False:
        return ""
    text = normalize(value)
    if not text:
        return ""
    if "%" in text:
        return text
    try:
        number = float(text.replace(",", ""))
    except ValueError:
        return text
    percent = number * 100 if abs(number) <= 1 else number
    if percent.is_integer():
        return f"{int(percent)}%"
    return f"{percent:.4f}".rstrip("0").rstrip(".") + "%"


def legacy_has_payload_value(payload: dict[str, Any], *field_names: str) -> bool:
    for field_name in field_names:
        value = payload.get(field_name)
        if value is None or value is False:
            continue
        if normalize(value):
            return True
    return False


def stock_in_note_numbers(payload: dict[str, Any]) -> tuple[float, float]:
    note = normalize(payload.get("BZ") or payload.get("f_BZ"))
    if not note:
        return 0.0, 0.0
    match = re.search(
        r"(?P<qty>\d+(?:\.\d+)?)\s*(?:\*|×|x|X)\s*(?P<price>\d+(?:\.\d+)?)\s*(?:=|＝)\s*(?P<amount>\d+(?:\.\d+)?)",
        note,
    )
    if match:
        return float(match.group("qty")), float(match.group("amount"))
    match = re.search(r"(?P<qty>\d+(?:\.\d+)?)\s*(?:个|件|吨|方|米|袋|匹|卷|车|台|套|根|桶|盒|包|张|块|瓶)", note)
    if match:
        return float(match.group("qty")), 0.0
    return 0.0, 0.0


def legacy_amount_status(paid: float, total: float, *, paid_label: str, partial_label: str, unpaid_label: str) -> str:
    if total <= 0:
        return unpaid_label
    if paid <= 0:
        return unpaid_label
    if paid + 0.000001 >= total:
        return paid_label
    return partial_label


def common_computed_visible_value(payload: dict[str, Any], field_name: str) -> str:
    if field_name not in {
        "CCCC_FKZT",
        "CCCC_FKJE",
        "CCCC_WFKJE",
        "CCCC_SQZT",
        "CCCC_SQJE",
        "CCCC_WSQJE",
        "JSZT",
    }:
        return ""
    raw = payload.get(field_name)
    if raw is not None and raw is not False and normalize(raw):
        text = normalize(raw)
        if field_name == "CCCC_FKZT":
            return LEGACY_PAYMENT_STATUS_DISPLAY.get(text, text)
        if field_name == "CCCC_SQZT":
            return LEGACY_PAYMENT_REQUEST_STATUS_DISPLAY.get(text, text)
        return normalize(raw)
    total_amount = legacy_number(
        payload,
        "ZJE",
        "JEHJ",
        "JE",
        "ZHSJE",
        "SQBXJE",
        "f_JSJE",
        "SSJE",
        "HJ$T_RK_RKDCB",
        "RK_ZJE",
    )
    paid_amount = legacy_number(payload, "CCCC_FKJE", "YFKJE", "YFJE$T_RK_RKDCB", "FKJE")
    applied_amount = legacy_number(payload, "CCCC_SQJE", "SQJE")
    settlement_amount = legacy_number(payload, "f_JSJE", "JSJE", "ZJE")
    if field_name == "JSZT":
        return "已结算" if settlement_amount > 0 else "未结算"
    if field_name == "CCCC_FKZT":
        return legacy_amount_status(paid_amount, total_amount, paid_label="已付款", partial_label="部分付款", unpaid_label="未付款")
    if field_name == "CCCC_FKJE":
        return legacy_number_text(paid_amount)
    if field_name == "CCCC_WFKJE":
        raw_unpaid = legacy_number(payload, "WFKJE")
        return legacy_number_text(raw_unpaid if raw_unpaid else max(total_amount - paid_amount, 0.0))
    if field_name == "CCCC_SQZT":
        return legacy_amount_status(applied_amount, total_amount, paid_label="已申请", partial_label="部分申请", unpaid_label="未申请")
    if field_name == "CCCC_SQJE":
        return legacy_number_text(applied_amount)
    if field_name == "CCCC_WSQJE":
        raw_unapplied = legacy_number(payload, "WSQJE")
        return legacy_number_text(raw_unapplied if raw_unapplied else max(total_amount - applied_amount, 0.0))
    return ""


def stock_in_computed_visible_value(payload: dict[str, Any], visible_index: int) -> str:
    total_amount = legacy_number(payload, "ZJE", "RK_ZJE", "HJ$T_RK_RKDCB")
    note_quantity, note_amount = stock_in_note_numbers(payload)
    if total_amount <= 0 and note_amount:
        total_amount = note_amount
    paid_amount = legacy_number(payload, "CCCC_FKJE", "YFJE$T_RK_RKDCB")
    settled_amount = legacy_number(payload, "CCCC_JSJE", "ZJE", "RK_ZJE", "HJ$T_RK_RKDCB")
    if settled_amount <= 0 and total_amount:
        settled_amount = total_amount
    if visible_index == 11:
        quantity_fields = ("RK_ZSL", "ZSL", "SL$T_RK_RKDCB")
        quantity = legacy_number(payload, *quantity_fields)
        if quantity <= 0 and note_quantity:
            quantity = note_quantity
        if quantity or legacy_has_payload_value(payload, *quantity_fields):
            return legacy_number_text(quantity)
        if total_amount:
            return legacy_number_text(0.0)
        return ""
    if visible_index == 12:
        text = normalize(payload.get("CCCC_FKZT"))
        return text or legacy_amount_status(paid_amount, total_amount, paid_label="已付款", partial_label="部分付款", unpaid_label="未付款")
    if visible_index == 13:
        return legacy_number_text(paid_amount)
    if visible_index == 14:
        return legacy_number_text(max(total_amount - paid_amount, 0.0))
    if visible_index == 15:
        text = normalize(payload.get("CCCC_JSZT"))
        return text or legacy_amount_status(settled_amount, total_amount, paid_label="已结算", partial_label="部分结算", unpaid_label="未结算")
    if visible_index == 16:
        return legacy_number_text(settled_amount)
    return ""


def visible_cell_text(payload: dict[str, Any], field_name: str, *, label: str = "", visible_index: int = 0) -> str:
    if label == "还租" and field_name in {"f_LRR", "f_LRSJ"}:
        fallback_field = "XGR" if field_name == "f_LRR" else "XGSJ"
        return normalize(payload.get(field_name) or payload.get(fallback_field))
    if label == "入库":
        computed = stock_in_computed_visible_value(payload, visible_index)
        if computed:
            return computed
    computed = common_computed_visible_value(payload, field_name)
    if computed:
        return computed

    if field_name == "DJZTText":
        for status_field in ("DJZTText", "DJZT"):
            value = payload.get(status_field)
            if value is None or value is False:
                continue
            text = normalize(value)
            return LEGACY_DJZT_DISPLAY.get(text, text)
        return ""

    candidates: list[str] = []
    if field_name:
        if field_name.endswith("FJ") or field_name.endswith("_FJ") or field_name == "FJ":
            candidates.extend([f"{field_name}_FJ", "f_FJ_FJ", "FJ_FJ", "FJ"])
        candidates.append(field_name)
    for candidate in candidates:
        value = payload.get(candidate)
        if value is None or value is False:
            continue
        if isinstance(value, (list, dict)):
            text = json.dumps(value, ensure_ascii=False, sort_keys=True)
        else:
            text = normalize(value)
        if text:
            if field_name.endswith("FJ") or field_name.endswith("_FJ") or field_name == "FJ":
                return text if text.startswith("附件(") else "附件(1)"
            if field_name in {"SLV", "SLVS", "D_SCBSJS_SL1"}:
                return legacy_tax_rate_text(text)
            return text
    return ""


def old_visible_columns(config: dict[str, Any]) -> list[dict[str, str]]:
    detail = json.loads(config.get("DETAIL_CONFIG") or "{}")
    columns = detail.get("ContentTable", {}).get("TableConfig", {}).get("ColumnConfig") or []
    out: list[dict[str, str]] = []
    for column in columns:
        info = column.get("Info") if isinstance(column, dict) else {}
        if not isinstance(info, dict):
            continue
        if info.get("IsHide") is True:
            continue
        name = clean(info.get("Name") or info.get("Title") or info.get("Label"))
        field = clean(info.get("Field"))
        if name and field:
            out.append({"name": name, "field": field})
    return out


def flattened_menu(nodes: list[dict[str, Any]], parents: list[str] | None = None) -> list[dict[str, Any]]:
    parents = parents or []
    out: list[dict[str, Any]] = []
    for node in nodes or []:
        if not isinstance(node, dict):
            continue
        label = normalize(node.get("name") or node.get("label") or node.get("title"))
        path_parts = [*parents, label] if label else [*parents]
        item = dict(node)
        item["__path"] = "/".join(path_parts)
        out.append(item)
        children = node.get("children")
        if isinstance(children, list):
            out.extend(flattened_menu(children, path_parts))
    return out


def new_request(session: requests.Session, token: str, payload: dict[str, Any]) -> dict[str, Any]:
    headers = {"X-Odoo-DB": DB_NAME}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    elif payload.get("intent") == "login":
        headers["X-Anonymous-Intent"] = "1"
    response = session.post(
        f"{NEW_BASE_URL.rstrip('/')}/api/v1/intent?db={DB_NAME}",
        json=payload,
        headers=headers,
        timeout=180,
    )
    response.raise_for_status()
    body = response.json()
    if body.get("ok") is False:
        raise RuntimeError(body.get("error") or body)
    return body.get("data") or {}


def new_login(session: requests.Session) -> str:
    if NEW_AUTH_TOKEN:
        return NEW_AUTH_TOKEN
    data = new_request(
        session,
        "",
        {"intent": "login", "params": {"db": DB_NAME, "login": NEW_LOGIN, "password": NEW_PASSWORD}},
    )
    token = data.get("token")
    if not token:
        raise RuntimeError("new system login did not return token")
    return str(token)


def new_navigation(session: requests.Session, token: str) -> list[dict[str, Any]]:
    response = session.post(
        f"{NEW_BASE_URL.rstrip('/')}/api/menu/navigation?db={DB_NAME}",
        json={},
        headers={"Authorization": f"Bearer {token}", "X-Odoo-DB": DB_NAME},
        timeout=180,
    )
    response.raise_for_status()
    body = response.json()
    if body.get("ok") is False:
        raise RuntimeError(body.get("error") or body)
    nav = body.get("nav_explained") or {}
    return [*(nav.get("flat") or []), *flattened_menu(nav.get("tree") or [])]


def node_label(node: dict[str, Any]) -> str:
    return normalize(node.get("name") or node.get("label") or node.get("title"))


def score_node(original_label: str, candidate_label: str, node: dict[str, Any]) -> int:
    label = node_label(node)
    path_text = normalize(node.get("__path"))
    score = 0
    if ("用户验收" in path_text and "直营项目系统菜单" in path_text) or "直营项目数据核对" in path_text:
        score += 5000
    if node.get("menu_id") == PREFERRED_MENU_IDS.get(original_label):
        score += 1000
    if label == original_label:
        score += 200
    if label == candidate_label:
        score += 160
    if candidate_label and candidate_label in label:
        score += 40
    if node.get("is_clickable"):
        score += 30
    if node.get("native_action_id"):
        score += 20
    return score


def find_new_node(label: str, flat: list[dict[str, Any]]) -> tuple[str, dict[str, Any] | None]:
    labels = [label, *MENU_ALIASES.get(label, [])]
    hits: list[tuple[int, str, dict[str, Any]]] = []
    for index, candidate in enumerate(labels):
        candidate = normalize(candidate)
        for node in flat:
            text = node_label(node)
            if text == candidate or (candidate and candidate in text):
                mode = "exact" if index == 0 and text == label else "alias" if index else "contains"
                hits.append((score_node(label, candidate, node), mode, node))
    hits.sort(key=lambda item: item[0], reverse=True)
    return (hits[0][1], hits[0][2]) if hits else ("missing", None)


def exact_clickable_nodes(label: str, flat: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [node for node in flat if node_label(node) == label and node.get("is_clickable")]


def node_path(node: dict[str, Any]) -> str:
    return normalize(node.get("__path") or node.get("path") or node.get("complete_name"))


def columns_from_contract(data: dict[str, Any]) -> tuple[list[str], list[str], list[Any]]:
    tree = ((data.get("views") or {}).get("tree") or {})
    schema = tree.get("columns_schema") if isinstance(tree.get("columns_schema"), list) else []
    fields = [str(item) for item in (tree.get("columns") or [])]
    headers = [normalize((col or {}).get("label") or (col or {}).get("string") or (col or {}).get("name")) for col in schema]
    return fields, [item for item in headers if item], (data.get("head") or {}).get("domain") or []


def identity_value(row: dict[str, Any], identity_field: str) -> str:
    for field in [identity_field, "Id", "id", "DJBH", "PID", "Pid", "pid", "RowIndex"]:
        value = normalize(row.get(field))
        if value:
            return value
    return "hash:" + canonical_hash(row)


def fetch_all_new_records(
    session: requests.Session,
    token: str,
    model: str,
    domain: list[Any],
    fields: list[str],
    total: int,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    offset = 0
    while offset < total:
        data = new_request(
            session,
            token,
            {
                "intent": "api.data",
                "params": {
                    "op": "list",
                    "model": model,
                    "domain": domain,
                    "fields": fields,
                    "limit": min(PAGE_LIMIT, max(total - offset, 1)),
                    "offset": offset,
                },
            },
        )
        batch = data.get("records") or []
        if not batch:
            break
        records.extend(batch)
        offset += len(batch)
    return records


def row_dump_by_label() -> dict[str, dict[str, Any]]:
    if not OLD_ROW_SUMMARY.exists():
        return {}
    out: dict[str, dict[str, Any]] = {}
    for row in load_json(OLD_ROW_SUMMARY).get("rows", []):
        label = normalize(row.get("label"))
        path = Path(row.get("path") or "")
        if label:
            out[label] = {**row, "path": str(path)}
    return out


def identity_by_label() -> dict[str, dict[str, Any]]:
    if not OLD_IDENTITY_LOCK.exists():
        return {}
    return {normalize(row.get("label")): row for row in load_json(OLD_IDENTITY_LOCK).get("rows", [])}


def markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# SCBSLY Direct Project Strict Visible Acceptance v1",
        "",
        f"Status: `{payload['status']}`",
        f"Old: `{payload['old_base_url']}`",
        f"New: `{payload['new_base_url']}` / DB `{payload['db_name']}`",
        f"Generated: `{payload['generated_at']}`",
        "",
        "| 分类 | 菜单 | 旧数 | 新数 | 旧可见列 | 新可见列 | 行级 | 状态 |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for row in payload["rows"]:
        lines.append(
            "| {category} | {label} | {old_count} | {new_count} | {old_header_count} | {new_header_count} | {row_compare_status} | {status} |".format(
                **{**row, "old_count": "" if row.get("old_count") is None else row.get("old_count"), "new_count": "" if row.get("new_count") is None else row.get("new_count")}
            )
        )
    lines.extend(["", "## Failures", "", "```json", json.dumps(payload["failures"], ensure_ascii=False, indent=2), "```", ""])
    return "\n".join(lines)


def filtered_manifest_items() -> list[dict[str, str]]:
    items = labels_from_manifest()
    if TARGET_CATEGORY:
        items = [item for item in items if normalize(item.get("category")) == TARGET_CATEGORY]
    if TARGET_LABELS:
        items = [item for item in items if normalize(item.get("label")) in TARGET_LABELS]
    if (TARGET_CATEGORY or TARGET_LABELS) and not items:
        raise RuntimeError(
            {
                "strict_acceptance_filter_matched_no_items": {
                    "category": TARGET_CATEGORY,
                    "labels": sorted(TARGET_LABELS),
                }
            }
        )
    return items


def output_paths() -> tuple[Path, Path]:
    if not TARGET_CATEGORY and not TARGET_LABELS:
        return OUTPUT, OUTPUT_MD
    parts = []
    if TARGET_CATEGORY:
        parts.append(re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "_", TARGET_CATEGORY).strip("_"))
    if TARGET_LABELS:
        labels_key = "_".join(sorted(TARGET_LABELS))
        parts.append(re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "_", labels_key).strip("_"))
    suffix = "_".join(item for item in parts if item) or "filtered"
    return (
        ROOT / f"artifacts/migration/scbsly_direct_project_strict_visible_acceptance_{suffix}_v1.json",
        ROOT / f"artifacts/migration/scbsly_direct_project_strict_visible_acceptance_{suffix}_v1.md",
    )


def main() -> int:
    old_session = requests.Session()
    old_user = old_login(old_session)
    old_token = old_user["Token"]
    home = requests.post(
        f"{OLD_BASE_URL.rstrip('/')}/api/HomeApi/GetCommonHomeInfo",
        json={},
        headers={"Token": old_token},
        timeout=180,
    )
    home.raise_for_status()
    old_menus = home.json().get("Data", {}).get("MenuInfoArr") or []

    new_session = requests.Session()
    token = new_login(new_session)
    new_flat = new_navigation(new_session, token)
    dumps = row_dump_by_label()
    identities = identity_by_label()

    rows: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for item in filtered_manifest_items():
        label = item["label"]
        row: dict[str, Any] = {
            "category": item["category"],
            "label": label,
            "status": "FAIL",
            "failures": [],
            "old_route_kind": "",
            "old_config_id": "",
            "old_count": None,
            "old_headers": [],
            "old_fields": [],
            "old_header_count": 0,
            "new_match_mode": "missing",
            "new_menu_id": None,
            "new_action_id": None,
            "new_model": "",
            "new_count": None,
            "new_headers": [],
            "new_fields": [],
            "new_header_count": 0,
            "row_compare_status": "NOT_RUN",
            "row_compare": {},
        }

        match_mode, old_candidates = find_candidates(label, old_menus)
        old_best = old_candidates[0] if old_candidates else {}
        old_link = clean(old_best.get("LINK_URL")) if old_best else ""
        old_kind = route_kind(old_link)
        old_config_id = config_id_from_link(old_link)
        row["old_route_kind"] = old_kind
        row["old_config_id"] = old_config_id
        dump_info = dumps.get(label) or {}
        identity = identities.get(label) or {}
        if dump_info:
            row["old_count"] = int(dump_info.get("actual_count") or dump_info.get("expected_count") or 0)
        if old_kind == "lowcode_form_list" and old_config_id:
            try:
                config = api_get(old_session, old_token, f"LowCode/FormApi/GetConfigById?Id={old_config_id}&LoadInitData=true")["Data"]
                columns = old_visible_columns(config)
                row["old_headers"] = [col["name"] for col in columns]
                row["old_fields"] = [col["field"] for col in columns]
                row["old_header_count"] = len(columns)
            except Exception as exc:  # noqa: BLE001
                row["failures"].append(f"old_visible_columns_failed:{exc}")
        elif label not in REPORT_LABELS:
            row["failures"].append(f"old_route_not_form_list:{old_kind}")

        new_mode, new_node = find_new_node(label, new_flat)
        row["new_match_mode"] = new_mode
        if not new_node:
            row["failures"].append("new_menu_missing")
        else:
            row["new_menu_id"] = new_node.get("menu_id")
            row["new_action_id"] = int(new_node.get("native_action_id") or 0)
            if not row["new_action_id"]:
                row["failures"].append("new_action_missing")
            else:
                try:
                    contract = new_request(
                        new_session,
                        token,
                        {
                            "intent": "ui.contract",
                            "params": {
                                "op": "action_open",
                                "action_id": row["new_action_id"],
                                "menu_id": row["new_menu_id"],
                                "source_mode": "backend_internal",
                            },
                        },
                    )
                    row["new_model"] = normalize((contract.get("head") or {}).get("model") or new_node.get("native_model"))
                    new_fields, new_headers, domain = columns_from_contract(contract)
                    row["new_fields"] = new_fields
                    row["new_headers"] = new_headers
                    row["new_header_count"] = len(new_headers)
                    count_data = new_request(
                        new_session,
                        token,
                        {"intent": "api.data", "params": {"op": "count", "model": row["new_model"], "domain": domain}},
                    )
                    row["new_count"] = int(count_data.get("total") or 0)
                    row["_domain"] = domain
                except Exception as exc:  # noqa: BLE001
                    row["failures"].append(f"new_contract_or_count_failed:{exc}")

        if label not in REPORT_LABELS and row["old_count"] is not None and row["new_count"] is not None and row["old_count"] != row["new_count"]:
            row["failures"].append(f"count_mismatch:{row['new_count']}!={row['old_count']}")

        if label not in REPORT_LABELS and row["old_headers"] and row["new_headers"] and row["old_headers"] != row["new_headers"]:
            row["failures"].append("visible_headers_mismatch")

        if label in STRICT_SHADOW_LABELS:
            shadow_failures = []
            for shadow_node in exact_clickable_nodes(label, new_flat):
                if shadow_node.get("menu_id") == row.get("new_menu_id"):
                    continue
                if "用户验收/直营项目系统菜单" in node_path(shadow_node):
                    continue
                action_id = int(shadow_node.get("native_action_id") or 0)
                if not action_id:
                    shadow_failures.append(
                        {
                            "menu_id": shadow_node.get("menu_id"),
                            "path": node_path(shadow_node),
                            "reason": "shadow_action_missing",
                        }
                    )
                    continue
                try:
                    shadow_contract = new_request(
                        new_session,
                        token,
                        {
                            "intent": "ui.contract",
                            "params": {
                                "op": "action_open",
                                "action_id": action_id,
                                "menu_id": shadow_node.get("menu_id"),
                                "source_mode": "backend_internal",
                            },
                        },
                    )
                    shadow_model = normalize((shadow_contract.get("head") or {}).get("model") or shadow_node.get("native_model"))
                    _, shadow_headers, _ = columns_from_contract(shadow_contract)
                    if shadow_model != "sc.legacy.direct.acceptance.fact" or shadow_headers != row["old_headers"]:
                        shadow_failures.append(
                            {
                                "menu_id": shadow_node.get("menu_id"),
                                "action_id": action_id,
                                "path": node_path(shadow_node),
                                "model": shadow_model,
                                "headers": shadow_headers,
                            }
                        )
                except Exception as exc:  # noqa: BLE001
                    shadow_failures.append(
                        {
                            "menu_id": shadow_node.get("menu_id"),
                            "action_id": action_id,
                            "path": node_path(shadow_node),
                            "reason": f"shadow_contract_failed:{exc}",
                        }
                    )
            if shadow_failures:
                row["shadow_menu_failures"] = shadow_failures
                row["failures"].append("shadow_exact_label_menu_mismatch")

        if label in REPORT_LABELS:
            row["row_compare_status"] = "REPORT_ROUTE"
        elif row["old_count"] == 0 and label in NO_ROW_OLD_LIST_LABELS:
            row["row_compare_status"] = "EMPTY_OLD_LIST"
        elif dump_info and row.get("new_model") in RAW_PAYLOAD_MODELS and row.get("new_count") is not None:
            dump_path = Path(dump_info.get("path") or "")
            if not dump_path.exists():
                fallback = OLD_ROWS_DIR / dump_path.name
                dump_path = fallback if fallback.exists() else dump_path
            if not dump_path.exists():
                row["failures"].append(f"old_dump_missing:{dump_info.get('path')}")
                row["row_compare_status"] = "FAIL"
            else:
                old_payload = load_json(dump_path)
                old_rows = old_payload.get("rows") or []
                identity_field = normalize(identity.get("identity_field"))
                old_by_id = {identity_value(item, identity_field): canonical_hash(item) for item in old_rows if isinstance(item, dict)}
                new_records = fetch_all_new_records(
                    new_session,
                    token,
                    row["new_model"],
                    row.get("_domain") or [],
                    ["legacy_record_id", "raw_payload", *row["new_fields"]],
                    int(row["new_count"] or 0),
                )
                new_by_id: dict[str, str] = {}
                new_records_by_id: dict[str, dict[str, Any]] = {}
                parse_failures = 0
                for record in new_records:
                    key = normalize(record.get("legacy_record_id"))
                    if key:
                        new_records_by_id[key] = record
                    try:
                        payload = json.loads(record.get("raw_payload") or "{}")
                        new_by_id[key] = canonical_hash(payload)
                    except Exception:  # noqa: BLE001
                        parse_failures += 1
                missing = sorted(set(old_by_id) - set(new_by_id))[:20]
                extra = sorted(set(new_by_id) - set(old_by_id))[:20]
                hash_mismatch = sorted(key for key in set(old_by_id) & set(new_by_id) if old_by_id[key] != new_by_id[key])[:20]
                row["row_compare"] = {
                    "identity_field": identity_field,
                    "old_identity_count": len(old_by_id),
                    "new_identity_count": len(new_by_id),
                    "parse_failures": parse_failures,
                    "missing_sample": missing,
                    "extra_sample": extra,
                    "hash_mismatch_sample": hash_mismatch,
                }
                if missing or extra or hash_mismatch or parse_failures:
                    row["row_compare_status"] = "FAIL"
                    row["failures"].append("raw_payload_row_hash_mismatch")
                else:
                    row["row_compare_status"] = "PASS"

                visible_missing_samples: list[dict[str, Any]] = []
                visible_mismatch_samples: list[dict[str, Any]] = []
                visible_extra_samples: list[dict[str, Any]] = []
                visible_compared = 0
                old_nonempty_new_empty_count = 0
                old_empty_new_nonempty_count = 0
                visible_mismatch_count = 0
                pairs = list(zip(row["old_headers"], row["old_fields"], row["new_fields"]))
                for old_item in old_rows:
                    if not isinstance(old_item, dict):
                        continue
                    key = identity_value(old_item, identity_field)
                    new_item = new_records_by_id.get(key)
                    if not new_item:
                        continue
                    for visible_index, (old_header, old_field, new_field) in enumerate(pairs, start=1):
                        old_text = visible_cell_text(old_item, old_field, label=label, visible_index=visible_index)
                        new_text = normalize(new_item.get(new_field))
                        if not old_text and not new_text:
                            continue
                        visible_compared += 1
                        if old_text and not new_text:
                            old_nonempty_new_empty_count += 1
                            if len(visible_missing_samples) < 20:
                                visible_missing_samples.append(
                                    {
                                        "identity": key,
                                        "header": old_header,
                                        "old_field": old_field,
                                        "new_field": new_field,
                                        "old_value": old_text,
                                        "new_value": new_text,
                                    }
                                )
                        elif not old_text and new_text:
                            old_empty_new_nonempty_count += 1
                            if len(visible_extra_samples) < 20:
                                visible_extra_samples.append(
                                    {
                                        "identity": key,
                                        "header": old_header,
                                        "old_field": old_field,
                                        "new_field": new_field,
                                        "old_value": old_text,
                                        "new_value": new_text,
                                    }
                                )
                        elif old_text != new_text:
                            visible_mismatch_count += 1
                            if len(visible_mismatch_samples) < 20:
                                visible_mismatch_samples.append(
                                    {
                                        "identity": key,
                                        "header": old_header,
                                        "old_field": old_field,
                                        "new_field": new_field,
                                        "old_value": old_text,
                                        "new_value": new_text,
                                    }
                                )
                row["visible_cell_compare"] = {
                    "status": "PASS" if not old_nonempty_new_empty_count and not old_empty_new_nonempty_count and not visible_mismatch_count else "FAIL",
                    "compared_nonempty_pairs": visible_compared,
                    "old_nonempty_new_empty_count": old_nonempty_new_empty_count,
                    "old_empty_new_nonempty_count": old_empty_new_nonempty_count,
                    "visible_mismatch_count": visible_mismatch_count,
                    "missing_samples": visible_missing_samples,
                    "extra_samples": visible_extra_samples,
                    "mismatch_samples": visible_mismatch_samples,
                }
                if old_nonempty_new_empty_count or old_empty_new_nonempty_count or visible_mismatch_count:
                    row["row_compare_status"] = "FAIL"
                    row["failures"].append("visible_cell_value_mismatch")
        elif dump_info and row.get("new_count") is not None and row.get("new_model"):
            identity_field = normalize(identity.get("identity_field"))
            fields = ["legacy_record_id"] if "legacy_record_id" in row.get("new_fields", []) else ["id"]
            new_records = fetch_all_new_records(
                new_session,
                token,
                row["new_model"],
                row.get("_domain") or [],
                fields,
                int(row["new_count"] or 0),
            )
            row["row_compare_status"] = "IDENTITY_ONLY" if fields == ["legacy_record_id"] else "COUNT_ONLY"
            row["row_compare"] = {
                "identity_field": identity_field,
                "new_records_read": len(new_records),
                "reason": "target model does not expose raw_payload for full old-row hash comparison",
            }
            if fields == ["id"]:
                row["failures"].append("raw_payload_not_available_for_strict_row_hash")

        row.pop("_domain", None)
        row["status"] = "FAIL" if row["failures"] else "PASS"
        rows.append(row)
        if row["failures"]:
            failures.append(row)
        print(
            "[scbsly-strict] {status} {label} old={old} new={new} old_cols={oc} new_cols={nc} row={rc}".format(
                status=row["status"],
                label=label,
                old=row["old_count"] if row["old_count"] is not None else "",
                new=row["new_count"] if row["new_count"] is not None else "",
                oc=row["old_header_count"],
                nc=row["new_header_count"],
                rc=row["row_compare_status"],
            ),
            flush=True,
        )

    payload = {
        "status": "FAIL" if failures else "PASS",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "filter": {
            "category": TARGET_CATEGORY,
            "labels": sorted(TARGET_LABELS),
        },
        "manifest": str(MANIFEST.relative_to(ROOT)),
        "old_base_url": OLD_BASE_URL,
        "new_base_url": NEW_BASE_URL,
        "db_name": DB_NAME,
        "old_menu_evidence": str(OLD_MENU_EVIDENCE.relative_to(ROOT)),
        "old_row_summary": str(OLD_ROW_SUMMARY.relative_to(ROOT)),
        "old_identity_lock": str(OLD_IDENTITY_LOCK.relative_to(ROOT)),
        "checked_count": len(rows),
        "pass_count": len([row for row in rows if row["status"] == "PASS"]),
        "failure_count": len(failures),
        "visible_header_mismatch_count": len([row for row in rows if "visible_headers_mismatch" in row["failures"]]),
        "count_mismatch_count": len([row for row in rows if any(str(f).startswith("count_mismatch:") for f in row["failures"])]),
        "raw_hash_pass_count": len([row for row in rows if row["row_compare_status"] == "PASS"]),
        "failures": failures,
        "rows": rows,
    }
    output_json, output_md = output_paths()
    write_json(output_json, payload)
    output_md.write_text(markdown(payload), encoding="utf-8")
    print(f"SCBSLY_DIRECT_PROJECT_STRICT_VISIBLE_ACCEPTANCE={payload['status']} output={output_json}")
    return 0 if not failures else 2


if __name__ == "__main__":
    raise SystemExit(main())
