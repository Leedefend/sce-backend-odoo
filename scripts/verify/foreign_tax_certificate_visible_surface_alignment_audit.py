#!/usr/bin/env python3
"""Audit foreign tax certificate visible headers and replay coverage."""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile


DEFAULT_SOURCE = "/home/odoo/workspace/partner_import_source/3/外经证登记639153428231093750.xlsx"
CONTAINER_SOURCE = "/tmp/foreign_tax_certificate_visible_alignment.xlsx"
NS = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
CSV_SOURCE = Path("/mnt/artifacts/migration/fresh_db_legacy_payment_residual_replay_payload_v1.csv")


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
        os.getenv("FOREIGN_TAX_CERTIFICATE_XLSX"),
        DEFAULT_SOURCE,
        CONTAINER_SOURCE,
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return Path(candidate)
    raise RuntimeError({"foreign_tax_certificate_xlsx_missing": [candidate for candidate in candidates if candidate]})


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
        first: list[str] = []
        parsed_rows = 0
        for row in rows:
            values: list[str] = []
            for cell in row.findall("a:c", NS):
                idx = col_index(cell.attrib["r"])
                value = ""
                value_node = cell.find("a:v", NS)
                if value_node is not None:
                    value = value_node.text or ""
                    if cell.attrib.get("t") == "s":
                        value = shared[int(value)]
                elif cell.attrib.get("t") == "inlineStr":
                    value = "".join(text.text or "" for text in cell.findall(".//a:t", NS))
                while len(values) <= idx:
                    values.append("")
                values[idx] = clean(value)
            if any(values):
                parsed_rows += 1
                if not first:
                    first = values
        return first, max(parsed_rows - 1, 0)


def tree_labels() -> tuple[list[str], list[str]]:
    Model = env["sc.legacy.payment.residual.fact"].sudo()  # noqa: F821
    view = env.ref("smart_construction_core.view_sc_tax_certificate_registration_tree")  # noqa: F821
    root = ET.fromstring(view.arch_db.encode("utf-8"))
    labels: list[str] = []
    fields: list[str] = []
    for node in root.iter("field"):
        name = node.get("name") or ""
        field = Model._fields.get(name)
        labels.append(node.get("string") or (field.string if field else name))
        fields.append(name)
    return labels, fields


def csv_tax_certificate_rows() -> int:
    candidates = [
        Path(os.getenv("PAYMENT_RESIDUAL_REPLAY_CSV", "")) if os.getenv("PAYMENT_RESIDUAL_REPLAY_CSV") else None,
        Path("/mnt/artifacts/migration/fresh_db_legacy_payment_residual_replay_payload_v1.csv"),
        Path.cwd() / "artifacts/migration/fresh_db_legacy_payment_residual_replay_payload_v1.csv",
        CSV_SOURCE,
    ]
    for candidate in candidates:
        if candidate and candidate.exists():
            with candidate.open("r", encoding="utf-8-sig", newline="") as handle:
                return sum(1 for row in csv.DictReader(handle) if row.get("source_table") == "ZJGL_WJZ_WJZDJB")
    return 0


def runtime_coverage(expected_labels: list[str], field_names: list[str]) -> dict[str, object]:
    Model = env["sc.legacy.payment.residual.fact"].sudo()  # noqa: F821
    domain = [("payment_family", "=", "tax_certificate_registration")]
    records = Model.with_context(active_test=False).search(domain, order="created_time desc, id desc", limit=200)
    alias_by_label = dict(zip(expected_labels, field_names[: len(expected_labels)]))
    blank_counts: dict[str, int] = {}
    for label, field_name in alias_by_label.items():
        blank = 0
        for record in records:
            value = record[field_name] if field_name in Model._fields else ""
            if not clean(value):
                blank += 1
        blank_counts[label] = blank
    status_project_name_hits = []
    for record in records:
        status = clean(record.document_state_label)
        project_name = clean(record.project_name)
        if status and project_name and project_name in status:
            status_project_name_hits.append({
                "id": record.id,
                "document_no": record.document_no,
                "status": status,
                "project_name": project_name,
            })
    attachment_ref_rows = Model.with_context(active_test=False).search_count(domain + [("attachment_ref", "!=", False)])
    attachment_link_rows = 0
    unreadable_attachment_examples = []
    for record in Model.with_context(active_test=False).search(domain + [("attachment_ref", "!=", False)], limit=500):
        links = clean(record.attachment_links)
        if "legacy-file://" in links or "legacy-file-id://" in links or "/web/content/" in links:
            attachment_link_rows += 1
        elif len(unreadable_attachment_examples) < 5:
            unreadable_attachment_examples.append({
                "document_no": record.document_no,
                "attachment_ref": record.attachment_ref,
                "attachment_links": links,
            })
    examples = []
    for record in records[:5]:
        examples.append({
            "legacy_record_id": record.legacy_record_id,
            "document_no": record.document_no,
            "visible": {
                label: clean(record[field_name]) if field_name in Model._fields else ""
                for label, field_name in alias_by_label.items()
            },
        })
    return {
        "runtime_total_rows": Model.with_context(active_test=False).search_count(domain),
        "runtime_active_rows": Model.search_count(domain),
        "runtime_attachment_ref_rows": attachment_ref_rows,
        "runtime_attachment_link_rows_sampled": attachment_link_rows,
        "unreadable_attachment_examples": unreadable_attachment_examples,
        "sample_size": len(records),
        "blank_counts": blank_counts,
        "status_project_name_contamination_count": len(status_project_name_hits),
        "status_project_name_contamination_examples": status_project_name_hits[:5],
        "examples": examples,
    }


def action_context_audit() -> dict[str, object]:
    action = env.ref("smart_construction_core.action_sc_tax_certificate_registration_user")  # noqa: F821
    context_text = clean(action.context)
    return {
        "context": context_text,
        "has_default_project_group": "search_default_group_project" in context_text,
        "decision": "foreign_tax_certificate_action_should_not_default_group_by_project_name",
    }


source = source_path()
headers, source_data_rows = read_headers(source)
expected = [item for item in headers if item != "序号"]
if "附件" not in expected and "录入人" in expected:
    expected.insert(expected.index("录入人"), "附件")
labels, fields = tree_labels()
first_labels = labels[: len(expected)]
first_fields = fields[: len(expected)]
missing = [label for label in expected if label not in labels]
order_mismatch = [
    {"position": idx + 1, "expected": exp, "actual": act}
    for idx, (exp, act) in enumerate(zip(expected, first_labels))
    if exp != act
]
coverage = runtime_coverage(expected, first_fields)
action_context = action_context_audit()
csv_rows = csv_tax_certificate_rows()
payload = {
    "status": "PASS" if (
        not missing
        and not order_mismatch
        and coverage["runtime_total_rows"] == csv_rows
        and coverage["runtime_attachment_ref_rows"] == coverage["runtime_attachment_link_rows_sampled"]
        and coverage["status_project_name_contamination_count"] == 0
        and not action_context["has_default_project_group"]
    ) else "FAIL",
    "mode": "foreign_tax_certificate_visible_surface_alignment_audit",
    "database": env.cr.dbname,  # noqa: F821
    "source_path": str(source),
    "source_data_rows_ignored": source_data_rows,
    "expected_headers": expected,
    "actual_first_headers": first_labels,
    "actual_first_fields": first_fields,
    "missing_headers": missing,
    "order_mismatch": order_mismatch,
    "replay_csv_tax_certificate_rows": csv_rows,
    "runtime_coverage": coverage,
    "action_context_audit": action_context,
    "decision": "excel_used_as_header_order_spec_only; values_are_checked_against_existing_legacy_replay_records",
}
write_json(artifact_root() / "foreign_tax_certificate_visible_surface_alignment_audit.json", payload)
print("FOREIGN_TAX_CERTIFICATE_VISIBLE_SURFACE_ALIGNMENT_AUDIT=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
