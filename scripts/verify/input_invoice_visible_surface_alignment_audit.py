#!/usr/bin/env python3
"""Audit input invoice report visible headers against an Excel header sample.

The Excel file is used only as a header/order specification. Row values are not
written or treated as replay payload.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile


DEFAULT_SOURCE = "/home/odoo/workspace/partner_import_source/3/+进项上报639153867537031250.xlsx"
CONTAINER_SOURCE = "/tmp/input_invoice_visible_alignment.xlsx"
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
        os.getenv("INPUT_INVOICE_VISIBLE_XLSX"),
        DEFAULT_SOURCE,
        CONTAINER_SOURCE,
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return Path(candidate)
    raise RuntimeError({"input_invoice_xlsx_missing": [candidate for candidate in candidates if candidate]})


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


def tree_labels() -> tuple[list[str], list[str]]:
    Model = env["sc.invoice.registration"].sudo()  # noqa: F821
    view = env.ref("smart_construction_core.view_sc_invoice_input_report_user_tree")  # noqa: F821
    root = ET.fromstring(view.arch_db.encode("utf-8"))
    labels: list[str] = []
    fields: list[str] = []
    for node in root.iter("field"):
        name = node.get("name") or ""
        field = Model._fields.get(name)
        labels.append(node.get("string") or (field.string if field else name))
        fields.append(name)
    return labels, fields


def action_audit() -> dict[str, object]:
    action = env.ref("smart_construction_core.action_sc_invoice_input_report_user")  # noqa: F821
    view = env.ref("smart_construction_core.view_sc_invoice_input_report_user_tree")  # noqa: F821
    return {
        "action_name": action.name,
        "res_model": action.res_model,
        "domain": clean(action.domain),
        "context": clean(action.context),
        "view_id": action.view_id.id,
        "expected_view_id": view.id,
        "uses_input_report_tree": action.view_id.id == view.id,
    }


def visible_value_coverage(expected_labels: list[str], field_names: list[str]) -> dict[str, object]:
    Model = env["sc.invoice.registration"].sudo()  # noqa: F821
    records = Model.search([
        ("source_kind", "=", "input_invoice_tax"),
        ("direction", "=", "input"),
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
    return {
        "sample_size": len(records),
        "blank_counts": blank_counts,
        "examples": examples,
    }


source = source_path()
headers, source_data_rows = read_headers(source)
expected = [item for item in headers if item != "序号"]
labels, fields = tree_labels()
first_labels = labels[: len(expected)]
first_fields = fields[: len(expected)]
missing = [label for label in expected if label not in labels]
order_mismatch = [
    {"position": idx + 1, "expected": exp, "actual": act}
    for idx, (exp, act) in enumerate(zip(expected, first_labels))
    if exp != act
]
action = action_audit()
coverage = visible_value_coverage(expected, first_fields)
payload = {
    "status": "PASS" if not missing and not order_mismatch and action["uses_input_report_tree"] else "FAIL",
    "mode": "input_invoice_visible_surface_alignment_audit",
    "database": env.cr.dbname,  # noqa: F821
    "source_path": str(source),
    "source_data_rows_ignored": source_data_rows,
    "expected_headers": expected,
    "actual_first_headers": first_labels,
    "actual_first_fields": first_fields,
    "missing_headers": missing,
    "order_mismatch": order_mismatch,
    "action": action,
    "migration_value_coverage": coverage,
    "decision": "excel_used_as_header_order_spec_only; values_are_checked_against_existing_input_invoice_report_records",
}
write_json(artifact_root() / "input_invoice_visible_surface_alignment_audit.json", payload)
print("INPUT_INVOICE_VISIBLE_SURFACE_ALIGNMENT_AUDIT=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
