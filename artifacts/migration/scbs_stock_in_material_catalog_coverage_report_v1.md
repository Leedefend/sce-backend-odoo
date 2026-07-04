# SCBS Stock-In Material Catalog Coverage Report

## Business Policy

SCBS stock-in material facts use `sc.material.catalog` as the management-control dimension.
This slice should not promote historical materials into a product library.

## Summary

- distinct line material groups: 1658
- distinct legacy material IDs: 1641
- coverage counts: `{"catalog_candidate_exact_text": 128, "catalog_candidate_name_spec": 58, "catalog_ready_by_legacy_id": 1463, "missing_legacy_material_id": 9}`
- coverage amounts: `{"catalog_candidate_exact_text": 5452447.77, "catalog_candidate_name_spec": 5293410.42, "catalog_ready_by_legacy_id": 77470561.98, "missing_legacy_material_id": 2238454.0}`

## Target Baseline

| Metric | Rows |
| --- | ---: |
| product_template_legacy_material | 0 |
| product_product_total | 1 |
| sc_material_catalog | 2281189 |
| sc_material_catalog_legacy | 2281189 |

## Projection Rule

- Use `material_catalog_id` as the business fact dimension for cost statistics, budget comparison, and control reports.
- Do not run product promotion for SCBS stock-in acceptance.
- Legacy material ID matching is preferred, but this SCBS slice may use a different legacy ID namespace from the existing target catalog; text candidates are review suggestions only.
- If a formal model still requires `product_id`, use the existing system-default material only as a technical placeholder and keep `material_catalog_id` as the source of truth.
- Any future product promotion must be a separate operational decision, not a migration prerequisite.

## Artifacts

- JSON: `artifacts/migration/scbs_stock_in_material_catalog_coverage_report_v1.json`
- CSV: `artifacts/migration/scbs_stock_in_material_catalog_coverage_v1.csv`
