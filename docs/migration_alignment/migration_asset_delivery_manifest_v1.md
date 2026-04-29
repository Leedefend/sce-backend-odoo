# Migration Asset Delivery Manifest v1

Status: `DELIVERY_READY_WITH_PACKAGING_ACTIONS`

## 1. 目标

面向上线交付冻结迁移资产包边界，明确：

- 哪些文件属于生产加载资产。
- 哪些文件属于离线 replay payload，生产服务器不再依赖旧库生成。
- 哪些文件不应进入最终发布压缩包。
- 上线前必须通过哪些只读门禁。

本文不改变迁移资产内容，不改变 `history_continuity_oneclick.sh` 重放顺序。
生产重放默认跳过旧库 adapter，直接使用资产包内的离线 payload。

## 2. 当前事实

以 `make migration.assets.delivery_audit` 最新结果为准：

- catalog 包数：`23`
- 资产文件数：`98`
- catalog 引用文件数：`93`
- 未纳入 catalog 引用文件数：`5`
- 资产目录总大小：`467.27 MB`
- 一键重放 step 数：`144`
- 阻断项：`0`
- 包装整理项：`2`

审计产物：

- JSON：`artifacts/migration/migration_asset_delivery_audit_v1.json`
- 报告：`docs/migration_alignment/migration_asset_delivery_audit_v1.md`

## 3. 生产加载资产

生产加载资产以 `migration_assets/manifest/migration_asset_catalog_v1.json` 为唯一目录。

交付包必须包含：

- `migration_assets/manifest/migration_asset_catalog_v1.json`
- catalog 中 23 个 `asset_manifest_path`
- 每个 asset manifest 内声明的 `assets[].path`
- `artifacts/migration/**` 中冻结的 replay payload、adapter result 和门禁证据
- 生产重放入口：
  - `scripts/deploy/fresh_production_history_init.sh`
  - `scripts/migration/history_continuity_oneclick.sh`
  - `Makefile`

上线前必须验证：

```bash
make migration.assets.verify_all
make migration.assets.delivery_audit
```

## 4. 离线 Payload 与交付证据

生产服务器不安装旧库，不要求 `legacy-mssql-restore` 存在。最终发布包必须携带
`artifacts/migration` 下的冻结 payload；`history.production.fresh_init` 默认
设置 `HISTORY_CONTINUITY_USE_PACKAGED_PAYLOADS=1`，所有 `*_adapter` step 会跳过，
后续 replay/write step 直接读取这些 payload。

如需在非生产环境重新从旧库生成 payload，必须显式设置：

```bash
HISTORY_CONTINUITY_USE_PACKAGED_PAYLOADS=0
```

以下文件是资产治理证据，不是 catalog 加载入口：


- `migration_assets/manifest/migration_asset_coverage_snapshot_v1.json`
- `migration_assets/manifest/receipt_blocker_policy_snapshot_v1.json`

处理规则：

- 可随完整审计包归档。
- 不作为 `migration_asset_catalog_v1.json` 的加载资产。
- 不允许一键重放脚本直接依赖这些证据文件。

## 5. 最终发布包排除项

`legacy_workflow_audit_v1.xml` 已经物化为完整 XML，同时仍保留 `.parts` 分片。

当前重复项：

- `migration_assets/30_relation/legacy_workflow_audit/legacy_workflow_audit_v1.xml`
- `migration_assets/30_relation/legacy_workflow_audit/legacy_workflow_audit_v1.xml.parts/part-000.part`
- `migration_assets/30_relation/legacy_workflow_audit/legacy_workflow_audit_v1.xml.parts/part-001.part`
- `migration_assets/30_relation/legacy_workflow_audit/legacy_workflow_audit_v1.xml.parts/part-002.part`

交付决策：

- 仓库内暂不删除 `.parts`，避免破坏既有恢复路径。
- 最终发布压缩包只保留完整 XML，不携带 `.parts`。
- 如需改为只保留 `.parts`，必须新开批次同步修改物化规则、manifest hash 和交付验证。

## 6. 一键重放入口

非生产演练：

```bash
DB_NAME=<target_db> make history.continuity.rehearse
DB_NAME=<target_db> HISTORY_CONTINUITY_USE_PACKAGED_PAYLOADS=1 make history.continuity.replay
```

生产新库初始化：

```bash
ENV=prod ENV_FILE=.env.prod DB_NAME=sc_prod PROD_DANGER=1 \
  RUN_ID=prod_history_init_YYYYMMDDTHHMMSS \
  BASE_URL=https://<production-host> \
  FRONTEND_BASE_URL=https://<production-host> \
  make history.production.fresh_init
```

生产断点续跑仍使用生产入口：

```bash
ENV=prod ENV_FILE=.env.prod DB_NAME=sc_prod PROD_DANGER=1 \
  RUN_ID=<same_run_id> HISTORY_CONTINUITY_START_AT=<failed_step> \
  make history.production.fresh_init
```

## 7. 上线前门禁

必须通过：

```bash
make migration.assets.verify_all
make migration.assets.delivery_audit
make migration.assets.release_package
make verify.docs.links
```

prod-sim / UAT 必须完成：

```bash
ENV=test ENV_FILE=.env.prod.sim DB_NAME=sc_prod_sim \
  RUN_ID=rehearsal_YYYYMMDDTHHMMSS \
  HISTORY_CONTINUITY_USE_PACKAGED_PAYLOADS=1 \
  make history.continuity.rehearse

ENV=test ENV_FILE=.env.prod.sim DB_NAME=sc_prod_sim \
  RUN_ID=rehearsal_YYYYMMDDTHHMMSS \
  HISTORY_CONTINUITY_USE_PACKAGED_PAYLOADS=1 \
  make history.continuity.replay

ENV=test ENV_FILE=.env.prod.sim DB_NAME=sc_prod_sim \
  make history.business.usable.probe
```

## 8. 停机条件

出现以下任一情况，不得进入生产重建：

- `migration.assets.verify_all` 失败。
- `migration.assets.delivery_audit` 出现 blocker。
- catalog hash 与 asset manifest hash 不一致。
- 生产发布包同时携带完整 `legacy_workflow_audit_v1.xml` 和 `.parts`。
- prod-sim/UAT 未跑完整 replay。
- 缺少 `RUN_ID`、artifact root 或回滚点。

## 9. 发布包生成

本批次已提供发布包生成入口：

```bash
make migration.assets.release_package
```

默认输出：

- tar 包目录：`/tmp/sce_migration_asset_release`
- 小型证据：`artifacts/migration/migration_asset_release_package_v1.json`（本地生成，不入 Git）
- 文档证据：`docs/migration_alignment/migration_asset_release_package_v1.md`

发布包规则：

- 包内包含 `migration_assets/manifest/migration_asset_catalog_v1.json`。
- 包内包含 catalog 与 asset manifest 声明的加载资产。
- 包内包含 `artifacts/migration/**` 离线 replay payload 与重放证据。
- 包内包含两个治理证据文件。
- 包内包含完整 `legacy_workflow_audit_v1.xml`。
- 包内排除 `legacy_workflow_audit_v1.xml.parts/**`。

下一步在 prod-sim 解包后重跑：

```bash
make migration.assets.verify_all
make migration.assets.delivery_audit
```
