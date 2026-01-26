# Codex Execution Allowlist
（Codex 自动执行授权清单 · Policy as Code）

## 目的（Why）

本清单用于**授权 Codex 在无需人工逐条许可的前提下**，在本仓库内执行**受限、可重复、可审计**的工程验证与迭代操作。

目标不是“让 Codex 更自由”，而是：
- 把日常验证流程**固化为标准工程动作**
- 避免每次迭代都触发 **模块升级 / DB 重建 / demo.reset**
- 让所有重动作**只能在明确的 Gate 模式下发生**
- 确保所有执行都有 **日志与证据产出**

> Codex 被视为一个 **CI Runner / 初级工程执行者**，而非系统管理员。

---

## 核心原则（Non-Negotiable Rules）

1. **所有操作必须通过 Makefile target 执行**
   - ❌ 禁止直接运行 `docker compose exec odoo -u ...`
   - ❌ 禁止直接连接 `psql` 执行破坏性 SQL
   - ❌ 禁止绕过 Makefile 的 prod guard

2. **默认最小动作原则（Fast by Default）**
   - 未显式声明 Gate 模式前，禁止重建 / 重置 / 全量门禁

3. **模式即授权（Mode = Authority）**
   - `CODEX_MODE=fast`：只允许轻量迭代
   - `CODEX_MODE=gate`：允许门禁级动作

4. **升级必须显式声明**
   - 模块升级不是默认行为
   - 只有在明确涉及入库元数据时才允许

---

## 执行模式定义（Execution Modes）

### MODE=fast（默认 · 快迭代模式）

**用途**
- 前端 UI / Portal 页面调试
- Python 业务逻辑修正
- Contract 输出结构微调
- 文档 / 脚本调整

**允许的 Make Targets**
- `make restart`
- `make odoo.recreate`
- `make logs`
- `make ps`
- `make odoo-shell`（只读调试，不执行破坏性命令）
- `make contract.export`（单 case）
- `make mod.upgrade`  
  ⚠️ **仅当同时满足：**
  - `CODEX_NEED_UPGRADE=1`
  - 明确声明 `CODEX_MODULES=...`

**禁止的 Make Targets**
- ❌ `make demo.reset`
- ❌ `make db.reset`
- ❌ `make dev.rebuild`
- ❌ `make gate.full`
- ❌ `make gate.demo`
- ❌ `make gate.baseline`

**升级判定说明**
只有当改动涉及以下路径，才允许设置 `CODEX_NEED_UPGRADE=1`：
- `addons/**/views/**`
- `addons/**/security/**`
- `addons/**/data/**`
- `addons/**/ir.model.access.csv`
- 新增/修改模型字段（schema 变化）

---

### MODE=gate（门禁 / 验收模式）

**用途**
- 合并分支前
- 打 tag / Release 前
- Contract 协议稳定性验证
- Demo/Scenario 可重复性验收

**允许的 Make Targets**
- MODE=fast 中的全部
- `make demo.reset`
- `make contract.export_all`
- `make gate.full`

**推荐标准执行链**
1. （可选）`make mod.upgrade`
2. `make demo.reset`
3. `make contract.export_all`
4. `make gate.full`

---

## Codex 标准入口（Single Entry Points）

Codex **必须** 通过以下入口执行：

### 快迭代
```bash
make codex.fast
```

如需升级模块（明确声明）：

```bash
make codex.fast CODEX_NEED_UPGRADE=1 CODEX_MODULES=smart_construction_portal
```

### 门禁验收

```bash
make codex.gate
```

或（涉及入库变更）：

```bash
make codex.gate CODEX_NEED_UPGRADE=1 CODEX_MODULES=smart_construction_portal
```

> Codex **不得** 直接调用被禁止的 Make targets；
> 若违反，本仓库的 guard 将强制失败。

---

## 环境与安全约束（Safety Constraints）

* ❌ 禁止在 `ENV=prod` 或 `.env.prod` 下执行任何 reset / rebuild / gate
* ❌ 禁止在未设置 `PROD_DANGER=1` 的情况下执行危险操作
* ❌ 禁止在 Codex 执行中修改 `.env*` 文件

---

## 产出与审计（Artifacts & Evidence）

每次 Codex 执行应至少产出：

* 控制台日志（stdout/stderr）
* Contract snapshots（如涉及 contract）
* CI / gate 日志（MODE=gate）

推荐输出目录：

```
artifacts/codex/<timestamp>/
```

---

## 违规处理（Failure is Correct）

* 若 Codex 触发 guard 并失败：

  * 这是**正确行为**
  * 表示操作超出了授权清单
* Codex 应停止执行并报告：

  * 当前模式
  * 尝试执行的目标
  * 被拒绝原因

---

## 最终原则（One Sentence）

> **Codex 不被“信任”，Codex 被“约束”；
> 所有允许的能力，必须写进仓库。**
