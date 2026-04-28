````md
# Codex Execution Allowlist (Autonomous Mode)

**Codex 自治执行授权清单 · v4.3（Replace v4.2）**

---

## 0. 定位（What Codex Is）

Codex 在本仓库中的角色被明确为：

> **自治执行体（Autonomous Engineering Executor）**

其职责是在 **独立分支（feature/* / feat/* / codex/* / experiment/*）** 内，
围绕既定目标进行 **连续的代码迭代、验证与交互完善**，
并在 **不需要人工逐步授权** 的前提下，完成以下闭环：

* 实现改动
* 运行验证
* 修复失败
* 重复迭代
* 输出可审计结果

Codex **不是管理员**，也 **不是决策者**；
Codex 是一个 **被严格约束的工程执行单元**。

### 0.1 适用范围边界

本文仅适用于 **Codex 自治开发 / 自治验证 / PR 协作** 场景。

本文不适用于人工监督下的服务器生产部署。生产服务器从 `main`、tag
或冻结 commit 执行正式部署时，适用：

- `docs/ops/codex_production_assist_policy.md`
- `docs/ops/prod_command_policy.md`
- `docs/ops/production_deployment_runbook_v1.md`

生产协助模式下，Codex 只能做只读检查、执行生产策略允许的 Makefile target
和整理部署证据；不得修改仓库文件、提交代码或绕过 Makefile 操作生产数据。

---

## 1. 执行边界总原则（Hard Rules）

### 1.1 分支约束（最重要）

Codex **只能** 在以下分支类型中执行自治操作：

* `feat/*`
* `feature/*`
* `codex/*`
* `experiment/*`

❌ 严禁：

* `main`
* `master`
* `release/*`
* 任何已打 tag 的分支

若当前分支不符合要求，Codex **必须立即停止并报告**。

例外：若当前任务是人工监督的生产部署协助，并且没有任何仓库写入或 Git
写操作，则不按本文的自治分支限制处理，改按
`docs/ops/codex_production_assist_policy.md` 执行。

**分支判定规则：**

```bash
git branch --show-current
````

允许的分支正则：

```
^(feat|feature|codex|experiment)\/.+
```

---

### 1.2 环境约束

* 仅允许 `ENV=dev` / `ENV=test`
* ❌ 禁止 `ENV=prod`
* ❌ 禁止使用 `.env.prod`
* ❌ 禁止设置或使用 `PROD_DANGER=1`

> `.env.prod` 文件允许存在（作为模板/参考），但禁止在 Codex 自治执行中启用 `ENV=prod` 或设置 `PROD_DANGER=1`。

说明：上述限制只约束 Codex 自治执行。生产协助模式允许 `ENV=prod`、
`ENV_FILE=.env.prod` 和经人工确认的 `PROD_DANGER=1`，但只能执行
`docs/ops/prod_command_policy.md` 允许的 Makefile target。

---

### 1.3 执行方式约束（Makefile 优先）

* **默认原则**：
  所有 **运行态 / 容器 / 数据库 / 服务状态变更 / 远端状态变更**
  **必须通过 Makefile target 执行**

* **明确例外**：
  §1.4 中列出的 **Safe Git 命令**
  👉 允许直接执行（不要求 Makefile 封装）

❌ 禁止直接调用（除非有对应 Makefile target）：

* `docker compose exec ... odoo -u`
* `psql`
* `gh pr edit / comment / ready / close`
* `curl` / `python` 直接写 GitHub API
* 任何绕过 Makefile 的远端状态修改

---

### 1.3.1 PR 内容更新通道（PR Update Channel）

Codex 被授权在 **合规分支内** 更新 PR 内容（包括代码与文本），但必须满足：

* ✅ **只能通过 Makefile target 执行**
* ❌ 禁止直接使用 `git push` / `gh` / GitHub API

允许的 PR 相关 Makefile targets：

* `make pr.open`

  * 创建 PR（或输出创建指引 / URL）

* `make pr.update`

  * 更新 PR 标题 / 描述 / labels / assignees / reviewers
  * 不允许修改 base 分支

* `make pr.status`

  * 查询 PR 状态（只读，允许任何分支）

* `make pr.push`

  * 将当前分支 push 到远端，用于 **更新 PR 的代码内容**
  * 必须校验：

    * 分支合法
    * 非 prod 环境
    * 非 main / release

> 说明：
> **PR 内容更新属于远端状态变更**，必须统一走 Makefile 封装流程，
> 以保证分支校验、环境校验与审计能力。

---

## 1.4 Git 执行边界（Safe Git Rules）

> ⚠️ 所有 Git 操作仍受 §1.1 分支约束
> **分支不合规时，任何 Git 写操作都必须停止**

---

### 1.4.1 允许的 Git 命令（Safe Git）

#### A) 只读类（允许在任何分支执行）

用于识别仓库状态、生成证据、定位问题：

* `git status`
* `git status -sb`
* `git diff`
* `git diff --stat`
* `git diff --name-only`
* `git diff --cached`
* `git diff --cached --name-only`
* `git log --oneline -n <N>`
* `git log --oneline --decorate -n <N>`
* `git show <commit>`
* `git show --name-only <commit>`
* `git branch --show-current`
* `git rev-parse HEAD`
* `git rev-parse --short HEAD`
* `git remote -v`
* `git ls-files`
* `git grep <pattern> [-- <path>]`
* `git fetch --prune origin`

> 说明：
> 上述命令 **不修改工作区、不影响远端**，
> 是 Codex 做工程自治与证据输出的必要能力。

---

#### B) 本地写入（仅限合规分支）

仅影响本地工作区，不影响远端：

* `git add <path>`
* `git add -A`
* `git restore <path>`
* `git restore --staged <path>`
* `git rm <path>`
* `git commit -m "<message>"`
* `git commit --amend -m "<message>"`
* `git commit --amend --no-edit`

> ⚠️ 说明：
> `--no-edit` 被明确允许，用于**修正提交内容而不改语义说明**，
> 是自治执行中的常见且安全操作。

---

#### C) 分支内同步（仅限合规分支）

* `git switch <allowed-branch>`
* `git checkout <allowed-branch>`
* `git switch -c <new-allowed-branch>`
* `git checkout -b <new-allowed-branch>`
* `git pull --ff-only origin <same-branch>`

---

### 1.4.2 明确禁止的 Git 命令（Hard Ban）

以下命令 **任何情况下都禁止**：

* ❌ `git push`
  （**除非** 通过 `make pr.push` / `make branch.cleanup.feature` 执行）
* ❌ `git push --force / -f`
* ❌ `git reset --hard`
* ❌ `git rebase`
* ❌ `git cherry-pick`
* ❌ `git merge`
* ❌ `git tag`
* ❌ `git branch -d / -D`
  （**除非** 通过 `make branch.cleanup.feature` 执行）
* ❌ `git worktree`
* ❌ `git config`
* ❌ `git clean -fdx`

> ⚠️ 所有 **远端状态变更**
> 必须通过 Makefile 封装流程完成。

> 解释：
> PR 的代码更新 **必须通过 `make pr.push`**，
> 以便统一注入分支校验、远端保护与审计日志。

---

### 1.5 Git 与分支绑定规则（Critical）

* Codex 执行任何 **Git 写操作** 前，必须确认：

  * 当前分支 ∈ {feat/*, feature/*, codex/*, experiment/*}

* 若检测到以下情况之一：

  * `main`
  * `master`
  * `release/*`
  * HEAD detached

  Codex **必须立即停止**，不得执行任何 Git 写操作。

* 对 `main` 的同步：

  * 仅允许通过：

    ```bash
    make main.sync
    ```

---

## 2. Codex 的自治生命周期

在独立分支内，Codex 被授权执行完整自治循环：

```
理解目标
↓
修改代码
↓
选择执行模式（fast / gate）
↓
执行验证
↓
失败 → 定位 → 修复
↓
再次验证
↓
直到通过或触发停机条件
```

---

## 3. 执行模式（Execution Modes）

### 3.1 MODE=fast（默认 · 连续迭代模式）

#### 适用范围

* UI / Portal 交互调优
* Python 逻辑修正
* Resolver / 状态机演进
* Contract 输出结构优化
* 文档 / 脚本 / 工具链改进

#### 允许的 Make Targets

（保持你现有清单，完全不改）

---

### 3.2 MODE=gate（自治验收模式）

Codex **被授权自行进入 gate 模式**。

（保持你现有清单，完全不改）

---

## 4. 模块升级授权（升级不是默认）

（保持你现有规则，完全不改）

---

## 5. 失败即许可（Failure Is Allowed）

Gate / Smoke / Snapshot 失败 **允许发生**。
Codex 的责任是 **定位 → 修复 → 重试**。

---

## 5.1 System-bound Verification（强制）

**任何由 Codex 产生的代码改动，必须同时提供 system-bound verification。**

不接受：

* 真实用户登录
* 浏览器点击验证
* 人工 token

---

## 6. 唯一需要人工中断的情况

仅限以下情形：

1. 需要改动 `main` / `release`
2. 需要新增或修改 prod 策略
3. 不可逆 DB 操作
4. 连续 ≥3 次 gate.full 失败且原因不收敛
5. 引入全新模块或外部依赖

---

## 6.0 Codex Branch Bootstrap Rule

* `codex/*` 分支首次推送必须人工完成
* 远端分支存在后，Codex 接管自治流程

---

## 6.1 Branch-local autonomy（All allowed branches）

在合规分支（`feat/*` `feature/*` `codex/*` `experiment/*`）内，
仅允许通过 Makefile 执行以下自治闭环能力：

* `make codex.preflight`
* `make codex.run FLOW=fast|snapshot|gate|pr|merge|cleanup|rollback`
* `make codex.pr`
* `make pr.open`
* `make pr.update`
* `make pr.status`
* `make pr.push`
* `make codex.sync-main`
* `make branch.cleanup.feature`

> 若某 target 尚未实现，**必须先补 Makefile 封装**，
> Codex 不得绕过直接调用底层命令。

---

## 7. 产出与证据（必须）

一次自治周期内，Codex **必须产出**：

* 日志摘要
* Gate / Smoke 结果
* Contract snapshot diff（如有）
* System-bound verification 结果
* 最终状态说明（通过 / 阻塞）

推荐目录结构：

```
artifacts/codex/<branch>/<timestamp>/
```
文档形成规则
目录结构一致：同名文件 .md + .en.md 成对出现（或 README.zh.md/README.en.md 成对出现，但全仓统一一种）

链接一致：中文文档里链接到英文同位置的英文文档；英文文档同理

术语表一致：建立 docs/TERMS.zh.md 与 docs/TERMS.en.md（可放 Phase A 或 C），约束 intent/scene/reason_code 的翻译固定用词（避免“contract”一会叫契约一会叫合约）
---

## 8. 一句话执行准则（给 Codex 用）

> **只在独立分支；
> 默认 fast；
> 升级需声明；
> PR 更新走 Makefile；
> 验证必须自证；
> gate 可自治；
> 失败可重试；
> 越权即停。**

---

```
```
