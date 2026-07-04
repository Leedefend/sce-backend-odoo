# SCBS Stock-In Material Mapping Workbook

## Policy

Use `sc.material.catalog` as the material management dimension. Do not promote SCBS materials into product templates/products for this acceptance path.

## Summary

- review rows: 1658
- amount: 90454874.17

## By Action

| Action | Rows | Amount |
| --- | ---: | ---: |
| confirm_exact_text_catalog_or_create_new | 28 | 3812618.16 |
| create_or_map_material_catalog | 1563 | 79110391.59 |
| manual_material_identity_required | 9 | 2238454.0 |
| review_name_spec_catalog_or_create_new | 58 | 5293410.42 |

## Split Workbooks

| Batch | Rows | Amount | Path |
| --- | ---: | ---: | --- |
| 01_manual_material_identity_required | 9 | 2238454.0 | `artifacts/migration/scbs_stock_in_material_mapping_01_manual_material_identity_required_v1.csv` |
| 02_confirm_exact_text_catalog_or_create_new | 28 | 3812618.16 | `artifacts/migration/scbs_stock_in_material_mapping_02_confirm_exact_text_catalog_or_create_new_v1.csv` |
| 03_review_name_spec_catalog_or_create_new | 58 | 5293410.42 | `artifacts/migration/scbs_stock_in_material_mapping_03_review_name_spec_catalog_or_create_new_v1.csv` |
| 04_create_or_map_material_catalog_high_amount | 158 | 60110682.76 | `artifacts/migration/scbs_stock_in_material_mapping_04_create_or_map_material_catalog_high_amount_v1.csv` |
| 05_create_or_map_material_catalog_remaining | 1405 | 18999708.83 | `artifacts/migration/scbs_stock_in_material_mapping_05_create_or_map_material_catalog_remaining_v1.csv` |
