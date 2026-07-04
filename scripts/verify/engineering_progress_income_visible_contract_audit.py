#!/usr/bin/env python3
"""Audit the formal engineering-progress income list contract."""

from __future__ import annotations

import json
import os
from pathlib import Path
from xml.etree import ElementTree as ET

from odoo.tools.safe_eval import safe_eval


OUTPUT_JSON_NAME = "engineering_progress_income_visible_contract_audit_v1.json"
ACTION_XMLID = "smart_construction_core.action_sc_receipt_income_engineering_progress"
VIEW_XMLID = "smart_construction_core.view_sc_receipt_income_engineering_progress_formal_tree"
ACTION_NAME = "工程进度款收入登记"
MODEL_NAME = "sc.receipt.income"
EXPECTED_DOMAIN = [
    ("business_category_id.code", "=", "finance.receipt.income.progress"),
]
EXPECTED_FIELDS = [
    ("state", "单据状态"),
    ("project_id", "项目名称"),
    ("partner_id", "往来单位"),
    ("company_id", "承包单位"),
    ("legacy_contract_no", "施工管理合同"),
    ("name", "单据编号"),
    ("creator_name", "填写人"),
    ("receiving_account", "收款账户"),
    ("amount", "进账金额"),
    ("income_category", "收入类别"),
    ("date_receipt", "收款时间"),
    ("note", "备注"),
    ("receipt_income_attachment_text_display", "附件"),
    ("creator_name", "录入人"),
    ("created_time", "录入时间"),
]


def artifact_root() -> Path:
    raw = os.getenv("MIGRATION_ARTIFACT_ROOT") or os.getenv("ARTIFACT_ROOT")
    candidates = [Path(raw)] if raw else []
    candidates.extend([Path("/mnt/artifacts/backend"), Path(f"/tmp/engineering_progress_income/{env.cr.dbname}")])  # noqa: F821
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return candidate
        except OSError:
            continue
    return Path("/tmp")


def clean(value: object) -> str:
    if value is False or value is None:
        return ""
    text = str(value or "").strip()
    return "" if text.lower() in {"false", "none", "null"} else text


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def fail(reason: str, payload: dict[str, object]) -> None:
    result = {"status": "FAIL", "reason": reason, **payload}
    write_json(artifact_root() / OUTPUT_JSON_NAME, result)
    raise RuntimeError(result)


Model = env[MODEL_NAME].sudo()  # noqa: F821
action = env.ref(ACTION_XMLID, raise_if_not_found=False)  # noqa: F821
view = env.ref(VIEW_XMLID, raise_if_not_found=False)  # noqa: F821
if not action:
    fail("missing_action", {"action_xmlid": ACTION_XMLID})
if not view:
    fail("missing_view", {"view_xmlid": VIEW_XMLID})

missing_fields = [name for name, _label in EXPECTED_FIELDS if name not in Model._fields]
if missing_fields:
    fail("missing_model_fields", {"missing_fields": missing_fields})

root = ET.fromstring(view.arch_db.encode("utf-8"))
actual_fields = [(node.get("name") or "", node.get("string") or "") for node in root.iter("field")]
if root.get("string") != ACTION_NAME:
    fail("wrong_tree_label", {"actual_label": root.get("string"), "expected_label": ACTION_NAME})
if actual_fields != EXPECTED_FIELDS:
    fail("wrong_tree_fields", {"actual_fields": actual_fields, "expected_fields": EXPECTED_FIELDS})

actual_domain = safe_eval(action.domain or "[]")
if actual_domain != EXPECTED_DOMAIN:
    fail("wrong_action_domain", {"actual_domain": actual_domain, "expected_domain": EXPECTED_DOMAIN})
if action.name != ACTION_NAME:
    fail("wrong_action_name", {"actual_name": action.name, "expected_name": ACTION_NAME})
if action.res_model != MODEL_NAME:
    fail("wrong_action_model", {"actual_model": action.res_model, "expected_model": MODEL_NAME})
if action.view_id.id != view.id:
    fail("wrong_primary_view", {"actual_view": action.view_id.name, "expected_view": view.name})

tree_bindings = action.view_ids.filtered(lambda item: item.view_mode == "tree").sorted("sequence")
if not tree_bindings or tree_bindings[0].view_id.id != view.id:
    fail(
        "wrong_tree_binding",
        {"bindings": [(item.sequence, item.view_mode, item.view_id.name) for item in action.view_ids.sorted("sequence")]},
    )

record_count = Model.search_count(EXPECTED_DOMAIN)
if record_count <= 0:
    fail("empty_engineering_progress_income_domain", {"domain": EXPECTED_DOMAIN})

records = Model.search(EXPECTED_DOMAIN, order="id desc", limit=50)
blank_counts: dict[str, int] = {}
for field_name, _label in EXPECTED_FIELDS:
    blank_counts[field_name] = sum(1 for record in records if not clean(record[field_name]))
critical_fields = ["name", "project_id", "amount", "date_receipt"]
critical_blank = {name: blank_counts[name] for name in critical_fields if blank_counts[name] == len(records)}
if critical_blank:
    fail("critical_visible_fields_all_blank", {"critical_blank": critical_blank, "sample_size": len(records)})

examples = []
for record in records[:3]:
    examples.append({field_name: clean(record[field_name]) for field_name, _label in EXPECTED_FIELDS})

payload = {
    "status": "PASS",
    "database": env.cr.dbname,  # noqa: F821
    "mode": "engineering_progress_income_visible_contract_audit",
    "action_id": int(action.id),
    "action_name": action.name,
    "view_id": int(view.id),
    "view_name": view.name,
    "record_count": int(record_count),
    "field_count": len(EXPECTED_FIELDS),
    "blank_counts_in_latest_50": blank_counts,
    "examples": examples,
}
write_json(artifact_root() / OUTPUT_JSON_NAME, payload)
print("ENGINEERING_PROGRESS_INCOME_VISIBLE_CONTRACT_AUDIT=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
