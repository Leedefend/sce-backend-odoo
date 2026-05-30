# SCBS55 迁移资产包冻结专题 v1

状态：`TOPIC_OPEN`

分支：`topic/scbs55-migration-asset-freeze`

## 目标

把用户验收面用到的迁移数据资产从“临时在线核对 + 手工补差”推进为可复核、可重放、可交付的资产包。

本专题的判断标准不是“新系统数量看起来一致”，而是：

- 旧系统在线菜单配置、默认过滤条件、列表接口总数可复核。
- 旧系统行级身份集合和新系统承载集合可复核。
- 新系统用户可见菜单浏览器总数可复核。
- 数据补齐逻辑在迁移资产层或承载视图层，不进入契约层。
- 生产交付不得依赖临时 `/tmp` 文件、手工 SQL 或开发库残留状态。

## 当前冻结对象

冻结清单：

- `docs/migration_alignment/scbs55_user_acceptance_asset_freeze_v1.json`
- `docs/migration_alignment/scbs55_user_acceptance_evidence_lock_v1.json`

首批冻结 6 个用户验收面：

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

- 静态 manifest guard：验证冻结清单结构、唯一性、计数字段和证据引用。
- 证据 guard：在存在旧系统 row dump 和浏览器 summary 时复核 count。
- 在线 guard：后续加入，使用旧系统登录态重新拉取 count/row identity，与新系统 API 或浏览器结果比较。
- replay 规范：把本轮 2 条自筹垫付收入、249 条供货合同、29 条供货合同移出口径等补差动作转成幂等 replay 资产。

## 当前验收命令

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
