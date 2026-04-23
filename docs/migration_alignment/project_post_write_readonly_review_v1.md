# Project Post-Write Readonly Review v1

## Result

WARN

## Scope

- Target database: `sc_demo`
- Target model: `project.project`
- Source write trial: `ITER-2026-04-13-1825`
- Review artifact: `artifacts/migration/project_post_write_readonly_review_v1.json`

The review was read-only. It did not create, update, or delete records.

## Summary

| Metric | Value |
| --- | ---: |
| sample rows | 30 |
| records found | 30 |
| unique identities found | 30 |
| missing identities | 0 |
| duplicate identities | 0 |
| empty names | 0 |
| rows with relation/default warning | 30 |

## Warning

All 30 records have a non-empty `stage_id`. The create-only script did not write
`stage_id`; this appears to be Odoo/project default behavior during
`project.project` creation. This must be manually accepted before expanding the
sample.

No `company_id`, `project_type_id`, or `project_category_id` values were found
by the read-only review.

## Identity Review

| `legacy_project_id` | Odoo ID | Name |
| --- | ---: | --- |
| `00a4bb196d944fa5a8c56e3bd3f1e448` | 2107 | 德阳市罗江区鄢家镇高垭村山坪塘整治项目 |
| `00c73f013e234461883beac337e8d75d` | 2108 | 石亭江-绵远河生态廊道场地平整工程 |
| `00db8d3baa894d1e8efd7acd181f6499` | 2109 | 渝数科技公司重庆数字大厦第6层办公用房装修改造项目 |
| `04c36990cc144f04b8f2423c36e5f713` | 2110 | 喀什地区一市四县带动农户养殖喀什黑鸡基础设施建设项目-喀什市一期电力 |
| `16f30c8b960c4e6dbedd7a507d96f4ce` | 2111 | 明源电力公寓小区路灯维修改造 |
| `2ea97dc724a9493ea18676d910616d8a` | 2112 | 盐亭县2024年新章路、垢巨路、刘黑路水毁恢复工程 |
| `4d5d46d841c24c629fd4ebdd4796980f` | 2113 | 大唐甘肃发电有限公司碧口水力发电厂碧口水电站右岸泄洪洞护坦防护结构改造施工 |
| `7f29aa1fea1745cf8868ec7db11261f2` | 2114 | 高地库房 |
| `910ed968bceb422f9ce302e2799da9b8` | 2115 | 西藏方向军事设施建设项目施工总承包合同90项目工程工序劳务作业 |
| `0201344da1b74e008006a7a96f90be6f` | 2116 | 四川艺术职业学院消防隐患整治工程 |
| `020eddc09afb4260a5843a84ee58d826` | 2117 | 龙泉驿区2020年人行道整治提升工程（怡安路、合聚路、玉扬路） |
| `027c5b467ae94e52aabb6f6218d310d4` | 2118 | 成渝双城经济圈川渝高竹新区制造产业园及配套基础设施建设项目（L3-1线道路及配套工程劳务分包） |
| `02df67b4ddb6469b81ed551e9b544d25` | 2119 | 剑阁县文化广电新闻出版局人才基地建设项目 |
| `037fddc6219449c3840477989cc06f82` | 2120 | 中江县仓山镇郪江桥梁工程 |
| `03f8997135504039a36557ec6e57909b` | 2121 | 工程部后油库油罐清洗 |
| `045206e3bf2f49b6b6b544b1be1aff22` | 2122 | 中国移动四川公司2025-2027年全省汇聚机房土建工程施工集中采购项目（标包4-乐山分公司）框架协议-（TD） |
| `04d0a65675424e41b8c65ba26ef48b4e` | 2123 | 中江公司变电检修班“工人先锋号”环境整治 |
| `05139ca820724561bee71e016b22fd55` | 2124 | 2022年日常维护项目（竞标12） |
| `0550ea3a2e1b4161b25a697476e344b5` | 2125 | 准环对称仿星器项目 |
| `059742d9ac094c018b91894306d5fc2d` | 2126 | ALC预制隔墙板供应及施工分包合同 |
| `069cd56871fd4307b836a3167fddf14b` | 2127 | 和田地区于田县高速公路10千伏线路迁改工程 |
| `06c94694eb3e418bb4ceb5e55a987583` | 2128 | 崴和路边坡滑坡治理 |
| `06cd855d5ede4a279a81568903836256` | 2129 | 白鹤花园修建建筑垃圾池 |
| `072425c9c9ad453eb60c137fd4215459` | 2130 | 珠峰文化旅游创意产业园区基础设施项目一期工程第三标段 |
| `076d8bcae3064dca8927f4f629bf2356` | 2131 | 中国移动四川西区二枢纽“车库改机房”土建工程 |
| `07e6484cc40d4609b0bcafcf187dd9af` | 2132 | 德阳市天府旌城石亭江河段堤防改建给水迁改工程 |
| `080a2d8ee204424a8b7edd08817eee20` | 2133 | 2017年公路水毁修复工程（双石镇） |
| `088193c97f1443b58f1489b321c1288a` | 2134 | 浪卡子县白地乡龙桑村水塘工程项目(1标段) |
| `08ac2e586f574d39a3272852fa22bf71` | 2135 | 德昌县宽裕镇花园村文化休闲广场 |
| `08fa00e1bf9d4c88bcbfa652610aa347` | 2136 | 永川区卫星中型灌区续建配套与节水改造工程 |

## Conclusion

The 30 written records are identifiable and rollback-targetable. Expansion is
not yet allowed until the `stage_id` default behavior is accepted or explicitly
handled in a later write gate.
