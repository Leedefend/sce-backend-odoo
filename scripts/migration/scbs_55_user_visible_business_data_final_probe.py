#!/usr/bin/env python3
"""Final read-only business-data probe for SCBS55 user-visible entries."""

from __future__ import annotations

import ast
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SOURCE_DOCUMENT = "/home/odoo/workspace/partner_import_source/5.6优化（老系统菜单，字段列表展示）1.docx"
OUTPUT_JSON_NAME = "scbs_55_user_visible_business_data_final_probe_result_v1.json"
OUTPUT_REPORT_NAME = "scbs_55_user_visible_business_data_final_probe_report_v1.md"

HEX_RE = re.compile(r"\b[0-9a-fA-F]{24,64}\b")
HASH_FILE_RE = re.compile(r"^[0-9a-fA-F]{24,64}(?:\.[A-Za-z0-9]{1,8})?$")
SOURCE_TABLE_RE = re.compile(r"\b[A-Za-z][A-Za-z0-9_]{2,}\b")
CRITICAL_LABEL_RE = re.compile(r"(单据|编号|项目|名称|日期|时间|金额|税额|类型|状态|凭证|发票|合同)")
OPTIONAL_CRITICAL_LABELS = {"附件", "录入人", "录入时间", "申请人", "推送结果", "金蝶单据编号"}
ACCOUNT_LABEL_RE = re.compile(r"(账号|账户|卡号)")
ALLOWED_ZERO_SEQS = {130}
SAMPLE_LIMIT = 80


def artifact_root() -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.append(Path("/mnt/artifacts/migration"))
    candidates.append(Path(f"/tmp/scbs_55_final_business_data/{env.cr.dbname}"))  # noqa: F821
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return candidate
        except Exception:
            continue
    return Path(f"/tmp/scbs_55_final_business_data/{env.cr.dbname}")  # noqa: F821


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def alias_field_name(label: str) -> str:
    return "p1_visible_" + hashlib.sha1(label.encode("utf-8")).hexdigest()[:12]


def clean(value: object) -> str:
    if value in (None, False):
        return ""
    if isinstance(value, tuple):
        return clean(value[1] if len(value) > 1 else value[0])
    if isinstance(value, list):
        return ", ".join(clean(item) for item in value if clean(item))
    return str(value).strip()


def action_domain(action) -> list[Any]:
    try:
        return ast.literal_eval(action.domain or "[]")
    except Exception:
        return []


def contract_items(record) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    for item in record.list_field_contract or []:
        if not isinstance(item, dict):
            continue
        label = clean(item.get("legacy_label"))
        if label:
            result.append({"label": label, "field": alias_field_name(label)})
    return result


def source_tables(record, domain: list[Any]) -> list[str]:
    tables: set[str] = set()
    for text in (record.legacy_source_tables or "", record.legacy_field_list or ""):
        for token in SOURCE_TABLE_RE.findall(text):
            if "_" in token and not token.startswith(("p1_visible_", "ir_", "sc_")):
                tables.add(token)
    for leaf in domain:
        if (
            isinstance(leaf, (list, tuple))
            and len(leaf) >= 3
            and leaf[0] in {"legacy_source_table", "source_table"}
            and leaf[1] in {"=", "in"}
        ):
            raw = leaf[2]
            if isinstance(raw, str):
                tables.add(raw)
            elif isinstance(raw, (list, tuple)):
                tables.update(str(item) for item in raw if item)
    return sorted(tables)


def non_empty_count(model_name: str, field_name: str, domain: list[Any]) -> int | None:
    field = env[model_name]._fields.get(field_name)  # noqa: F821
    if not field or (field.compute and not field.store):
        return None
    if field.type == "boolean":
        return env[model_name].sudo().search_count(domain)  # noqa: F821
    return env[model_name].sudo().search_count(domain + [(field_name, "!=", False)])  # noqa: F821


def sample_records(model_name: str, fields: list[str], domain: list[Any]) -> list[dict[str, str]]:
    if not fields:
        return []
    existing = [field for field in fields if field in env[model_name]._fields]  # noqa: F821
    if not existing:
        return []
    rows = env[model_name].sudo().search_read(domain, ["id"] + existing, limit=SAMPLE_LIMIT, order="id desc")  # noqa: F821
    return [{key: clean(value) for key, value in row.items()} for row in rows]


def looks_like_double_display(value: str) -> bool:
    parts = [part.strip() for part in re.split(r"[\r\n]+", value) if part.strip()]
    if len(parts) >= 2 and (parts[0].startswith(parts[1]) or parts[1].startswith(parts[0])):
        return True
    if len(value) >= 8 and len(value) % 2 == 0 and value[: len(value) // 2] == value[len(value) // 2 :]:
        return True
    return False


def looks_like_raw_hash(label: str, value: str) -> bool:
    text = clean(value)
    if not text or ACCOUNT_LABEL_RE.search(label):
        return False
    if text.isdigit():
        return False
    if HEX_RE.fullmatch(text):
        return True
    if "附件" in label:
        tokens = [token.strip() for token in re.split(r"[\s,;|]+", text) if token.strip()]
        return any(HASH_FILE_RE.match(token) or token.startswith(("legacy-file://", "legacy-file-id://")) for token in tokens)
    return False


def sample_token(model_name: str, fields: list[str], domain: list[Any], token: str) -> dict[str, Any] | None:
    existing = [
        field
        for field in fields
        if field in env[model_name]._fields  # noqa: F821
        and not (env[model_name]._fields[field].compute and not env[model_name]._fields[field].store)  # noqa: F821
    ]
    if not existing:
        return None
    or_domain: list[Any] = []
    for field in existing:
        if or_domain:
            or_domain.insert(0, "|")
        or_domain.append((field, "ilike", token))
    try:
        rows = env[model_name].sudo().search_read(domain + or_domain, ["id"] + existing, limit=1)  # noqa: F821
    except Exception as exc:
        return {"token": token, "error": repr(exc)}
    if not rows:
        return None
    return {"token": token, "record": {key: clean(value) for key, value in rows[0].items()}}


def status_for(row: dict[str, Any]) -> str:
    if row["model_missing"] or not row["action_id"]:
        return "FAIL_ACTION"
    if row["contract_field_count"] and row["missing_alias_fields"]:
        return "FAIL_VISIBLE_FIELD_MISSING"
    if row["delivered_count"] == 0 and row["seq"] not in ALLOWED_ZERO_SEQS:
        return "FAIL_ZERO_DATA"
    if row["critical_empty_labels"]:
        return "REVIEW_CRITICAL_EMPTY"
    if row["raw_hash_hit_count"] or row["double_display_hit_count"]:
        return "REVIEW_VISIBLE_VALUE_ANOMALY"
    return "PASS"


def report_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# SCBS55 User Visible Business Data Final Probe v1",
        "",
        f"Status: {payload['status']}",
        f"Database: {payload['database']}",
        f"Generated At: {payload['generated_at']}",
        "",
        "| seq | menu | model | count | fields | critical empty | hash | double | status |",
        "| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in payload["rows"]:
        lines.append(
            "| {seq} | {name} | {model} | {delivered_count} | {contract_field_count} | "
            "{critical_empty_count} | {raw_hash_hit_count} | {double_display_hit_count} | {status} |".format(**row)
        )
    lines.extend(
        [
            "",
            "## Review Rows",
            "",
            "```json",
            json.dumps(payload["review_rows"], ensure_ascii=False, indent=2, sort_keys=True),
            "```",
            "",
            "## Named Samples",
            "",
            "```json",
            json.dumps(payload["named_samples"], ensure_ascii=False, indent=2, sort_keys=True),
            "```",
            "",
        ]
    )
    return "\n".join(lines)


artifact_dir = artifact_root()
Plan = env["sc.legacy.user.priority.menu.plan"].sudo().with_context(active_test=False)  # noqa: F821
records = Plan.search([("source_document", "=", SOURCE_DOCUMENT)], order="priority_sequence")

result_rows: list[dict[str, Any]] = []
named_samples: list[dict[str, Any]] = []
for record in records:
    seq = int(record.priority_sequence or 0)
    model = clean(record.target_model)
    action = record.target_action_id
    domain = action_domain(action)
    items = contract_items(record)
    fields = [item["field"] for item in items]
    model_missing = bool(model and model not in env)  # noqa: F821
    delivered_count = 0
    missing_alias_fields: list[str] = []
    coverage: list[dict[str, Any]] = []
    critical_empty_labels: list[str] = []
    raw_hash_hits: list[dict[str, Any]] = []
    double_display_hits: list[dict[str, Any]] = []
    samples: list[dict[str, str]] = []

    if model and not model_missing:
        Model = env[model].sudo()  # noqa: F821
        delivered_count = Model.search_count(domain)
        missing_alias_fields = [field for field in fields if field not in Model._fields]
        samples = sample_records(model, [field for field in fields if field not in missing_alias_fields], domain)
        for item in items:
            field = item["field"]
            label = item["label"]
            full_filled = non_empty_count(model, field, domain) if field in Model._fields else 0
            if full_filled is None:
                sample_filled = sum(1 for sample in samples if clean(sample.get(field)))
                ratio = round(sample_filled / len(samples), 4) if samples else 1.0
                coverage.append(
                    {
                        "label": label,
                        "field": field,
                        "filled": sample_filled,
                        "ratio": ratio,
                        "coverage_mode": "sample_nonstored",
                        "sample_size": len(samples),
                    }
                )
                empty_for_review = bool(samples) and sample_filled == 0
            else:
                ratio = round(full_filled / delivered_count, 4) if delivered_count else 1.0
                coverage.append(
                    {
                        "label": label,
                        "field": field,
                        "filled": full_filled,
                        "ratio": ratio,
                        "coverage_mode": "full_stored",
                    }
                )
                empty_for_review = delivered_count > 0 and full_filled == 0
            if (
                delivered_count
                and label not in OPTIONAL_CRITICAL_LABELS
                and CRITICAL_LABEL_RE.search(label)
                and empty_for_review
            ):
                critical_empty_labels.append(label)
        for sample in samples:
            for item in items:
                value = clean(sample.get(item["field"]))
                if not value:
                    continue
                if looks_like_raw_hash(item["label"], value):
                    raw_hash_hits.append({"id": sample.get("id"), "label": item["label"], "value": value[:120]})
                if looks_like_double_display(value):
                    double_display_hits.append({"id": sample.get("id"), "label": item["label"], "value": value[:160]})
        for token in ("DKQRB-20260206-006", "YJSKDJ-20260410"):
            found = sample_token(model, fields, domain, token)
            if found:
                found.update({"seq": seq, "name": record.legacy_menu_name or "", "model": model})
                named_samples.append(found)

    row = {
        "seq": seq,
        "group": record.legacy_menu_group or "",
        "name": record.legacy_menu_name or "",
        "model": model,
        "model_missing": model_missing,
        "action_id": int(action.id or 0),
        "view_id": int(record.target_view_id.id or 0),
        "domain": domain,
        "legacy_source_tables": source_tables(record, domain),
        "contract_field_count": len(items),
        "delivered_count": delivered_count,
        "missing_alias_fields": missing_alias_fields,
        "critical_empty_labels": critical_empty_labels,
        "critical_empty_count": len(critical_empty_labels),
        "raw_hash_hits": raw_hash_hits[:20],
        "raw_hash_hit_count": len(raw_hash_hits),
        "double_display_hits": double_display_hits[:20],
        "double_display_hit_count": len(double_display_hits),
        "field_coverage": coverage,
        "sample_rows": samples[:5],
    }
    row["status"] = status_for(row)
    result_rows.append(row)

review_rows = [row for row in result_rows if row["status"] != "PASS"]
payload = {
    "status": "PASS" if not review_rows else "REVIEW",
    "mode": "scbs_55_user_visible_business_data_final_probe",
    "database": env.cr.dbname,  # noqa: F821
    "source_document": SOURCE_DOCUMENT,
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "row_count": len(result_rows),
    "review_count": len(review_rows),
    "pass_count": len(result_rows) - len(review_rows),
    "review_rows": review_rows,
    "named_samples": named_samples,
    "rows": result_rows,
    "db_writes": 0,
}
write_json(artifact_dir / OUTPUT_JSON_NAME, payload)
(artifact_dir / OUTPUT_REPORT_NAME).write_text(report_markdown(payload), encoding="utf-8")
print(
    "SCBS_55_USER_VISIBLE_BUSINESS_DATA_FINAL_PROBE="
    + json.dumps(
        {
            "status": payload["status"],
            "row_count": payload["row_count"],
            "pass_count": payload["pass_count"],
            "review_count": payload["review_count"],
            "output_json": str(artifact_dir / OUTPUT_JSON_NAME),
            "output_report": str(artifact_dir / OUTPUT_REPORT_NAME),
        },
        ensure_ascii=False,
        sort_keys=True,
    )
)
if review_rows:
    raise SystemExit(2)
