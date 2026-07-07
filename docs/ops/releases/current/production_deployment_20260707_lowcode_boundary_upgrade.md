# Production Deployment Record

## 1. 基本信息

| 项目 | 值 |
| --- | --- |
| 部署编号 | `lowcode_boundary_upgrade_20260707` |
| 部署窗口 | `2026-07-07 16:45-17:05 Asia/Shanghai` |
| 操作人 | `Codex assisted` |
| 审批人 | `user approved` |
| 生产主机 | `sc-prod` |
| 生产目录 | `/opt/sce/production/sce-backend-odoo` |
| 生产数据库 | `sc_prod` |
| 发布类型 | `incremental package` |
| 发布包 | `/tmp/lowcode_boundary_upgrade_20260707.tar.gz` |
| 发布包 sha256 | `1f8d6d6abeef847687db44f5499e1ff7f3842d6af36736592ffb05b6e06478ef` |
| 目标 commit/tag | `c802c81abeef5054d385f4291cc91bcf2596fdb7` |

## 2. 发布范围声明

本次发布范围：

- [x] 发布包增量对齐。
- [x] 低代码配置边界 guard 对齐。
- [x] `smart_core` 平台核心低代码边界运行态对齐。
- [x] 生产验证资产和生产升级标准文档对齐。
- [ ] 生产与日常开发服务器全量一致。

生产与日常开发服务器不是全量一致。本次结论仅限于低代码边界增量发布包范围和发布后验证结果。

变更文件清单：

```text
Makefile
addons/smart_core/**
scripts/verify/**
docs/architecture/**
docs/product/**
docs/low_code_config_capability_matrix.md
docs/ops/**
frontend/apps/web/scripts/**
frontend/apps/web/src/app/businessConfigBoundaries.ts
frontend/apps/web/src/views/MenuConfigView.vue
frontend/apps/web/src/views/BusinessConfigSurfaceView.vue
frontend/apps/web/src/pages/ContractFormPage.vue
```

模块清单：

```text
smart_core
```

Migration 清单：

```text
无新增数据库 migration。本次运行态变更通过 smart_core 模块升级和安全重启生效。
```

## 3. 发布前状态

生产服务状态：

```text
sc-backend-odoo-prod-odoo-1    healthy
sc-backend-odoo-prod-db-1      healthy
sc-backend-odoo-prod-redis-1   healthy
HTTP / => 303 SEE OTHER -> /web
```

生产模块版本：

```text
smart_core installed
smart_construction_demo|uninstalled|
smart_construction_demo XMLID count=0
```

日常开发与生产差异登记：

| 差异类型 | 结果 | 说明 |
| --- | --- | --- |
| 发布包文件差异 | `0` | 本次增量发布包范围已同步到生产 |
| 模块版本差异 | `PASS` | `smart_core` 已在生产执行模块升级 |
| 全量代码树差异 | `present` | 生产目录不是 Git 工作区，不声明全量一致 |
| 数据差异 | `PASS` | 非 demo 污染和业务 readiness 已通过 |

## 4. 备份

生产写入前已记录文件级回滚点。

| 类型 | 路径 | 校验 | 结果 |
| --- | --- | --- | --- |
| 覆盖文件 | `/data/backups/deploy/lowcode_boundary_guard_20260707T164554+0800` | `tar backup created` | `PASS` |
| 覆盖文件 | `/data/backups/deploy/lowcode_runtime_boundary_upgrade_20260707T164727+0800` | `tar backup created` | `PASS` |
| 发布标准文档 | `/data/backups/deploy/production_upgrade_standard_docs_20260707T1705+0800` | `tar backup created` | `PASS` |

备份验证命令：

```bash
ssh sc-prod 'test -d /data/backups/deploy/lowcode_boundary_guard_20260707T164554+0800'
ssh sc-prod 'test -d /data/backups/deploy/lowcode_runtime_boundary_upgrade_20260707T164727+0800'
```

## 5. Prod-Sim 验证

本次发布为已授权的生产增量升级，生产侧以文件级备份为回滚点执行。低代码边界变更已先在本地和日常开发服务器通过 guard，随后生产执行同一专项 guard 和发布后验证矩阵。

| 检查项 | 结果 | 证据 |
| --- | --- | --- |
| 日常开发服务器目标 commit | `PASS` | `c802c81abeef5054d385f4291cc91bcf2596fdb7` |
| 候选发布包应用 | `PASS` | `/tmp/lowcode_boundary_upgrade_20260707.tar.gz` |
| 模块升级 | `PASS` | production `make mod.upgrade MODULE=smart_core` |
| 业务烟测 | `PASS` | production `smoke.business_full` |
| 角色矩阵 | `PASS` | production `smoke.role_matrix` |
| 非 demo 污染 | `PASS` | production `verify.non_demo_data_contamination` |

prod-sim 运行 ID：

```text
dev-server-c802c81ab-lowcode-boundary-guard
```

## 6. 生产执行摘要

发布包校验：

```text
1f8d6d6abeef847687db44f5499e1ff7f3842d6af36736592ffb05b6e06478ef  /tmp/lowcode_boundary_upgrade_20260707.tar.gz
changed_files.txt entries=2413
```

文件同步和备份：

```bash
rsync -av --relative Makefile addons/smart_core/ scripts/verify/ docs/architecture/ docs/product/ docs/ops/ ...
```

模块升级：

```bash
ENV=prod ENV_FILE=.env.prod DB_NAME=sc_prod PROD_DANGER=1 \
  CODEX_NEED_UPGRADE=1 CODEX_MODULES=smart_core MODULE=smart_core \
  make mod.upgrade
```

升级结果：

```text
79 modules loaded
Registry loaded
module upgrade result=PASS
```

服务重启：

```bash
ENV=prod ENV_FILE=.env.prod DB_NAME=sc_prod PROD_DANGER=1 make prod.restart.safe
```

专项 guard：

```text
lowcode_config_boundary_guard PASS
business_config_guard_inventory PASS
backend_contract_boundary_guard PASS
production_release_flow_guard PASS
```

## 7. 发布后验证

最低验证矩阵：

| 检查项 | 结果 | 摘要 |
| --- | --- | --- |
| `verify.baseline` | `PASS` | `PASS ALL on sc_prod` |
| `verify.p0` | `PASS` | 登录环境 `prod`，P0 通过 |
| `smoke.business_full` | `PASS` | 材料计划、合同、结算、付款申请全链路通过 |
| `smoke.role_matrix` | `PASS` | 角色读写边界与审批路径通过 |
| `verify.non_demo_data_contamination` | `PASS` | `PASS db=sc_prod mode=default` |
| `history.attachment.custody.probe.prod` | `PASS` | `history_attachment_custody_ready`，gap_count=0，legacy_url_attachments=19541 |
| 服务健康 | `PASS` | `running healthy`，HTTP `/` 返回 `303 SEE OTHER` |

补充只读 readiness：

```text
verify.business_system.usability_readiness.prod PASS
decision=ready_for_business_system_use
history_business_usable_ready gap_count=0
formal_business_backfill_ready gap_count=0
```

Demo 状态：

```text
smart_construction_demo XMLID count=0
smart_construction_demo|uninstalled|
```

## 8. 回滚点

| 回滚对象 | 路径/版本 | 操作说明 |
| --- | --- | --- |
| 低代码 guard 文件 | `/data/backups/deploy/lowcode_boundary_guard_20260707T164554+0800` | 恢复对应文件后执行 `prod.restart.safe` |
| 低代码运行态文件 | `/data/backups/deploy/lowcode_runtime_boundary_upgrade_20260707T164727+0800` | 恢复对应文件后执行 `prod.restart.safe` |
| 发布标准文档 | `/data/backups/deploy/production_upgrade_standard_docs_20260707T1705+0800` | 恢复 docs/scripts 验证资产即可 |
| 发布包 | `/tmp/lowcode_boundary_upgrade_20260707.tar.gz` | sha256 已记录 |

## 9. 收口结论

- [x] 本次发布包范围已与生产对齐。
- [x] 生产模块版本已达到目标版本。
- [x] 生产服务健康检查通过。
- [x] 生产验证矩阵全部通过。
- [x] demo 模块和 demo XMLID 状态符合生产要求。
- [ ] 生产与日常开发服务器全量一致。

生产与日常开发服务器不是全量一致。本次结论仅限于低代码边界发布包范围、`smart_core` 模块升级结果和发布后验证矩阵。

最终发布结论：

```text
本次低代码边界生产增量发布已完成。生产服务健康，低代码专项 guard、业务 smoke、角色矩阵、非 demo 污染、业务 readiness 和附件 custody 探针均通过，具备生产运行条件。
```

## 10. 后续事项

| 事项 | 负责人 | 截止时间 | 状态 |
| --- | --- | --- | --- |
| 后续生产发布优先按生产升级标准构建正式 release package | `Ops` | `2026-07-08` | `closed: production upgrade standard is now the required path` |
| 生产附件剩余在线源不可取文件继续按运维专项跟踪 | `Ops` | `post-release operations` | `tracked: legacy attachment residual专项` |
| 下一轮迭代从 `main@c802c81ab` 和本部署记录出发 | `Ops` | `2026-07-07` | `closed: superseded by main_full_alignment_20260707` |
