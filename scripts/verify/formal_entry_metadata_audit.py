#!/usr/bin/env python3
"""Audit source-entry metadata coverage on formal user-facing business models.

Run inside ``odoo shell``:
ENV=dev ENV_FILE=.env.dev DB_NAME=sc_demo make verify.formal_entry_metadata.audit
"""

from __future__ import annotations

import csv
import json
import os
import sys
from collections import Counter, OrderedDict
from pathlib import Path


INCLUDE_PREFIXES = ("sc.", "project.", "construction.", "payment.", "tender.")
EXCLUDE_PREFIXES = (
    "sc.legacy.",
    "sc.scene",
    "sc.capability",
    "sc.pack",
    "sc.subscription",
    "sc.entitlement",
    "sc.usage",
    "sc.audit",
    "sc.workflow",
    "sc.dictionary",
    "sc.delete.",
    "sc.system.",
    "sc.execute.",
    "sc.project.next.action",
    "project.task",
    "project.tags",
    "project.update",
    "payment.provider",
    "payment.method",
    "payment.token",
    "payment.transaction",
)
ENTRY_PAIRS = (
    ("legacy_source_created_by", "legacy_source_created_at"),
    ("creator_name", "created_time"),
    ("source_created_by", "source_created_at"),
    ("sc_source_created_by", "sc_source_created_at"),
)
TECHNICAL_EMPTY_VALUES = {"false", "none", "null"}
DEFAULT_REQUIRED_MODELS = ("project.project",)


def clean(value):
    if value is None or value is False:
        return ""
    text = str(value).strip()
    return "" if text.lower() in TECHNICAL_EMPTY_VALUES else text


def artifact_root() -> Path:
    raw = os.getenv("MIGRATION_ARTIFACT_ROOT") or os.getenv("FORMAL_ENTRY_METADATA_ARTIFACT_ROOT")
    candidates = [Path(raw)] if raw else []
    candidates.extend([Path("/mnt/artifacts/backend"), Path(f"/tmp/formal_entry_metadata/{env.cr.dbname}")])  # noqa: F821
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


def safe_count(Model, domain=None):
    try:
        with env.cr.savepoint():  # noqa: F821
            return int(Model.search_count(domain or []))
    except Exception as exc:
        return {"error": "%s: %s" % (type(exc).__name__, str(exc)[:240])}


def technical_empty_count(Model, field_name):
    field = Model._fields.get(field_name)
    if not field:
        return None
    if getattr(field, "type", "") not in {"char", "text", "html", "selection"}:
        return 0
    return safe_count(Model, [(field_name, "in", ["False", "false", "None", "none", "NULL", "null"])])


def collect_user_models():
    user_models = set()
    Action = env["ir.actions.act_window"].sudo()  # noqa: F821
    for action in Action.search([("res_model", "!=", False)]):
        model = action.res_model
        if model and model.startswith(INCLUDE_PREFIXES) and not model.startswith(EXCLUDE_PREFIXES):
            user_models.add(model)
    View = env["ir.ui.view"].sudo()  # noqa: F821
    for view in View.search([("model", "!=", False), ("type", "in", ["tree", "form"])]):
        model = view.model
        if model and model.startswith(INCLUDE_PREFIXES) and not model.startswith(EXCLUDE_PREFIXES):
            user_models.add(model)
    return sorted(user_models)


def audit_model(model_name):
    Model = env[model_name].sudo().with_context(active_test=False)  # noqa: F821
    if getattr(Model, "_abstract", False) or getattr(Model, "_transient", False) or not getattr(Model, "_auto", True):
        return None

    fields = Model._fields
    Action = env["ir.actions.act_window"].sudo()  # noqa: F821
    View = env["ir.ui.view"].sudo()  # noqa: F821
    actions = Action.search([("res_model", "=", model_name)])
    views = View.search([("model", "=", model_name), ("type", "in", ["tree", "form"])])
    arch_text = "\n".join(v.arch_db or "" for v in views)
    present_pairs = [(a, b) for a, b in ENTRY_PAIRS if a in fields and b in fields]
    visible_pairs = [(a, b) for a, b in ENTRY_PAIRS if a in arch_text and b in arch_text]

    first_pair = present_pairs[0] if present_pairs else None
    with_creator = None
    with_time = None
    technical_creator = None
    technical_time = None
    if first_pair:
        creator_field, time_field = first_pair
        with_creator = safe_count(Model, [(creator_field, "!=", False)])
        with_time = safe_count(Model, [(time_field, "!=", False)])
        technical_creator = technical_empty_count(Model, creator_field)
        technical_time = technical_empty_count(Model, time_field)

    if present_pairs and visible_pairs:
        state = "ok_visible"
    elif present_pairs:
        state = "has_fields_not_visible"
    else:
        state = "missing_fields"

    return OrderedDict(
        [
            ("model", model_name),
            ("description", getattr(Model, "_description", "") or ""),
            ("count", safe_count(Model)),
            ("actions", len(actions)),
            ("views", len(views)),
            ("present_pairs", ["%s/%s" % pair for pair in present_pairs]),
            ("visible_pairs", ["%s/%s" % pair for pair in visible_pairs]),
            ("with_creator", with_creator),
            ("with_time", with_time),
            ("technical_creator", technical_creator),
            ("technical_time", technical_time),
            ("state", state),
        ]
    )


rows = []
errors = []
for model_name in collect_user_models():
    try:
        row = audit_model(model_name)
        if row:
            rows.append(row)
    except Exception as exc:
        env.cr.rollback()  # noqa: F821
        errors.append({"model": model_name, "error": "%s: %s" % (type(exc).__name__, str(exc)[:500])})

rows_by_model = {row["model"]: row for row in rows}
required_models = [
    item.strip()
    for item in os.getenv("FORMAL_ENTRY_METADATA_REQUIRED_MODELS", ",".join(DEFAULT_REQUIRED_MODELS)).split(",")
    if item.strip()
]
required_failures = []
for model_name in required_models:
    row = rows_by_model.get(model_name)
    if not row:
        required_failures.append({"model": model_name, "reason": "not_audited"})
        continue
    reasons = []
    if row["state"] != "ok_visible":
        reasons.append("metadata_pair_not_visible")
    for key in ("technical_creator", "technical_time"):
        value = row.get(key)
        if isinstance(value, dict):
            reasons.append("%s_error" % key)
        elif value:
            reasons.append("%s_nonzero" % key)
    if reasons:
        required_failures.append({"model": model_name, "reason": ",".join(reasons), "row": row})

state_counts = Counter(row["state"] for row in rows)
result = OrderedDict(
    [
        ("status", "FAIL" if errors or required_failures else "PASS"),
        ("mode", "formal_entry_metadata_audit"),
        ("database", env.cr.dbname),  # noqa: F821
        ("audited_user_models", len(rows)),
        ("state_counts", dict(sorted(state_counts.items()))),
        ("required_models", required_models),
        ("required_failures", required_failures),
        ("errors", errors),
        ("rows", rows),
    ]
)

root = artifact_root()
json_path = root / "formal_entry_metadata_audit_result_v1.json"
csv_path = root / "formal_entry_metadata_audit_rows_v1.csv"
json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
with csv_path.open("w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(
        handle,
        fieldnames=[
            "model",
            "description",
            "count",
            "actions",
            "views",
            "present_pairs",
            "visible_pairs",
            "with_creator",
            "with_time",
            "technical_creator",
            "technical_time",
            "state",
        ],
    )
    writer.writeheader()
    for row in rows:
        writer.writerow({key: json.dumps(row[key], ensure_ascii=False) if isinstance(row.get(key), list) else row.get(key) for key in writer.fieldnames})

result["artifact_json"] = str(json_path)
result["artifact_csv"] = str(csv_path)
print("FORMAL_ENTRY_METADATA_AUDIT=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
if result["status"] != "PASS":
    sys.exit(1)
