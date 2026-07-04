# SCBS Stock-In Detail Readiness Report

## Conclusion

SCBS stock-in has usable line-level legacy detail, but formal projection is blocked until SCBS materials are mapped to `sc.material.catalog`.

## Key Counts

| Metric | Rows | Amount |
| --- | ---: | ---: |
| active_headers | 703 | 90338220.17 |
| active_headers_with_lines | 700 | 90454874.17 |
| active_lines | 2209 | 90454874.17 |
| active_headers_without_lines | 3 | .00 |
| line_catalog_match_by_clid_id | 2197 | 88216420.17 |
| line_without_catalog_id_match | 12 | 2238454.00 |

## Line Coverage

- active lines: 2209
- with legacy material ID: 2197
- with material name: 2208
- with unit: 2159
- with quantity: 2177
- with price: 2177
- distinct legacy material IDs: 1641
- distinct material names: 870

## Target Baseline

- product templates: 1
- product variants: 1
- material catalog rows: 2279734
- formal material inbound documents: 0

## Projection Gate

- Do not create formal `sc.material.inbound` rows from header totals only.
- Use `sc.material.catalog` as the business material dimension for cost statistics, budget comparison, and management control.
- Do not promote SCBS historical materials into product templates/products as part of this acceptance path.
- First map legacy materials from `T_Base_MaterialDetail` and line `CLID/CLMC/GGXH/DW` to material catalog rows.
- After material mapping, generate source-tagged inbound headers and lines using `T_RK_RKD.ID` and `T_RK_RKDCB.ID` as duplicate keys.
- Six active headers have zero header amount but non-zero line amount; keep line amount as factual detail and flag these headers for review.

## Artifacts

- JSON: `artifacts/migration/scbs_stock_in_detail_readiness_report_v1.json`
- Summary CSV: `artifacts/migration/scbs_stock_in_detail_readiness_summary_v1.csv`
- Mismatch examples: `artifacts/migration/scbs_stock_in_detail_mismatch_examples_v1.csv`
- Top materials: `artifacts/migration/scbs_stock_in_top_materials_v1.csv`
