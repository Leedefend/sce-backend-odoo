# UI Base Contract Asset Layer 设计说明 v1

日期：2026-03-15  
范围：`UI Base Contract` 后端资产化边界、生命周期与运行模式

---

## 1. 设计结论（先行）

`UI Base Contract` 资产化是必要能力，但不是运行时唯一主链。

本层定位：

> **可治理契约资产层（Asset/Snapshot/Replay/Compare/Cache/Audit）**

不是：

> **新的运行时真相中心（Single Source of Runtime Truth）**

---

## 2. 架构定位与边界

### 2.1 Layer Target / Module / Reason

- Layer Target：`Platform Layer + Scene Layer`
- Module：`UI Base Contract Asset Layer`
- Reason：将原生契约从瞬时返回升级为可治理资产，同时保持运行时实时生成为主事实源

### 2.2 真相源划分

- 运行时真相源：`UI Base Contract Runtime Generator`（实时）
- 资产层：`UI Base Contract Asset Store`（治理副本）
- 场景编排输入：优先运行时，按策略可从资产层读取

### 2.3 严格禁区

- 禁止前端直接写入/更新资产表
- 禁止 Scene Layer 直接操作 ORM
- 禁止资产层替代运行时实时生成逻辑
- 禁止“资产 miss 即失败”而不做 runtime fallback

---

## 3. 资产层职责（允许做什么）

资产层只服务治理与工程控制，核心职责为：

1. Snapshot：保存 `scene/role/company` 维度的原生契约快照
2. Compare：版本与 hash 对比（跨时间/环境/角色）
3. Replay：按历史版本回放 Scene 编译链路
4. Cache：为稳定场景提供受控缓存输入
5. Publish Gate：发布前后关键场景漂移检测
6. Audit：提供审计与问题复盘证据

---

## 4. 与 Scene Orchestrator 的关系

编排层不得感知资产表细节，只能调用统一解析接口：

```text
resolve_ui_base_contract(scene_key, role_code, company_id, mode, version?)
```

返回统一结构：

```json
{
  "payload": {},
  "meta": {
    "source": "runtime|asset",
    "asset_id": 0,
    "asset_version": "v1",
    "asset_hash": "...",
    "stale": false,
    "code_version": "..."
  }
}
```

编排层只消费 `payload + meta`，不直接查询资产模型。

---

## 5. 三种运行模式

### 模式 A：Runtime First（默认）

```text
intent -> runtime base contract -> scene compile
                         └-> optional asset write-back
```

适用：大多数实时页面。

### 模式 B：Asset-backed Compile（受控）

```text
asset lookup(active) -> hit -> scene compile
                    └-> miss/stale -> runtime fallback -> optional refresh
```

适用：稳定场景（workspace/dashboard/list）。

### 模式 C：Replay / Audit（指定版本）

```text
load asset(version=x) -> scene compile(replay)
```

适用：复盘、回归、发布对比。

---

## 6. 生命周期语义

`status` 为资产生命周期，不是业务状态：

- `draft`：已生成，待校验/待发布
- `active`：当前可消费版本
- `archived`：历史归档，仅审计/回放

治理要求：同一作用域（`scene_key + role_code + company_id`）任一时刻仅允许一个 `active`。

---

## 7. 数据模型规范（v1 建议）

当前最小模型：

- `scene_key`
- `role_code`
- `company_id`
- `status`
- `asset_version`
- `asset_hash`
- `source_ref`
- `payload_json`

建议补充字段（v1.1）：

- `contract_kind`：默认 `ui_base`（为多契约资产化预留）
- `source_type`：`runtime_intent|precompile|snapshot_import|replay_capture|seed`
- `scope_hash`：作用域签名（快速命中与审计）
- `generated_at`：语义化生成时间
- `code_version`：生成时代码版本（git sha/module version）

约束建议：

- 已有：`unique(scene_key, role_code, company_id, asset_version)`
- 增加：单作用域唯一 `active`（逻辑/索引约束）

---

## 8. 一致性与回退策略

### 8.1 一致性原则

- 运行时正确性优先于资产命中率
- 资产失效不可阻塞主业务请求
- 资产命中必须可追溯（`meta.source`）

### 8.2 回退规则

- `asset miss`：回退 runtime
- `asset stale`：回退 runtime，并标记 `stale=true`
- `asset parse error`：回退 runtime，并计入治理告警

---

## 9. 治理指标与门禁

最小指标集：

- `ui_base_contract_asset_scene_count`
- `ui_base_contract_bound_scene_count`
- `ui_base_contract_missing_scene_count`
- `base_contract_bound_scene_count`（scene_ready meta）

门禁策略：

1. 结构门禁：字段/接线完整性检查（已纳入 verify）
2. 阈值门禁：按环境和角色分层配置覆盖率阈值（后续启用）

---

## 10. 与现有实现对齐（当前状态）

已落地：

- 资产模型：`addons/smart_core/models/ui_base_contract_asset.py`
- 资产仓储：`addons/smart_core/core/ui_base_contract_asset_repository.py`
- `system.init` 绑定注入：`addons/smart_core/handlers/system_init.py`
- 结构 guard：`scripts/verify/scene_base_contract_asset_coverage_guard.py`

当前仍保持：

- 运行时主链可独立工作（未被资产层替代）
- 资产层作为治理增强输入，不强制主事实源切换

---

## 11. 迭代路线（建议）

### T15：资产生产链路

- 事件触发生产（模型/视图/权限变更）
- 定时预热生产（关键场景）

### T16：版本治理

- 引入 `code_version + source_type + generated_at`
- 明确 `asset_version` 规则（语义版本或构建版本）

### T17：阈值门禁

- 在 `verify.scene.runtime_boundary.gate` 增加覆盖率阈值策略
- 按 `dev/test/prod-like` 分层阈值

---

## 12. 最终原则

**UI Base Contract Asset Layer 是“可治理契约资产层”，不是“运行时真相中心”。**

可简化为一句：

> 资产层像 Git 仓库，用于治理与回放；运行时生成仍是在线事实源。

