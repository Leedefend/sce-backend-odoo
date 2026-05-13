#!/usr/bin/env python3
"""Project legacy material budget facts into project budget surfaces.

Run inside ``odoo shell``.  This is a source-backed projection: only legacy
budget facts with a stable project anchor are materialized into user-visible
budget records.  Unanchored facts remain in the legacy fact table for later
reconciliation instead of being attached to an arbitrary project.
"""

from __future__ import annotations

import json


uid = env.uid  # noqa: F821
currency_id = env.company.currency_id.id  # noqa: F821

env.cr.execute(  # noqa: F821
    """
    WITH source AS (
      SELECT DISTINCT ON (material_code)
        material_code AS code,
        COALESCE(NULLIF(material_name, ''), material_code) AS name,
        CONCAT_WS(' / ', NULLIF(project_name, ''), NULLIF(material_spec, ''), NULLIF(material_uom, '')) AS source_note
      FROM sc_legacy_material_stock_fact
      WHERE active IS TRUE
        AND fact_type = 'material_cost_relation'
        AND project_id IS NOT NULL
        AND NULLIF(material_code, '') IS NOT NULL
      ORDER BY material_code, id
    ),
    updated AS (
      UPDATE project_cost_code target
      SET
        name = source.name,
        type = 'material',
        active = TRUE,
        note = CASE
          WHEN POSITION('历史材料成本关系投影' IN COALESCE(target.note, '')) > 0 THEN target.note
          ELSE CONCAT_WS('；', NULLIF(target.note, ''), '历史材料成本关系投影')
        END,
        write_uid = %s,
        write_date = NOW()
      FROM source
      WHERE target.code = source.code
      RETURNING target.id
    ),
    inserted AS (
      INSERT INTO project_cost_code (
        name, code, type, active, note, create_uid, create_date, write_uid, write_date
      )
      SELECT
        source.name,
        source.code,
        'material',
        TRUE,
        CONCAT_WS('；', '历史材料成本关系投影', NULLIF(source.source_note, '')),
        %s,
        NOW(),
        %s,
        NOW()
      FROM source
      WHERE NOT EXISTS (
        SELECT 1 FROM project_cost_code existing WHERE existing.code = source.code
      )
      RETURNING id
    )
    SELECT
      (SELECT COUNT(*) FROM source),
      (SELECT COUNT(*) FROM updated),
      (SELECT COUNT(*) FROM inserted)
    """,
    [uid, uid, uid],
)
cost_code_source, cost_codes_updated, cost_codes_inserted = env.cr.fetchone()  # noqa: F821

env.cr.execute(  # noqa: F821
    """
    WITH source_projects AS (
      SELECT
        project_id,
        COUNT(*) AS line_count,
        COALESCE(SUM(amount_total), 0) AS amount_total,
        MIN(COALESCE(document_date, created_time))::date AS version_date
      FROM sc_legacy_material_stock_fact
      WHERE active IS TRUE
        AND fact_type = 'material_budget_item'
        AND project_id IS NOT NULL
        AND NULLIF(material_name, '') IS NOT NULL
      GROUP BY project_id
    ),
    upserted AS (
      INSERT INTO project_budget (
        name, budget_kind, project_id, version, version_date, is_active,
        currency_id, amount_cost_target, amount_revenue_target, note,
        legacy_source_model, legacy_record_id, legacy_document_state,
        create_uid, create_date, write_uid, write_date
      )
      SELECT
        CONCAT('历史材料预算 - ', p.name),
        'material',
        s.project_id,
        'LEGACY-MATERIAL-BUDGET',
        COALESCE(s.version_date, CURRENT_DATE),
        TRUE,
        %s,
        s.amount_total,
        0,
        CONCAT('历史材料预算项投影；源事实数：', s.line_count),
        'sc.legacy.material.stock.fact',
        CONCAT('material_budget_item:project:', s.project_id),
        'legacy_confirmed',
        %s,
        NOW(),
        %s,
        NOW()
      FROM source_projects s
      JOIN project_project p ON p.id = s.project_id
      ON CONFLICT (project_id, version) DO UPDATE SET
        name = EXCLUDED.name,
        budget_kind = EXCLUDED.budget_kind,
        version_date = EXCLUDED.version_date,
        is_active = TRUE,
        currency_id = EXCLUDED.currency_id,
        amount_cost_target = EXCLUDED.amount_cost_target,
        note = EXCLUDED.note,
        legacy_source_model = EXCLUDED.legacy_source_model,
        legacy_record_id = EXCLUDED.legacy_record_id,
        legacy_document_state = EXCLUDED.legacy_document_state,
        write_uid = EXCLUDED.write_uid,
        write_date = NOW()
      RETURNING id, project_id
    )
    SELECT COUNT(*) FROM upserted
    """,
    [currency_id, uid, uid],
)
budget_headers_upserted = env.cr.fetchone()[0]  # noqa: F821

env.cr.execute(  # noqa: F821
    """
    DELETE FROM project_budget_boq_line line
    USING project_budget budget
    WHERE line.budget_id = budget.id
      AND budget.legacy_source_model = 'sc.legacy.material.stock.fact'
      AND budget.legacy_record_id LIKE 'material_budget_item:project:%'
    """
)
budget_lines_deleted = env.cr.rowcount  # noqa: F821

env.cr.execute(  # noqa: F821
    """
    WITH source AS (
      SELECT
        f.id AS fact_id,
        f.project_id,
        f.document_no,
        f.material_code,
        f.material_name,
        f.material_spec,
        f.material_uom,
        f.qty,
        f.unit_price,
        f.amount_total,
        f.note,
        b.id AS budget_id,
        ROW_NUMBER() OVER (
          PARTITION BY f.project_id
          ORDER BY COALESCE(NULLIF(f.document_no, ''), NULLIF(f.material_code, ''), f.id::text), f.id
        ) AS seq
      FROM sc_legacy_material_stock_fact f
      JOIN project_budget b
        ON b.project_id = f.project_id
       AND b.legacy_source_model = 'sc.legacy.material.stock.fact'
       AND b.legacy_record_id = CONCAT('material_budget_item:project:', f.project_id)
      WHERE f.active IS TRUE
        AND f.fact_type = 'material_budget_item'
        AND f.project_id IS NOT NULL
        AND NULLIF(f.material_name, '') IS NOT NULL
    ),
    inserted AS (
      INSERT INTO project_budget_boq_line (
        budget_id, sequence, boq_code, name, qty_bidded, price_bidded,
        measure_rule, cost_collection_method, cost_allocation_method,
        revenue_recognition, create_uid, create_date, write_uid, write_date
      )
      SELECT
        budget_id,
        seq * 10,
        COALESCE(NULLIF(material_code, ''), NULLIF(document_no, ''), fact_id::text),
        CONCAT_WS(' / ', NULLIF(material_name, ''), NULLIF(material_spec, ''), NULLIF(material_uom, '')),
        COALESCE(qty, 0),
        COALESCE(unit_price, 0),
        'qty',
        'non_contract',
        'direct',
        'progress',
        %s,
        NOW(),
        %s,
        NOW()
      FROM source
      RETURNING id
    )
    SELECT COUNT(*) FROM source
    """,
    [uid, uid],
)
budget_line_source = env.cr.fetchone()[0]  # noqa: F821

env.cr.execute(  # noqa: F821
    """
    SELECT COUNT(*) FROM project_budget_boq_line line
    JOIN project_budget budget ON budget.id = line.budget_id
    WHERE budget.legacy_source_model = 'sc.legacy.material.stock.fact'
      AND budget.legacy_record_id LIKE 'material_budget_item:project:%'
    """
)
budget_lines_inserted = env.cr.fetchone()[0]  # noqa: F821

env.cr.commit()  # noqa: F821

payload = {
    "status": "PASS",
    "counts": {
        "cost_code_source": cost_code_source,
        "cost_codes_inserted": cost_codes_inserted,
        "cost_codes_updated": cost_codes_updated,
        "budget_headers_upserted": budget_headers_upserted,
        "budget_lines_deleted": budget_lines_deleted,
        "budget_line_source": budget_line_source,
        "budget_lines_inserted": budget_lines_inserted,
    },
}
print("FRESH_DB_PROJECT_BUDGET_PROJECTION_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
