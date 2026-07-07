# 生产发布链路规范 v1

## 1. 目标

本文规范从日常开发到生产部署的完整链路，解决以下问题：

- 日常开发服务器、生产模拟环境、生产服务器的职责边界不清。
- 只验证增量发布包，却误认为生产与开发全量一致。
- 生产升级缺少固定的备份、包校验、模块升级、验证和证据归档顺序。
- 后续迭代缺少从生产基线出发的可重复发布节奏。

本文是生产发布的流程总纲；具体命令红线继续以
`docs/ops/prod_command_policy.md` 为准，生产部署细节继续以
`docs/ops/production_deployment_runbook_v1.md` 为准。

## 2. 环境职责

| 环境 | 标准标识 | 数据库 | 职责 | 不得用于 |
| --- | --- | --- | --- | --- |
| 日常开发 | `ENV=dev` | `sc_demo` | 日常功能开发、局部验证、开发态回归 | 证明可生产发布 |
| 测试/门禁 | `ENV=test` | `sc_test` | CI 类验证、严格 gate、非生产破坏性测试 | 承载正式客户数据 |
| 生产模拟 | `ENV=prod-sim` 或隔离 compose | 生产备份回放库 | 用生产备份验证迁移、升级、发布包 | 日常随意调试 |
| 生产 | `ENV=prod` | `sc_prod` | 正式运行、受控升级、发布后验收 | demo、reset、gate、临时试错 |

三层事实源：

- 代码事实源：Git commit/tag/release package。
- 数据事实源：生产数据库备份、filestore 备份、生产迁移记录。
- 运行事实源：Makefile target、compose project、验证报告。

## 3. 对齐定义

发布前后必须明确声明本次对齐范围。

### 3.1 发布包对齐

发布包对齐表示：

- 发布包文件清单中的文件，本地包、生产服务器文件、包内 sha256 一致。
- 发布包已经在生产模拟环境通过升级和验证。
- 生产服务器已应用该包，并通过发布后验证矩阵。

发布包对齐不表示开发服务器和生产服务器整棵代码树完全一致。

### 3.2 模块版本对齐

模块版本对齐表示：

```sql
select name, state, latest_version
from ir_module_module
where name in (...);
```

在目标环境中结果一致，且相关 migration 已执行完成。

### 3.3 全量代码树对齐

全量代码树对齐表示 Git 跟踪普通文件在开发工作区和生产服务器逐文件 sha256 一致。
该状态只允许在明确执行“全量发布”时作为目标；常规生产升级默认是发布包增量对齐。

### 3.4 数据对齐

数据对齐不是逐行相同，而是生产业务数据满足本次发布的承载规则：

- 非 demo 污染检查通过。
- 迁移投影、历史事实、业务闭环、角色矩阵验证通过。
- 生产数据没有被 demo、测试或开发数据污染。

## 4. 硬规则

1. 生产不得直接用日常开发目录整包覆盖，除非本次发布明确批准为全量发布。
2. 生产不得执行 `db.reset`、`demo.*`、`gate.*`、`ci.*`。
3. 生产 seed 只能使用 `PROFILE=base`，且必须显式指定 `DB_NAME=sc_prod` 和 `SEED_DB_NAME_EXPLICIT=1`。
4. 所有生产状态变更必须通过 Makefile target 或已审批的发布包同步命令完成。
5. 发布包必须包含：
   - `changed_files.txt`
   - `SHA256SUMS`
   - 操作命令说明
   - 验证矩阵
   - 当前生产状态摘要
6. 每次生产部署必须基于
   `docs/ops/releases/templates/production_deployment_record_TEMPLATE.zh.md`
   留存一份部署记录。
7. 生产写入前必须完成数据库和 filestore 备份，并记录备份路径。
8. 生产升级后必须跑完验证矩阵；只完成模块升级不算发布完成。
9. 任何生产修复必须回写到本地代码和发布包，避免生产成为唯一真实版本。

## 5. 标准发布流程

### 5.1 日常开发阶段

使用 dev 环境进行功能开发和局部验证：

```bash
ENV=dev ENV_FILE=.env.dev DB_NAME=sc_demo make up
ENV=dev ENV_FILE=.env.dev DB_NAME=sc_demo make verify.dev.acceptance.release
```

开发阶段允许模块版本领先生产，但必须记录该差异。不能因为 dev 验证通过就直接判断生产可部署。

### 5.2 发布冻结

冻结时必须生成候选发布说明：

- 本次发布类型：增量发布或全量发布。
- 目标生产基线：生产当前模块版本、包 sha256、数据库备份时间。
- 变更范围：文件清单、模块清单、migration 清单。
- 风险范围：菜单/XMLID、数据库结构、权限、历史数据、seed、demo 清理。

推荐检查：

```bash
git status --short
git diff --check
ENV=dev ENV_FILE=.env.dev DB_NAME=sc_demo make verify.dev.acceptance.release
```

### 5.3 生产备份回放

下一次正式发布必须优先从生产备份回放开始，而不是从 dev 数据库判断。

流程：

1. 从生产获取数据库和 filestore 备份。
2. 在隔离 prod-sim 环境恢复备份。
3. 应用候选代码或候选发布包。
4. 执行模块升级。
5. 执行完整验证矩阵。

prod-sim 通过后，才允许进入生产发布窗口。

### 5.4 发布包构建

发布包至少包含：

```text
package/
  files/
  changed_files.txt
  SHA256SUMS
  OPERATOR_COMMANDS.sh
  VALIDATION_MATRIX.md
  PROD_STATUS_CURRENT.txt
  PRODUCTION_HANDOFF_RUNBOOK.md
```

发布包校验要求：

```bash
tar -xzf <release>.tar.gz -C <verify_dir>
(cd <verify_dir>/package && sha256sum -c SHA256SUMS)
sha256sum <release>.tar.gz > <release>.tar.gz.sha256
```

### 5.5 生产执行

生产执行顺序固定：

1. 确认生产状态和当前备份点。
2. 上传发布包和 sha256。
3. 校验远端 sha256。
4. 备份即将覆盖的生产文件。
5. 同步发布包文件。
6. 执行模块升级。
7. 应用业务策略和角色策略。
8. 重启或刷新服务。
9. 等待健康检查。
10. 执行发布后验证矩阵。

常用命令形态：

```bash
ENV=prod ENV_FILE=.env.prod DB_NAME=sc_prod PROD_DANGER=1 \
  make mod.upgrade MODULE=<modules>

ENV=prod ENV_FILE=.env.prod DB_NAME=sc_prod PROD_DANGER=1 \
  make policy.apply.business_full

ENV=prod ENV_FILE=.env.prod DB_NAME=sc_prod PROD_DANGER=1 \
  make policy.apply.role_matrix
```

### 5.6 发布后验证矩阵

生产发布后最低验证矩阵：

```bash
ENV=prod ENV_FILE=.env.prod DB_NAME=sc_prod PROD_DANGER=1 make verify.baseline
SC_LOGIN_ENV_EXPECTED=prod ENV=prod ENV_FILE=.env.prod DB_NAME=sc_prod PROD_DANGER=1 make verify.p0
BASE_URL=http://127.0.0.1:8072 ENV=prod ENV_FILE=.env.prod DB_NAME=sc_prod PROD_DANGER=1 make smoke.business_full
BASE_URL=http://127.0.0.1:8072 ENV=prod ENV_FILE=.env.prod DB_NAME=sc_prod PROD_DANGER=1 make smoke.role_matrix
ENV=prod ENV_FILE=.env.prod DB_NAME=sc_prod make verify.non_demo_data_contamination
ENV=prod ENV_FILE=.env.prod DB_NAME=sc_prod PROD_READONLY_VERIFY=1 make verify.business_system.usability_readiness.prod
ENV=prod ENV_FILE=.env.prod DB_NAME=sc_prod PROD_READONLY_VERIFY=1 make history.attachment.custody.probe.prod
```

如果本次发布范围包含历史附件镜像或补齐任务，还必须执行对应的生产只读附件验收：

```bash
ENV=prod ENV_FILE=.env.prod DB_NAME=sc_prod PROD_READONLY_VERIFY=1 make verify.legacy_attachment.mirror.completeness.audit.prod
ENV=prod ENV_FILE=.env.prod DB_NAME=sc_prod PROD_READONLY_VERIFY=1 make verify.legacy_online_attachment.mirror.job.audit.prod
```

如果附件 custody 探针报告 `legacy_url_attachment_boundary_marker_gap`，必须先保存受影响
`ir_attachment` 行快照，再通过受控写入入口补齐 marker，并复跑只读探针：

```bash
ENV=prod ENV_FILE=.env.prod DB_NAME=sc_prod PROD_DANGER=1 make legacy_attachment.custody_marker.backfill.prod
ENV=prod ENV_FILE=.env.prod DB_NAME=sc_prod PROD_READONLY_VERIFY=1 make history.attachment.custody.probe.prod
```

必须额外确认：

```bash
docker inspect <prod-odoo-container> --format '{{.State.Status}} {{if .State.Health}}{{.State.Health.Status}}{{end}}'
```

以及：

```sql
select count(*) from ir_model_data where module='smart_construction_demo';
select name, state, latest_version
from ir_module_module
where name in (...);
```

## 6. 发布后差异登记

发布完成后必须登记四类差异：

| 差异类型 | 记录内容 | 处理方式 |
| --- | --- | --- |
| 发布包差异 | 发布包文件与生产文件是否一致 | 必须为 0 |
| 模块版本差异 | dev/test/prod 的模块版本差异 | 允许存在，但必须记录 |
| 全量代码差异 | Git 跟踪文件缺失/不同数量 | 增量发布允许存在，但不得误称全量对齐 |
| 数据差异 | demo 残留、业务烟测、角色矩阵 | 必须通过验证矩阵 |

发布报告中的结论必须使用明确措辞：

- 可以说：本次发布包范围已与生产对齐。
- 可以说：生产已通过发布后验证，具备生产运行条件。
- 不得说：生产与日常开发服务器完全一致，除非全量代码树和模块版本均已验证一致。

生产部署记录必须从模板复制生成：

```bash
cp docs/ops/releases/templates/production_deployment_record_TEMPLATE.zh.md \
  docs/ops/releases/current/production_deployment_<YYYYMMDD>_<id>.md
```

部署记录完成后必须通过机器检查：

```bash
make verify.production_deployment.record.guard
```

## 7. 后续迭代节奏

后续迭代按以下节奏推进：

1. 以当前生产发布包和生产模块版本作为 `prod baseline`。
2. dev 继续开发，但所有新变更必须归入下一候选发布范围。
3. 下一次发布先在 prod-sim 使用生产备份回放，从 `prod baseline` 升级到目标版本。
4. prod-sim 通过后生成新发布包。
5. 生产只应用该新发布包，不直接同步 dev 整目录。
6. 发布完成后更新生产状态摘要和差异登记。

## 8. 收口判定

一次生产发布只有同时满足以下条件，才算收口：

- 生产备份路径已记录。
- 发布包 sha256 已记录，远端校验通过。
- 模块升级成功退出。
- 策略刷新成功。
- 主服务健康检查为 `running healthy`。
- 发布后验证矩阵全部通过。
- demo 模块和 demo XMLID 状态符合生产要求。
- 最终发布包已包含所有生产修复文件。
- 发布结论区分了“发布包对齐”和“全量对齐”。
- `make verify.production_deployment.record.guard` 通过。
