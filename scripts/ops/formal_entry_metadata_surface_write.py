#!/usr/bin/env python3
"""Materialize formal entry metadata fields and view surface for visible business models."""

from __future__ import annotations

import json
import os
from pathlib import Path

from lxml import etree
from psycopg2 import sql


INCLUDE_PREFIXES = ("sc.", "project.", "construction.", "payment.", "tender.")
EXCLUDE_MODELS = {
    "sc.business.category",
}
EXCLUDE_PREFIXES = (
    "sc.legacy.",
    "sc.scene",
    "sc.capability",
    "sc.pack",
    "sc.subscription",
    "sc.entitlement",
    "sc.usage",
    "sc.ops.",
    "sc.audit",
    "sc.workflow",
    "sc.dictionary",
    "sc.delete.",
    "sc.system.",
    "sc.execute.",
    "sc.edition.",
    "sc.login.",
    "sc.product.policy",
    "sc.release.",
    "sc.project.next.action",
    "project.task",
    "project.tags",
    "project.update",
    "payment.provider",
    "payment.method",
    "payment.token",
    "payment.transaction",
)
ENTRY_FIELDS = ("source_created_by", "source_created_at")
ACCEPTED_ENTRY_FIELDS = ("settlement_acceptance_creator", "settlement_acceptance_created_at")
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
TECHNICAL_EMPTY_VALUES = ("False", "false", "None", "none", "NULL", "null", "")
NON_BUSINESS_CREATOR_VALUES = (
    "admin",
    "administrator",
    "false",
    "none",
    "null",
    "odoobot",
    "system",
    "系统",
    "系统导入",
)
_COLUMN_EXISTS_CACHE = {}


def column_exists(table_name, column_name):
    key = (table_name, column_name)
    if key not in _COLUMN_EXISTS_CACHE:
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


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def collect_user_models():
    user_models = set()
    Action = env["ir.actions.act_window"].sudo()  # noqa: F821
    for action in Action.search([("res_model", "!=", False)]):
        model = action.res_model
        if model and model not in EXCLUDE_MODELS and model.startswith(INCLUDE_PREFIXES) and not model.startswith(EXCLUDE_PREFIXES):
            user_models.add(model)
    View = env["ir.ui.view"].sudo()  # noqa: F821
    for view in View.search([("model", "!=", False), ("type", "in", ["tree", "form"])]):
        model = view.model
        if model and model not in EXCLUDE_MODELS and model.startswith(INCLUDE_PREFIXES) and not model.startswith(EXCLUDE_PREFIXES):
            user_models.add(model)
    return sorted(user_models)


def clean(value):
    if value is None or value is False:
        return ""
    text = str(value).strip()
    return "" if text in TECHNICAL_EMPTY_VALUES or text.lower() in {"false", "none", "null"} else text


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


def existing_entry_pairs(Model):
    return [(creator, time) for creator, time in ENTRY_PAIRS if creator in Model._fields and time in Model._fields]


def visible_entry_pairs(model_name, Model):
    View = env["ir.ui.view"].sudo()  # noqa: F821
    views = View.search([("model", "=", model_name), ("type", "in", ["tree", "form"])])
    arch = "\n".join(view.arch_db or "" for view in views)
    return ["%s/%s" % pair for pair in existing_entry_pairs(Model) if pair[0] in arch and pair[1] in arch]


def has_accepted_entry_pair(Model):
    return all(field in Model._fields for field in ACCEPTED_ENTRY_FIELDS)


def sync_from_accepted_entry_fields(Model):
    if not all(field in Model._fields and column_exists(Model._table, field) for field in ENTRY_FIELDS):
        return 0
    if not has_accepted_entry_pair(Model):
        return 0
    if not all(column_exists(Model._table, field) for field in ACCEPTED_ENTRY_FIELDS):
        updated = 0
        for record in Model.search([]):
            vals = {}
            creator = clean(record.settlement_acceptance_creator)
            if creator and clean(record.source_created_by) != creator:
                vals["source_created_by"] = creator
            created_at = record.settlement_acceptance_created_at
            if created_at and not record.source_created_at:
                vals["source_created_at"] = created_at
            if vals:
                record.write(vals)
                updated += 1
        return updated
    query = sql.SQL(
        """
        UPDATE {table} AS t
           SET source_created_by = COALESCE(NULLIF(BTRIM(t.settlement_acceptance_creator), ''), NULLIF(BTRIM(t.source_created_by), '')),
               source_created_at = COALESCE(
                   CASE
                     WHEN NULLIF(BTRIM(t.settlement_acceptance_created_at), '') ~ '^[0-9]{{4}}-[0-9]{{2}}-[0-9]{{2}}'
                     THEN NULLIF(BTRIM(t.settlement_acceptance_created_at), '')::timestamp
                     ELSE NULL
                   END,
                   t.source_created_at
               )
         WHERE (
                NULLIF(BTRIM(t.settlement_acceptance_creator), '') IS NOT NULL
            AND COALESCE(NULLIF(BTRIM(t.source_created_by), ''), '') <> NULLIF(BTRIM(t.settlement_acceptance_creator), '')
         )
            OR (
                t.settlement_acceptance_created_at IS NOT NULL
            AND NULLIF(BTRIM(t.settlement_acceptance_created_at), '') ~ '^[0-9]{{4}}-[0-9]{{2}}-[0-9]{{2}}'
            AND (
                   t.source_created_at IS NULL
                OR t.source_created_at <> NULLIF(BTRIM(t.settlement_acceptance_created_at), '')::timestamp
            )
         )
        """
    ).format(table=sql.Identifier(Model._table))
    env.cr.execute(query)  # noqa: F821
    return int(env.cr.rowcount or 0)  # noqa: F821


def clear_non_business_existing_entry_pairs(Model):
    if has_accepted_entry_pair(Model):
        return 0
    cleared = 0
    for creator_field, _time_field in existing_entry_pairs(Model):
        field = Model._fields.get(creator_field)
        if not field or field.type not in {"char", "text", "html", "selection"}:
            continue
        query = sql.SQL(
            """
            UPDATE {table}
               SET {creator_field} = NULL
             WHERE LOWER(NULLIF(BTRIM({creator_field}::text), '')) = ANY(%s)
                OR NULLIF(BTRIM({creator_field}::text), '') = ANY(%s)
            """
        ).format(table=sql.Identifier(Model._table), creator_field=sql.Identifier(creator_field))
        env.cr.execute(query, [list(NON_BUSINESS_CREATOR_VALUES), list(NON_BUSINESS_CREATOR_VALUES)])  # noqa: F821
        cleared += int(env.cr.rowcount or 0)  # noqa: F821
    return cleared


def _sql_text_value(table_alias, field_name):
    raw = sql.SQL("NULLIF(BTRIM({alias}.{field}::text), '')").format(
        alias=sql.Identifier(table_alias),
        field=sql.Identifier(field_name),
    )
    lower_non_business = sql.SQL(", ").join(
        sql.Literal(value) for value in {value.lower() for value in NON_BUSINESS_CREATOR_VALUES}
    )
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


def _source_value_exprs(Source):
    source_fields = Source._fields
    creator_candidates, time_candidates = best_source_fields(Source)
    creator_exprs = [_sql_text_value("s", field_name) for field_name in creator_candidates]
    time_exprs = [_sql_datetime_value("s", field_name, source_fields[field_name]) for field_name in time_candidates]
    return (
        sql.SQL("COALESCE({})").format(sql.SQL(", ").join(creator_exprs)) if creator_exprs else sql.SQL("NULL"),
        sql.SQL("COALESCE({})").format(sql.SQL(", ").join(time_exprs)) if time_exprs else sql.SQL("NULL"),
        bool(creator_exprs or time_exprs),
    )


def backfill_from_source_link(Model, Source, target_field, source_field, source_domain_sql=None, source_domain_params=None):
    if not all(field in Model._fields for field in ("source_created_by", "source_created_at", target_field)):
        return 0
    if source_field not in Source._fields:
        return 0
    if not column_exists(Model._table, target_field) or not column_exists(Source._table, source_field):
        return 0
    creator_expr, time_expr, has_source_values = _source_value_exprs(Source)
    if not has_source_values:
        return 0
    source_where = sql.SQL(source_domain_sql) if source_domain_sql else sql.SQL("TRUE")
    query = sql.SQL(
        """
        UPDATE {target_table} AS t
           SET source_created_by = COALESCE(src.creator_value, NULLIF(BTRIM(t.source_created_by), '')),
               source_created_at = COALESCE(src.time_value, t.source_created_at)
          FROM (
                SELECT {source_field}::text AS source_key,
                       {creator_expr} AS creator_value,
                       {time_expr} AS time_value
                  FROM {source_table} AS s
                 WHERE {source_where}
               ) AS src
         WHERE t.{target_field}::text = src.source_key
           AND NULLIF(BTRIM(t.{target_field}::text), '') IS NOT NULL
           AND (src.creator_value IS NOT NULL OR src.time_value IS NOT NULL)
           AND (
                t.source_created_by IS NULL
             OR BTRIM(t.source_created_by) = ''
             OR t.source_created_at IS NULL
           )
        """
    ).format(
        target_table=sql.Identifier(Model._table),
        source_table=sql.Identifier(Source._table),
        source_field=sql.Identifier(source_field),
        target_field=sql.Identifier(target_field),
        creator_expr=creator_expr,
        time_expr=time_expr,
        source_where=source_where,
    )
    env.cr.execute(query, source_domain_params or [])  # noqa: F821
    return int(env.cr.rowcount or 0)  # noqa: F821


def backfill_from_direct_source_fields(Model):
    updates = 0
    if all(field in Model._fields for field in ("legacy_fact_model", "legacy_fact_id")):
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
        for source_model_name, _count in list(env.cr.fetchall()):  # noqa: F821
            if source_model_name and source_model_name in env:  # noqa: F821
                updates += backfill_from_source_link(
                    Model,
                    env[source_model_name].sudo().with_context(active_test=False),  # noqa: F821
                    "legacy_fact_id",
                    "id",
                )
    if all(field in Model._fields for field in ("source_model", "source_res_id")):
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
        for source_model_name, _count in list(env.cr.fetchall()):  # noqa: F821
            if source_model_name and source_model_name in env:  # noqa: F821
                updates += backfill_from_source_link(
                    Model,
                    env[source_model_name].sudo().with_context(active_test=False),  # noqa: F821
                    "source_res_id",
                    "id",
                )
    for spec in SOURCE_LINK_SPECS:
        if spec["target_model"] != Model._name or spec["source_model"] not in env:  # noqa: F821
            continue
        updates += backfill_from_source_link(
            Model,
            env[spec["source_model"]].sudo().with_context(active_test=False),  # noqa: F821
            spec["target_field"],
            spec["source_field"],
        )
    return updates


def backfill_from_legacy_source_model(Model):
    target_fields = Model._fields
    if not all(field in target_fields for field in ("source_created_by", "source_created_at", "legacy_source_model", "legacy_record_id")):
        return 0

    updates = 0
    env.cr.execute(  # noqa: F821
        sql.SQL(
            """
            SELECT legacy_source_model, COUNT(*)
              FROM {table}
             WHERE legacy_source_model IS NOT NULL
               AND legacy_record_id IS NOT NULL
             GROUP BY legacy_source_model
             ORDER BY legacy_source_model
            """
        ).format(table=sql.Identifier(Model._table))
    )
    source_groups = list(env.cr.fetchall())  # noqa: F821
    for source_model_name, _count in source_groups:
        if not source_model_name or source_model_name not in env:  # noqa: F821
            continue
        Source = env[source_model_name].sudo().with_context(active_test=False)  # noqa: F821
        source_fields = Source._fields
        creator_expr, time_expr, has_source_values = _source_value_exprs(Source)
        if not has_source_values:
            continue
        identity_field = next(
            (
                field_name
                for field_name in ("legacy_record_id", "legacy_line_id", "legacy_account_id", "legacy_material_id")
                if field_name in source_fields
            ),
            None,
        )
        if not identity_field:
            continue
        query = sql.SQL(
            """
            UPDATE {target_table} AS t
               SET source_created_by = COALESCE(src.creator_value, NULLIF(BTRIM(t.source_created_by), '')),
                   source_created_at = COALESCE(src.time_value, t.source_created_at)
              FROM (
                    SELECT {identity_field}::text AS legacy_record_id,
                           {creator_expr} AS creator_value,
                           {time_expr} AS time_value
                      FROM {source_table} AS s
                   ) AS src
             WHERE t.legacy_source_model = %s
               AND t.legacy_record_id::text = src.legacy_record_id
               AND (src.creator_value IS NOT NULL OR src.time_value IS NOT NULL)
               AND (
                    t.source_created_by IS NULL
                 OR BTRIM(t.source_created_by) = ''
                 OR t.source_created_at IS NULL
               )
            """
        ).format(
            target_table=sql.Identifier(Model._table),
            source_table=sql.Identifier(Source._table),
            identity_field=sql.Identifier(identity_field),
            creator_expr=creator_expr,
            time_expr=time_expr,
        )
        env.cr.execute(query, [source_model_name])  # noqa: F821
        updates += int(env.cr.rowcount or 0)  # noqa: F821
    return updates


def backfill_model(Model):
    if has_accepted_entry_pair(Model):
        return sync_from_accepted_entry_fields(Model), 0

    table = Model._table
    creator_candidates, time_candidates = best_source_fields(Model)
    clear_query = sql.SQL(
        """
        UPDATE {table} AS t
           SET source_created_by = NULL,
               source_created_at = NULL
         WHERE LOWER(NULLIF(BTRIM(t.source_created_by), '')) = ANY(%s)
            OR NULLIF(BTRIM(t.source_created_by), '') = ANY(%s)
        """
    ).format(table=sql.Identifier(table))
    env.cr.execute(clear_query, [list(NON_BUSINESS_CREATOR_VALUES), list(NON_BUSINESS_CREATOR_VALUES)])  # noqa: F821
    cleared_synthetic = env.cr.rowcount  # noqa: F821

    if not creator_candidates and not time_candidates:
        return backfill_from_legacy_source_model(Model) + backfill_from_direct_source_fields(Model), int(cleared_synthetic or 0)

    creator_exprs = [_sql_text_value("s", field_name) for field_name in creator_candidates]
    time_exprs = [_sql_datetime_value("s", field_name, Model._fields[field_name]) for field_name in time_candidates]
    creator_expr = sql.SQL("COALESCE({})").format(sql.SQL(", ").join(creator_exprs)) if creator_exprs else sql.SQL("NULL")
    time_expr = sql.SQL("COALESCE({})").format(sql.SQL(", ").join(time_exprs)) if time_exprs else sql.SQL("NULL")

    query = sql.SQL(
        """
        UPDATE {table} AS t
           SET source_created_by = COALESCE(src.creator_value, NULLIF(BTRIM(t.source_created_by), '')),
               source_created_at = COALESCE(src.time_value, t.source_created_at)
          FROM (
                SELECT id,
                       {creator_expr} AS creator_value,
                       {time_expr} AS time_value
                  FROM {table} AS s
               ) AS src
         WHERE t.id = src.id
           AND (src.creator_value IS NOT NULL OR src.time_value IS NOT NULL)
           AND (
                t.source_created_by IS NULL
             OR BTRIM(t.source_created_by) = ''
             OR LOWER(NULLIF(BTRIM(t.source_created_by), '')) = ANY(%s)
             OR NULLIF(BTRIM(t.source_created_by), '') = ANY(%s)
             OR t.source_created_at IS NULL
           )
        """
    ).format(
        table=sql.Identifier(table),
        creator_expr=creator_expr,
        time_expr=time_expr,
    )
    env.cr.execute(query, [list(NON_BUSINESS_CREATOR_VALUES), list(NON_BUSINESS_CREATOR_VALUES)])  # noqa: F821
    real_source_updates = env.cr.rowcount  # noqa: F821
    real_source_updates = (
        int(real_source_updates or 0)
        + backfill_from_legacy_source_model(Model)
        + backfill_from_direct_source_fields(Model)
    )
    return real_source_updates, int(cleared_synthetic or 0)


def _has_entry_fields(arch):
    return "source_created_by" in (arch or "") and "source_created_at" in (arch or "")


def _has_tree_entry_surface(arch):
    if _has_entry_fields(arch):
        return True
    try:
        root = _parse_arch(arch)
    except Exception:
        return False
    labels = {
        clean(node.get("string"))
        for node in root.xpath("//tree//field")
        if clean(node.get("string"))
    }
    return "录入人" in labels and "录入时间" in labels


def _model_has_tree_entry_surface(model_name):
    View = env["ir.ui.view"].sudo()  # noqa: F821
    for view in View.search([("model", "=", model_name), ("type", "=", "tree")]):
        if str(view.name or "").startswith("formal.entry.metadata."):
            continue
        if _has_tree_entry_surface(view.arch_db):
            return True
    return False


def _parse_arch(arch):
    return etree.fromstring((arch or "").encode("utf-8"))


def _tree_extension_arch(arch):
    root = _parse_arch(arch)
    if root.xpath("//tree/field"):
        expr = "//tree/field[last()]"
        position = "after"
    else:
        expr = "//tree"
        position = "inside"
    return f"""
<data>
  <xpath expr="{expr}" position="{position}">
    <field name="source_created_by" string="录入人" optional="show"/>
    <field name="source_created_at" string="录入时间" optional="show"/>
  </xpath>
</data>
"""


def _form_extension_arch(arch):
    root = _parse_arch(arch)
    if root.xpath("//form/sheet"):
        expr = "//form/sheet"
    else:
        expr = "//form"
    return f"""
<data>
  <xpath expr="{expr}" position="inside">
    <group string="录入信息">
      <field name="source_created_by" readonly="1"/>
      <field name="source_created_at" readonly="1"/>
    </group>
  </xpath>
</data>
"""


def ensure_view_extensions(model_name):
    View = env["ir.ui.view"].sudo()  # noqa: F821
    created = 0
    skipped = 0
    failed = []
    base_views = View.search([("model", "=", model_name), ("type", "in", ["tree", "form"]), ("inherit_id", "=", False)])
    model_has_tree_entry_surface = _model_has_tree_entry_surface(model_name)
    if not base_views:
        view_name = f"formal.entry.metadata.{model_name}.tree.base"
        existing = View.search([("name", "=", view_name), ("model", "=", model_name), ("type", "=", "tree")], limit=1)
        arch = """
<tree string="录入信息">
  <field name="source_created_by" string="录入人" optional="show"/>
  <field name="source_created_at" string="录入时间" optional="show"/>
</tree>
"""
        if existing:
            existing.write({"arch_db": arch})
        else:
            View.create({"name": view_name, "model": model_name, "type": "tree", "arch_db": arch})
            created += 1
        return {"created": created, "skipped": skipped, "failed": failed}
    for view in base_views:
        if view.type == "tree" and model_has_tree_entry_surface:
            skipped += 1
            continue
        if view.type != "tree" and _has_entry_fields(view.arch_db):
            skipped += 1
            continue
        extension_name = f"formal.entry.metadata.{model_name}.{view.type}.{view.id}"
        existing = View.search([("name", "=", extension_name), ("model", "=", model_name), ("inherit_id", "=", view.id)], limit=1)
        try:
            arch = _tree_extension_arch(view.arch_db) if view.type == "tree" else _form_extension_arch(view.arch_db)
            values = {
                "name": extension_name,
                "model": model_name,
                "type": view.type,
                "inherit_id": view.id,
                "arch_db": arch,
            }
            if existing:
                existing.write({"arch_db": arch})
            else:
                View.create(values)
                created += 1
        except Exception as exc:
            env.cr.rollback()  # noqa: F821
            failed.append({"view_id": view.id, "view_name": view.name, "error": "%s: %s" % (type(exc).__name__, str(exc)[:240])})
    return {"created": created, "skipped": skipped, "failed": failed}


db_name = env.cr.dbname  # noqa: F821
allowlist = {
    item.strip()
    for item in os.getenv("FORMAL_ENTRY_METADATA_DB_ALLOWLIST", db_name).split(",")
    if item.strip()
}
if db_name not in allowlist:
    raise RuntimeError({"db_name_not_allowed_for_formal_entry_metadata": db_name, "allowlist": sorted(allowlist)})

rows = []
errors = []
for model_name in collect_user_models():
    try:
        Model = env[model_name].sudo().with_context(active_test=False)  # noqa: F821
        if getattr(Model, "_abstract", False) or getattr(Model, "_transient", False) or not getattr(Model, "_auto", True):
            continue
        visible_pairs = visible_entry_pairs(model_name, Model)
        cleared_existing_non_business = clear_non_business_existing_entry_pairs(Model)
        if visible_pairs and not all(field in Model._fields for field in ENTRY_FIELDS):
            rows.append(
                {
                    "model": model_name,
                    "status": "PASS",
                    "count": int(Model.search_count([])),
                    "existing_entry_pairs": visible_pairs,
                    "real_source_updates": 0,
                    "cleared_synthetic": cleared_existing_non_business,
                    "view_extensions_created": 0,
                    "view_extensions_skipped": 0,
                    "view_failures": [],
                }
            )
            env.cr.commit()  # noqa: F821
            continue
        if not all(field in Model._fields for field in ENTRY_FIELDS):
            rows.append({"model": model_name, "status": "missing_entry_fields_after_upgrade"})
            continue
        real_source_updates, cleared_synthetic = backfill_model(Model)
        view_result = ensure_view_extensions(model_name)
        rows.append(
            {
                "model": model_name,
                "status": "PASS" if not view_result["failed"] else "FAIL",
                "count": int(Model.search_count([])),
                "real_source_updates": real_source_updates,
                "cleared_synthetic": cleared_existing_non_business + cleared_synthetic,
                "view_extensions_created": view_result["created"],
                "view_extensions_skipped": view_result["skipped"],
                "view_failures": view_result["failed"],
            }
        )
        env.cr.commit()  # noqa: F821
    except Exception as exc:
        env.cr.rollback()  # noqa: F821
        errors.append({"model": model_name, "error": "%s: %s" % (type(exc).__name__, str(exc)[:500])})

env.cr.commit()  # noqa: F821
status = "FAIL" if errors or any(row.get("status") != "PASS" for row in rows) else "PASS"
payload = {
    "status": status,
    "mode": "formal_entry_metadata_surface_write",
    "database": db_name,
    "model_count": len(rows),
    "error_count": len(errors),
    "errors": errors,
    "rows": rows,
}
output_json = artifact_root() / "formal_entry_metadata_surface_write_result_v1.json"
write_json(output_json, payload)
payload["artifact"] = str(output_json)
print("FORMAL_ENTRY_METADATA_SURFACE_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
if status != "PASS":
    raise SystemExit(1)
