# 生产环境正式部署规范 v1

## 1. 适用范围

本文用于服务器生产环境正式部署、首次上线、版本升级和生产数据重建。

- 目标环境：`ENV=prod`
- 标准数据库：`sc_prod`
- 标准入口：Makefile target
- 重点约束：生产环境禁止 `db.reset`、`demo.reset`、`demo.*`、`gate.*`、`ci.*`

本文不替代以下专项文档：

- 生产命令策略：`docs/ops/prod_command_policy.md`
- Codex 生产协助策略：`docs/ops/codex_production_assist_policy.md`
- 数据库命名策略：`docs/ops/db_strategy.md`
- 历史连续性重放：`docs/ops/history_continuity_server_replay_runbook_v1.md`
- 历史用户重建：`docs/ops/history_user_rebuild_runbook_v1.md`
- 迁移资产交付清单：`docs/migration_alignment/migration_asset_delivery_manifest_v1.md`

## 2. 架构与治理边界

- Layer Target：Ops Documentation / Production Runtime Procedure
- Module：`docs/ops`、`docs/deploy`
- Reason：将生产部署、数据重建、验证、回滚和证据归档固化为可执行 SOP。
- 不触达：业务代码、contract/schema、启动链、前端页面、public intent。

生产部署必须遵守：

- 启动链不可破坏：`login -> system.init -> ui.contract`
- role 真源唯一：`role_surface.role_code`
- default_route 必须来自后端 contract
- public intent 禁止 rename 或语义漂移
- 所有运行态、容器、数据库、服务状态变更必须通过 Makefile target
- 如由 Codex 协助服务器部署，必须按 `docs/ops/codex_production_assist_policy.md` 执行；
  允许从 `main`、tag 或冻结 commit 部署，但禁止 Codex 修改仓库文件或执行 Git 写操作。

## 3. 发布前冻结条件

正式部署前必须完成以下冻结：

| 项目 | 要求 |
| --- | --- |
| 代码版本 | 明确 commit、tag 或 release branch，不允许临时工作区部署 |
| 配置 | `.env.prod` 已评审，`ENV=prod`、`DB_NAME=sc_prod`、`COMPOSE_PROJECT_NAME` 唯一 |
| 依赖 | `addons_external/oca_server_ux/base_tier_validation` 存在 |
| 迁移资产 | `make migration.assets.verify_all` 与 `make migration.assets.delivery_audit` 通过 |
| 备份 | 当前生产库和 filestore 已完成离线备份 |
| 数据方案 | 明确是“升级保留数据”还是“新库重建数据” |
| 回滚方案 | 明确代码回滚、数据库回滚、filestore 回滚、DNS/反代回滚 |
| 窗口 | 明确停机窗口、冻结写入时间和验收负责人 |

依赖检查：

```bash
test -d addons_external/oca_server_ux/base_tier_validation \
  && echo "OK: base_tier_validation present" \
  || echo "MISSING: base_tier_validation"
```

Compose 配置检查：

```bash
ENV=prod ENV_FILE=.env.prod make check-compose-project
ENV=prod ENV_FILE=.env.prod make check-compose-env
```

## 4. 生产命令红线

生产环境只允许使用 `docs/ops/prod_command_policy.md` 中列出的命令。

禁止：

```bash
ENV=prod make db.reset
ENV=prod make demo.reset
ENV=prod make demo.load
ENV=prod make demo.rebuild
ENV=prod make gate.full
ENV=prod make ci
```

需要显式危险开关的命令必须带 `PROD_DANGER=1`，例如：

```bash
ENV=prod ENV_FILE=.env.prod DB_NAME=sc_prod PROD_DANGER=1 \
  make mod.upgrade MODULE=smart_construction_core
```

生产 seed 只能使用 `PROFILE=base`，且必须显式指定数据库：

```bash
ENV=prod ENV_FILE=.env.prod DB_NAME=sc_prod \
  SEED_DB_NAME_EXPLICIT=1 PROFILE=base make seed.run
```

如需初始化管理员用户，必须同时满足：

```bash
ENV=prod ENV_FILE=.env.prod DB_NAME=sc_prod \
  SEED_DB_NAME_EXPLICIT=1 \
  SEED_ALLOW_USERS_BOOTSTRAP=1 \
  SC_BOOTSTRAP_USERS=1 \
  SC_BOOTSTRAP_ADMIN_PASSWORD='<strong-password>' \
  PROFILE=base make seed.run
```

## 5. 标准部署流程

### 5.1 首次部署预检

```bash
git rev-parse --short HEAD
git status --short
ENV=prod ENV_FILE=.env.prod make check-compose-project
ENV=prod ENV_FILE=.env.prod make check-compose-env
ENV=prod ENV_FILE=.env.prod make diag.project
```

预期：

- 工作区无未提交改动
- `ENV=prod`
- `DB_NAME=sc_prod`
- compose project 不与 dev/test/prod-sim 冲突
- Odoo、Postgres、filestore volume 指向生产专用资源

### 5.2 启动服务

```bash
ENV=prod ENV_FILE=.env.prod make up
ENV=prod ENV_FILE=.env.prod make ps
ENV=prod ENV_FILE=.env.prod make logs
```

服务启动后先确认 Odoo 可以连到目标数据库，再进入安装、升级或重建步骤。

### 5.3 模块安装或升级

常规生产升级：

```bash
ENV=prod ENV_FILE=.env.prod DB_NAME=sc_prod PROD_DANGER=1 \
  make mod.upgrade MODULE=smart_core,smart_construction_core,smart_construction_portal,smart_construction_custom
```

核心模块升级快捷入口：

```bash
ENV=prod ENV_FILE=.env.prod DB_NAME=sc_prod PROD_DANGER=1 \
  make prod.upgrade.core
```

权限策略升级后必须应用：

```bash
ENV=prod ENV_FILE=.env.prod DB_NAME=sc_prod PROD_DANGER=1 \
  make policy.apply.business_full

ENV=prod ENV_FILE=.env.prod DB_NAME=sc_prod PROD_DANGER=1 \
  make policy.apply.role_matrix
```

### 5.4 发布后验证

最小生产验证：

```bash
ENV=prod ENV_FILE=.env.prod DB_NAME=sc_prod PROD_DANGER=1 make verify.baseline
ENV=prod ENV_FILE=.env.prod DB_NAME=sc_prod PROD_DANGER=1 make verify.p0
ENV=prod ENV_FILE=.env.prod DB_NAME=sc_prod PROD_DANGER=1 make smoke.business_full
ENV=prod ENV_FILE=.env.prod DB_NAME=sc_prod PROD_DANGER=1 make smoke.role_matrix
```

验收必须确认：

- 登录页可访问
- `system.init` 返回稳定，且 role/default_route 来自后端契约
- 关键业务菜单可见
- `ui.contract` 可加载目标模型/场景
- Business Full 最小业务 smoke 通过
- role matrix smoke 通过
- 生产日志无安装、升级、ACL、contract 相关阻断错误

## 6. 数据重建流程

数据重建必须先判定类型。禁止在生产环境用 `db.reset` 或 `demo.reset` 重建数据。

| 类型 | 使用场景 | 标准入口 |
| --- | --- | --- |
| A. 新库历史重建 | 首次上线，生产库为空，需要从历史资产重建业务连续性 | `history.production.fresh_init` |
| B. 已有生产库升级 | 生产库已有正式业务数据，只做代码和模块升级 | `mod.upgrade` / `prod.upgrade.core` |
| C. 演练或模拟生产 | 非生产环境验证完整链路 | `history.continuity.rehearse` / `history.continuity.replay` |
| D. 局部历史补链 | 已上线后补某一类历史事实 | 单独评审后使用对应 `fresh_db.*` 或 `history.*` target，默认禁止直接在 prod 执行 |

### 6.1 新库历史重建推荐流程

适用条件：

- `sc_prod` 是新库或已经确认可以整体替换的空库
- 历史迁移资产已随部署包上线
- `artifacts/migration` 离线 replay payload 已随资产包上线
- filestore 已初始化或为空
- 已完成旧系统写入冻结
- 已完成旧库导出校验和资产 hash 校验

生产服务器不安装旧库，也不依赖 `legacy-mssql-restore`。生产入口默认
`HISTORY_CONTINUITY_USE_PACKAGED_PAYLOADS=1`，会跳过所有旧库 adapter step，
直接使用资产包内的 `artifacts/migration` payload 重放。只有在非生产环境需要
重新从旧库生成 payload 时，才允许显式设置
`HISTORY_CONTINUITY_USE_PACKAGED_PAYLOADS=0`。

生产一键入口：

```bash
ENV=prod ENV_FILE=.env.prod DB_NAME=sc_prod PROD_DANGER=1 \
  RUN_ID=prod_history_init_$(date +%Y%m%dT%H%M%S) \
  BASE_URL=https://<production-host> \
  FRONTEND_BASE_URL=https://<production-host> \
  make history.production.fresh_init
```

该入口会执行：

1. 启动 compose stack。
2. 使用 `--without-demo=all` 安装生产模块集。
3. 应用 extension module registry。
4. 重启 Odoo。
5. 执行平台初始化 preflight。
6. 使用离线 payload 执行历史连续性 replay。
7. 执行业务可用性 probe。
8. 执行 full business smoke。
9. 执行 role matrix smoke。
10. 执行 frontend smoke。

如果模块已由外部发布系统安装完成：

```bash
ENV=prod ENV_FILE=.env.prod DB_NAME=sc_prod PROD_DANGER=1 \
  HISTORY_PRODUCTION_INSTALL_MODULES=0 \
  RUN_ID=prod_history_init_$(date +%Y%m%dT%H%M%S) \
  BASE_URL=https://<production-host> \
  FRONTEND_BASE_URL=https://<production-host> \
  make history.production.fresh_init
```

### 6.2 重建前演练

正式生产重建前，必须在 prod-sim 或 UAT 环境使用同一份资产演练。

```bash
ENV=test ENV_FILE=.env.prod.sim DB_NAME=sc_prod_sim \
  RUN_ID=rehearsal_$(date +%Y%m%dT%H%M%S) \
  HISTORY_CONTINUITY_USE_PACKAGED_PAYLOADS=1 \
  make history.continuity.rehearse

ENV=test ENV_FILE=.env.prod.sim DB_NAME=sc_prod_sim \
  RUN_ID=rehearsal_$(date +%Y%m%dT%H%M%S) \
  HISTORY_CONTINUITY_USE_PACKAGED_PAYLOADS=1 \
  make history.continuity.replay

ENV=test ENV_FILE=.env.prod.sim DB_NAME=sc_prod_sim \
  make history.business.usable.probe
```

演练必须记录：

- `RUN_ID`
- 源数据快照时间
- 目标 DB 名
- 资产包版本和 hash
- replay artifact 目录
- 失败 step 和修复结论
- 用户可见性验收结论

### 6.3 历史重建的顺序

历史重建必须按固定顺序执行，不允许为了绕过错误跳步上线。

1. 环境预检：compose、dbfilter、外部依赖、磁盘、备份。
2. 模块初始化：只安装生产模块，不安装 demo。
3. 主数据重建：用户、伙伴、项目、项目成员 carrier。
4. 历史事实重放：合同、收款、付款、发票、资金、物料、文件索引、审批痕迹等。
5. 运行态投影：将需要用户可见的历史事实投影到新系统 runtime carrier。
6. 状态恢复：只恢复已有证据支撑的历史状态，不伪造新审批。
7. 权限策略：应用 Business Full 和 role matrix。
8. 可用性 probe：验证历史数据可查、关键入口可用。
9. 业务 smoke：验证新业务动作不被历史缺口全局阻断。
10. 证据归档：归档 replay 输出、日志、probe 结果和验收记录。

### 6.4 断点续跑

如果重建中断，禁止重新发明服务器脚本。保留同一个 `RUN_ID`，用失败 step 续跑：

```bash
ENV=prod ENV_FILE=.env.prod DB_NAME=sc_prod PROD_DANGER=1 \
  RUN_ID=<same_run_id> \
  HISTORY_CONTINUITY_START_AT=<failed_step> \
  make history.production.fresh_init
```

如需指定 artifact 目录：

```bash
ENV=prod ENV_FILE=.env.prod DB_NAME=sc_prod PROD_DANGER=1 \
  RUN_ID=<same_run_id> \
  MIGRATION_ARTIFACT_ROOT=/tmp/history_continuity/sc_prod/<same_run_id> \
  HISTORY_CONTINUITY_START_AT=<failed_step> \
  make history.production.fresh_init
```

说明：`history.continuity.replay` 在 Makefile 中受 `guard.prod.forbid` 保护，仅用于
prod-sim/UAT 演练；生产环境断点续跑必须继续走 `history.production.fresh_init`。

断点续跑前必须确认：

- 失败 step 是幂等或已有跳过重复记录的保护。
- 上游 step 输出完整。
- 目标 DB 未被手工修补污染。
- artifact root 未被删除。

### 6.5 局部重建规则

局部重建仅用于已评审的历史事实补链，不用于替代完整重建。

允许原则：

- 只补一个事实域。
- 必须先在 prod-sim 重放。
- 必须明确 `HISTORY_CONTINUITY_START_AT` 和可选 `HISTORY_CONTINUITY_STOP_AFTER`。
- 必须保留 artifact。
- 必须写明是否会影响用户可见 runtime carrier。

禁止：

- 直接在生产库执行 `fresh_db.*` 单点 target 而无评审。
- 直接执行 Odoo shell 或 psql 修数据。
- 用 demo seed 修复生产数据。
- 通过前端隐藏问题代替后端事实补链。

## 7. 数据重建验收标准

重建完成后，以下结论必须全部记录。

| 验收项 | 通过标准 |
| --- | --- |
| replay | `history.production.fresh_init` 内部历史重建链路无阻断失败 |
| usable probe | `history_business_usable_ready`，且 `gap_count=0` |
| smoke | Business Full、role matrix、frontend smoke 通过 |
| 历史数据 | 用户、项目、合同、资金、付款、发票、文件索引等核心事实有记录数和样本 |
| 新业务 | 新增、提交、审批、查看动作不被历史缺口全局阻断 |
| 权限 | 角色入口和菜单符合 role surface |
| contract | `system.init`、`ui.contract` 无启动链漂移 |
| 证据 | artifact、日志、RUN_ID、源数据版本已归档 |

`history_business_usable_visible_but_promotion_gaps` 不得作为新库正式切换的默认通过标准。若剩余缺口指向用户可见 runtime 承载模型，必须先补齐 projection 和 runtime probe。任何豁免都必须由人工在部署记录中说明缺口不影响真实用户业务动作。若出现 `history_business_usable_runtime_gap`，不得上线。

## 8. 回滚策略

### 8.1 升级型部署回滚

适用于已有生产库升级失败：

1. 停止写入入口或切维护页。
2. 回退到上一版本镜像/代码。
3. 恢复升级前数据库备份和 filestore 备份。
4. 启动服务。
5. 执行登录、`system.init`、核心菜单和 smoke 验证。

### 8.2 新库历史重建回滚

适用于首次上线重建失败：

1. 保留失败库，不覆盖 artifact。
2. 切回旧系统或维护页。
3. 使用重建前的空库快照重新创建 `sc_prod`，或新建候选库重新跑。
4. 修复资产或重建脚本后从 prod-sim 重新演练。
5. 重新申请上线窗口。

如果重建失败但断点可恢复，优先使用 `HISTORY_CONTINUITY_START_AT` 续跑；只有在数据污染或幂等边界不成立时才整体回滚。

### 8.3 生产数据禁止事项

- 禁止无备份删除生产库。
- 禁止手工 `psql` 修业务数据。
- 禁止直接改 `ir.model.data` 逃避幂等冲突。
- 禁止删除 filestore 后继续使用原库。
- 禁止让旧系统和新系统同时写同一业务事实。

## 9. 证据归档

每次正式部署必须归档：

- 发布版本：commit/tag/镜像版本。
- 环境参数：脱敏后的 `.env.prod` 关键项。
- 预检输出：compose、依赖、磁盘、DB 名。
- 执行命令：完整命令和时间。
- `RUN_ID`：数据重建必须有。
- artifact：`/tmp/history_continuity/<db>/<run_id>` 或配置的 `MIGRATION_ARTIFACT_ROOT`。
- Odoo 日志：部署窗口内完整日志。
- 验证结果：baseline、p0、business smoke、role matrix smoke、frontend smoke。
- 验收人和验收时间。
- 回滚点：数据库备份路径、filestore 备份路径、上一版本 commit/tag。

## 10. 最小上线清单

上线负责人逐项确认：

- [ ] 当前版本已冻结。
- [ ] `.env.prod` 已评审。
- [ ] 生产备份已完成并可恢复。
- [ ] 外部依赖目录存在。
- [ ] 已完成 prod-sim 或 UAT 重建演练。
- [ ] 已明确本次是升级还是新库历史重建。
- [ ] 已准备 `RUN_ID` 和 artifact 目录。
- [ ] 已确认停机窗口和旧系统写入冻结时间。
- [ ] 已执行生产部署命令。
- [ ] 已执行权限策略 apply。
- [ ] 已执行 baseline/p0/smoke 验证。
- [ ] 已归档日志和 artifact。
- [ ] 已完成业务验收。
- [ ] 已记录回滚点。
