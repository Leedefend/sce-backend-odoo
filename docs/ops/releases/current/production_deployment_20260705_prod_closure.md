# Production Deployment Record — prod_closure_20260705

## 1. 基本信息

| 项目 | 值 |
| --- | --- |
| 部署编号 | `prod_closure_20260705` |
| 部署窗口 | `2026-07-05 Asia/Shanghai` |
| 操作人 | `Codex assisted` |
| 审批人 | `user approved` |
| 生产主机 | `sc-prod` |
| 生产目录 | `/opt/sce/production/sce-backend-odoo` |
| 生产数据库 | `sc_prod` |
| 发布类型 | `incremental package` |
| 发布包 | `/tmp/prod_closure_release_package_20260705.tar.gz` |
| 发布包 sha256 | `52316809ef441cdf11edf676d17be82ce7c9f1b8f1bbdabed1ec3d16b6ed9e57` |
| 目标 commit/tag | `dirty workspace incremental release package` |

## 2. 发布范围声明

本次发布范围：

- [x] 发布包增量对齐
- [ ] 模块版本对齐
- [ ] 全量代码树对齐
- [x] 数据承载规则对齐

本次结论仅限于发布包范围与发布后验证结果。生产服务器与日常开发服务器不是全量一致。

变更文件清单：见最终发布包内 `package/changed_files.txt`。

模块清单：

```text
smart_core
smart_construction_core
smart_construction_portal
smart_construction_custom
smart_construction_seed
```

Migration 清单：

```text
smart_construction_seed/migrations/17.0.0.2.1/post-migration.py
```

## 3. 发布前状态

生产服务状态在执行写入前保持健康；升级过程使用一次性 Odoo 容器执行模块升级。

生产模块版本发布后确认：

```text
smart_construction_core|installed|17.0.0.52
smart_construction_custom|installed|17.0.1.0
smart_construction_demo|uninstalled|
smart_construction_portal|installed|17.0.1.1
smart_construction_seed|installed|17.0.0.2.1
smart_core|installed|17.0.1.0
```

日常开发与生产差异登记：

| 差异类型 | 结果 | 说明 |
| --- | --- | --- |
| 发布包文件差异 | `0` | 最终发布包文件与本地、生产文件校验一致 |
| 模块版本差异 | `present` | dev 与 prod 模块版本不同，dev 不能代表生产镜像 |
| 全量代码树差异 | `missing=3235, diff=694` | 生产不是开发工作区全量同步 |
| 数据差异 | `PASS` | 生产非 demo 污染检查通过 |

## 4. 备份

| 类型 | 路径 | 校验 | 结果 |
| --- | --- | --- | --- |
| 生产整体备份 | `/data/backups/prod_backup_20260705T105732+0800` | 已检查存在 | `PASS` |
| 覆盖文件备份 | `/data/backups/deploy/prod_closure_apply_20260705T134544+0800` | 文件级备份 | `PASS` |
| 覆盖文件备份 | `/data/backups/deploy/prod_closure_dep_apply_20260705T134650+0800` | 文件级备份 | `PASS` |
| 覆盖文件备份 | `/data/backups/deploy/prod_closure_menu_fix_20260705T134813+0800` | 文件级备份 | `PASS` |
| 覆盖文件备份 | `/data/backups/deploy/prod_closure_history_parent_fix_20260705T134948+0800` | 文件级备份 | `PASS` |
| 覆盖文件备份 | `/data/backups/deploy/prod_closure_missing_menu_fix_20260705T135234+0800` | 文件级备份 | `PASS` |
| 覆盖文件备份 | `/data/backups/deploy/prod_closure_schema_guard_sync_20260705T135458+0800` | 文件级备份 | `PASS` |
| 覆盖文件备份 | `/data/backups/deploy/prod_closure_non_demo_guard_sync_20260705T135547+0800` | 文件级备份 | `PASS` |

## 5. Prod-Sim 验证

| 检查项 | 结果 | 证据 |
| --- | --- | --- |
| 生产级完整回放 | `PASS` | `artifacts/migration/prod_sim_fresh_replay_20260705T124509` |
| 模块升级兼容 | `PASS` | prod-sim replay and production upgrade |
| 业务烟测 | `PASS` | prod-sim and production smoke |
| 角色矩阵 | `PASS` | prod-sim and production smoke |
| 非 demo 污染 | `PASS` | production guard |

prod-sim 运行 ID：

```text
prod_sim_fresh_replay_20260705T124509
```

## 6. 生产执行摘要

发布包远端校验：

```text
expected=52316809ef441cdf11edf676d17be82ce7c9f1b8f1bbdabed1ec3d16b6ed9e57
actual=52316809ef441cdf11edf676d17be82ce7c9f1b8f1bbdabed1ec3d16b6ed9e57
REMOTE_PACKAGE_SHA_OK
```

模块升级：

```bash
ENV=prod ENV_FILE=.env.prod DB_NAME=sc_prod PROD_DANGER=1 \
  CODEX_NEED_UPGRADE=1 \
  CODEX_MODULES=smart_core,smart_construction_core,smart_construction_portal,smart_construction_custom,smart_construction_seed \
  MODULE=smart_core,smart_construction_core,smart_construction_portal,smart_construction_custom,smart_construction_seed \
  make mod.upgrade
```

策略刷新：

```text
apply_business_full_policy: True
apply_role_matrix: True
```

服务健康：

```text
running healthy
```

## 7. 发布后验证

| 检查项 | 结果 | 摘要 |
| --- | --- | --- |
| `verify.baseline` | `PASS` | 基线配置通过 |
| `verify.p0` | `PASS` | 登录环境为 prod，P0 配置通过 |
| `smoke.business_full` | `PASS` | 业务全链路通过 |
| `smoke.role_matrix` | `PASS` | 角色矩阵通过 |
| `verify.non_demo_data_contamination` | `PASS` | 数据守卫与 schema guard 均通过 |
| 服务健康 | `PASS` | `running healthy` |

Demo 状态：

```text
smart_construction_demo XMLID count=0
smart_construction_demo|uninstalled|
```

## 8. 回滚点

| 回滚对象 | 路径/版本 | 操作说明 |
| --- | --- | --- |
| 生产整体 | `/data/backups/prod_backup_20260705T105732+0800` | 按生产恢复 runbook 执行 |
| 文件级变更 | `/data/backups/deploy/prod_closure_*` | 按批次恢复对应文件 |
| 发布包 | `/tmp/prod_closure_release_package_20260705.tar.gz` | sha256 已记录 |

## 9. 收口结论

- [x] 本次发布包范围已与生产对齐。
- [x] 生产模块版本已达到本次发布目标。
- [x] 生产服务健康检查通过。
- [x] 生产验证矩阵全部通过。
- [x] demo 模块和 demo XMLID 状态符合生产要求。
- [ ] 生产与日常开发服务器全量一致。

生产与日常开发服务器不是全量一致。本次结论仅限于发布包范围和发布后验证结果。

最终发布结论：

```text
本次生产增量发布已完成，生产服务健康，验证矩阵通过，具备生产运行条件。
后续迭代必须从当前生产基线出发，经 prod-sim 回放验证后再形成下一发布包。
```

## 10. 后续事项

| 事项 | 负责人 | 截止时间 | 状态 |
| --- | --- | --- | --- |
| 下一次迭代从当前生产基线建立候选发布范围 | `TBD` | `TBD` | `open` |
| 将本次规范和部署记录纳入下一次 release evidence | `TBD` | `TBD` | `open` |
