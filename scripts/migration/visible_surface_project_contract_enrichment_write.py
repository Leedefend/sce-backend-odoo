# -*- coding: utf-8 -*-
"""Enrich visible project headers from uniquely attributable income contracts."""

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


RESULT_JSON = artifact_root() / "visible_surface_project_contract_enrichment_write_result_v1.json"
uid = env.uid  # noqa: F821

env.cr.execute(  # noqa: F821
    """
    WITH source AS (
      SELECT
        project_id,
        COUNT(DISTINCT partner_id) FILTER (WHERE partner_id IS NOT NULL) AS partner_count,
        MIN(partner_id) FILTER (WHERE partner_id IS NOT NULL) AS partner_id,
        COUNT(DISTINCT NULLIF(engineering_address, '')) AS address_count,
        MIN(NULLIF(engineering_address, '')) AS engineering_address,
        COUNT(DISTINCT NULLIF(legacy_contract_no, '')) AS contract_no_count,
        MIN(NULLIF(legacy_contract_no, '')) AS contract_no,
        MIN(date_contract) AS min_contract_date,
        MAX(date_contract) AS max_contract_date
      FROM construction_contract
      WHERE type = 'out'
        AND legacy_income_surface_visible IS TRUE
        AND project_id IS NOT NULL
      GROUP BY project_id
    ),
    project_address_source AS (
      SELECT
        id AS project_id,
        NULLIF(detail_address, '') AS detail_address
      FROM project_project
      WHERE NULLIF(detail_address, '') IS NOT NULL
    ),
    updated AS (
      UPDATE project_project p
      SET
        partner_id = CASE WHEN p.partner_id IS NULL AND source.partner_count = 1 THEN source.partner_id ELSE p.partner_id END,
        owner_id = CASE WHEN p.owner_id IS NULL AND source.partner_count = 1 THEN source.partner_id ELSE p.owner_id END,
        location = CASE
          WHEN COALESCE(p.location, '') = '' AND source.address_count = 1 THEN source.engineering_address
          WHEN COALESCE(p.location, '') = '' THEN project_address_source.detail_address
          ELSE p.location
        END,
        contract_no = CASE WHEN COALESCE(p.contract_no, '') = '' AND source.contract_no_count = 1 THEN source.contract_no ELSE p.contract_no END,
        date_start = CASE WHEN p.date_start IS NULL THEN source.min_contract_date ELSE p.date_start END,
        date = CASE WHEN p.date IS NULL THEN source.max_contract_date ELSE p.date END,
        write_uid = %s,
        write_date = NOW()
      FROM source
      LEFT JOIN project_address_source ON project_address_source.project_id = source.project_id
      WHERE p.id = source.project_id
        AND (
          (p.partner_id IS NULL AND source.partner_count = 1)
          OR (p.owner_id IS NULL AND source.partner_count = 1)
          OR (COALESCE(p.location, '') = '' AND source.address_count = 1)
          OR (COALESCE(p.location, '') = '' AND project_address_source.detail_address IS NOT NULL)
          OR (COALESCE(p.contract_no, '') = '' AND source.contract_no_count = 1)
          OR (p.date_start IS NULL AND source.min_contract_date IS NOT NULL)
          OR (p.date IS NULL AND source.max_contract_date IS NOT NULL)
        )
      RETURNING
        (p.partner_id = source.partner_id AND source.partner_count = 1) AS partner_filled,
        (p.owner_id = source.partner_id AND source.partner_count = 1) AS owner_filled,
        (
          (p.location = source.engineering_address AND source.address_count = 1)
          OR (p.location = project_address_source.detail_address AND project_address_source.detail_address IS NOT NULL)
        ) AS location_filled,
        (p.contract_no = source.contract_no AND source.contract_no_count = 1) AS contract_no_filled,
        (p.date_start = source.min_contract_date AND source.min_contract_date IS NOT NULL) AS date_start_filled,
        (p.date = source.max_contract_date AND source.max_contract_date IS NOT NULL) AS date_filled
    ),
    address_updated AS (
      UPDATE project_project p
      SET
        location = project_address_source.detail_address,
        write_uid = %s,
        write_date = NOW()
      FROM project_address_source
      WHERE p.id = project_address_source.project_id
        AND COALESCE(p.location, '') = ''
        AND project_address_source.detail_address IS NOT NULL
        AND NOT EXISTS (SELECT 1 FROM source WHERE source.project_id = p.id)
      RETURNING TRUE AS location_filled
    ),
    combined AS (
      SELECT
        partner_filled,
        owner_filled,
        location_filled,
        contract_no_filled,
        date_start_filled,
        date_filled
      FROM updated
      UNION ALL
      SELECT
        FALSE AS partner_filled,
        FALSE AS owner_filled,
        location_filled,
        FALSE AS contract_no_filled,
        FALSE AS date_start_filled,
        FALSE AS date_filled
      FROM address_updated
    )
    SELECT
      COUNT(*),
      COUNT(*) FILTER (WHERE partner_filled),
      COUNT(*) FILTER (WHERE owner_filled),
      COUNT(*) FILTER (WHERE location_filled),
      COUNT(*) FILTER (WHERE contract_no_filled),
      COUNT(*) FILTER (WHERE date_start_filled),
      COUNT(*) FILTER (WHERE date_filled)
    FROM combined
    """,
    [uid, uid],
)
(
    updated_projects,
    partner_filled,
    owner_filled,
    location_filled,
    contract_no_filled,
    date_start_filled,
    date_filled,
) = env.cr.fetchone()  # noqa: F821
env.cr.commit()  # noqa: F821

result = {
    "status": "PASS",
    "mode": "visible_surface_project_contract_enrichment_write",
    "database": env.cr.dbname,  # noqa: F821
    "updated_projects": updated_projects,
    "partner_filled": partner_filled,
    "owner_filled": owner_filled,
    "location_filled": location_filled,
    "contract_no_filled": contract_no_filled,
    "date_start_filled": date_start_filled,
    "date_filled": date_filled,
}
RESULT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print("VISIBLE_SURFACE_PROJECT_CONTRACT_ENRICHMENT_WRITE=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
