# SCBS55 迁移资产包冻结专题 v1

状态：`TOPIC_OPEN`

分支：`topic/scbs55-migration-asset-freeze`

## 目标

把 SCBS55 全量数据迁移从“运行态产物 + 临时在线核对 + 手工补差”推进为可复核、可重放、可交付的资产包。

首批 6 个用户反馈页面只是高风险验收切片，用来验证专题方法是否正确；它不是本专题边界。本专题边界是完整迁移资产包，包括 `migration_assets/`、`artifacts/migration/` 离线 payload、历史重放脚本、生产初始化入口、全量用户可见面和资产交付门禁。

本专题的判断标准不是“新系统数量看起来一致”，而是：

- 全量迁移发布包可按 lock 拉取、校验、解包、重放。
- 旧系统在线菜单配置、默认过滤条件、列表接口总数可复核。
- 旧系统行级身份集合和新系统承载集合可复核，并逐步从 6 页扩展到 42 个用户可见面。
- 新系统用户可见菜单浏览器总数和字段可复核。
- 数据补齐逻辑在迁移资产层或承载视图层，不进入契约层。
- 生产交付不得依赖临时 `/tmp` 文件、手工 SQL 或开发库残留状态。

## 当前冻结对象

冻结清单：

- `docs/migration_alignment/scbs55_full_migration_asset_freeze_v1.json`
- `docs/migration_alignment/scbs55_full_migration_asset_inventory_v1.json`
- `docs/migration_alignment/scbs55_replay_payload_gap_report_v1.json`
- `docs/migration_alignment/scbs55_payload_promotion_queue_v1.json`
- `docs/migration_alignment/migration_asset_package_lock_v1.json`
- `docs/migration_alignment/scbs55_user_acceptance_asset_freeze_v1.json`
- `docs/migration_alignment/scbs55_user_acceptance_evidence_lock_v1.json`

全量迁移当前基线：

- 发布包：`migration_assets_release_20260429T135959Z_baseline`
- sha256：`6ec233be3798c4957b58035de30a5162c9f3a6a6602dbd1ea701f76fc5a65716`
- 物化目录：`migration_assets/ and artifacts/migration/`
- 全量用户可见列表：`artifacts/migration/scbs55_wutao_old_new_final_aligned_compare.json`
- 当前列表证据：42 个用户可见面 `PASS`，blocking = 0
- 当前资产台账：225 个运行态 artifact，历史连续性重放 221 个 step，42 个用户可见面合计 142427 行旧/新一致
- 当前 replay gap：221 个 step、69 个 adapter step、128 条 required missing input（106 个唯一文件）、262 条 runtime output backlog（258 个唯一文件）；在未物化完整 release package 的工作区里，缺口报告为 `PASS_WITH_GAPS`，用于推进 payload 晋级队列，不替代发布包校验
- 当前 payload 晋级队列：11 个 lane，按 foundation、用户权限、主数据、合同/供应商、收款、付款、财务、物资投标、附件流程、正式投影、runtime probe 顺序推进；JSON 固化 128/262 全量 backlog 明细，其中 10 个缺失输入文件跨 lane 共享，全量守卫禁止 `unclassified` lane 并校验明细计数、唯一文件数和跨 lane 清单
- 当前 delivery/release 必需 replay artifact 口径：`docs/migration_alignment/scbs55_delivery_replay_requirement_lock_v1.json` 锁定 115 个 required input 唯一路径扣除 4 个 baseline excluded recovery artifact 后，最终发布包门禁要求 111 个；`make migration.assets.full_scope_guard` 校验 delivery audit、release package、replay gap 三方集合一致

首批高风险验收切片 6 个页面：

这 6 个页面不是全量迁移边界，只是用户反复反馈的首批高风险验收切片。它们与 42 个全量用户可见面的关系已经写入
`docs/migration_alignment/scbs55_user_acceptance_asset_freeze_v1.json` 的 `full_scope_lineage`：

- `自筹保证金`、`自筹保证金退回` 直接映射 42 面全量证据 seq 18、19。
- `自筹垫付收入`、`自筹垫付退回`、`工程进度收款`、`供货合同` 是独立高风险验收切片，由专门的旧系统在线、浏览器、row dump evidence lock 约束，不冒充 42 面全量 compare 行。
- `make migration.assets.full_scope_guard` 会校验上述 lineage，不允许 6 页切片和全量范围关系漂移。

| 页面 | 旧 ConfigId | 旧表 | 旧系统总数 | 新菜单 | 新 action | 新系统总数 |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| 自筹保证金 | `74fcd2b29acb4101aee0da39851971f4` | `ZJGL_BZJGL_Branch_SBZJDJ` | 1580 | 613 | 868 | 1580 |
| 自筹保证金退回 | `2aa899a761964e42a9bd63c9e5de7446` | `ZJGL_BZJGL_Branch_SBZJTH` | 823 | 614 | 869 | 823 |
| 自筹垫付收入 | `cd66fc4948074ccb935d328a19f08a64` | `C_JFHKLR` | 2141 | 731 | 901 | 2141 |
| 自筹垫付退回 | `758c318d761548c4875859fc6ecc665c` | `C_JFHKLR_TH_ZCDF` | 827 | 732 | 902 | 827 |
| 工程进度收款 | `e65e4a85bed946968daad69271e91ca2` | `C_JFHKLR` | 3259 | 729 | 899 | 3259 |
| 供货合同 | `77585134a02a48e7bd578e8ee3dd5bf2` | `T_GYSHT_INFO` | 5565 | 730 | 900 | 5565 |

直营项目系统菜单验收分组：

用户指定的 `https://www.builderp.cn/SCBSLY_V2` 直营项目系统菜单已经进入
`docs/migration_alignment/scbs55_user_acceptance_asset_freeze_v1.json` 的 `user_acceptance_groups`，
作为 `scbsly_direct_project_business_menus` 独立验收分组。当前在线证据：
`artifacts/migration/scbsly_direct_project_acceptance_menu_probe_v1.json`，34/34 菜单可见并通过；
其中 32 个 LowCode 列表已拉取旧系统 DataCount，2 个报表入口为 LowCode Report 路由。该分组不是 6 页 evidence lock
的一部分，后续新系统浏览器/API 验证完成后再晋级为逐页 count、字段、身份集合锁。

日常开发新系统在线验证证据：
`artifacts/migration/scbsly_direct_project_new_system_alignment_probe_v1.json`。当前结论是 `PASS`：
34 个菜单全部通过；用户可见菜单/路由缺口为 0，字段缺口为 0，旧/新数量口径差异为 0。
注意：该证据是后端 API/菜单交付合同口径，不等同于用户浏览器实际侧边栏渲染口径。
本轮已补充真实浏览器验收脚本
`scripts/verify/scbsly_direct_project_browser_menu_acceptance.js`，在服务器日常开发环境
`http://1.95.85.92:18081` 登录 `wutao/sc_demo` 后逐级展开侧边栏，校验
`用户验收 / 直营项目系统菜单` 的 43 个可见标签（根、分组、34 个叶子）。
最新浏览器报告：
`artifacts/browser/scbsly-direct-project-menu/20260530T090744/report.json`，结论 `PASS`，
`expected_count=43`、`visible_count=43`、`missing_count=0`。对应平台发布快照已在
`sc_platform_core` 重新冻结并发布为
`v20260530_scbsly_direct_acceptance_menu_daily_dev`，发布页 355 个，其中用户验收 34 个。
菜单交付层对 `用户验收` 分组保留旧系统原始标签，避免通用重命名把 `进项上报` 改为
`进项税额上报` 导致浏览器验收口径漂移。
其中 `油卡登记`、`充值登记`、`加油登记` 已通过新增 legacy fact 承载和在线 replay 对齐到 8/32/500；`工程进度收款` 已并入同一 `sc.legacy.receipt.income.fact` 事实承载，主系统通过 `operation_strategy=joint` 保持 3259/3259，直营验收入口 `工程进度收款（直营）` 通过 `operation_strategy=direct` 对齐到 639/639；`还租` 已通过独立验收 action 和 `sc.material.rental.order` 身份回放对齐到 37/37，且 `租入` 保持 0/0。
其余 26 个此前口径不一致的直营项目菜单已通过 `sc.legacy.direct.acceptance.fact` 只读验收承载回放旧系统 identity lock 对齐；
回放结果为 `artifacts/migration/scbsly_direct_project_direct_acceptance_replay_result_v1.json`，26/26 标签通过。
整改矩阵已固化为
`artifacts/migration/scbsly_direct_project_alignment_gap_matrix_v1.json`。该结论说明当前日常开发新系统已经对齐
`SCBSLY_V2` 直营项目用户验收面；补齐发生在迁移资产 replay 或验收承载层，未在契约层按菜单裁剪。

旧系统行级资产已经开始分批固化：`artifacts/migration/scbsly_direct_project_old_row_dump_summary_v1.json`
当前锁定 32 个 LowCode 列表、76411/76411 行，覆盖合同类 6 项、材料管理列表含入库、劳务/分包/机械租赁列表含机械台班记录、零星用工、项目费用报销、油卡/充值/加油等资金类小表、支付申请、往来单位付款、进项上报和施工日志。2 个剩余入口是旧系统报表路由，没有列表 DataCount。
当前缓存目录为 `/tmp/scbsly_direct_project_old_pages_20260530/_pages/...`；后续进入新系统 replay/身份集合锁。

旧系统身份集合锁：`artifacts/migration/scbsly_direct_project_old_identity_lock_v1.json`。32 个列表、76411 行通过；
其中 24 个列表使用旧系统首选业务字段，7 个旧系统明细展开列表使用 `RowIndex` 作为用户可见行身份兜底，
`租入` 是 0 行空列表。后续新系统 replay 和验收比对必须绑定该 identity lock，不接受只按数量补齐。

新系统承载/replay 计划：`artifacts/migration/scbsly_direct_project_replay_carrier_plan_v1.json`。当前拆分为：
21 个已有承载但需要 identity replay 或独立验收承载，7 个菜单别名已补但仍需 replay，1 个菜单别名对应旧系统
0 行，3 个油卡/充值/加油页面已新增 legacy fact 承载且已在日常开发 `sc_odoo` 回放通过，`工程进度收款` 已在既有历史收款事实承载中按经营方式切片回放通过，`还租` 已用独立 action 避免污染 `租入` 口径并回放通过，2 个报表入口不做列表 replay。服务器侧整改从该计划开始，
按 identity lock 做 replay/验收比对。
本轮已进一步把剩余 26 个直营项目列表通过 `sc.legacy.direct.acceptance.fact` 验收承载回放完成，作为用户启用前的可见面锁定结果；
正式业务模型的资产包规范化仍按本专题后续任务推进。

| 分类 | 验收菜单 |
| --- | --- |
| 合同类单据 | 施工合同、分包合同、租赁合同、供货合同、劳务合同、机械合同（合同） |
| 材料管理类单据 | 材料计划、报价单、入库、材料结算单、库存统计表（新） |
| 劳务管理类单据 | 方单、零星用工、劳务结算 |
| 分包管理类单据 | 分包方单、分包结算单 |
| 机械与租赁管理类单据 | 机械台班记录、机械结算单、租入、还租、租赁结算单 |
| 费用与资金管理类单据 | 项目费用报销单、管理人员工资表、油卡登记、充值登记、加油登记、支付申请、工程进度收款、往来单位付款、工程结算单、进项上报、总包进项上报、成本统计表（数据） |
| 项目管理类单据 | 施工日志（新） |

## 证据分层

### 1. 旧系统在线证据

使用旧系统登录态调用 LowCode 列表接口：

- count：`LowCode/FormApi/ListByTableName` 或配置指定的 `ListApi/ListProcedure`
- row dump：同一 payload 分页拉取全量 `Data`
- 凭据通过环境变量传入，不写入仓库：
  - `OLD_SCBS_USERNAME`
  - `OLD_SCBS_PASSWORD`

### 2. 新系统承载证据

每个页面必须声明：

- 新菜单 `menu_id`
- 新 action `action_id`
- 新承载模型 `model`
- 用户可见 domain 或承载 source family
- 行级身份字段

### 3. 浏览器验收证据

最新日常开发环境浏览器证据：

- `/tmp/scbs55_six_pages_aligned_20260530/summary.json`
- 6/6 页面总数与旧系统一致
- console errors = 0
- `artifacts/browser/scbsly-direct-project-menu/20260530T090744/report.json`
- 直营项目系统菜单真实浏览器侧边栏展开 43/43 可见，缺失 0

该路径是本轮开发证据，不是最终交付资产。进入资产包前必须复制为带 hash 的归档产物，或由专题脚本重新生成。

### 4. 证据锁

`scbs55_user_acceptance_evidence_lock_v1.json` 固化以下不可漂移事实：

- 每个旧系统 row dump 的 `sha256`、文件大小、行数。
- 每个旧系统身份字段的总数、唯一数、缺失数。
- 浏览器 summary 的 `sha256` 和 6 个菜单总数。

guard 会在存在证据文件时校验 hash；开启 `SCBS55_REQUIRE_ACCEPTANCE_EVIDENCE=1` 时，缺少证据文件会直接失败。

## 禁止事项

- 禁止在契约层按 action 或菜单写数据裁剪特例。
- 禁止只按数量补齐，不做旧行身份集合核对。
- 禁止把演示项目、样例项目或开发临时数据作为用户验收依据。
- 禁止最终迁移包依赖 `/tmp`、在线旧系统、开发库手工 SQL。

## 专题第一阶段交付

- 全量 scope guard：验证本专题确实覆盖完整迁移资产包、42 个用户可见面、发布包 lock 和首批验收切片。
- 静态 manifest guard：验证冻结清单结构、唯一性、计数字段和证据引用。
- 证据 guard：在存在旧系统 row dump 和浏览器 summary 时复核 count。
- 在线 guard：使用旧系统登录态重新拉取 count，并绑定旧页面 `DETAIL_CONFIG.WhereInfo`，避免通用探针注入口径。
- 浏览器字段 guard：按 manifest 固化的 6 个新菜单逐页校验用户可见总数、表头顺序、首行可见数据、`api.data` 字段返回和 console error。
- replay 资产：从证据锁定的旧系统 row dump 幂等重放自筹垫付收入、自筹垫付退回、工程进度收款、供货合同；保证写入前先校验 row dump sha256。

临时脚本 `scripts/migration/scbs55_live_delta_backfill_write.py` 不进入本专题交付范围。它覆盖合同、收款、付款申请、付款执行等宽口径补差，来源是全量 seq dump，不受本 manifest 和 evidence lock 约束，容易把“用户验收面补齐”扩散成“数据库猜测迁移”。本专题只接受 manifest/evidence 约束 replay。

## 当前验收命令

全量专题范围校验：

```bash
make migration.assets.full_scope_refresh
```

发布包级门禁：

```bash
make migration.assets.fetch
make migration.assets.verify_all
make migration.assets.delivery_audit
make migration.assets.release_package
```

静态校验：

```bash
python3 scripts/verify/scbs55_user_acceptance_asset_manifest_guard.py
```

带本轮临时证据校验：

```bash
SCBS55_REQUIRE_ACCEPTANCE_EVIDENCE=1 \
SCBS55_OLD_ROWS_DIR=/tmp/scbs55_old_pages_20260530 \
SCBS55_BROWSER_SUMMARY=/tmp/scbs55_six_pages_aligned_20260530/summary.json \
python3 scripts/verify/scbs55_user_acceptance_asset_manifest_guard.py
```

重新在线核对旧系统 count：

以下命令还必须按 `docs/security/online_capture_configuration_contract_v1.md`
注入 online 模式、目标 allowlist、采集窗口和输出目录；缺失时会在网络请求前失败。

```bash
OLD_SCBS_USERNAME=<provided-via-secret-environment> \
OLD_SCBS_PASSWORD=<provided-via-secret-environment> \
python3 scripts/verify/scbs55_user_acceptance_online_probe.py
```

或：

```bash
OLD_SCBS_USERNAME=<provided-via-secret-environment> \
OLD_SCBS_PASSWORD=<provided-via-secret-environment> \
make migration.assets.user_acceptance_online_probe
```

注意：该在线探针使用旧页面 `DETAIL_CONFIG` 的默认 `WhereInfo`，不会像旧的通用 count probe 那样自动注入 `DJZT` 过滤。`自筹垫付收入` 已验证会因这种通用注入从 `2141` 漂移为 `2139`，因此本专题后续所有验收面必须使用 manifest 绑定的页面口径探针。

新系统浏览器字段和数据验收：

```bash
FRONTEND_URL=http://1.95.85.92:18081 \
DB_NAME=sc_demo \
E2E_LOGIN=wutao \
E2E_PASSWORD=<REVOKED_LEGACY_SECRET> \
make migration.assets.user_acceptance_browser_field_guard
```

受 evidence lock 保护的日常开发库 replay：

```bash
SCBS55_OLD_ROWS_DIR=/tmp/scbs55_old_pages_20260530 \
DB_NAME=sc_demo \
make migration.assets.user_acceptance_replay.write
```

容器内路径可直接用 `MIGRATION_SCBS55_OLD_ROWS_DIR` 覆盖。该 replay 只允许写 `MIGRATION_REPLAY_DB_ALLOWLIST` 中的数据库，默认由 Makefile 绑定为当前 `DB_NAME`。如果 row dump 与 `scbs55_user_acceptance_evidence_lock_v1.json` 的 sha256 不一致，脚本在写库前失败。
