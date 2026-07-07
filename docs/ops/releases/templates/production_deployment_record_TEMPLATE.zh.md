# Production Deployment Record — <DEPLOYMENT_ID>

## 1. 基本信息

| 项目 | 值 |
| --- | --- |
| 部署编号 | `<DEPLOYMENT_ID>` |
| 部署窗口 | `<YYYY-MM-DD HH:mm-HH:mm TZ>` |
| 操作人 | `<name>` |
| 审批人 | `<name>` |
| 生产主机 | `<host>` |
| 生产目录 | `<path>` |
| 生产数据库 | `sc_prod` |
| 发布类型 | `incremental package` / `full tree` / `hotfix` |
| 发布包 | `<path>` |
| 发布包 sha256 | `<sha256>` |
| 目标 commit/tag | `<commit-or-tag>` |

## 2. 发布范围声明

本次发布范围：

- [ ] 发布包增量对齐
- [ ] 模块版本对齐
- [ ] 全量代码树对齐
- [ ] 数据承载规则对齐

禁止使用含糊结论。若只做增量发布，只能写“发布包范围已对齐”，不得写“生产与开发完全一致”。

变更文件清单：

```text
<paste changed_files.txt or link>
```

模块清单：

```text
<module list>
```

Migration 清单：

```text
<migration list>
```

## 3. 发布前状态

生产服务状态：

```text
<docker compose ps / health output>
```

生产模块版本：

```sql
select name, state, latest_version
from ir_module_module
where name in (...);
```

日常开发与生产差异登记：

| 差异类型 | 结果 | 说明 |
| --- | --- | --- |
| 发布包文件差异 | `<count>` | `<notes>` |
| 模块版本差异 | `<summary>` | `<notes>` |
| 全量代码树差异 | `<missing/diff count>` | `<notes>` |
| 数据差异 | `<summary>` | `<notes>` |

## 4. 备份

生产写入前必须记录备份。

| 类型 | 路径 | 校验 | 结果 |
| --- | --- | --- | --- |
| 数据库 | `<path>` | `<sha/check command>` | `PASS/FAIL` |
| filestore | `<path>` | `<sha/check command>` | `PASS/FAIL` |
| 覆盖文件 | `<path>` | `<sha/check command>` | `PASS/FAIL` |

备份验证命令：

```bash
<commands>
```

## 5. Prod-Sim 验证

prod-sim 必须从生产备份回放或明确声明豁免原因。

| 检查项 | 结果 | 证据 |
| --- | --- | --- |
| 生产备份恢复 | `PASS/FAIL/SKIP` | `<artifact>` |
| 候选发布包应用 | `PASS/FAIL` | `<artifact>` |
| 模块升级 | `PASS/FAIL` | `<artifact>` |
| 业务烟测 | `PASS/FAIL` | `<artifact>` |
| 角色矩阵 | `PASS/FAIL` | `<artifact>` |
| 非 demo 污染 | `PASS/FAIL` | `<artifact>` |

prod-sim 运行 ID：

```text
<run id>
```

## 6. 生产执行命令

发布包校验：

```bash
sha256sum -c <release>.tar.gz.sha256
```

文件同步和备份：

```bash
<commands>
```

模块升级：

```bash
ENV=prod ENV_FILE=.env.prod DB_NAME=sc_prod PROD_DANGER=1 \
  make mod.upgrade MODULE=<modules>
```

策略刷新：

```bash
ENV=prod ENV_FILE=.env.prod DB_NAME=sc_prod PROD_DANGER=1 \
  make policy.apply.business_full

ENV=prod ENV_FILE=.env.prod DB_NAME=sc_prod PROD_DANGER=1 \
  make policy.apply.role_matrix
```

服务健康：

```bash
docker inspect <prod-odoo-container> \
  --format '{{.State.Status}} {{if .State.Health}}{{.State.Health.Status}}{{end}}'
```

## 7. 发布后验证

最低验证矩阵：

```bash
ENV=prod ENV_FILE=.env.prod DB_NAME=sc_prod PROD_DANGER=1 make verify.baseline
SC_LOGIN_ENV_EXPECTED=prod ENV=prod ENV_FILE=.env.prod DB_NAME=sc_prod PROD_DANGER=1 make verify.p0
BASE_URL=http://127.0.0.1:8072 ENV=prod ENV_FILE=.env.prod DB_NAME=sc_prod PROD_DANGER=1 make smoke.business_full
BASE_URL=http://127.0.0.1:8072 ENV=prod ENV_FILE=.env.prod DB_NAME=sc_prod PROD_DANGER=1 make smoke.role_matrix
ENV=prod ENV_FILE=.env.prod DB_NAME=sc_prod make verify.non_demo_data_contamination
ENV=prod ENV_FILE=.env.prod DB_NAME=sc_prod PROD_READONLY_VERIFY=1 make history.attachment.custody.probe.prod
```

验证结果：

| 检查项 | 结果 | 摘要 |
| --- | --- | --- |
| `verify.baseline` | `PASS/FAIL` | `<summary>` |
| `verify.p0` | `PASS/FAIL` | `<summary>` |
| `smoke.business_full` | `PASS/FAIL` | `<summary>` |
| `smoke.role_matrix` | `PASS/FAIL` | `<summary>` |
| `verify.non_demo_data_contamination` | `PASS/FAIL` | `<summary>` |
| `history.attachment.custody.probe.prod` | `PASS/FAIL` | `<history_attachment_custody_ready / gap summary>` |
| 服务健康 | `PASS/FAIL` | `<summary>` |

Demo 状态：

```sql
select count(*) from ir_model_data where module='smart_construction_demo';
select name, state, latest_version
from ir_module_module
where name='smart_construction_demo';
```

Production Git authority evidence for `full tree` releases:

```bash
PRODUCTION_GIT_AUTHORITY_REQUIRE_ENV_SKIP=1 \
  make verify.production_git.authority.guard
```

```json
{
  "guard": "production_git_authority_guard",
  "status": "PASS",
  "branch": "main",
  "head": "<production-head-sha>",
  "remote_head": "<origin-main-sha>",
  "status_porcelain": "",
  "remote_auth_ok": true,
  "env_file_skip_worktree": true
}
```

## 8. 回滚点

| 回滚对象 | 路径/版本 | 操作说明 |
| --- | --- | --- |
| 数据库 | `<backup path>` | `<restore command or runbook>` |
| filestore | `<backup path>` | `<restore command or runbook>` |
| 代码文件 | `<backup path>` | `<restore command or runbook>` |
| 发布包 | `<previous package>` | `<restore command or runbook>` |

## 9. 收口结论

只能选择已被证据支持的结论：

- [ ] 本次发布包范围已与生产对齐。
- [ ] 生产模块版本已达到目标版本。
- [ ] 生产服务健康检查通过。
- [ ] 生产验证矩阵全部通过。
- [ ] demo 模块和 demo XMLID 状态符合生产要求。
- [ ] 生产与日常开发服务器全量一致。

若最后一项未勾选，必须说明：

```text
生产与日常开发服务器不是全量一致。本次结论仅限于发布包范围和发布后验证结果。
```

最终发布结论：

```text
<deployment conclusion>
```

## 10. 后续事项

| 事项 | 负责人 | 截止时间 | 状态 |
| --- | --- | --- | --- |
| `<item>` | `<owner>` | `<date or cadence>` | `planned: <meaning>` / `retained: <meaning>` / `tracked: <meaning>` / `closed: <evidence>` |
