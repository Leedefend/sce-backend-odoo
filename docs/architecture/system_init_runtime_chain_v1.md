# System Init Runtime Chain v1

状态：Draft Runtime Governance Note  
适用范围：`login -> system.init -> startup surface`

## 1. 目标

本文件用于把当前 `system_init.py` 从“黑盒总装配器”说明成一条可读的运行总线。

当前目标不是大拆文件，而是先冻结职责切块，让排查和后续治理有统一口径。

## 2. 当前事实

当前真实复杂启动链主要在：

- `addons/smart_core/handlers/system_init.py`

而不是轻量版：

- `addons/smart_core/v2/services/system_service.py`

`system_service.py` 更像一个简化 rebuild 路径；真实运行态复杂装配仍集中在 `system_init.py`。

## 3. 建议的逻辑切块

当前 `system_init.py` 建议按六段理解：

1. identity bootstrap
2. scene bootstrap
3. navigation bootstrap
4. capability bootstrap
5. runtime diagnostics
6. release / extension facts

## 4. 六段职责定义

### 4.1 Identity Bootstrap

目标：

- 确定当前用户、公司、角色、surface 归属

关键内容：

- user/company identity
- role surface
- landing scene / default route 的身份基础

### 4.2 Scene Bootstrap

目标：

- 加载 scene runtime 主数据并 resolve target

关键组件：

- `SceneRuntimeOrchestrator`
- `scene_provider.py`
- `smart_construction_scene.scene_registry`

真实行为：

1. 先尝试 scene contract
2. 没拿到则 fallback
3. fallback 会走 DB scenes / registry content
4. normalize / resolve / drift / auto-degrade

### 4.3 Navigation Bootstrap

目标：

- 生成 startup nav、scene nav、default route、entry target

关键组件：

- `OdooNavAdapter`
- `SystemInitPayloadBuilder`
- `build_scene_nav_contract`
- menu/nav related builders

### 4.4 Capability Bootstrap

目标：

- 确定 capability groups、capability entry targets、角色能力可见性

关键组件：

- capability provider
- capability target resolution
- role/capability payload

### 4.5 Runtime Diagnostics

目标：

- 记录 trace、drift、resolve_errors、auto-degrade、timing

关键组件：

- diagnostics helper
- scene diagnostics builder
- request diagnostics collector

### 4.6 Release / Extension Facts

目标：

- 把行业扩展事实、发布入口、ext_facts 等补进 startup payload

关键组件：

- extension fact merger
- released scene surface builders
- enterprise / industry extension hooks

## 5. 当前 system.init 的真实问题

### 5.1 职责过多

`system_init.py` 当前同时承担：

- scene runtime
- nav
- capability
- startup surface
- diagnostics
- release surface
- extension facts

这让它功能强，但排查成本高。

### 5.2 逻辑已经切块，文件却还像一个总装配器

虽然内部已经有大量 builder / orchestrator / helper，但外部观察仍然像一个“大 handler”。

所以当前最应该先做的不是物理拆文件，而是：

- 先冻结逻辑分段
- 先补可观测命名
- 先补阶段日志

### 5.3 v2 rebuild 路线容易让人误判主链

`v2/services/system_service.py` 看起来更简单，但它不是当前后端场景化真实复杂主链。

治理时必须明确：

- 简化服务存在
- 但主运行链 authority 仍在 `system_init.py`

## 6. 治理建议

### 6.1 短期

先不大拆文件，只做：

- 六段职责冻结
- 每段单独埋点
- 每段单独 builder/service 命名归口

### 6.2 中期

在不改语义的前提下，把 `system_init.py` 逐步显式整理成逻辑调用序列：

```python
build_identity_surface()
build_scene_surface()
build_navigation_surface()
build_capability_surface()
build_runtime_diagnostics()
build_release_surface()
```

### 6.3 长期

只有在 authority hierarchy、canonical entry、provider completeness 都冻结后，才考虑物理拆分文件。

## 7. 临时结论

当前 `system.init` 不应被理解为一个普通 bootstrap handler，而应被理解为：

> 后端场景化运行总线。

它的问题不在于没有 builder，而在于：

- 段落边界尚未对外冻结
- 运行职责过多
- 说明文档不足

所以治理顺序必须是：

1. 先冻结链路语义
2. 再补可观测
3. 最后才谈物理重构
