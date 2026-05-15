#!/usr/bin/env python3
"""Read-only runtime gap probe for P0 daily business visible-surface specs."""

from __future__ import annotations

import json
import os
from pathlib import Path
from xml.etree import ElementTree


SOURCE_DOCUMENT = "/home/odoo/workspace/partner_import_source/老系统列表，填单页面截图.docx"
EXPECTED_ROWS = 18


def resolve_artifact_root() -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.append(Path("/mnt/artifacts/migration"))
    candidates.append(Path(f"/tmp/daily_business_visible_surface_p0/{env.cr.dbname}"))  # noqa: F821
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return candidate
        except Exception:
            continue
    return Path(f"/tmp/daily_business_visible_surface_p0/{env.cr.dbname}")  # noqa: F821


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_report(path: Path, payload: dict[str, object]) -> None:
    lines = [
        "# Daily Business Visible Surface P0 Runtime Gap Probe v1",
        "",
        f"Status: {payload['status']}",
        f"Database: {payload['database']}",
        "",
        "## Runtime Gaps",
        "",
        "| priority | entry | target model | list fields | tree matched | form matched | missing model labels |",
        "| ---: | --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for row in payload["entries"]:
        lines.append(
            "| {priority_sequence} | {legacy_menu_group}/{legacy_menu_name} | {target_model} | "
            "{list_field_count} | {tree_matched_count} | {form_matched_count} | {missing_model_label_count} |".format(
                **row
            )
        )
    lines.extend(["", "## Detail", "", "```json", json.dumps(payload["entries"], ensure_ascii=False, indent=2), "```", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def normalize(value: object) -> str:
    return str(value or "").strip().replace(" ", "").replace("\u3000", "")


def field_nodes_from_arch(arch: str) -> list[ElementTree.Element]:
    if not arch:
        return []
    try:
        root = ElementTree.fromstring(arch.encode("utf-8"))
    except Exception:
        return []
    return list(root.iter("field"))


def view_field_labels(model_name: str, view_type: str, fields_meta: dict[str, dict[str, object]]) -> set[str]:
    try:
        views = env[model_name].sudo().get_views([(False, view_type)], {})  # noqa: F821
    except Exception:
        return set()
    view = ((views.get("views") or {}).get(view_type) or {}) if isinstance(views, dict) else {}
    labels = set()
    for node in field_nodes_from_arch(str(view.get("arch") or "")):
        name = str(node.attrib.get("name") or "").strip()
        label = str(node.attrib.get("string") or "").strip()
        if not label and name:
            meta = fields_meta.get(name) or {}
            label = str(meta.get("string") or "").strip()
        if label:
            labels.add(normalize(label))
        if name:
            labels.add(normalize(name))
    return labels


artifact_root = resolve_artifact_root()
output_json = artifact_root / "daily_business_visible_surface_p0_runtime_gap_probe_result_v1.json"
output_report = artifact_root / "daily_business_visible_surface_p0_runtime_gap_probe_report_v1.md"

Plan = env["sc.legacy.user.priority.menu.plan"].sudo().with_context(active_test=False)  # noqa: F821
records = Plan.search(
    [
        ("source_document", "=", SOURCE_DOCUMENT),
        ("target_iteration", "=", "p0_daily_business_visible_surface"),
    ],
    order="priority_sequence, legacy_menu_group, legacy_menu_name",
)

entries = []
for record in records:
    target_model = str(record.target_model or "").strip()
    labels = [
        str(row.get("legacy_label") or "").strip()
        for row in (record.list_field_contract or [])
        if isinstance(row, dict) and str(row.get("legacy_label") or "").strip()
    ]
    model_exists = bool(target_model and target_model in env)  # noqa: F821
    fields_meta = env[target_model].sudo().fields_get() if model_exists else {}  # noqa: F821
    model_labels = {normalize(name) for name in fields_meta}
    model_labels.update(normalize(meta.get("string")) for meta in fields_meta.values() if isinstance(meta, dict))
    tree_labels = view_field_labels(target_model, "tree", fields_meta) if model_exists else set()
    form_labels = view_field_labels(target_model, "form", fields_meta) if model_exists else set()
    normalized_required = {normalize(label) for label in labels if normalize(label)}
    tree_missing = sorted(label for label in labels if normalize(label) not in tree_labels)
    form_missing = sorted(label for label in labels if normalize(label) not in form_labels)
    model_missing = sorted(label for label in labels if normalize(label) not in model_labels)
    entries.append(
        {
            "priority_sequence": record.priority_sequence,
            "legacy_menu_group": record.legacy_menu_group,
            "legacy_menu_name": record.legacy_menu_name,
            "target_model": target_model,
            "model_exists": model_exists,
            "target_action_id": int(record.target_action_id.id or 0),
            "list_field_count": len(labels),
            "tree_matched_count": len(normalized_required - {normalize(label) for label in tree_missing}),
            "form_matched_count": len(normalized_required - {normalize(label) for label in form_missing}),
            "model_matched_count": len(normalized_required - {normalize(label) for label in model_missing}),
            "missing_tree_labels": tree_missing,
            "missing_form_labels": form_missing,
            "missing_model_labels": model_missing,
            "missing_model_label_count": len(model_missing),
        }
    )

errors = []
if len(records) != EXPECTED_ROWS:
    errors.append({"check": "row_count", "expected": EXPECTED_ROWS, "actual": len(records)})
if any(not row["model_exists"] for row in entries):
    errors.append({"check": "target_model_exists", "entries": [row["legacy_menu_name"] for row in entries if not row["model_exists"]]})

payload = {
    "status": "PASS" if not errors else "FAIL",
    "mode": "daily_business_visible_surface_p0_runtime_gap_probe",
    "database": env.cr.dbname,  # noqa: F821
    "source_document": SOURCE_DOCUMENT,
    "expected_rows": EXPECTED_ROWS,
    "row_count": len(records),
    "entries": entries,
    "errors": errors,
    "db_writes": 0,
    "decision": "daily_business_visible_surface_p0_runtime_gap_audited" if not errors else "STOP_REVIEW_REQUIRED",
}
write_json(output_json, payload)
write_report(output_report, payload)
print("DAILY_BUSINESS_VISIBLE_SURFACE_P0_RUNTIME_GAP_PROBE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
if errors:
    raise SystemExit(2)
