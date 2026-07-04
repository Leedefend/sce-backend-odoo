# SCBS Fact Staging Reconciliation

Database: `sc_prod_sim`
Status: `HAS_PROJECTION_READY_ROWS`

## Total

| row_count | amount_total | with_entity_map | with_project_map | with_partner_map | projection_ready | staging_ready | blocked | conflict |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 15190 | 2012171862.45 | 8963 | 7999 | 11376 | 15190 | 0 | 0 | 0 |

## Excluded Total

| row_count | amount_total |
| --- | --- |
| 33 | 8139399.0 |

## By Gate

| fact_family | mapping_gate_state | row_count | amount_total | with_entity_map | with_project_map | with_partner_map |
| --- | --- | --- | --- | --- | --- | --- |
| fund_daily | projection_ready | 3798 | 1290762428.64 | 3798 | 0 | 0 |
| payment | projection_ready | 9107 | 359251657.39 | 3120 | 6499 | 9095 |
| stock_in | projection_ready | 700 | 88592370.17 | 700 | 355 | 696 |
| supplier_contract | projection_ready | 1585 | 273565406.25 | 1345 | 1145 | 1585 |

## Excluded By Gate

| fact_family | mapping_gate_state | row_count | amount_total |
| --- | --- | --- | --- |
| payment | conflict | 23 | 5444756.0 |
| stock_in | conflict | 3 | 1745850.0 |
| supplier_contract | conflict | 2 | 777000.0 |
| supplier_contract | staging_ready | 5 | 171793.0 |

## By Source

| source_table | fact_family | row_count | amount_total | min_date | max_date |
| --- | --- | --- | --- | --- | --- |
| D_SCBSJS_ZJGL_ZJSZ_ZJRBB | fund_daily | 3798 | 1290762428.64 | 2024-03-02 | 2026-04-16 |
| T_FK_Supplier | payment | 9107 | 359251657.39 | 2018-09-01 | 2026-04-14 |
| T_GYSHT_INFO | supplier_contract | 1585 | 273565406.25 | 2021-10-10 | 2026-03-31 |
| T_RK_RKD | stock_in | 700 | 88592370.17 | 2021-04-20 | 2024-12-31 |

## Formal Table Counts

| model | all_count | active_count | inactive_count |
| --- | --- | --- | --- |
| res_company | 1 | 1 | 0 |
| project_project | 823 | 823 | 0 |
| res_partner | 7917 | 7913 | 4 |
| construction_contract | 6934 | 6934 | 0 |

## Conclusion

SCBS facts are imported into staging only. Formal projection remains blocked because no staged row is projection-ready.
