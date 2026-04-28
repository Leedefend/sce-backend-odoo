# Codex 生产部署协助策略 v1

## 1. 目标

本策略用于区分两类完全不同的行为：

- Codex 自治开发：改代码、改文档、跑开发/测试验证，必须遵守 `docs/ops/codex_execution_allowlist.md`。
- Codex 生产协助：在人工监督下辅助服务器生产部署，只能按本文和 `docs/ops/prod_command_policy.md` 执行。

生产部署不是 Codex 自治开发。生产服务器从 `main`、tag 或冻结 commit 部署是允许的，但 Codex 在该场景下不得修改仓库内容。

## 2. 适用场景

本文适用于：

- 服务器上从 `main`、tag 或 release commit 执行正式部署。
- 使用 `ENV=prod` / `ENV_FILE=.env.prod` 的生产操作。
- 需要 `PROD_DANGER=1` 的受控生产命令。
- 生产数据重建、断点续跑、验收和证据归档。

本文不适用于：

- 功能开发。
- 代码修复。
- 文档编辑。
- 本地开发验证。
- PR 创建、提交、push、merge。

上述行为仍必须在 `feat/*`、`feature/*`、`codex/*`、`experiment/*` 分支中执行。

## 3. 分支规则

生产协助模式允许当前仓库处于：

- `main`
- 已审定 tag
- 已审定 release commit
- 人工明确指定的只读部署 commit

但该允许仅限生产部署只读检查和受控 Makefile target 执行，不代表允许 Codex 在这些分支上写文件、提交或变更 Git 状态。

## 4. Codex 可执行动作

Codex 在生产协助模式下可以执行：

- 只读 Git 检查：
  - `git status --short`
  - `git rev-parse --short HEAD`
  - `git branch --show-current`
  - `git log --oneline -n <N>`
  - `git show --name-only <commit>`
- 只读部署预检：
  - `ENV=prod ENV_FILE=.env.prod make check-compose-project`
  - `ENV=prod ENV_FILE=.env.prod make check-compose-env`
  - `ENV=prod ENV_FILE=.env.prod make diag.project`
  - `ENV=prod ENV_FILE=.env.prod make ps`
  - `ENV=prod ENV_FILE=.env.prod make logs`
- `docs/ops/prod_command_policy.md` 明确允许的 Makefile target。
- 执行后整理命令、时间、结果、artifact 路径和风险结论。

## 5. 需要人工确认的动作

以下动作必须由人工明确确认后，Codex 才能协助执行：

- 任何带 `PROD_DANGER=1` 的命令。
- 模块安装或升级：
  - `make mod.install`
  - `make mod.upgrade`
  - `make prod.upgrade.core`
- 生产服务重启：
  - `make restart`
  - `make prod.restart.safe`
  - `make prod.restart.full`
- 权限策略应用：
  - `make policy.apply.business_full`
  - `make policy.apply.role_matrix`
- 生产数据重建：
  - `make history.production.fresh_init`
  - 使用 `HISTORY_CONTINUITY_START_AT` 的生产断点续跑。

人工确认必须包含：

- 目标环境：`ENV=prod`
- 目标数据库：如 `DB_NAME=sc_prod`
- 当前 commit 或 tag
- 是否已备份数据库和 filestore
- 是否允许本次命令写入生产数据库

## 6. 禁止动作

生产协助模式下 Codex 禁止：

- 修改任何仓库文件。
- 执行 `git add`、`git commit`、`git push`、`git merge`、`git rebase`、`git reset`、`git checkout` 写操作。
- 创建临时服务器脚本修数据。
- 直接执行 `psql` 修改生产数据。
- 直接执行 `docker compose exec ... odoo shell` 写生产数据。
- 绕过 Makefile 调用 Odoo 升级、seed、replay 或 policy 脚本。
- 执行 `make db.reset`、`make demo.*`、`make gate.*`、`make ci.*`。
- 在生产库上使用 demo seed 修复数据。

## 7. 生产数据重建规则

生产数据重建必须遵守 `docs/ops/production_deployment_runbook_v1.md`。

核心原则：

- 生产库禁止 `db.reset` 和 `demo.reset`。
- 新库历史重建使用 `history.production.fresh_init`。
- 断点续跑使用同一个 `RUN_ID` 和 `HISTORY_CONTINUITY_START_AT`。
- 生产断点续跑仍通过 `history.production.fresh_init` 进入；`history.continuity.replay`
  仅用于非生产演练环境。
- 局部补链必须先在 prod-sim 或 UAT 重放。
- 所有 replay artifact、日志和 smoke 结果必须归档。

## 8. 冲突处理

当规则冲突时按以下顺序判断：

1. 是否是生产服务器、`ENV=prod` 或 `.env.prod`。
2. 是否是人工监督的正式部署或数据重建。
3. 是否只执行 `prod_command_policy.md` 允许的 Makefile target。
4. 是否没有仓库写入和 Git 写操作。

若以上条件都满足，适用本文，不适用 Codex 自治开发分支限制。

若任一条件不满足，回到 `docs/ops/codex_execution_allowlist.md` 和 `docs/ops/codex_workspace_execution_rules.md`。

## 9. 最小生产协助记录

每次生产协助必须记录：

- 当前分支/tag/commit。
- 执行人和确认人。
- 命令原文。
- 开始和结束时间。
- 结果：PASS / FAIL。
- artifact 和日志路径。
- 回滚点。
- 后续动作。
