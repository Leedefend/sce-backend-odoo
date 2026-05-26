#!/usr/bin/env python3
"""Audit prepaid tax visible headers against an Excel header sample.

The Excel file is used only as a header/order specification. Row values are not
written or treated as replay payload.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile


DEFAULT_SOURCE = "/home/odoo/workspace/partner_import_source/3/+预缴税款639153288551406250.xlsx"
CONTAINER_SOURCE = "/tmp/prepaid_tax_visible_alignment.xlsx"
NS = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def artifact_root() -> Path:
    env_root = os.getenv("ARTIFACT_ROOT") or os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.append(Path("/mnt/artifacts/backend"))
    candidates.append(Path(f"/tmp/history_continuity/{env.cr.dbname}/audit"))  # noqa: F821
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return candidate
        except Exception:
            continue
    return Path(f"/tmp/history_continuity/{env.cr.dbname}/audit")  # noqa: F821


def clean(value: object) -> str:
    if value is False or value is None:
        return ""
    text = str(value or "").strip()
    return "" if text in {"False", "false", "None", "NULL"} else text


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def source_path() -> Path:
    candidates = [
        os.getenv("PREPAID_TAX_XLSX"),
        DEFAULT_SOURCE,
        CONTAINER_SOURCE,
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return Path(candidate)
    raise RuntimeError({"prepaid_tax_xlsx_missing": [candidate for candidate in candidates if candidate]})


def col_index(cell_ref: str) -> int:
    letters = "".join(ch for ch in cell_ref if ch.isalpha())
    index = 0
    for char in letters:
        index = index * 26 + ord(char.upper()) - 64
    return index - 1


def read_headers(path: Path) -> tuple[list[str], int]:
    with ZipFile(path) as archive:
        shared: list[str] = []
        if "xl/sharedStrings.xml" in archive.namelist():
            root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            for item in root.findall("a:si", NS):
                shared.append("".join(text.text or "" for text in item.findall(".//a:t", NS)))
        sheet = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))
        rows = sheet.findall("a:sheetData/a:row", NS)
        if not rows:
            return [], 0
        parsed_rows = 0
        first: list[str] = []
        for row in rows:
            values: list[str] = []
            for cell in row.findall("a:c", NS):
                idx = col_index(cell.attrib["r"])
                text = ""
                value_node = cell.find("a:v", NS)
                if value_node is not None:
                    text = value_node.text or ""
                    if cell.attrib.get("t") == "s":
                        text = shared[int(text)]
                elif cell.attrib.get("t") == "inlineStr":
                    text = "".join(text.text or "" for text in cell.findall(".//a:t", NS))
                while len(values) <= idx:
                    values.append("")
                values[idx] = clean(text)
            if any(values):
                parsed_rows += 1
                if not first:
                    first = values
        return first, max(parsed_rows - 1, 0)


def tree_labels():
    Model = env["sc.invoice.registration"].sudo()  # noqa: F821
    view = env.ref("smart_construction_core.view_sc_invoice_prepaid_tax_user_tree")  # noqa: F821
    root = ET.fromstring(view.arch_db.encode("utf-8"))
    labels: list[str] = []
    fields: list[str] = []
    for node in root.iter("field"):
        name = node.get("name") or ""
        field = Model._fields.get(name)
        labels.append(node.get("string") or (field.string if field else name))
        fields.append(name)
    return labels, fields


def visible_value_coverage(expected_labels: list[str], field_names: list[str]) -> dict[str, object]:
    Model = env["sc.invoice.registration"].sudo()  # noqa: F821
    records = Model.search([
        ("source_kind", "=", "prepaid_tax"),
        ("direction", "=", "prepaid"),
        ("source_origin", "=", "legacy"),
    ], order="id desc", limit=200)
    alias_by_label = dict(zip(expected_labels, field_names[: len(expected_labels)]))
    blank_counts: dict[str, int] = {}
    examples: list[dict[str, object]] = []
    for label, field_name in alias_by_label.items():
        blank = 0
        for record in records:
            value = record[field_name] if field_name in Model._fields else ""
            if not clean(value):
                blank += 1
        blank_counts[label] = blank
    for record in records[:5]:
        examples.append({
            "name": record.name,
            "legacy_source_model": record.legacy_source_model,
            "legacy_record_id": record.legacy_record_id,
            "visible": {
                label: clean(record[field_name]) if field_name in Model._fields else ""
                for label, field_name in alias_by_label.items()
            },
        })
    metadata_notes = Model.search_count([
        ("source_kind", "=", "prepaid_tax"),
        ("direction", "=", "prepaid"),
        ("active", "=", True),
        ("note", "ilike", "[migration:"),
    ])
    return {
        "sample_size": len(records),
        "blank_counts": blank_counts,
        "metadata_note_rows": metadata_notes,
        "examples": examples,
    }


def projection_coverage() -> dict[str, object]:
    Fact = env["sc.legacy.income.invoice.fact"].sudo()  # noqa: F821
    Invoice = env["sc.invoice.registration"].sudo()  # noqa: F821
    fact_domain = [("fact_type", "=", "prepaid_tax_line")]
    eligible_domain = fact_domain + [("active", "=", True), ("amount_total", "!=", 0)]
    missing_project = Fact.search(eligible_domain + [("project_id", "=", False)], order="document_date desc, id", limit=20)
    runtime_domain = [("source_kind", "=", "prepaid_tax"), ("direction", "=", "prepaid"), ("active", "=", True)]
    runtime_records = Invoice.search(runtime_domain, order="id desc", limit=200)
    status_project_name_hits: list[dict[str, object]] = []
    for record in runtime_records:
        status = clean(record.p1_visible_62e951a692ff)
        project_name = clean(record.project_id.display_name)
        if status and project_name and project_name in status:
            status_project_name_hits.append({
                "id": record.id,
                "name": record.name,
                "status": status,
                "project_name": project_name,
            })
    return {
        "fact_total": Fact.search_count(fact_domain),
        "fact_active": Fact.search_count(fact_domain + [("active", "=", True)]),
        "eligible_fact_rows": Fact.search_count(eligible_domain),
        "eligible_fact_rows_with_project_anchor": Fact.search_count(eligible_domain + [("project_id", "!=", False)]),
        "missing_project_anchor_count": Fact.search_count(eligible_domain + [("project_id", "=", False)]),
        "runtime_active_rows": Invoice.search_count(runtime_domain),
        "missing_project_anchor_examples": [
            {
                "legacy_record_id": rec.legacy_record_id,
                "document_no": rec.document_no,
                "project_legacy_id": rec.project_legacy_id,
                "project_name": rec.project_name,
                "amount_total": rec.amount_total,
                "document_state": rec.document_state,
            }
            for rec in missing_project
        ],
        "status_project_name_contamination_count": len(status_project_name_hits),
        "status_project_name_contamination_examples": status_project_name_hits[:5],
        "decision": "runtime_rows_match_project_anchored_eligible_prepaid_tax_lines",
    }


def action_context_audit() -> dict[str, object]:
    action = env.ref("smart_construction_core.action_sc_invoice_prepaid_tax_user")  # noqa: F821
    context_text = clean(action.context)
    return {
        "context": context_text,
        "has_default_project_group": "search_default_group_project" in context_text,
        "decision": "prepaid_tax_action_should_not_default_group_by_project_name",
    }


source = source_path()
headers, source_data_rows = read_headers(source)
expected = [item for item in headers if item != "序号"]
if "金额" in expected:
    amount_index = expected.index("金额")
    for offset, label in enumerate(("不含税金额", "税额"), start=1):
        if label not in expected:
            expected.insert(amount_index + offset, label)
if "附件" not in expected and "录入人" in expected:
    expected.insert(expected.index("录入人"), "附件")
if "数据类型" not in expected and "录入人" in expected:
    expected.insert(expected.index("录入人"), "数据类型")
labels, fields = tree_labels()
first_labels = labels[: len(expected)]
first_fields = fields[: len(expected)]
missing = [label for label in expected if label not in labels]
order_mismatch = [
    {"position": idx + 1, "expected": exp, "actual": act}
    for idx, (exp, act) in enumerate(zip(expected, first_labels))
    if exp != act
]
coverage = visible_value_coverage(expected, first_fields)
projection = projection_coverage()
action_context = action_context_audit()
payload = {
    "status": "PASS" if (
        not missing
        and not order_mismatch
        and coverage["metadata_note_rows"] == 0
        and projection["status_project_name_contamination_count"] == 0
        and not action_context["has_default_project_group"]
    ) else "FAIL",
    "mode": "prepaid_tax_visible_surface_alignment_audit",
    "database": env.cr.dbname,  # noqa: F821
    "source_path": str(source),
    "source_data_rows_ignored": source_data_rows,
    "expected_headers": expected,
    "actual_first_headers": first_labels,
    "actual_first_fields": first_fields,
    "missing_headers": missing,
    "order_mismatch": order_mismatch,
    "migration_value_coverage": coverage,
    "projection_coverage": projection,
    "action_context_audit": action_context,
    "decision": "excel_used_as_header_order_spec_only; values_are_checked_against_existing_migration_records",
}
write_json(artifact_root() / "prepaid_tax_visible_surface_alignment_audit.json", payload)
print("PREPAID_TAX_VISIBLE_SURFACE_ALIGNMENT_AUDIT=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
