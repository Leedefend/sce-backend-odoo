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

from psycopg2 import sql


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
SOURCE_LINK_SPECS = (
    {"target_model": "construction.contract.income", "source_model": "construction.contract", "target_field": "contract_id", "source_field": "id"},
    {"target_model": "sc.material.inbound", "source_model": "sc.legacy.scbs.fact.staging", "target_field": "legacy_fact_id", "source_field": "id"},
    {"target_model": "sc.settlement.adjustment", "source_model": "sc.legacy.deduction.adjustment.line", "target_field": "legacy_line_id", "source_field": "legacy_line_id"},
    {"target_model": "sc.treasury.ledger", "source_model": "payment.request", "target_field": "payment_request_id", "source_field": "id"},
    {"target_model": "tender.bid", "source_model": "sc.legacy.tender.registration.fact", "target_field": "legacy_fact_id", "source_field": "id"},
)
TECHNICAL_EMPTY_VALUES = {"false", "none", "null"}
NON_BUSINESS_CREATOR_VALUES = {
    "admin",
    "administrator",
    "false",
    "none",
    "null",
    "odoobot",
    "system",
    "系统",
    "系统导入",
}
DEFAULT_REQUIRED_MODELS = ("__all__",)
_COLUMN_EXISTS_CACHE = {}


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


def column_exists(table_name, column_name):
    key = (table_name, column_name)
    if key not in _COLUMN_EXISTS_CACHE:
        with env.cr.savepoint():  # noqa: F821
            env.cr.execute(  # noqa: F821
                """
                SELECT 1
                  FROM information_schema.columns
                 WHERE table_name = %s
                   AND column_name = %s
                 LIMIT 1
                """,
                [table_name, column_name],
            )
            _COLUMN_EXISTS_CACHE[key] = bool(env.cr.fetchone())  # noqa: F821
    return _COLUMN_EXISTS_CACHE[key]


def technical_empty_count(Model, field_name):
    field = Model._fields.get(field_name)
    if not field:
        return None
    if getattr(field, "type", "") not in {"char", "text", "html", "selection"}:
        return 0
    return safe_count(Model, [(field_name, "in", ["False", "false", "None", "none", "NULL", "null"])])


def non_business_creator_count(Model, field_name):
    field = Model._fields.get(field_name)
    if not field:
        return None
    if getattr(field, "type", "") not in {"char", "text", "html", "selection"}:
        return 0
    return safe_count(Model, [(field_name, "in", sorted(NON_BUSINESS_CREATOR_VALUES | {value.title() for value in NON_BUSINESS_CREATOR_VALUES}))])


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


def best_source_fields(Model):
    fields = Model._fields
    creator_candidates = [
        name
        for name in (
            "legacy_source_created_by",
            "creator_name",
            "sc_source_created_by",
            "created_by_name",
            "actor_name",
            "source_operator",
            "entry_user_text",
        )
        if name in fields and fields[name].type in {"char", "text", "selection"} and column_exists(Model._table, name)
    ]
    time_candidates = [
        name
        for name in (
            "legacy_source_created_at",
            "created_time",
            "sc_source_created_at",
            "received_at",
            "approved_at",
            "source_time",
            "legacy_created_at",
            "entry_time",
            "registration_time",
            "opening_time",
            "import_time",
        )
        if name in fields and fields[name].type in {"char", "text", "datetime", "date"} and column_exists(Model._table, name)
    ]
    return creator_candidates, time_candidates


def _sql_text_value(table_alias, field_name):
    raw = sql.SQL("NULLIF(BTRIM({alias}.{field}::text), '')").format(
        alias=sql.Identifier(table_alias),
        field=sql.Identifier(field_name),
    )
    lower_non_business = sql.SQL(", ").join(sql.Literal(value) for value in {value.lower() for value in NON_BUSINESS_CREATOR_VALUES})
    raw_non_business = sql.SQL(", ").join(sql.Literal(value) for value in NON_BUSINESS_CREATOR_VALUES)
    return sql.SQL(
        """
        CASE
          WHEN LOWER({raw}) IN ({lower_non_business}) OR {raw} IN ({raw_non_business}) THEN NULL
          ELSE {raw}
        END
        """
    ).format(raw=raw, lower_non_business=lower_non_business, raw_non_business=raw_non_business)


def _sql_datetime_value(table_alias, field_name, field):
    if field.type == "datetime":
        return sql.SQL("{alias}.{field}").format(alias=sql.Identifier(table_alias), field=sql.Identifier(field_name))
    if field.type == "date":
        return sql.SQL("{alias}.{field}::timestamp").format(alias=sql.Identifier(table_alias), field=sql.Identifier(field_name))
    return sql.SQL(
        """
        CASE
          WHEN NULLIF(BTRIM({alias}.{field}::text), '') ~ '^[0-9]{{4}}-[0-9]{{2}}-[0-9]{{2}}'
          THEN NULLIF(BTRIM({alias}.{field}::text), '')::timestamp
          ELSE NULL
        END
        """
    ).format(alias=sql.Identifier(table_alias), field=sql.Identifier(field_name))


def source_gap_for_link(Model, Source, target_field, source_field):
    if not all(field in Model._fields for field in ("source_created_by", "source_created_at", target_field)):
        return 0
    if source_field not in Source._fields:
        return 0
    if not column_exists(Model._table, target_field) or not column_exists(Source._table, source_field):
        return 0
    creator_candidates, time_candidates = best_source_fields(Source)
    if not creator_candidates and not time_candidates:
        return 0
    source_fields = Source._fields
    creator_expr = (
        sql.SQL("COALESCE({})").format(sql.SQL(", ").join(_sql_text_value("s", field_name) for field_name in creator_candidates))
        if creator_candidates
        else sql.SQL("NULL")
    )
    time_expr = (
        sql.SQL("COALESCE({})").format(sql.SQL(", ").join(_sql_datetime_value("s", field_name, source_fields[field_name]) for field_name in time_candidates))
        if time_candidates
        else sql.SQL("NULL")
    )
    query = sql.SQL(
        """
        SELECT COUNT(*)
          FROM {target_table} AS t
          JOIN {source_table} AS s
            ON t.{target_field}::text = s.{source_field}::text
         WHERE NULLIF(BTRIM(t.{target_field}::text), '') IS NOT NULL
           AND (
                ({creator_expr} IS NOT NULL AND (t.source_created_by IS NULL OR BTRIM(t.source_created_by) = ''))
             OR ({time_expr} IS NOT NULL AND t.source_created_at IS NULL)
           )
        """
    ).format(
        target_table=sql.Identifier(Model._table),
        source_table=sql.Identifier(Source._table),
        target_field=sql.Identifier(target_field),
        source_field=sql.Identifier(source_field),
        creator_expr=creator_expr,
        time_expr=time_expr,
    )
    try:
        with env.cr.savepoint():  # noqa: F821
            env.cr.execute(query)  # noqa: F821
            return int(env.cr.fetchone()[0] or 0)  # noqa: F821
    except Exception:
        return {"error": "source_gap_query_failed"}


def source_backfill_gap_count(model_name, Model):
    gaps = 0
    links = []
    if all(field in Model._fields for field in ("legacy_source_model", "legacy_record_id")):
        with env.cr.savepoint():  # noqa: F821
            env.cr.execute(  # noqa: F821
                sql.SQL(
                    """
                    SELECT legacy_source_model, COUNT(*)
                      FROM {table}
                     WHERE legacy_source_model IS NOT NULL
                       AND legacy_record_id IS NOT NULL
                     GROUP BY legacy_source_model
                    """
                ).format(table=sql.Identifier(Model._table))
            )
            groups = list(env.cr.fetchall())  # noqa: F821
        for source_model_name, _count in groups:
            if not source_model_name or source_model_name not in env:  # noqa: F821
                continue
            Source = env[source_model_name].sudo().with_context(active_test=False)  # noqa: F821
            identity_field = next(
                (
                    field_name
                    for field_name in ("legacy_record_id", "legacy_line_id", "legacy_account_id", "legacy_material_id")
                    if field_name in Source._fields
                ),
                None,
            )
            if identity_field:
                links.append((Source, "legacy_record_id", identity_field))
    if all(field in Model._fields for field in ("legacy_fact_model", "legacy_fact_id")):
        with env.cr.savepoint():  # noqa: F821
            env.cr.execute(  # noqa: F821
                sql.SQL(
                    """
                    SELECT legacy_fact_model, COUNT(*)
                      FROM {table}
                     WHERE legacy_fact_model IS NOT NULL
                       AND legacy_fact_id IS NOT NULL
                     GROUP BY legacy_fact_model
                    """
                ).format(table=sql.Identifier(Model._table))
            )
            groups = list(env.cr.fetchall())  # noqa: F821
        for source_model_name, _count in groups:
            if source_model_name and source_model_name in env:  # noqa: F821
                links.append((env[source_model_name].sudo().with_context(active_test=False), "legacy_fact_id", "id"))  # noqa: F821
    if all(field in Model._fields for field in ("source_model", "source_res_id")):
        with env.cr.savepoint():  # noqa: F821
            env.cr.execute(  # noqa: F821
                sql.SQL(
                    """
                    SELECT source_model, COUNT(*)
                      FROM {table}
                     WHERE source_model IS NOT NULL
                       AND source_res_id IS NOT NULL
                     GROUP BY source_model
                    """
                ).format(table=sql.Identifier(Model._table))
            )
            groups = list(env.cr.fetchall())  # noqa: F821
        for source_model_name, _count in groups:
            if source_model_name and source_model_name in env:  # noqa: F821
                links.append((env[source_model_name].sudo().with_context(active_test=False), "source_res_id", "id"))  # noqa: F821
    for spec in SOURCE_LINK_SPECS:
        if spec["target_model"] == model_name and spec["source_model"] in env:  # noqa: F821
            links.append((env[spec["source_model"]].sudo().with_context(active_test=False), spec["target_field"], spec["source_field"]))  # noqa: F821
    for Source, target_field, source_field in links:
        value = source_gap_for_link(Model, Source, target_field, source_field)
        if isinstance(value, dict):
            return value
        gaps += value
    return gaps


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
    non_business_creator = None
    source_backfill_gaps = None
    if first_pair:
        creator_field, time_field = first_pair
        with_creator = safe_count(Model, [(creator_field, "!=", False)])
        with_time = safe_count(Model, [(time_field, "!=", False)])
        technical_creator = technical_empty_count(Model, creator_field)
        technical_time = technical_empty_count(Model, time_field)
        non_business_creator = non_business_creator_count(Model, creator_field)
    if all(field in fields for field in ("source_created_by", "source_created_at")):
        source_backfill_gaps = source_backfill_gap_count(model_name, Model)

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
            ("non_business_creator", non_business_creator),
            ("source_backfill_gaps", source_backfill_gaps),
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
if "__all__" in required_models:
    required_models = [row["model"] for row in rows]
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
    value = row.get("non_business_creator")
    if isinstance(value, dict):
        reasons.append("non_business_creator_error")
    elif value:
        reasons.append("non_business_creator_nonzero")
    value = row.get("source_backfill_gaps")
    if isinstance(value, dict):
        reasons.append("source_backfill_gap_error")
    elif value:
        reasons.append("source_backfill_gap_nonzero")
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
            "non_business_creator",
            "source_backfill_gaps",
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
