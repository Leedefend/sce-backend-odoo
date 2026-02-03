
# Codex Execution Allowlist (Autonomous Mode)

（Codex 自治执行授权清单 · v4.1）

---

## 0. 定位（What Codex Is）

Codex 在本仓库中的角色被明确为：

> **自治执行体（Autonomous Engineering Executor）**

其职责是在 **独立分支（feature/* / feat/* / codex/*）** 内，
围绕既定目标进行 **连续的代码迭代、验证与交互完善**，
并在 **不需要人工逐步授权** 的前提下，完成以下闭环：

* 实现改动
* 运行验证
* 修复失败
* 重复迭代
* 输出可审计结果

Codex **不是管理员**，也 **不是决策者**；
Codex 是一个 **被严格约束的工程执行单元**。

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

---

### 1.2 环境约束

* 仅允许 `ENV=dev` / `ENV=test`
* ❌ 禁止 `ENV=prod`
* ❌ 禁止使用 `.env.prod`
* ❌ 禁止设置或使用 `PROD_DANGER=1`

---

### 1.3 执行方式约束

* 所有操作 **必须通过 Makefile target**
* ❌ 禁止直接调用：

  * `docker compose exec ... odoo -u`
  * `psql`
  * `curl` 直接修改系统状态（只允许只读 smoke）

---

### 1.4 Git 执行边界（Safe Git Rules）

为支持 Codex 的日常工程自治，允许执行 **受限 Git 操作子集**。

#### 1.4.1 允许的 Git 命令（Safe Git）

仅允许以下 Git 操作，且 **只能在允许的分支类型中执行**：

**只读类**

* `git status`
* `git diff`
* `git diff --stat`
* `git log --oneline -n <N>`
* `git show <commit>`
* `git branch --show-current`

**本地写入（不影响远端）**

* `git add <path>`
* `git restore <path>`
* `git commit -m "<message>"`
* `git commit --amend`（仅允许修改 message，不允许 `--no-edit`）

**分支内同步**

* `git switch <allowed-branch>`
* `git checkout <allowed-branch>`
* `git pull --ff-only origin <same-branch>`

---

#### 1.4.2 明确禁止的 Git 命令（Hard Ban）

* ❌ `git push`（任何形式）
* ❌ `git push --force / -f`
* ❌ `git reset --hard`
* ❌ `git rebase`
* ❌ `git cherry-pick`
* ❌ `git merge`
* ❌ `git tag`
* ❌ `git branch -d / -D`
* ❌ `git worktree`
* ❌ `git config`

> ⚠️ 所有 **远端状态变更** 必须通过 Makefile 封装流程完成。

---

### 1.5 Git 与分支绑定规则（Critical）

* Codex 执行任何 Git 写操作前，**必须确认**：

  * 当前分支 ∈ {feat/*, feature/*, codex/*, experiment/*}

* 若检测到当前分支为：

  * `main`
  * `master`
  * `release/*`

  Codex **必须立即停止**，不得执行任何 Git 写操作（包括 `git add` / `git commit`）。

* 对 `main` 的同步行为：

  * 仅允许：

    * `git pull --ff-only origin main`
  * 且只能通过：

    * `make main.sync`

---

## 2. Codex 的“自治生命周期”

在 **独立分支** 内，Codex 被授权执行完整自治循环：

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
直到通过
```

> 在该循环中，**不需要人工逐步授权**。

---

## 3. 执行模式（Execution Modes）

### 3.1 MODE=fast（默认 · 连续迭代模式）

#### 适用范围

* UI / Portal 交互调优
* Python 逻辑修正
* Contract 输出结构演进
* 文档、脚本、工具链改进

#### 允许的 Make Targets

**运行态**

* `make restart`
* `make odoo.recreate`
* `make logs`
* `make ps`
* `make odoo-shell`（只读）
* `make codex.preflight`

**合同 / 接口**

* `make contract.export`
* `make contract.export_all`
* `make codex.run FLOW=snapshot`

**模块操作**

* `make mod.upgrade`

  * 前提：

    * `CODEX_NEED_UPGRADE=1`
    * 明确 `CODEX_MODULES=...`

**轻量验证**

* `make smoke.*`
* `make verify.portal.fe_smoke`
* `make verify.portal.view_state`
* `make verify.portal.v0_5`
* `make verify.portal.v0_5.all`
* `scripts/verify/*_smoke.sh`

#### 明确禁止

* ❌ `demo.reset`
* ❌ `db.reset`
* ❌ `dev.rebuild`
* ❌ `gate.full`
* ❌ `gate.demo`
* ❌ `gate.baseline`

---

### 3.2 MODE=gate（自治验收模式）

Codex **被授权自行进入 gate 模式**。

#### 允许的 Make Targets

* MODE=fast 的全部
* `make demo.reset`
* `make contract.export_all`
* `make gate.full`
* `make codex.run FLOW=gate`

---

## 4. 模块升级授权（升级不是默认）

Codex **只能在以下情况下**设置：

```bash
CODEX_NEED_UPGRADE=1
```

### 允许升级的改动类型

* `addons/**/views/**`
* `addons/**/security/**`
* `addons/**/data/**`
* `addons/**/ir.model.access.csv`
* 新增 / 修改模型字段（schema 变化）

### 禁止升级的原因

* JS / SCSS / 前端表现问题
* Python 纯逻辑修正
* 文档或脚本调整

---

## 5. 失败即许可（Failure Is Allowed）

以下情况 **允许发生**：

* Gate / Smoke 失败
* Contract diff 不一致
* 校验脚本返回非 0

Codex 的责任是：

* 读取失败信息
* 修复代码
* 重新执行
* 直到通过或触发停机条件

---

## 5.1 System-bound Verification（强制）

**任何由 Codex 产生的代码改动，必须同时提供 system-bound verification。**

### 定义

system-bound verification 指：

* ❌ 不依赖真实用户登录
* ❌ 不使用浏览器 session / cookie
* ❌ 不使用人工提供的真实 auth token
* ✅ 可在无用户态环境中重复执行
* ✅ 可由第三方仅凭仓库代码复现

### Codex 的验证责任（Hard Requirement）

Codex **不得** 以以下理由视为完成验证：

* “需要真实 token 才能测”
* “需要人工登录点一下”
* “浏览器里看起来是对的”

上述行为 **仅属于 user-bound verification**，不构成 Codex 交付。

### 可接受的验证形式

* Resolver / 状态机验证
* 只读 API 验证（system / service 用户）
* Contract / Snapshot diff 验证

### 不合格判定（Hard Fail）

满足任一条件即为 **未完成**：

* 未提供 system-bound verification
* 验证无法独立执行
* 验证依赖真实 token / 登录态
* 验证结果不可复现

---

## 6. 唯一需要人工中断的情况

仅限以下情况：

1. 需要改动 `main` / `release`
2. 需要新增或修改 prod 策略
3. 不可逆 DB 操作
4. 连续 ≥3 次 gate.full 失败且原因不收敛
5. 引入全新模块或外部依赖

---

### 6.0 Codex Branch Bootstrap Rule

* `codex/*` 分支首次推送：

  * **必须由人工完成**
* 远端分支存在后：

  * Codex 接管 PR / 验证 / merge / cleanup

---

## 6.1 Branch-local autonomy（codex/* only）

仅允许通过 Makefile：

* `make codex.preflight`
* `make codex.run FLOW=fast|snapshot|gate|pr|merge|cleanup|rollback`
* `make codex.pr`
* `make codex.merge`
* `make codex.cleanup`
* `make codex.sync-main`

---

## 7. 产出与证据（必须）

一次自治执行周期内，Codex **必须产出**：

* 日志摘要
* Gate / Smoke 结果
* Contract snapshot diff（如有）
* **System-bound verification 脚本与执行结果**
* 最终状态说明（通过 / 阻塞）

推荐目录：

```
artifacts/codex/<branch>/<timestamp>/
```

---

## 8. 一句话执行准则（给 Codex 用）

> **只在独立分支；
> 默认 fast；
> 升级需声明；
> 验证必须自证；
> gate 可自治；
> 失败可重试；
> 越权即停。**

---

