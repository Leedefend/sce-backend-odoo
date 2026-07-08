# 生产环境升级标准 v1

## 1. 目标

生产升级必须从“人工临时同步文件”升级为可重复、可审计、可回滚的工程流程。每次升级都必须能回答：

- 升级来源是什么：commit、tag、release package，还是经过批准的热修复包。
- 生产当前基线是什么：代码包、数据库、filestore、模块版本、运行容器状态。
- 本次升级范围是什么：文件、模块、数据迁移、策略刷新、前端资源。
- 如何回滚：文件备份、数据库备份、filestore 备份、容器重启方式。
- 如何验收：静态 guard、模块升级结果、HTTP/容器健康、业务 smoke、只读生产数据探针。

本文是生产升级执行标准；命令红线以 `docs/ops/prod_command_policy.md` 为准，生产部署细节以 `docs/ops/production_deployment_runbook_v1.md` 为准。

## 2. 升级类型

| 类型 | 使用场景 | 发布载体 | 生产代码目录要求 | 必须升级模块 |
| --- | --- | --- | --- | --- |
| 全量版本升级 | 正式版本、跨模块大范围变更、生产目录需要与主线完全对齐 | Git tag 或完整 release package | 生产目录可以是 Git 工作区或完整展开包 | 变更模块及其依赖 |
| 增量功能升级 | 少量模块/前端/验证资产变更 | 增量 release package | 不要求全量代码树一致，但必须声明范围 | 涉及 addon 运行时代码时必须升级/重启 |
| 只读验证资产升级 | 只新增 docs、scripts/verify、发布记录 | 增量 release package | 只同步验证资产 | 不需要 |
| 生产热修复 | 生产阻断、经人工批准的最小修复 | hotfix package，后续必须回写 main | 只允许最小文件集 | 按实际影响判定 |
| 数据重建/补链 | 历史迁移、附件、正式业务数据补链 | 受控 Make target + artifact | 不通过临时脚本修库 | 使用对应生产入口 |
| 生产 Git 权威对齐 | 生产目录已经是 Git 工作区，需要证明生产代码以主线为权威来源 | Git commit/tag | 必须在 `main`，`HEAD` 与 `origin/main` 一致 | 按变更影响判定 |

判断规则：

- 触达 `addons/*/models`、`handlers`、`controllers`、`views`、`security`、`data`、`migrations`，默认需要模块升级或服务重启。
- 只触达 `docs`、`scripts/verify` 且不被运行时代码引用，不需要模块升级。
- 触达前端源码但生产前端由构建产物承载时，必须同步对应构建产物或明确本次仅用于验收脚本，不得声称前端产品已升级。
- 生产目录不是 Git 工作区时，不允许 `git pull`；必须使用 release package 或明确文件清单的增量包。
- 生产 Git 工作区必须具备只读拉取主线的 deploy key；如果临时只能通过 bundle fast-forward，部署记录必须写明原因，并在后续事项中补齐 deploy key。
- 生产环境配置文件不作为代码权威来源。`.env.prod` 必须保留生产服务器当前配置；若该文件仍被 Git 跟踪，生产必须显式设置 `skip-worktree`，并在部署记录中声明这是环境配置例外。

## 3. 标准升级链路

### 3.1 候选冻结

候选冻结必须在本地或日常开发服务器完成：

```bash
git status --short
git rev-parse --short HEAD
git diff --check
```

必须产出：

- 目标 commit/tag。
- 变更文件清单。
- 受影响模块清单。
- 迁移清单。
- 验证矩阵。
- 是否需要 prod-sim 回放。

低风险文档/验证资产升级可以不跑完整 prod-sim，但必须说明不触达运行时。触达业务运行态、数据库结构、菜单、表单、权限、历史数据、附件的升级，必须优先使用生产备份在 prod-sim 演练。

### 3.2 发布包构建

禁止在生产上临时决定“复制哪些文件”。发布包必须至少包含：

```text
release/
  files/
  changed_files.txt
  module_upgrade.txt
  SHA256SUMS
  PRECHECK.md
  APPLY.md
  VALIDATION.md
  ROLLBACK.md
```

`changed_files.txt` 必须是最终同步到生产的文件列表。目录级同步也必须展开为文件清单，不能只写 `addons/smart_core/`。

发布包生成后必须校验：

```bash
(cd release && sha256sum -c SHA256SUMS)
sha256sum release.tar.gz
```

### 3.3 生产预检

生产服务器执行任何写入前，必须先做只读预检：

```bash
cd /opt/sce/production/sce-backend-odoo
ENV=prod ENV_FILE=.env.prod make check-compose-project
ENV=prod ENV_FILE=.env.prod make check-compose-env
ENV=prod ENV_FILE=.env.prod make ps
curl -sS -I --max-time 8 http://127.0.0.1:8072/ | sed -n '1,12p'
```

必须记录：

- 生产主机和目录。
- 生产数据库。
- 当前 Odoo/db/redis 容器状态。
- 当前是否 Git 工作区。
- 当前模块版本。
- 当前发布包或部署记录基线。

### 3.4 备份

生产写入前必须有回滚点。

全量或运行态升级：

- 数据库 dump。
- filestore 归档。
- 当前代码目录或受影响文件归档。

只读验证资产升级：

- 受影响文件备份即可。

备份路径必须写入部署记录。备份命名使用：

```text
/data/backups/deploy/<release_id>_<YYYYMMDDTHHMMSS+0800>
```

### 3.5 应用发布包

生产目录是 Git 工作区时：

```bash
git status --short
git fetch origin
git checkout <approved_commit_or_tag>
PRODUCTION_GIT_AUTHORITY_REQUIRE_ENV_SKIP=1 \
  make verify.production_git.authority.guard
```

`make verify.production_git.authority.guard` 只读检查生产工作区是否在 `main`、`HEAD`
是否等于 `origin/main`、工作区是否干净、`.env.prod` 是否作为生产配置例外被
`skip-worktree` 保护，以及生产服务器是否具备直接从 GitHub 只读拉取主线的能力。
该检查不连接 Odoo 或 Docker Compose，不使用 `PROD_READONLY_VERIFY`；其运行边界由
`PRODUCTION_GIT_AUTHORITY_*` 环境变量控制。
如果 `git_auth` 失败，不能把生产服务器声明为长期可自治升级状态；只能声明当前
commit 已对齐，并必须补齐 deploy key。

生产目录不是 Git 工作区时：

```bash
tar -xzf <release>.tar.gz -C /tmp/<release_id>
(cd /tmp/<release_id>/release && sha256sum -c SHA256SUMS)
rsync -av --relative $(cat changed_files.txt) /opt/sce/production/sce-backend-odoo/
```

注意：

- 不同步 `.env.prod`，除非本次配置变更已单独批准。
- 不同步 runtime artifact、日志、缓存、`__pycache__`。
- 不覆盖数据库、filestore、附件镜像目录。
- 如果生产原本缺少被新增的验证资产，应在部署记录中说明这是“新增发布资产”，不是生产运行态漂移。

### 3.6 升级模块和重启

模块升级规则：

```bash
ENV=prod ENV_FILE=.env.prod DB_NAME=sc_prod PROD_DANGER=1 \
  MODULE=<module_list> make mod.upgrade
```

服务重启规则：

```bash
ENV=prod ENV_FILE=.env.prod DB_NAME=sc_prod PROD_DANGER=1 \
  make prod.restart.safe
```

判定：

- Python handler/model 变更：至少 `prod.restart.safe`。
- XML/security/data/migration 变更：必须 `mod.upgrade`，然后 `prod.restart.safe`。
- 只读验证脚本/文档：不需要重启。
- 前端构建产物变更：按前端发布方式刷新静态资源或重建相关容器。

### 3.7 发布后验证

最低验证矩阵：

```bash
ENV=prod ENV_FILE=.env.prod DB_NAME=sc_prod PROD_DANGER=1 make verify.baseline
SC_LOGIN_ENV_EXPECTED=prod ENV=prod ENV_FILE=.env.prod DB_NAME=sc_prod PROD_DANGER=1 make verify.p0
ENV=prod ENV_FILE=.env.prod make ps
curl -sS -I --max-time 8 http://127.0.0.1:8072/ | sed -n '1,12p'
docker logs --tail 180 sc-backend-odoo-prod-odoo-1
```

业务运行态升级还必须执行：

```bash
BASE_URL=http://127.0.0.1:8072 ENV=prod ENV_FILE=.env.prod DB_NAME=sc_prod PROD_DANGER=1 make smoke.business_full
BASE_URL=http://127.0.0.1:8072 ENV=prod ENV_FILE=.env.prod DB_NAME=sc_prod PROD_DANGER=1 make smoke.role_matrix
ENV=prod ENV_FILE=.env.prod DB_NAME=sc_prod make verify.non_demo_data_contamination
```

历史数据、附件、正式业务承载升级还必须执行对应只读探针：

```bash
ENV=prod ENV_FILE=.env.prod DB_NAME=sc_prod PROD_READONLY_VERIFY=1 make verify.business_system.usability_readiness.prod
ENV=prod ENV_FILE=.env.prod DB_NAME=sc_prod PROD_READONLY_VERIFY=1 make history.attachment.custody.probe.prod
```

专项能力必须加入专项 guard。例如低代码升级必须执行：

```bash
make verify.lowcode_config.boundary.guard
ENV=prod ENV_FILE=.env.prod DB_NAME=sc_prod PROD_READONLY_VERIFY=1 make verify.lowcode_config.runtime_boundary.guard
ENV=prod ENV_FILE=.env.prod DB_NAME=sc_prod PROD_READONLY_VERIFY=1 make verify.business_config.snapshot
python3 scripts/verify/business_config_guard_inventory.py
python3 scripts/verify/backend_contract_boundary_guard.py
```

## 4. 回滚标准

回滚必须按影响层级执行：

| 影响层级 | 回滚对象 | 回滚方式 |
| --- | --- | --- |
| 文件级 | 本次同步文件 | 从 `/data/backups/deploy/<release_id>` 恢复 |
| 服务级 | Python/前端代码 | 恢复文件后 `prod.restart.safe` |
| 模块级 | XML/schema/data 变更 | 优先恢复数据库备份；禁止手工逆向删改核心元数据 |
| 数据级 | 迁移/补链写入 | 恢复数据库/filestore，或使用已审定的可逆修复脚本 |
| 反代/DNS | 外部访问异常 | 回滚 Nginx/DNS 配置或切回上一服务 |

禁止：

- 为了回滚临时改生产代码。
- 直接 psql 修改生产业务数据。
- 跳过数据库备份后执行不可逆迁移。

## 5. 部署记录

每次生产升级必须生成部署记录，来源模板：

```bash
cp docs/ops/releases/templates/production_deployment_record_TEMPLATE.zh.md \
  docs/ops/releases/current/production_deployment_<YYYYMMDD>_<release_id>.md
```

记录必须包含：

- 发布编号、时间、操作人、确认人。
- 生产主机、目录、数据库。
- 目标 commit/tag/release package sha256。
- 发布类型和发布范围。
- 备份路径。
- 执行命令原文。
- 验证结果。
- 差异登记：发布包差异、模块版本差异、全量代码树差异、数据差异。
- 回滚点和后续事项。

部署记录不得保留开放占位。常见三字母占位、`待填写`、`| open |` 和
``| `open` |`` 都会被 `make verify.production_deployment.record.guard`
拒绝；尚未执行的事项必须写成 `planned`、`retained` 或 `tracked` 等可解释状态。

## 6. 收口判定

生产升级只有同时满足以下条件，才算完成：

- 发布来源明确且可复现。
- 发布文件清单和 sha256 已校验。
- 生产写入前备份已记录。
- 文件同步或 Git checkout 成功。
- 必需模块升级和服务重启成功。
- 容器健康为 healthy。
- HTTP 入口可访问。
- 最低验证矩阵通过。
- 专项 guard 通过。
- 生产日志无启动、升级、ACL、contract 阻断错误。
- 部署记录已填写，且生产修复已回写 main 或下一候选发布包。

如果只是同步了文件但没有完成验证，状态只能写 `deployed_not_verified`；如果验证失败但服务恢复，状态写 `rolled_forward_with_open_risk` 或 `rolled_back`，不能写完成。
