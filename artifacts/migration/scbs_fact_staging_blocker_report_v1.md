# SCBS Fact Staging Blocker Report

Database: `sc_prod_sim`

## Totals

| blocked_rows | blocked_amount | conflict_rows | conflict_amount |
| --- | --- | --- | --- |
| 0 | 0.0 | 551 | 51298836.24 |

## By Source And Gate

| source_table | fact_family | mapping_gate_state | row_count | amount_total | missing_entity_map | missing_project_map | missing_partner_map | conflict_project_map | conflict_partner_map |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| D_SCBSJS_ZJGL_ZJSZ_ZJRBB | fund_daily | staging_ready | 3798 | 1290762428.64 | 0 | 0 | 0 | 0 | 0 |
| T_FK_Supplier | payment | conflict | 280 | 22363058.52 | 0 | 0 | 0 | 17 | 257 |
| T_FK_Supplier | payment | staging_ready | 8850 | 342333354.87 | 0 | 0 | 0 | 0 | 0 |
| T_GYSHT_INFO | supplier_contract | conflict | 161 | 16559188.81 | 0 | 0 | 0 | 1 | 159 |
| T_GYSHT_INFO | supplier_contract | staging_ready | 1431 | 257955010.44 | 0 | 0 | 0 | 0 | 0 |
| T_RK_RKD | stock_in | conflict | 110 | 12376588.91 | 0 | 0 | 0 | 0 | 107 |
| T_RK_RKD | stock_in | staging_ready | 593 | 77961631.26 | 0 | 0 | 0 | 0 | 0 |

## Top Missing Mapping Worklist

| dimension | source_table | legacy_name | row_count | amount_total |
| --- | --- | --- | --- | --- |

## Top Conflict Mapping Worklist

| dimension | source_table | legacy_name | row_count | amount_total |
| --- | --- | --- | --- | --- |
| partner | T_GYSHT_INFO | 德阳嘉泰水泥制品有限公司 | 14 | 4683344.85 |
| partner | T_FK_Supplier | 德阳市兴明鸿混凝土有限责任公司 | 10 | 3587158.22 |
| partner | T_RK_RKD | 德阳市兴明鸿混凝土有限责任公司 | 6 | 3511531.72 |
| project | T_FK_Supplier | 公司综合平台 | 6 | 2158206.0 |
| partner | T_GYSHT_INFO | 成都长红润晨建材有限公司 | 26 | 1919713.56 |
| partner | T_FK_Supplier | 成都梦农科技有限公司 | 20 | 1795339.6 |
| partner | T_GYSHT_INFO | 四川睿杰达贸易有限公司 | 1 | 1612600.0 |
| partner | T_GYSHT_INFO | 成都梦农科技有限公司 | 9 | 1524994.7 |
| partner | T_FK_Supplier | 德阳嘉泰水泥制品有限公司 | 16 | 1456197.64 |
| partner | T_FK_Supplier | 成都长红润晨建材有限公司 | 32 | 1445471.06 |
| partner | T_GYSHT_INFO | 四川文诚管业有限公司 | 8 | 1361875.8 |
| partner | T_RK_RKD | 成都梦农科技有限公司 | 6 | 1350377.2 |
| partner | T_FK_Supplier | 四川文诚管业有限公司 | 9 | 1189277.0 |
| partner | T_GYSHT_INFO | 德阳正弘金属材料有限公司 | 18 | 1091574.69 |
| partner | T_FK_Supplier | 四川可为景观园林工程有限公司 | 13 | 1017135.9 |
| partner | T_FK_Supplier | 四川睿杰达贸易有限公司 | 7 | 1007773.0 |
| partner | T_RK_RKD | 四川睿杰达贸易有限公司 | 2 | 1007773.0 |
| partner | T_FK_Supplier | 德阳正弘金属材料有限公司 | 28 | 923405.46 |
| partner | T_FK_Supplier | 德阳市区永沁建材经营部 | 10 | 901196.57 |
| partner | T_RK_RKD | 什邡市鑫雷石材有限公司 | 10 | 863671.2 |
| partner | T_FK_Supplier | 什邡市鑫雷石材有限公司 | 2 | 863671.2 |
| partner | T_GYSHT_INFO | 什邡市鑫雷石材有限公司 | 2 | 690195.0 |
| partner | T_RK_RKD | 德阳嘉泰水泥制品有限公司 | 8 | 615356.55 |
| partner | T_RK_RKD | 德阳市区永沁建材经营部 | 7 | 610643.44 |
| partner | T_RK_RKD | 成都长红润晨建材有限公司 | 9 | 588435.0 |
| partner | T_GYSHT_INFO | 德阳市区永沁建材经营部 | 10 | 560074.0 |
| partner | T_GYSHT_INFO | 成都灿安科技有限公司 | 4 | 548799.36 |
| partner | T_FK_Supplier | 德阳市华壹商贸有限公司 | 10 | 501403.7 |
| partner | T_GYSHT_INFO | 德阳市华壹商贸有限公司 | 9 | 488002.1 |
| partner | T_RK_RKD | 德阳市区兴鑫达管材经营部 | 4 | 444772.82 |
