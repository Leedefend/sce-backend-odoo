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
- `docs/migration_alignment/migration_asset_package_lock_v1.json`
- `docs/migration_alignment/scbs55_user_acceptance_asset_freeze_v1.json`
- `docs/migration_alignment/scbs55_user_acceptance_evidence_lock_v1.json`

全量迁移当前基线：

- 发布包：`migration_assets_release_20260429T135959Z_baseline`
- sha256：`6ec233be3798c4957b58035de30a5162c9f3a6a6602dbd1ea701f76fc5a65716`
- 物化目录：`migration_assets/ and artifacts/migration/`
- 全量用户可见列表：`artifacts/migration/scbs55_wutao_old_new_final_aligned_compare.json`
- 当前列表证据：42 个用户可见面 `PASS`，blocking = 0

首批高风险验收切片 6 个页面：

| 页面 | 旧 ConfigId | 旧表 | 旧系统总数 | 新菜单 | 新 action | 新系统总数 |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| 自筹保证金 | `74fcd2b29acb4101aee0da39851971f4` | `ZJGL_BZJGL_Branch_SBZJDJ` | 1580 | 613 | 868 | 1580 |
| 自筹保证金退回 | `2aa899a761964e42a9bd63c9e5de7446` | `ZJGL_BZJGL_Branch_SBZJTH` | 823 | 614 | 869 | 823 |
| 自筹垫付收入 | `cd66fc4948074ccb935d328a19f08a64` | `C_JFHKLR` | 2141 | 731 | 901 | 2141 |
| 自筹垫付退回 | `758c318d761548c4875859fc6ecc665c` | `C_JFHKLR_TH_ZCDF` | 827 | 732 | 902 | 827 |
| 工程进度收款 | `e65e4a85bed946968daad69271e91ca2` | `C_JFHKLR` | 3259 | 729 | 899 | 3259 |
| 供货合同 | `77585134a02a48e7bd578e8ee3dd5bf2` | `T_GYSHT_INFO` | 5565 | 730 | 900 | 5565 |

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
make migration.assets.full_scope_guard
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

```bash
OLD_SCBS_USERNAME=13518193984 \
OLD_SCBS_PASSWORD=****** \
python3 scripts/verify/scbs55_user_acceptance_online_probe.py
```

或：

```bash
OLD_SCBS_USERNAME=13518193984 \
OLD_SCBS_PASSWORD=****** \
make migration.assets.user_acceptance_online_probe
```

注意：该在线探针使用旧页面 `DETAIL_CONFIG` 的默认 `WhereInfo`，不会像旧的通用 count probe 那样自动注入 `DJZT` 过滤。`自筹垫付收入` 已验证会因这种通用注入从 `2141` 漂移为 `2139`，因此本专题后续所有验收面必须使用 manifest 绑定的页面口径探针。

新系统浏览器字段和数据验收：

```bash
FRONTEND_URL=http://1.95.85.92:18081 \
DB_NAME=sc_demo \
E2E_LOGIN=wutao \
E2E_PASSWORD=****** \
make migration.assets.user_acceptance_browser_field_guard
```

受 evidence lock 保护的日常开发库 replay：

```bash
SCBS55_OLD_ROWS_DIR=/tmp/scbs55_old_pages_20260530 \
DB_NAME=sc_demo \
make migration.assets.user_acceptance_replay.write
```

容器内路径可直接用 `MIGRATION_SCBS55_OLD_ROWS_DIR` 覆盖。该 replay 只允许写 `MIGRATION_REPLAY_DB_ALLOWLIST` 中的数据库，默认由 Makefile 绑定为当前 `DB_NAME`。如果 row dump 与 `scbs55_user_acceptance_evidence_lock_v1.json` 的 sha256 不一致，脚本在写库前失败。
