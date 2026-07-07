# Production Deployment Record — form_productization_20260707

## 1. 基本信息

| 项目 | 值 |
| --- | --- |
| 部署编号 | `form_productization_20260707` |
| 部署窗口 | `2026-07-07 Asia/Shanghai` |
| 操作人 | `Codex assisted` |
| 审批人 | `user approved` |
| 生产主机 | `sc-prod` |
| 生产目录 | `/opt/sce/production/sce-backend-odoo` |
| 生产数据库 | `sc_prod` |
| 发布类型 | `incremental package` |
| 发布包 | `/tmp/form_productization_20260707.tar.gz` |
| 发布包 sha256 | `5f07470fdecb9df334fb91492bf97190281329e9e42a07c13c78ca64a0854f0c` |
| 本地基线 | `origin/main@9532d05d43440f6b604e3af0b63c37e3b679a8cd` plus production hotfixes in this record |

## 2. 发布范围声明

本次发布范围：

- [x] 表单产品化发布包文件应用。
- [x] 受影响 addon 目录同步：`smart_core`、`smart_construction_core`、`smart_construction_custom`。
- [x] 模块升级：`smart_core`、`smart_construction_core`、`smart_construction_custom`。
- [x] 生产策略刷新和角色矩阵刷新。
- [x] 生产验证矩阵通过。
- [ ] 生产与日常开发服务器全量代码树一致。

本次结论仅限于表单产品化发布范围、受影响 addon 同步范围和发布后验证结果。生产服务器不是开发工作区全量镜像。

## 3. 发布前状态

生产服务在执行前为 `running healthy`。本次生产文件树早于当前发布基线，主发布包应用后继续按受影响范围补齐 manifest 依赖、受影响 addon 目录、迁移脚本和只读验证脚本。

日常开发与生产差异登记：

| 差异类型 | 结果 | 说明 |
| --- | --- | --- |
| 发布包文件差异 | `0` | 主发布包 39 个文件 sha 校验通过 |
| 受影响 addon 差异 | `0` | `smart_core`、`smart_construction_core`、`smart_construction_custom` 已按本次范围同步 |
| 全量代码树差异 | `present` | 生产不是开发工作区全量镜像 |
| 数据差异 | `PASS` | 生产非 demo 污染检查通过 |

Demo 状态：

```text
smart_construction_demo XMLID count=0
smart_construction_demo|uninstalled|
```

## 4. 备份

| 类型 | 路径 | 结果 |
| --- | --- | --- |
| 生产整体备份 | `/data/backups/prod_backup_form_productization_20260707T063806+0800` | `PASS` |
| 主发布包应用备份 | `/data/backups/deploy/form_productization_apply_20260707T064021+0800` | `PASS` |
| manifest 依赖补齐备份 | `/data/backups/deploy/form_productization_manifest_deps_20260707T064155+0800` | `PASS` |
| core validator 同步备份 | `/data/backups/deploy/form_productization_core_validator_20260707T064250+0800` | `PASS` |
| 受影响 addon 全量同步备份 | `/data/backups/deploy/form_productization_addons_full_20260707T064352+0800` | `PASS` |
| manifest 顺序修复备份 | `/data/backups/deploy/form_productization_manifest_order_20260707T064956+0800` | `PASS` |
| 迁移 17.0.0.56 修复备份 | `/data/backups/deploy/form_productization_migration_170056_20260707T070004+0800` | `PASS` |
| readiness 入口脚本补齐备份 | `/data/backups/deploy/form_productization_readiness_script_20260707T071530+0800` | `PASS` |
| history probe 同步备份 | `/data/backups/deploy/form_productization_history_probe_20260707T073241+0800` | `PASS` |
| history probe 白名单修复备份 | `/data/backups/deploy/form_productization_history_probe_whitelist_20260707T073331+0800` | `PASS` |
| BASE_SYSTEM_FILE 补齐脚本备份 | `/data/backups/deploy/form_productization_base_file_mirror_script_20260707T074029+0800` | `PASS` |

生产整体备份校验：

```text
sc_prod_prod_backup_20260707T063806+0800.dump sha256=a91ec4ea91da7caa38e67a7b0ac671f018530548be7b6532a1dea4d926cdc7f5
sc_prod_filestore_prod_backup_20260707T063806+0800.tar.gz sha256=b3deb9e63d5296ef3d7fe220711ac8af6373d2e4f71654ab0929d25ab22dd349
sce-backend-odoo_deploy_prod_backup_20260707T063806+0800.tar.gz sha256=6d941b965958172ada606f0d2a0f4ddf9d6d4bf642308f1ba44cea0c2335c44b
```

## 5. Prod-Sim 验证

本次生产窗口由用户授权直接按正式发布链路执行。由于生产文件树早于候选增量包，发布过程中以生产新备份为回滚点，在生产侧逐项补齐受影响文件并即时验证。后续发布仍应优先执行 prod-sim 回放。

| 检查项 | 结果 | 证据 |
| --- | --- | --- |
| 生产备份可用 | `PASS` | `/data/backups/prod_backup_form_productization_20260707T063806+0800` |
| 模块升级兼容 | `PASS` | production `make mod.upgrade` |
| 业务烟测 | `PASS` | production `smoke.business_full` |
| 角色矩阵 | `PASS` | production `smoke.role_matrix` |
| 非 demo 污染 | `PASS` | production `verify.non_demo_data_contamination` |

## 6. 生产执行摘要

主发布包远端校验：

```text
sha256=5f07470fdecb9df334fb91492bf97190281329e9e42a07c13c78ca64a0854f0c
post_apply_sha total=39 bad=0
```

生产升级链路：

```bash
ENV=prod ENV_FILE=.env.prod DB_NAME=sc_prod PROD_DANGER=1 \
  CODEX_NEED_UPGRADE=1 \
  CODEX_MODULES=smart_core,smart_construction_core,smart_construction_custom \
  MODULE=smart_core,smart_construction_core,smart_construction_custom \
  make mod.upgrade
```

升级结果：

```text
79 modules loaded in 628.09s
Registry loaded in 633.416s
module upgrade result=PASS
```

策略刷新：

```text
apply_business_full_policy: True
apply_role_matrix: True
```

服务健康：

```text
sc-backend-odoo-prod-odoo-1    Up 20 minutes (healthy)
sc-backend-odoo-prod-db-1      Up 5 weeks (healthy)
sc-backend-odoo-prod-redis-1   Up 5 weeks (healthy)
docker health=running healthy
```

## 6.1 发布中修复说明

生产升级暴露出生产文件树早于当前发布基线。本次按受影响范围补齐：

- manifest 依赖文件缺失。
- 表单产品化 contract 加载顺序早于 action/view 定义。
- 生产 `smart_core` validator 旧版本仍要求 `views.form.columns`。
- `sc.hr.payroll.document` 等新字段缺失。
- 迁移 `17.0.0.56` 将系统配置向导 `quota.import.wizard / 四川定额导入` 误判为业务配置契约阻断。
- 生产只读 readiness target 缺入口脚本。
- 历史可用性探针未显式白名单 SCBS55 用户核对只读历史事实面。

上述修复均已回补到本地代码并纳入本部署记录。

## 7. 发布后验证

| 检查项 | 结果 | 摘要 |
| --- | --- | --- |
| `verify.baseline` | `PASS` | `PASS ALL on sc_prod` |
| `verify.p0` | `PASS` | 登录环境 `prod`，P0 配置通过 |
| `smoke.business_full` | `PASS` | 材料计划、合同、结算、付款申请全链路通过 |
| `smoke.role_matrix` | `PASS` | 角色读写边界与审批路径通过 |
| `verify.non_demo_data_contamination` | `PASS` | `PASS db=sc_prod mode=default` |
| `verify.business_system.usability_readiness.prod` | `PASS` | `ready_for_business_system_use`，history gap=0，formal backfill gap=0 |
| `history.attachment.custody.probe.prod` | `PASS` | `history_attachment_custody_ready`，gap_count=0，legacy_url_attachments=19541 |
| 服务健康 | `PASS` | `running healthy` |

Demo 状态：

```text
smart_construction_demo XMLID count=0
smart_construction_demo|uninstalled|
```

## 7.1 附件补齐状态

附件补齐与表单产品化部署分开判定。

已通过：

```text
legacy_url_attachments=19541
legacy_url_local_file_ok=19541
legacy_url_missing_local_file=0
```

当前遗留：

```text
file_index_rows=243713
local_file_ok=243592
missing_local_file=121
source_table=BASE_SYSTEM_FILE
```

已尝试从两个在线源补齐 `BASE_SYSTEM_FILE` 缺失文件：

```text
records_checked=125213
already_local_ok=125096
downloaded_local_ok=3
download_failed=114
```

剩余缺失主要由旧系统 `ShowFileById` 返回 HTTP 500 导致，属于外部旧源不可取附件遗留，不阻塞本次表单产品化生产部署结论；后续应作为附件运维专项继续跟踪。

## 8. 回滚点

| 回滚对象 | 路径/版本 | 操作说明 |
| --- | --- | --- |
| 生产整体 | `/data/backups/prod_backup_form_productization_20260707T063806+0800` | 按生产恢复 runbook 执行 |
| 文件级变更 | `/data/backups/deploy/form_productization_*_20260707*` | 按批次恢复对应文件 |
| 发布包 | `/tmp/form_productization_20260707.tar.gz` | sha256 已记录 |

## 9. 收口结论

- [x] 本次发布包范围已与生产对齐。
- [x] 表单产品化发布范围已部署到生产。
- [x] 生产模块升级成功。
- [x] 生产服务健康检查通过。
- [x] 生产验证矩阵全部通过。
- [x] 生产只读业务可用性门禁通过。
- [x] demo 模块和 demo XMLID 状态符合生产要求。
- [ ] 生产与开发服务器全量代码树一致。
- [ ] 附件完整性严格审计全部通过。

最终发布结论：

```text
本次表单产品化生产增量发布已完成，生产服务健康，核心业务验证矩阵通过，具备生产运行条件。
生产不是开发工作区全量镜像；后续迭代必须从当前 main 和本部署记录出发，经 prod-sim 回放后形成下一发布包。
附件仍有 121 个 BASE_SYSTEM_FILE 本地文件缺失，需作为发布后运维专项继续处理。
```

## 10. 后续事项

| 事项 | 负责人 | 截止时间 | 状态 |
| --- | --- | --- | --- |
| 将 121 个 `BASE_SYSTEM_FILE` 缺失附件作为运维专项继续补齐 | `TBD` | `TBD` | `open` |
| 下一轮迭代从当前 `main` 和本部署记录出发建立候选发布范围 | `TBD` | `TBD` | `open` |
| 后续生产发布恢复 prod-sim 优先回放要求 | `TBD` | `TBD` | `open` |
