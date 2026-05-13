# -*- coding: utf-8 -*-
"""Project legacy material stock facts into inbound/outbound documents.

Run with:
  DB_NAME=sc_demo scripts/ops/odoo_shell_exec.sh < scripts/migration/fresh_db_material_stock_document_projection_write.py
"""

import json
import os
from pathlib import Path


def artifact_root():
    root = Path(os.getenv("MIGRATION_ARTIFACT_ROOT") or "/mnt/artifacts/migration")
    try:
        root.mkdir(parents=True, exist_ok=True)
        return root
    except Exception:
        fallback = Path("/tmp/history_continuity/%s/adhoc" % env.cr.dbname)  # noqa: F821
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback


def first(*values):
    for value in values:
        text = str(value or "").strip()
        if text:
            return text
    return ""


def as_date(value):
    if not value:
        return None
    return value.date() if hasattr(value, "date") else value


def amount(value):
    return float(value or 0.0)


def partner_by_name(name):
    text = first(name)
    if not text:
        return False
    Partner = env["res.partner"].sudo()  # noqa: F821
    partner = Partner.search([("name", "=", text)], limit=1)
    if not partner:
        partner = Partner.create({"name": text, "supplier_rank": 1, "company_type": "company"})
    return partner


def catalog_for_fact(fact):
    name = first(fact.material_name, "历史材料")
    return env["sc.material.catalog"].sudo().search(  # noqa: F821
        [
            ("active", "!=", False),
            ("source_origin", "=", "legacy_stock_projection"),
            ("name", "=", name),
            ("spec_model", "=", first(fact.material_spec)),
            ("uom_text", "=", first(fact.material_uom)),
        ],
        limit=1,
    )


ARTIFACT_DIR = artifact_root()
RESULT_JSON = ARTIFACT_DIR / "fresh_db_material_stock_document_projection_write_result_v1.json"

uid = env.uid  # noqa: F821
company_id = env.company.id  # noqa: F821
MaterialLine = env["sc.material.inbound.line"].sudo()  # noqa: F821

product_id = MaterialLine._sc_default_product_id()
product = env["product.product"].sudo().browse(product_id)  # noqa: F821
uom_id = product.uom_id.id if product and product.uom_id else None
warehouse_id = MaterialLine._sc_default_warehouse_id()
location_id = MaterialLine._sc_default_location_id(warehouse_id)

env.cr.execute("SELECT COUNT(*) FROM sc_material_inbound")  # noqa: F821
inbound_before = env.cr.fetchone()[0]  # noqa: F821
env.cr.execute("SELECT COUNT(*) FROM sc_material_outbound")  # noqa: F821
outbound_before = env.cr.fetchone()[0]  # noqa: F821

env.cr.execute(  # noqa: F821
    """
    WITH source_material AS (
      SELECT DISTINCT
        COALESCE(NULLIF(material_name, ''), '历史材料') AS name,
        NULLIF(material_spec, '') AS spec_model,
        NULLIF(material_uom, '') AS uom_text
      FROM sc_legacy_material_stock_fact
      WHERE active IS TRUE
        AND fact_type IN (
          'stock_in_line', 'stock_out_line', 'material_budget_item',
          'material_lease_contract', 'material_lease_settlement'
        )
        AND NULLIF(material_name, '') IS NOT NULL
    ),
    inserted AS (
      INSERT INTO sc_material_catalog (
        name, code, spec_model, uom_text, source_origin, company_id, active,
        create_uid, create_date, write_uid, write_date
      )
      SELECT
        sm.name,
        'LEG-STOCK-' || SUBSTRING(MD5(sm.name || '|' || COALESCE(sm.spec_model, '') || '|' || COALESCE(sm.uom_text, '')) FOR 12),
        sm.spec_model,
        sm.uom_text,
        'legacy_stock_projection',
        %s,
        TRUE,
        %s,
        NOW(),
        %s,
        NOW()
      FROM source_material sm
      WHERE NOT EXISTS (
        SELECT 1
        FROM sc_material_catalog c
        WHERE c.active IS NOT FALSE
          AND c.source_origin = 'legacy_stock_projection'
          AND c.name = sm.name
          AND COALESCE(c.spec_model, '') = COALESCE(sm.spec_model, '')
          AND COALESCE(c.uom_text, '') = COALESCE(sm.uom_text, '')
      )
      RETURNING id
    )
    SELECT COUNT(*) FROM inserted
    """,
    [company_id, uid, uid],
)
catalog_created = env.cr.fetchone()[0]  # noqa: F821

env.cr.execute(  # noqa: F821
    """
    WITH source AS (
      SELECT
        f.id AS fact_id,
        f.fact_type,
        f.document_no,
        f.project_id,
        p.company_id,
        COALESCE(f.document_date, f.created_time)::date AS business_date,
        f.qty AS material_qty,
        f.amount_total,
        f.partner_name,
        f.department_name,
        f.creator_name,
        f.note
      FROM sc_legacy_material_stock_fact f
      JOIN project_project p ON p.id = f.project_id
      WHERE f.active IS TRUE
        AND f.fact_type IN ('stock_in', 'scbs_stock_in')
        AND f.project_id IS NOT NULL
    ),
    updated AS (
      UPDATE sc_material_inbound t
      SET
        name = COALESCE(NULLIF(source.document_no, ''), '历史材料入库-' || source.fact_id::text),
        project_id = source.project_id,
        inbound_date = source.business_date::date,
        warehouse_id = %s,
        dest_location_id = %s,
        keeper_id = %s,
        currency_id = rc.currency_id,
        operation_strategy = p.operation_strategy,
        note = CONCAT_WS(
          E'\n',
          '历史材料入库',
          '来源类型：' || source.fact_type,
          '来源部门：' || COALESCE(NULLIF(source.department_name, ''), ''),
          '来源供应商：' || COALESCE(NULLIF(source.partner_name, ''), ''),
          '来源经办：' || COALESCE(NULLIF(source.creator_name, ''), ''),
          NULLIF(source.note, '')
        ),
        legacy_fact_type = source.fact_type,
        sc_has_system_default = TRUE,
        sc_system_default_fields = 'warehouse_id,dest_location_id,keeper_id',
        sc_system_default_note = '历史库存事实没有稳定映射到新系统仓库/库位/仓管员，使用系统默认技术值承接；原始仓库、经办信息保留在说明与来源事实。',
        write_uid = %s,
        write_date = NOW()
      FROM source
      JOIN project_project p ON p.id = source.project_id
      LEFT JOIN res_company rc ON rc.id = p.company_id
      WHERE t.legacy_fact_model = 'sc.legacy.material.stock.fact'
        AND t.legacy_fact_id = source.fact_id
      RETURNING t.id
    ),
    inserted AS (
      INSERT INTO sc_material_inbound (
        name, project_id, inbound_date, warehouse_id, dest_location_id, keeper_id,
        currency_id, operation_strategy, state, note,
        legacy_fact_model, legacy_fact_id, legacy_fact_type,
        sc_has_system_default, sc_system_default_fields, sc_system_default_note,
        create_uid, create_date, write_uid, write_date
      )
      SELECT
        COALESCE(NULLIF(source.document_no, ''), '历史材料入库-' || source.fact_id::text),
        source.project_id,
        source.business_date::date,
        %s,
        %s,
        %s,
        rc.currency_id,
        p.operation_strategy,
        'draft',
        CONCAT_WS(
          E'\n',
          '历史材料入库',
          '来源类型：' || source.fact_type,
          '来源部门：' || COALESCE(NULLIF(source.department_name, ''), ''),
          '来源供应商：' || COALESCE(NULLIF(source.partner_name, ''), ''),
          '来源经办：' || COALESCE(NULLIF(source.creator_name, ''), ''),
          NULLIF(source.note, '')
        ),
        'sc.legacy.material.stock.fact',
        source.fact_id,
        source.fact_type,
        TRUE,
        'warehouse_id,dest_location_id,keeper_id',
        '历史库存事实没有稳定映射到新系统仓库/库位/仓管员，使用系统默认技术值承接；原始仓库、经办信息保留在说明与来源事实。',
        %s,
        NOW(),
        %s,
        NOW()
      FROM source
      JOIN project_project p ON p.id = source.project_id
      LEFT JOIN res_company rc ON rc.id = p.company_id
      WHERE NOT EXISTS (
        SELECT 1
        FROM sc_material_inbound t
        WHERE t.legacy_fact_model = 'sc.legacy.material.stock.fact'
          AND t.legacy_fact_id = source.fact_id
      )
      RETURNING id
    )
    SELECT (SELECT COUNT(*) FROM source), (SELECT COUNT(*) FROM inserted), (SELECT COUNT(*) FROM updated)
    """,
    [warehouse_id, location_id, uid, uid, warehouse_id, location_id, uid, uid, uid],
)
inbound_source, inbound_created, inbound_updated = env.cr.fetchone()  # noqa: F821

MaterialFact = env["sc.legacy.material.stock.fact"].sudo().with_context(active_test=False)  # noqa: F821
Inbound = env["sc.material.inbound"].sudo()  # noqa: F821
inbound_supplier_updated = 0
for inbound in Inbound.search(
    [
        ("legacy_fact_model", "=", "sc.legacy.material.stock.fact"),
        ("legacy_fact_id", "!=", False),
        ("supplier_id", "=", False),
    ]
):
    fact = MaterialFact.browse(inbound.legacy_fact_id).exists()
    supplier = partner_by_name(fact.partner_name if fact else "")
    if supplier:
        inbound.write({"supplier_id": supplier.id})
        inbound_supplier_updated += 1

env.cr.execute(  # noqa: F821
    """
    WITH projected AS (
      SELECT id
      FROM sc_material_inbound
      WHERE legacy_fact_model = 'sc.legacy.material.stock.fact'
    ),
    deleted AS (
      DELETE FROM sc_material_inbound_line l
      USING projected p
      WHERE l.inbound_id = p.id
      RETURNING l.id
    ),
    line_source AS (
      SELECT
        h.id AS inbound_id,
        l.id AS line_fact_id,
        l.material_name,
        l.material_spec,
        l.material_uom,
        CASE WHEN COALESCE(l.qty, 0) > 0 THEN l.qty ELSE 1 END AS qty,
        CASE
          WHEN COALESCE(l.qty, 0) > 0 THEN COALESCE(l.amount_total, 0) / NULLIF(l.qty, 0)
          ELSE 0
        END AS unit_price,
        COALESCE(l.amount_total, 0) AS amount,
        l.note,
        h.project_id,
        h.operation_strategy,
        h.currency_id,
        (
          SELECT c.id
          FROM sc_material_catalog c
          WHERE c.active IS NOT FALSE
            AND c.source_origin = 'legacy_stock_projection'
            AND c.name = COALESCE(NULLIF(l.material_name, ''), '历史材料')
            AND COALESCE(c.spec_model, '') = COALESCE(NULLIF(l.material_spec, ''), '')
            AND COALESCE(c.uom_text, '') = COALESCE(NULLIF(l.material_uom, ''), '')
          ORDER BY c.id
          LIMIT 1
        ) AS catalog_id
      FROM sc_legacy_material_stock_fact header_fact
      JOIN sc_material_inbound h
        ON h.legacy_fact_model = 'sc.legacy.material.stock.fact'
       AND h.legacy_fact_id = header_fact.id
      JOIN sc_legacy_material_stock_fact l
        ON l.legacy_parent_id = header_fact.legacy_record_id
       AND l.fact_type = 'stock_in_line'
       AND l.active IS TRUE
      WHERE header_fact.active IS TRUE
        AND header_fact.fact_type IN ('stock_in', 'scbs_stock_in')
        AND header_fact.project_id IS NOT NULL
        AND NULLIF(l.material_name, '') IS NOT NULL
    ),
    inserted AS (
      INSERT INTO sc_material_inbound_line (
        inbound_id, sequence, project_id, product_id, material_catalog_id,
        material_spec, product_uom_id, qty, currency_id, unit_price, amount,
        note, operation_strategy,
        sc_has_system_default, sc_system_default_fields, sc_system_default_note,
        create_uid, create_date, write_uid, write_date
      )
      SELECT
        inbound_id,
        ROW_NUMBER() OVER (PARTITION BY inbound_id ORDER BY line_fact_id) * 10,
        project_id,
        %s,
        catalog_id,
        material_spec,
        %s,
        qty,
        currency_id,
        unit_price,
        amount,
        CONCAT_WS(
          '；',
          '源材料：' || COALESCE(NULLIF(material_name, ''), ''),
          '源规格：' || COALESCE(NULLIF(material_spec, ''), ''),
          '源单位：' || COALESCE(NULLIF(material_uom, ''), ''),
          NULLIF(note, '')
        ),
        operation_strategy,
        TRUE,
        CASE WHEN qty = 1 AND amount <> 0 THEN 'product_id,qty,product_uom_id' ELSE 'product_id,product_uom_id' END,
        '历史库存明细保留原始材料名称/规格/单位；product_id/product_uom_id为新系统技术必填占位。',
        %s,
        NOW(),
        %s,
        NOW()
      FROM line_source
      RETURNING id
    )
    SELECT (SELECT COUNT(*) FROM deleted), (SELECT COUNT(*) FROM inserted)
    """,
    [product_id, uom_id, uid, uid],
)
inbound_lines_deleted, inbound_lines_inserted = env.cr.fetchone()  # noqa: F821

env.cr.execute(  # noqa: F821
    """
    UPDATE sc_material_inbound h
    SET
      material_name_summary = summary.material_name_summary,
      material_spec_summary = summary.material_spec_summary,
      material_uom_summary = summary.material_uom_summary,
      total_qty = summary.total_qty,
      unit_price_summary = summary.unit_price_summary,
      line_note_summary = summary.line_note_summary,
      amount_total = summary.amount_total,
      write_uid = %s,
      write_date = NOW()
    FROM (
      SELECT
        h.id,
        STRING_AGG(DISTINCT NULLIF(src.material_name, ''), '、') AS material_name_summary,
        STRING_AGG(DISTINCT NULLIF(src.material_spec, ''), '、') AS material_spec_summary,
        STRING_AGG(DISTINCT NULLIF(src.material_uom, ''), '、') AS material_uom_summary,
        SUM(l.qty) AS total_qty,
        STRING_AGG(DISTINCT TRIM(TRAILING '.' FROM TRIM(TRAILING '0' FROM l.unit_price::text)), '、') AS unit_price_summary,
        STRING_AGG(DISTINCT NULLIF(l.note, ''), '、') AS line_note_summary,
        SUM(l.amount) AS amount_total
      FROM sc_material_inbound h
      JOIN sc_material_inbound_line l ON l.inbound_id = h.id
      LEFT JOIN sc_legacy_material_stock_fact header_fact ON header_fact.id = h.legacy_fact_id
      LEFT JOIN sc_legacy_material_stock_fact src
        ON src.legacy_parent_id = header_fact.legacy_record_id
       AND src.fact_type = 'stock_in_line'
       AND src.active IS TRUE
      WHERE h.legacy_fact_model = 'sc.legacy.material.stock.fact'
      GROUP BY h.id
    ) summary
    WHERE h.id = summary.id
    """,
    [uid],
)
inbound_summaries_updated = env.cr.rowcount  # noqa: F821

env.cr.execute(  # noqa: F821
    """
    WITH source AS (
      SELECT
        f.id AS fact_id,
        f.document_no,
        f.project_id,
        p.company_id,
        COALESCE(f.document_date, f.created_time)::date AS business_date,
        f.partner_name,
        f.department_name,
        f.creator_name,
        f.note
      FROM sc_legacy_material_stock_fact f
      JOIN project_project p ON p.id = f.project_id
      WHERE f.active IS TRUE
        AND f.fact_type = 'stock_out'
        AND f.project_id IS NOT NULL
    ),
    updated AS (
      UPDATE sc_material_outbound t
      SET
        name = COALESCE(NULLIF(source.document_no, ''), '历史材料出库-' || source.fact_id::text),
        project_id = source.project_id,
        outbound_date = source.business_date::date,
        warehouse_id = %s,
        source_location_id = %s,
        keeper_id = %s,
        purpose = NULLIF(source.note, ''),
        note = CONCAT_WS(
          E'\n',
          '历史材料出库',
          '来源部门：' || COALESCE(NULLIF(source.department_name, ''), ''),
          '领用单位/对象：' || COALESCE(NULLIF(source.partner_name, ''), ''),
          '来源经办：' || COALESCE(NULLIF(source.creator_name, ''), ''),
          NULLIF(source.note, '')
        ),
        legacy_fact_type = 'stock_out',
        sc_has_system_default = TRUE,
        sc_system_default_fields = 'warehouse_id,source_location_id,keeper_id',
        sc_system_default_note = '历史库存事实没有稳定映射到新系统仓库/库位/仓管员，使用系统默认技术值承接；原始仓库、领用信息保留在说明与来源事实。',
        write_uid = %s,
        write_date = NOW()
      FROM source
      WHERE t.legacy_fact_model = 'sc.legacy.material.stock.fact'
        AND t.legacy_fact_id = source.fact_id
      RETURNING t.id
    ),
    inserted AS (
      INSERT INTO sc_material_outbound (
        name, project_id, outbound_date, warehouse_id, source_location_id, keeper_id,
        state, purpose, note,
        legacy_fact_model, legacy_fact_id, legacy_fact_type,
        sc_has_system_default, sc_system_default_fields, sc_system_default_note,
        create_uid, create_date, write_uid, write_date
      )
      SELECT
        COALESCE(NULLIF(source.document_no, ''), '历史材料出库-' || source.fact_id::text),
        source.project_id,
        source.business_date::date,
        %s,
        %s,
        %s,
        'draft',
        NULLIF(source.note, ''),
        CONCAT_WS(
          E'\n',
          '历史材料出库',
          '来源部门：' || COALESCE(NULLIF(source.department_name, ''), ''),
          '领用单位/对象：' || COALESCE(NULLIF(source.partner_name, ''), ''),
          '来源经办：' || COALESCE(NULLIF(source.creator_name, ''), ''),
          NULLIF(source.note, '')
        ),
        'sc.legacy.material.stock.fact',
        source.fact_id,
        'stock_out',
        TRUE,
        'warehouse_id,source_location_id,keeper_id',
        '历史库存事实没有稳定映射到新系统仓库/库位/仓管员，使用系统默认技术值承接；原始仓库、领用信息保留在说明与来源事实。',
        %s,
        NOW(),
        %s,
        NOW()
      FROM source
      WHERE NOT EXISTS (
        SELECT 1
        FROM sc_material_outbound t
        WHERE t.legacy_fact_model = 'sc.legacy.material.stock.fact'
          AND t.legacy_fact_id = source.fact_id
      )
      RETURNING id
    )
    SELECT (SELECT COUNT(*) FROM source), (SELECT COUNT(*) FROM inserted), (SELECT COUNT(*) FROM updated)
    """,
    [warehouse_id, location_id, uid, uid, warehouse_id, location_id, uid, uid, uid],
)
outbound_source, outbound_created, outbound_updated = env.cr.fetchone()  # noqa: F821

env.cr.execute(  # noqa: F821
    """
    WITH projected AS (
      SELECT id
      FROM sc_material_outbound
      WHERE legacy_fact_model = 'sc.legacy.material.stock.fact'
    ),
    deleted AS (
      DELETE FROM sc_material_outbound_line l
      USING projected p
      WHERE l.outbound_id = p.id
      RETURNING l.id
    ),
    line_source AS (
      SELECT
        h.id AS outbound_id,
        l.id AS line_fact_id,
        l.material_name,
        l.material_spec,
        l.material_uom,
        CASE WHEN COALESCE(l.qty, 0) > 0 THEN l.qty ELSE 1 END AS qty,
        l.note,
        h.project_id,
        (
          SELECT c.id
          FROM sc_material_catalog c
          WHERE c.active IS NOT FALSE
            AND c.source_origin = 'legacy_stock_projection'
            AND c.name = COALESCE(NULLIF(l.material_name, ''), '历史材料')
            AND COALESCE(c.spec_model, '') = COALESCE(NULLIF(l.material_spec, ''), '')
            AND COALESCE(c.uom_text, '') = COALESCE(NULLIF(l.material_uom, ''), '')
          ORDER BY c.id
          LIMIT 1
        ) AS catalog_id
      FROM sc_legacy_material_stock_fact header_fact
      JOIN sc_material_outbound h
        ON h.legacy_fact_model = 'sc.legacy.material.stock.fact'
       AND h.legacy_fact_id = header_fact.id
      JOIN sc_legacy_material_stock_fact l
        ON l.legacy_parent_id = header_fact.legacy_record_id
       AND l.fact_type = 'stock_out_line'
       AND l.active IS TRUE
      WHERE header_fact.active IS TRUE
        AND header_fact.fact_type = 'stock_out'
        AND header_fact.project_id IS NOT NULL
        AND NULLIF(l.material_name, '') IS NOT NULL
    ),
    inserted AS (
      INSERT INTO sc_material_outbound_line (
        outbound_id, sequence, project_id, product_id, material_catalog_id,
        material_spec, product_uom_id, qty, note,
        sc_has_system_default, sc_system_default_fields, sc_system_default_note,
        create_uid, create_date, write_uid, write_date
      )
      SELECT
        outbound_id,
        ROW_NUMBER() OVER (PARTITION BY outbound_id ORDER BY line_fact_id) * 10,
        project_id,
        %s,
        catalog_id,
        material_spec,
        %s,
        qty,
        CONCAT_WS(
          '；',
          '源材料：' || COALESCE(NULLIF(material_name, ''), ''),
          '源规格：' || COALESCE(NULLIF(material_spec, ''), ''),
          '源单位：' || COALESCE(NULLIF(material_uom, ''), ''),
          NULLIF(note, '')
        ),
        TRUE,
        CASE WHEN qty = 1 THEN 'product_id,qty,product_uom_id' ELSE 'product_id,product_uom_id' END,
        '历史库存明细保留原始材料名称/规格/单位；product_id/product_uom_id为新系统技术必填占位。',
        %s,
        NOW(),
        %s,
        NOW()
      FROM line_source
      RETURNING id
    )
    SELECT (SELECT COUNT(*) FROM deleted), (SELECT COUNT(*) FROM inserted)
    """,
    [product_id, uom_id, uid, uid],
)
outbound_lines_deleted, outbound_lines_inserted = env.cr.fetchone()  # noqa: F821

env.cr.execute(  # noqa: F821
    """
    WITH deleted AS (
      DELETE FROM sc_material_price
      WHERE source_model = 'sc.legacy.material.stock.fact'
        AND source_type IN ('stock_in_line', 'material_budget_item')
      RETURNING id
    ),
    source AS (
      SELECT
        f.id AS fact_id,
        f.fact_type,
        f.project_id,
        COALESCE(f.document_date, f.created_time)::date AS effective_date,
        f.material_name,
        f.material_spec,
        f.material_uom,
        f.unit_price,
        f.tax_rate,
        f.note,
        (
          SELECT c.id
          FROM sc_material_catalog c
          WHERE c.active IS NOT FALSE
            AND c.source_origin = 'legacy_stock_projection'
            AND c.name = COALESCE(NULLIF(f.material_name, ''), '历史材料')
            AND COALESCE(c.spec_model, '') = COALESCE(NULLIF(f.material_spec, ''), '')
            AND COALESCE(c.uom_text, '') = COALESCE(NULLIF(f.material_uom, ''), '')
          ORDER BY c.id
          LIMIT 1
        ) AS catalog_id
      FROM sc_legacy_material_stock_fact f
      WHERE f.active IS TRUE
        AND f.fact_type IN ('stock_in_line', 'material_budget_item')
        AND NULLIF(f.material_name, '') IS NOT NULL
        AND COALESCE(f.unit_price, 0) > 0
    ),
    inserted AS (
      INSERT INTO sc_material_price (
        material_catalog_id, project_id, price_type, currency_id, unit_price,
        tax_rate, tax_included, effective_date, source_model, source_res_id,
        source_type, note, active, create_uid, create_date, write_uid, write_date
      )
      SELECT
        catalog_id,
        project_id,
        CASE WHEN fact_type = 'stock_in_line' THEN 'latest_purchase' ELSE 'planned' END,
        %s,
        unit_price,
        COALESCE(tax_rate, 0),
        TRUE,
        COALESCE(effective_date, CURRENT_DATE),
        'sc.legacy.material.stock.fact',
        fact_id,
        fact_type,
        CONCAT_WS(E'\n', '历史材料单价', '来源类型：' || fact_type, NULLIF(note, '')),
        TRUE,
        %s,
        NOW(),
        %s,
        NOW()
      FROM source
      WHERE catalog_id IS NOT NULL
      RETURNING id
    )
    SELECT (SELECT COUNT(*) FROM deleted), (SELECT COUNT(*) FROM source), (SELECT COUNT(*) FROM inserted)
    """,
    [env.company.currency_id.id, uid, uid],  # noqa: F821
)
material_prices_deleted, material_price_source, material_prices_inserted = env.cr.fetchone()  # noqa: F821

env.cr.execute(  # noqa: F821
    """
    UPDATE sc_material_price p
    SET
      company_id = c.company_id,
      spec_model = c.spec_model,
      uom_text = c.uom_text,
      write_uid = %s,
      write_date = NOW()
    FROM sc_material_catalog c
    WHERE p.material_catalog_id = c.id
      AND p.source_model = 'sc.legacy.material.stock.fact'
      AND p.source_type IN ('stock_in_line', 'material_budget_item')
    """,
    [uid],
)
material_prices_related_updated = env.cr.rowcount  # noqa: F821

MaterialFact = env["sc.legacy.material.stock.fact"].sudo().with_context(active_test=False)  # noqa: F821
RentalOrder = env["sc.material.rental.order"].sudo()  # noqa: F821
RentalSettlement = env["sc.material.rental.settlement"].sudo()  # noqa: F821
rental_counts = {
    "order": {"source": 0, "created": 0, "updated": 0, "skipped": 0},
    "settlement": {"source": 0, "created": 0, "updated": 0, "skipped": 0},
}

rental_contract_facts = MaterialFact.search(
    [
        ("active", "=", True),
        ("project_id", "!=", False),
        ("partner_name", "!=", False),
        ("material_name", "!=", False),
        ("fact_type", "=", "material_lease_contract"),
    ]
)
rental_counts["order"]["source"] = len(rental_contract_facts)
for fact in rental_contract_facts:
    supplier = partner_by_name(fact.partner_name)
    catalog = catalog_for_fact(fact)
    if not supplier:
        rental_counts["order"]["skipped"] += 1
        continue
    qty = fact.qty or 1.0
    total = amount(fact.amount_total)
    daily_price = amount(fact.unit_price) or total
    vals = {
        "name": first(fact.document_no, fact.contract_no, "历史租赁单-%s" % fact.id),
        "project_id": fact.project_id.id,
        "supplier_id": supplier.id,
        "rental_date": as_date(fact.document_date or fact.created_time),
        "planned_return_date": as_date(fact.created_time),
        "owner_id": uid,
        "currency_id": env.company.currency_id.id,  # noqa: F821
        "state": "active" if fact.state == "legacy_confirmed" else "cancel",
        "note": "\n".join(
            item
            for item in [
                "历史周转材料租赁合同",
                "来源合同：%s" % first(fact.contract_no, fact.document_no),
                "来源状态：%s/%s" % (first(fact.document_state), first(fact.state)),
                first(fact.note),
            ]
            if item
        ),
        "legacy_fact_model": fact._name,
        "legacy_fact_id": fact.id,
        "legacy_fact_type": fact.fact_type,
        "line_ids": [
            (5, 0, 0),
            (
                0,
                0,
                {
                    "material_catalog_id": catalog.id if catalog else False,
                    "product_id": product_id,
                    "material_name": first(fact.material_name, "历史租赁材料"),
                    "material_spec": first(fact.material_spec),
                    "unit_name": first(fact.material_uom, "项"),
                    "qty": qty,
                    "rental_days": 1.0,
                    "daily_price": daily_price,
                    "note": first(fact.work_part, fact.note),
                },
            ),
        ],
    }
    existing = RentalOrder.search([("legacy_fact_model", "=", fact._name), ("legacy_fact_id", "=", fact.id)], limit=1)
    if existing:
        existing.write(vals)
        rental_counts["order"]["updated"] += 1
    else:
        RentalOrder.create(vals)
        rental_counts["order"]["created"] += 1

rental_settlement_facts = MaterialFact.search(
    [
        ("active", "=", True),
        ("project_id", "!=", False),
        ("partner_name", "!=", False),
        ("material_name", "!=", False),
        ("fact_type", "=", "material_lease_settlement"),
    ]
)
rental_counts["settlement"]["source"] = len(rental_settlement_facts)
for fact in rental_settlement_facts:
    supplier = partner_by_name(fact.partner_name)
    catalog = catalog_for_fact(fact)
    total = amount(fact.amount_total)
    if not supplier or total <= 0:
        rental_counts["settlement"]["skipped"] += 1
        continue
    order = RentalOrder.search(
        [("legacy_fact_model", "=", fact._name), ("legacy_fact_type", "=", "material_lease_contract"), ("project_id", "=", fact.project_id.id)],
        limit=1,
    )
    vals = {
        "name": first(fact.document_no, fact.contract_no, "历史租赁结算-%s" % fact.id),
        "project_id": fact.project_id.id,
        "rental_order_id": order.id if order else False,
        "supplier_id": supplier.id,
        "settlement_date": as_date(fact.document_date or fact.created_time),
        "owner_id": uid,
        "currency_id": env.company.currency_id.id,  # noqa: F821
        "state": "confirmed" if fact.state == "legacy_confirmed" else "cancel",
        "note": "\n".join(
            item
            for item in [
                "历史周转材料租赁结算",
                "来源合同：%s" % first(fact.contract_no, fact.document_no),
                "来源状态：%s/%s" % (first(fact.document_state), first(fact.state)),
                first(fact.note),
            ]
            if item
        ),
        "legacy_fact_model": fact._name,
        "legacy_fact_id": fact.id,
        "legacy_fact_type": fact.fact_type,
        "line_ids": [
            (5, 0, 0),
            (
                0,
                0,
                {
                    "material_catalog_id": catalog.id if catalog else False,
                    "product_id": product_id,
                    "material_name": first(fact.material_name, "历史租赁材料"),
                    "material_spec": first(fact.material_spec),
                    "unit_name": first(fact.material_uom, "项"),
                    "qty": fact.qty or 1.0,
                    "rental_days": 1.0,
                    "daily_price": amount(fact.unit_price) or total,
                    "damage_amount": 0.0,
                    "note": first(fact.work_part, fact.note),
                },
            ),
        ],
    }
    existing = RentalSettlement.search([("legacy_fact_model", "=", fact._name), ("legacy_fact_id", "=", fact.id)], limit=1)
    if existing:
        existing.write(vals)
        rental_counts["settlement"]["updated"] += 1
    else:
        RentalSettlement.create(vals)
        rental_counts["settlement"]["created"] += 1

env.cr.commit()  # noqa: F821

env.cr.execute("SELECT COUNT(*) FROM sc_material_inbound")  # noqa: F821
inbound_after = env.cr.fetchone()[0]  # noqa: F821
env.cr.execute("SELECT COUNT(*) FROM sc_material_outbound")  # noqa: F821
outbound_after = env.cr.fetchone()[0]  # noqa: F821
env.cr.execute(  # noqa: F821
    """
    SELECT h.name, p.name, h.material_name_summary, h.total_qty, h.amount_total
    FROM sc_material_inbound h
    JOIN project_project p ON p.id = h.project_id
    WHERE h.legacy_fact_model = 'sc.legacy.material.stock.fact'
    ORDER BY h.id
    LIMIT 5
    """
)
inbound_sample = [
    {"name": name, "project": project, "material": material, "qty": qty, "amount": float(amount or 0)}
    for name, project, material, qty, amount in env.cr.fetchall()  # noqa: F821
]
env.cr.execute(  # noqa: F821
    """
    SELECT h.name, p.name, COUNT(l.id) AS lines
    FROM sc_material_outbound h
    JOIN project_project p ON p.id = h.project_id
    LEFT JOIN sc_material_outbound_line l ON l.outbound_id = h.id
    WHERE h.legacy_fact_model = 'sc.legacy.material.stock.fact'
    GROUP BY h.id, h.name, p.name
    ORDER BY h.id
    LIMIT 5
    """
)
outbound_sample = [
    {"name": name, "project": project, "lines": lines}
    for name, project, lines in env.cr.fetchall()  # noqa: F821
]

result = {
    "status": "PASS",
    "mode": "fresh_db_material_stock_document_projection_write",
    "database": env.cr.dbname,  # noqa: F821
    "catalog_created": catalog_created,
    "product_id": product_id,
    "warehouse_id": warehouse_id,
    "location_id": location_id,
    "inbound": {
        "before": inbound_before,
        "after": inbound_after,
        "source": inbound_source,
        "created": inbound_created,
        "updated": inbound_updated,
        "supplier_updated": inbound_supplier_updated,
        "lines_deleted": inbound_lines_deleted,
        "lines_inserted": inbound_lines_inserted,
        "summaries_updated": inbound_summaries_updated,
        "sample": inbound_sample,
    },
    "outbound": {
        "before": outbound_before,
        "after": outbound_after,
        "source": outbound_source,
        "created": outbound_created,
        "updated": outbound_updated,
        "lines_deleted": outbound_lines_deleted,
        "lines_inserted": outbound_lines_inserted,
        "sample": outbound_sample,
    },
    "material_price": {
        "deleted": material_prices_deleted,
        "source": material_price_source,
        "inserted": material_prices_inserted,
        "related_updated": material_prices_related_updated,
    },
    "material_rental": rental_counts,
}
RESULT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print("FRESH_DB_MATERIAL_STOCK_DOCUMENT_PROJECTION_WRITE=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
