# Codex Execution Allowlist (Autonomous Mode)
（Codex 自治执行授权清单 · v3）

## 0. 定位（What Codex Is）

Codex 在本仓库中的角色被明确为：

> **自治执行体（Autonomous Engineering Executor）**

其职责是在**独立分支（feature/* / feat/* / codex/*）**内，
围绕既定目标进行**连续的代码迭代、验证与交互完善**，
并在不需要人工逐步授权的前提下，完成以下闭环：

- 实现改动
- 运行验证
- 修复失败
- 重复迭代
- 输出可审计结果

Codex **不是管理员**，也**不是决策者**；
Codex 是一个**被严格约束的工程执行单元**。

---

## 1. 执行边界总原则（Hard Rules）

### 1.1 分支约束（最重要）

Codex **只能** 在以下分支类型中执行自治操作：

- `feat/*`
- `feature/*`
- `codex/*`
- `experiment/*`

❌ 严禁：
- `main`
- `master`
- `release/*`
- 任何已打 tag 的分支

若当前分支不符合要求，Codex **必须停止并报告**。

---

### 1.2 环境约束

- 仅允许 `ENV=dev` / `ENV=test`
- ❌ 禁止 `ENV=prod`
- ❌ 禁止使用 `.env.prod`
- ❌ 禁止设置或使用 `PROD_DANGER=1`

---

### 1.3 执行方式约束

- 所有操作 **必须通过 Makefile target**
- ❌ 禁止直接调用：
  - `docker compose exec ... odoo -u`
  - `psql`
  - `curl` 直接修改系统状态（只允许只读 smoke）

---

## 2. Codex 的“自治生命周期”（你要的关键补齐）

在**独立分支**内，Codex 被授权执行完整的自治循环：

```
理解目标
↓
修改代码
↓
选择合适执行模式（fast / gate）
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
- UI / Portal 交互调优
- Python 逻辑修正
- Contract 输出结构演进
- 文档、脚本、工具链改进

#### 允许的 Make Targets（完整）

- 生命周期/运行态
  - `make restart`
  - `make odoo.recreate`
  - `make logs`
  - `make ps`
  - `make odoo-shell`（只读）
  - `make codex.preflight`

- 合同与接口
  - `make contract.export`
  - `make contract.export_all`（允许，用于对比）
  - `make codex.run FLOW=snapshot`（稳定快照）

- 模块操作
  - `make mod.upgrade`
    - 前提：
      - `CODEX_NEED_UPGRADE=1`
      - 明确 `CODEX_MODULES=...`

- 验证（轻量）
  - `make smoke.*`
  - 自定义 `scripts/verify/*_smoke.sh`

#### 明确禁止
- ❌ `demo.reset`
- ❌ `db.reset`
- ❌ `dev.rebuild`
- ❌ `gate.full`
- ❌ `gate.demo`
- ❌ `gate.baseline`

---

### 3.2 MODE=gate（自治验收模式）

> **在独立分支中，Codex 被授权自行进入 gate 模式。**

#### 适用范围
- 本阶段目标完成后的自验收
- Contract 稳定性验证
- Demo 场景回归

#### 允许的 Make Targets

- MODE=fast 的全部
- `make demo.reset`
- `make contract.export_all`
- `make gate.full`
 - `make codex.run FLOW=gate`

#### 推荐自治执行链

```
（可选）mod.upgrade
→ demo.reset
→ contract.export_all
→ gate.full
```

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
* 新增/修改模型字段（schema 变化）

### 禁止因以下原因升级

* JS / SCSS / 前端表现问题
* Python 纯逻辑修正
* 文档或脚本调整

---

## 5. 失败即许可（Failure Is Allowed）

在自治执行过程中：

* ❌ Gate / Smoke 失败
* ❌ Contract diff 不一致
* ❌ 校验脚本返回非 0

**都是被允许的状态**。

Codex 的责任是：

* 读取失败信息
* 修复代码
* 重新执行
* 直到通过或触发“停机条件”

---

## 6. 唯一需要中断并请求人工的情况（极少数）

Codex **必须停止并请求人工决策**，仅限以下情况：

1. **需要改动 main / release 分支**
2. **需要新增/修改 prod 策略**
3. **需要执行不可逆 DB 操作**
4. **连续 N 次（建议 N=3） gate.full 失败，且失败原因不收敛**
5. **需要引入全新模块 / 外部依赖**

---

## 6.1 Branch-local autonomy (codex/* only)

仅在 `codex/*` 分支允许以下流程动作，并且必须通过 Makefile 入口执行：

允许的 Make targets（ONLY）：
- `make codex.preflight`
- `make codex.run FLOW=fast|snapshot|gate|pr|cleanup|main`
- `make codex.pr PR_TITLE=... PR_BODY_FILE=...`
- `make codex.cleanup CLEAN_BRANCH=codex/...`
- `make codex.sync-main`
- `make pr.create PR_TITLE=... PR_BODY_FILE=...`
- `make branch.cleanup CLEAN_BRANCH=codex/...`
- `make main.sync`（仅 fast-forward）

硬性约束：
- PR 与 cleanup 必须在 `codex/*` 分支执行。
- 禁止任何直接 `gh` / `git branch` / `git push --delete`。
- 禁止任何包含 shell 重定向的命令（`>`, `2>&1`, `| tee`）；日志必须由 Makefile/scripts 内部处理。
- main 受保护：禁止 reset/force-push/重写历史。

---

## 7. 产出与证据（必须）

在一次自治执行周期内，Codex 应产出：

* 日志摘要
* Gate / Smoke 结果
* Contract snapshot diff（如有）
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
> gate 可自治；  
> 失败可重试；  
> 越权即停。**
