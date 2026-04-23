# Project Sample Selection v1

## Scope

- Task: `ITER-2026-04-13-1820`
- Source: `tmp/raw/project/project.csv`
- Sample output: `data/migration_samples/project_sample_v1.csv`
- Sample size: 30 rows

This sample selection does not import legacy data. It is used only for the
no-database, no-ORM dry-run importer.

## Selection Rules

The sample was selected from the legacy CSV using the frozen safe-slice fields
only. The selection intentionally includes:

- the first available project row;
- every observed legacy company name where possible;
- `PROJECT_ENV=正式项目`, empty environment, and the single `PROJECT_ENV=测试项目`
  warning case;
- a mix of exact-covered and unresolved specialty labels;
- rows with and without `other_system_id`.

## Sample Coverage

| Dimension | Coverage |
| --- | --- |
| row count | 30 |
| company names | 7 |
| project environments | empty, `正式项目`, `测试项目` |
| specialty names | 13 |
| rows missing `other_system_id` | 3 |
| required `legacy_project_id` present | 30 / 30 |
| required `name` present | 30 / 30 |

## Selected Rows

| # | Legacy Project ID | Project Name | Legacy Company | Environment | Specialty | Other System ID |
| ---: | --- | --- | --- | --- | --- | --- |
| 1 | `00a4bb196d944fa5a8c56e3bd3f1e448` | 德阳市罗江区鄢家镇高垭村山坪塘整治项目 | 四川保盛建设集团有限公司 | empty | 房建工程 | `162253` |
| 2 | `00c73f013e234461883beac337e8d75d` | 石亭江-绵远河生态廊道场地平整工程 | 四川保盛建设集团有限公司 | 正式项目 | 市政 | `109745` |
| 3 | `00db8d3baa894d1e8efd7acd181f6499` | 渝数科技公司重庆数字大厦第6层办公用房装修改造项目 | 保盛重庆分公司 | 正式项目 | 房建工程 | `109396` |
| 4 | `04c36990cc144f04b8f2423c36e5f713` | 喀什地区一市四县带动农户养殖喀什黑鸡基础设施建设项目-喀什市一期电力 | 保盛新疆分公司 | empty | 电力工程 | `109359` |
| 5 | `16f30c8b960c4e6dbedd7a507d96f4ce` | 明源电力公寓小区路灯维修改造 | 四川保盛建设集团有限公司 | 测试项目 | 市政工程 | `109440` |
| 6 | `2ea97dc724a9493ea18676d910616d8a` | 盐亭县2024年新章路、垢巨路、刘黑路水毁恢复工程 | 保盛绵阳分公司 | empty | 公路工程 | `198589` |
| 7 | `4d5d46d841c24c629fd4ebdd4796980f` | 大唐甘肃发电有限公司碧口水力发电厂碧口水电站右岸泄洪洞护坦防护结构改造施工 | 保盛广元分公司 | empty | 水利工程 | `177128` |
| 8 | `7f29aa1fea1745cf8868ec7db11261f2` | 高地库房 | 项目实施分公司 | 正式项目 | 市政工程 | empty |
| 9 | `910ed968bceb422f9ce302e2799da9b8` | 西藏方向军事设施建设项目施工总承包合同90项目工程工序劳务作业 | 保盛西藏分公司 | empty | 房建工程 | `139653` |
| 10 | `0201344da1b74e008006a7a96f90be6f` | 四川艺术职业学院消防隐患整治工程 | 四川保盛建设集团有限公司 | 正式项目 | 专业分包 | `109506` |
| 11 | `020eddc09afb4260a5843a84ee58d826` | 龙泉驿区2020年人行道整治提升工程（怡安路、合聚路、玉扬路） | 四川保盛建设集团有限公司 | 正式项目 | 劳务工程 | `109702` |
| 12 | `027c5b467ae94e52aabb6f6218d310d4` | 成渝双城经济圈川渝高竹新区制造产业园及配套基础设施建设项目（L3-1线道路及配套工程劳务分包） | 四川保盛建设集团有限公司 | 正式项目 | 劳务工程 | `109507` |
| 13 | `02df67b4ddb6469b81ed551e9b544d25` | 剑阁县文化广电新闻出版局人才基地建设项目 | 四川保盛建设集团有限公司 | 正式项目 | 房建 | `109812` |
| 14 | `037fddc6219449c3840477989cc06f82` | 中江县仓山镇郪江桥梁工程 | 四川保盛建设集团有限公司 | 正式项目 | 市政工程 | `109716` |
| 15 | `03f8997135504039a36557ec6e57909b` | 工程部后油库油罐清洗 | 四川保盛建设集团有限公司 | empty | 专业分包 | `178417` |
| 16 | `045206e3bf2f49b6b6b544b1be1aff22` | 中国移动四川公司2025-2027年全省汇聚机房土建工程施工集中采购项目（标包4-乐山分公司）框架协议-（TD） | 四川保盛建设集团有限公司 | empty | 房建工程 | empty |
| 17 | `04d0a65675424e41b8c65ba26ef48b4e` | 中江公司变电检修班“工人先锋号”环境整治 | 四川保盛建设集团有限公司 | 正式项目 | 装修装饰 | `109703` |
| 18 | `05139ca820724561bee71e016b22fd55` | 2022年日常维护项目（竞标12） | 四川保盛建设集团有限公司 | 正式项目 | 桥梁隧道 | `109474` |
| 19 | `0550ea3a2e1b4161b25a697476e344b5` | 准环对称仿星器项目 | 四川保盛建设集团有限公司 | empty | 专业分包 | `191777` |
| 20 | `059742d9ac094c018b91894306d5fc2d` | ALC预制隔墙板供应及施工分包合同 | 四川保盛建设集团有限公司 | 正式项目 | 专业分包 | `109622` |
| 21 | `069cd56871fd4307b836a3167fddf14b` | 和田地区于田县高速公路10千伏线路迁改工程 | 四川保盛建设集团有限公司 | 正式项目 | 市政工程 | `109570` |
| 22 | `06c94694eb3e418bb4ceb5e55a987583` | 崴和路边坡滑坡治理 | 四川保盛建设集团有限公司 | empty | 公路工程 | empty |
| 23 | `06cd855d5ede4a279a81568903836256` | 白鹤花园修建建筑垃圾池 | 四川保盛建设集团有限公司 | empty | 市政工程 | `191770` |
| 24 | `072425c9c9ad453eb60c137fd4215459` | 珠峰文化旅游创意产业园区基础设施项目一期工程第三标段 | 四川保盛建设集团有限公司 | 正式项目 | 市政工程 | `109667` |
| 25 | `076d8bcae3064dca8927f4f629bf2356` | 中国移动四川西区二枢纽“车库改机房”土建工程 | 四川保盛建设集团有限公司 | 正式项目 | 装修装饰 | `109735` |
| 26 | `07e6484cc40d4609b0bcafcf187dd9af` | 德阳市天府旌城石亭江河段堤防改建给水迁改工程 | 四川保盛建设集团有限公司 | empty | 市政工程 | `115139` |
| 27 | `080a2d8ee204424a8b7edd08817eee20` | 2017年公路水毁修复工程（双石镇） | 四川保盛建设集团有限公司 | 正式项目 | 公路交通 | `109681` |
| 28 | `088193c97f1443b58f1489b321c1288a` | 浪卡子县白地乡龙桑村水塘工程项目(1标段) | 四川保盛建设集团有限公司 | empty | 水利工程 | `190048` |
| 29 | `08ac2e586f574d39a3272852fa22bf71` | 德昌县宽裕镇花园村文化休闲广场 | 四川保盛建设集团有限公司 | 正式项目 | 市政工程 | `109837` |
| 30 | `08fa00e1bf9d4c88bcbfa652610aa347` | 永川区卫星中型灌区续建配套与节水改造工程 | 四川保盛建设集团有限公司 | 正式项目 | 水利水电工程 | `109492` |
