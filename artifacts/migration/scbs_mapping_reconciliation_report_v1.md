# SCBS Mapping Reconciliation

Database: `sc_prod_sim`
Status: `BLOCK_FORMAL_FACT_PROJECTION`

## Gate Summary

| Dimension | Candidates | Confirmed | Unconfirmed | Conflicts | Mapped targets | Fact rows | Amount signal |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| business_entity | 12 | 0 | 12 | 0 | 12 | 10638 | 1790066407.44 |
| project | 43 | 0 | 43 | 2 | 1 | 8017 | 466134237.43 |
| partner | 549 | 0 | 549 | 32 | 113 | 1115 | 0.00 |

## Detailed Split

| Dimension | Suggested state | Mapping state | Match method | Candidates | Mapped targets | Fact rows | Amount signal |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| business_entity | labor | candidate |  | 2 | 2 | 1660 | 210435711.68 |
| business_entity | platform | candidate |  | 1 | 1 | 1048 | 13207512.15 |
| business_entity | trade | candidate |  | 5 | 5 | 4945 | 1237628081.85 |
| business_entity | unknown | candidate |  | 4 | 4 | 2985 | 328795101.76 |
| project | not_real_project_review | conflict | none | 2 | 0 | 18 | 2170006.0 |
| project | project_candidate | candidate | exact | 1 | 1 | 363 | 31019536.48 |
| project | project_candidate | candidate | fuzzy | 12 | 0 | 3317 | 191867309.96 |
| project | project_candidate | candidate | none | 16 | 0 | 4187 | 230582290.54 |
| project | single_source_project_candidate | candidate | fuzzy | 3 | 0 | 34 | 4724375.72 |
| project | single_source_project_candidate | candidate | none | 9 | 0 | 98 | 5770718.73 |
| partner | duplicate_across_carriers | candidate | exact_name | 99 | 99 | 205 |  |
| partner | duplicate_across_carriers | candidate | multiple | 19 | 0 | 39 |  |
| partner | duplicate_across_carriers | candidate | none | 311 | 0 | 642 |  |
| partner | duplicate_same_carrier_or_empty_tax | candidate | exact_name | 14 | 14 | 28 |  |
| partner | duplicate_same_carrier_or_empty_tax | candidate | multiple | 11 | 0 | 22 |  |
| partner | duplicate_same_carrier_or_empty_tax | candidate | none | 63 | 0 | 118 |  |
| partner | tax_code_conflict | conflict | exact_name | 3 | 0 | 7 |  |
| partner | tax_code_conflict | conflict | multiple | 3 | 0 | 5 |  |
| partner | tax_code_conflict | conflict | none | 19 | 0 | 36 |  |
| partner | tax_code_conflict | conflict | tax_code | 7 | 0 | 13 |  |

## Largest Unresolved Examples

| Dimension | Legacy key | Legacy name | State | Fact rows | Amount signal |
| --- | --- | --- | --- | ---: | ---: |
| business_entity | `95f1fe93331842488d5469ad771a1543` | 德阳泰诚硕商贸有限公司 | candidate | 1214 | 383103993.42 |
| business_entity | `af1d4b6f50504cfd9c6b0b13065fecff` | 四川世旺鑫润商贸有限公司 | candidate | 1595 | 305412446.55 |
| business_entity | `547603a871bd42c5b19681683626a314` | 四川迈投建筑工程有限公司 | candidate | 1548 | 214296736.75 |
| business_entity | `306434aba43f4128b4ab6d8a6b289674` | 四川晟博通达商贸有限公司 | candidate | 870 | 212633363.35 |
| business_entity | `88ca50467a784725aa4b42467b549e21` | 德阳市博众建材销售有限公司 | candidate | 598 | 212190437.11 |
| business_entity | `b8bc05aace5149f2af36878e9c030f4c` | 四川鑫垚建筑劳务有限公司 | candidate | 1124 | 159023433.13 |
| business_entity | `fa8bdd0d90aa4585bf8c27011d01b6d5` | 四川翔驰恒瑞商贸有限公司 | candidate | 668 | 124287841.42 |
| business_entity | `ad4866a0a8a24b629a87165d98be5948` | 四川宏政嘉斯建筑工程有限公司 | candidate | 735 | 73281963.05 |
| business_entity | `8e63129abde54614ae66ef7df8f91046` | 四川宏川建筑劳务有限公司 | candidate | 536 | 51412278.55 |
| business_entity | `0d7cd766eb9f4d23b53761e593148e25` | 德阳森元路面工程有限公司 | candidate | 479 | 34769657.22 |
| project | `旌阳区供水项目——柏隆净水厂` | 旌阳区供水项目——柏隆净水厂 | candidate | 1082 | 80565147.13 |
| project | `高新产业园配套项目（包2）` | 高新产业园配套项目（包2） | candidate | 715 | 53969657.86 |
| project | `高新产业园配套项目（包3）` | 高新产业园配套项目（包3） | candidate | 526 | 41693664.61 |
| project | `三星堆环线基础设施改造` | 三星堆环线基础设施改造 | candidate | 487 | 40570598.45 |
| project | `2023年高标准农田改造提升-东美村` | 2023年高标准农田改造提升-东美村 | candidate | 363 | 31019536.48 |
| project | `二重厂西路等4条道路工程` | 二重厂西路等4条道路工程 | candidate | 678 | 30999034.82 |
| project | `旌阳区供水项目——柏隆供水管网` | 旌阳区供水项目——柏隆供水管网 | candidate | 426 | 24169122.39 |
| project | `澜沧江西路（苗山街-蓥华山路）` | 澜沧江西路（苗山街-蓥华山路） | candidate | 441 | 16596414.15 |
| project | `2024高标准农田建设项目-龙泉村` | 2024高标准农田建设项目-龙泉村 | candidate | 64 | 16353265.39 |
| project | `龙泉山路二段(赣江路-信江路)` | 龙泉山路二段(赣江路-信江路) | candidate | 334 | 13130246.22 |
| partner | `郑红明||duplicate_across_carriers` | 郑红明 | candidate | 5 |  |
| partner | `旌阳区新豪五金机电商贸部||duplicate_across_carriers` | 旌阳区新豪五金机电商贸部 | candidate | 4 |  |
| partner | `旌阳区芝英五金经营部||duplicate_across_carriers` | 旌阳区芝英五金经营部 | candidate | 4 |  |
| partner | `李合贵||duplicate_across_carriers` | 李合贵 | candidate | 4 |  |
| partner | `周路林||duplicate_across_carriers` | 周路林 | candidate | 4 |  |
| partner | `德阳经开区科纳机械租赁部||duplicate_across_carriers` | 德阳经开区科纳机械租赁部 | candidate | 3 |  |
| partner | `成都梦农科技有限公司|91510184ma641plm9p|tax_code_conflict` | 成都梦农科技有限公司 | conflict | 3 |  |
| partner | `德阳市区海旺建材经营部||duplicate_across_carriers` | 德阳市区海旺建材经营部 | candidate | 3 |  |
| partner | `四川晟博通达商贸有限公司||duplicate_across_carriers` | 四川晟博通达商贸有限公司 | candidate | 3 |  |
| partner | `成都市林楠家俱有限公司||duplicate_across_carriers` | 成都市林楠家俱有限公司 | candidate | 3 |  |

## Conclusion

Formal fact projection is blocked until required mapping rows are confirmed. Staging import can proceed only if it preserves raw legacy keys and mapping state.
