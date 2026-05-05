# prod-sim 从零重建与完整数据重放

本文档是服务器模拟生产环境的唯一标准入口。不要再把 `deploy.prod.sim.oneclick`、`history.production.fresh_init`、单个 `fresh_db.*` 或 `history.*` 目标作为正式重建入口；这些只保留给排障和局部续跑。

## 唯一入口

在服务器仓库根目录执行：

```bash
cd /path/to/sce-backend-odoo
make prod.sim.fresh.replay ENV=test ENV_FILE=.env.prod.sim PROD_SIM_FRESH_REPLAY=1
```

默认数据库来自 `.env.prod.sim`：

```text
COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim
DB_NAME=sc_prod_sim
NGINX_PORT=80
ODOO_PORT=18069
```

`PROD_SIM_FRESH_REPLAY=1` 是必需确认项。该动作会删除 prod-sim 隔离环境的 Docker volumes，并从空库重新构建。

## 跨机器执行前提

任意机器执行时必须满足：

- 已安装 Docker，并可使用 `docker compose` 或 `docker-compose`。
- 已拉取完整仓库，且在仓库根目录执行命令。
- `.env.prod.sim` 存在并包含 `COMPOSE_PROJECT_NAME`、`DB_NAME`、`DB_USER`、`DB_PASSWORD`、`ADMIN_PASSWD`、`JWT_SECRET`、`ODOO_DBFILTER`。
- 第一次历史完整重放资产存在：
  - `artifacts/migration/fresh_db_replay_manifest_v1.json`
  - `artifacts/migration/fresh_db_*_payload_v1.csv`
  - `artifacts/migration/history_*_payload_v1.csv`
  - `migration_assets/` 下的 XML 和 manifest 资产。
- 第二次 SCBS no-legacy 资产包存在：
  - `artifacts/migration/scbs_replay_asset_v1/manifest.json`
  - `artifacts/migration/scbs_replay_asset_v1/artifacts/migration/*.csv`
  - `artifacts/migration/scbs_replay_asset_v1/artifacts/migration/scbs_replay_expected_baseline_v1.json`
- Docker Compose 中 Odoo 服务必须把仓库 `artifacts/` 挂载到容器 `/mnt/artifacts`，脚本默认使用 `/mnt/artifacts/migration/scbs_replay_asset_v1`。

资产可以已经位于仓库标准路径，也可以作为外部资产包提供。外部资产包必须包含：

```text
<asset-root>/artifacts/migration/...
<asset-root>/migration_assets/...
```

也兼容：

```text
<asset-root>/migration/...
<asset-root>/migration_assets/...
```

使用外部资产包执行：

```bash
make prod.sim.fresh.replay \
  ENV=test \
  ENV_FILE=.env.prod.sim \
  PROD_SIM_FRESH_REPLAY=1 \
  DATA_REPLAY_ASSET_ROOT=/path/to/data_replay_asset
```

默认只补齐缺失文件，不覆盖仓库内已有资产。需要用资产包覆盖当前仓库资产时显式加：

```bash
DATA_REPLAY_ASSET_OVERWRITE=1
```

入口会在清空 volumes 之前执行 portable preflight。缺 Docker、缺 env、缺脚本、缺任一历史 payload、缺 `migration_assets`、缺 SCBS 资产包或资产路径不在 `/mnt` 下时会直接失败，不进入破坏性清库。

只验证当前机器是否具备执行条件，不清库、不重放：

```bash
make prod.sim.fresh.replay \
  ENV=test \
  ENV_FILE=.env.prod.sim \
  PROD_SIM_FRESH_REPLAY=1 \
  PROD_SIM_FRESH_REPLAY_PREFLIGHT_ONLY=1 \
  DATA_REPLAY_ASSET_ROOT=/path/to/data_replay_asset
```

## 统一动作内容

入口 `make prod.sim.fresh.replay` 会按固定顺序执行：

1. 执行 portable preflight，确认当前机器具备执行条件。
2. 校验 Docker Compose 配置。
3. 删除 prod-sim 隔离栈和 volumes。
4. 使用 `docker-compose.yml + docker-compose.prod-sim.yml` 从空卷启动数据库和 Odoo 运行环境。
5. 安装生产模块集。
6. 应用扩展模块注册。
7. 重建核心税率基线，确保历史合同写入需要的 `销项VAT 9%` 和 `进项VAT 13%` 存在。
8. 执行第一次历史完整重放主链 `history_continuity_oneclick.sh`：
   - 历史用户、部门、角色、真实登录账号。
   - 项目锚点、往来单位、合同、采购合同、收款、付款/支出、实际付款。
   - 附件索引/附件回填、税票、资金流水/快照、融资、结算调整、费用报销、施工日志。
   - 历史待办、工作台、驾驶舱和运行态投影。
   - 历史业务运行探针。
9. 设置运行语言基线，确保 `admin/wutao/chenshuai` 为 `zh_CN` / `Asia/Shanghai`。
10. 执行平台初始化预检。
11. 执行第二次 SCBS no-legacy 材料/业务事实重放。
12. 执行 SCBS closure、no-legacy acceptance 和 strict release acceptance。
13. 执行 Business Full 和角色矩阵 smoke。

该入口不构建前端，不执行前端 smoke，不导出数据库备份，不生成 zip，不上传服务器。前端验证、备份和上传都是重建验收通过后的独立动作。

## 达标标准

该流程只验证数据库和业务运行态：

- 新库能从零安装生产模块。
- 第一次历史完整重放主链能一次跑通，并修复历史业务数据。
- 第二次 SCBS no-legacy 重放能一次跑通。
- 用户、权限、语言、项目、合同、收付款、材料入库等核心业务数据通过运行态探针。
- 不以任意前端构建、前端页面访问或浏览器 smoke 作为数据重建达标条件。

真实用户默认归一化密码：

```text
wutao / 123456
chenshuai / 123456
```

## 材料数据策略

统一入口不重放旧系统完整材料库，不加载 `sc.legacy.material.detail`
的 220 万级明细。

使用的资产包是：

```text
artifacts/migration/scbs_replay_asset_v1
```

其策略是：

```text
full_legacy_material_library_replay=false
material_replay_scope=SCBS stock-in material mapping and material catalog facts only
```

材料相关输入规模：

```text
scbs_stock_in_legacy_lines_v1.csv: 2209 rows
scbs_stock_in_material_mapping_workbook_v1.csv: 1658 rows
```

## 输出位置

重放过程证据：

```text
artifacts/migration/<RUN_ID>/
```

命令结束时只打印 `RUN_ID` 和 `MIGRATION_ARTIFACT_ROOT`。

## 单独备份入口

重建验收通过后，如需备份，再单独执行：

```bash
mkdir -p artifacts/db_backups/<run_id>
docker compose --env-file .env.prod.sim -p sc-backend-odoo-prod-sim \
  -f docker-compose.yml -f docker-compose.prod-sim.yml \
  exec -T db pg_dump -U odoo -d sc_prod_sim -Fc \
  > artifacts/db_backups/<run_id>/sc_prod_sim.dump

sha256sum artifacts/db_backups/<run_id>/sc_prod_sim.dump \
  > artifacts/db_backups/<run_id>/sc_prod_sim.dump.sha256
```

## 允许的调试入口

以下入口不作为正式执行路径，只用于局部排障：

- `make deploy.prod.sim.oneclick`：只部署 prod-sim 栈和模块，不保证从零重放。
- `scripts/diag/fe_smoke.sh`：前端独立验收，不属于数据重建流程。
- `make history.production.fresh_init`：旧生产初始化入口，不作为当前模拟生产统一重建入口。
- `make history.continuity.replay`：第一次历史完整重放主链，只能作为统一入口的内部步骤或局部排障入口，不能单独代表最终 SCBS 正式重建。
- 单个 `fresh_db.*`、`history.*`：只用于定位某一条数据通道。

## 失败续跑

正式路径默认重新从零跑。需要定位失败点时，才使用：

```bash
bash scripts/migration/scbs_no_legacy_replay_apply.sh \
  sc_prod_sim \
  /mnt/artifacts/migration/scbs_replay_asset_v1 \
  /mnt/artifacts/migration/<原RUN_ID>
```

续跑只用于排障。最终交付前仍要重新执行唯一入口。
