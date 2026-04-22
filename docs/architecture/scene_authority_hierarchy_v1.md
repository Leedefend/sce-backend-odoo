# Scene Authority Hierarchy v1

状态：Draft Governance Freeze  
适用范围：后端场景化身份、入口、内容、降级、菜单解释治理

## 1. 目标

本文件只解决一个问题：

> 一个 scene 的身份、入口、内容、降级路径，到底谁说了算。

当前系统已经具备后端场景化运行能力，但 authority 分散在：

- `scene_registry_content.py`
- scene profile / scene layout XML
- capability default payload
- portal / dashboard service payload
- 原生 menu/action XML

如果没有明确 hierarchy，系统会继续出现：

- scene identity 能跑，但入口语义打架
- menu 说一个 action，profile 说另一个 action
- provider、registry、capability payload 互相漂移
- `/s/...`、`/a/...`、native action 同时成立，但没有统一解释

## 2. 核心结论

后端场景化的 authority 必须冻结为四层：

1. `scene_registry_content.py`  
   负责 scene identity authority

2. provider  
   负责 scene content authority

3. merge/policy/runtime orchestration  
   负责 scene orchestration authority

4. 原生 menu / action / model-view  
   只保留为 source fact / compatibility fact，不再反向定义 scene 身份

## 3. 权威层级

### 3.1 Identity Authority

唯一权威源：

- `addons/smart_construction_scene/profiles/scene_registry_content.py`

这个层只负责回答：

- 这个 scene 是谁
- 它的正式 route 是什么
- 它绑定哪个 menu/action/model/view
- 它属于哪个 family
- 它的 canonical entry 是什么类型

registry entry 至少应冻结这些字段：

- `code`
- `family`
- `route`
- `menu_xmlid`
- `action_xmlid`
- `model`
- `view_type`
- `canonical_entry_kind`
- `native_fallback_kind`
- `provider_key`
- `status`
- `owner_module`
- `delivery_tier`

约束：

- scene identity 的正式定义只能在 registry
- profile/layout/capability/menu 不能反向覆盖 registry identity
- 同一 `scene_key` 只能有一个 canonical identity

### 3.2 Content Authority

唯一职责源：

- provider

provider 只负责：

- `page`
- `runtime`
- `guidance`
- `next_action`
- `blocks`
- `next_scene`

provider 不负责：

- 改 scene 是谁
- 改 canonical entry
- 改 menu/action 身份

规则：

- provider 可以补内容，不能改 identity
- provider 依赖 registry 的 `scene_key` 与 provider registry 注册关系

### 3.3 Orchestration Authority

唯一职责源：

- merge resolver / policy / runtime orchestrator

这一层只负责：

- permission merge
- layout merge
- policy override
- runtime degrade
- diagnostics / drift

不负责：

- 定义 scene identity
- 决定 scene canonical entry
- 改写原生 menu/action 事实

### 3.4 Native Fact Layer

来源事实：

- Odoo menu
- Odoo act_window / action
- model + view_mode

它们的职责是：

- 证明“从哪来”
- 作为 compatibility fallback 的来源
- 作为 menu interpreter 的输入事实

它们不再承担：

- 定义 scene identity
- 定义 canonical scene entry
- 定义 scene page content

## 4. 入口语义规则

系统必须明确区分两类入口：

### 4.1 Native Entry

原生入口语义：

- Odoo menu/action 默认入口
- 保留原始系统组织方式
- 允许作为兼容入口存在

### 4.2 Canonical Scene Entry

scene 工作入口语义：

- 用户实际工作的编排入口
- 由 registry authority 明确指定
- 可与原生 menu/action 不一致

规则：

- scene 可以有自己的 canonical work entry
- 原生 menu/action 可以继续存在
- 两者不一致时：
  - scene canonical entry = 产品正式入口
  - native action = 兼容入口

## 5. Canonical Entry 字段规范

registry entry 需要明确表达：

- `canonical_entry_kind`
  - `scene_work`
  - `native`
  - `hybrid`

- `native_fallback_kind`
  - `action`
  - `record`
  - `menu_only`
  - `none`

- `provider_key`

- `delivery_tier`
  - `startup`
  - `navigation`
  - `contract`
  - `compat`

解释：

- `canonical_entry_kind` 回答“用户正式从哪进”
- `native_fallback_kind` 回答“scene 不能完全落地时退到哪”
- `delivery_tier` 回答“这个 scene 在哪个 delivery 面先被消费”

## 6. 冲突裁决规则

当不同来源冲突时，统一按以下顺序裁决：

1. registry identity
2. provider content
3. policy/runtime override
4. native menu/action fact

示例：

- menu 绑定 `action_payment_request`
- scene profile 用 `action_payment_request_my`
- registry 定义 `action_payment_request_my`

最终结论：

- scene canonical entry = `action_payment_request_my`
- native menu = compatibility/source fact

## 7. Menu Interpreter 规则

`MenuTargetInterpreterService` 的解释顺序必须固定为：

1. scene
2. native action
3. url
4. compatibility
5. unavailable

输出至少应稳定包含：

- `target_type`
- `scene_key`
- `route`
- `native_action_id`
- `native_model`
- `native_view_mode`
- `reason_code`
- `confidence`
- `compatibility_used`

目标：

- 一眼区分 scene 命中还是兼容降级
- 避免导航链变成黑盒

## 8. 守卫要求

后续 verify 必须至少补四个守卫：

1. `authority_guard`
   - 检查同一 `scene_key` 是否存在冲突身份定义

2. `canonical_entry_guard`
   - 检查每个已发布 family 是否只有一个 canonical entry

3. `menu_scene_mapping_guard`
   - 检查 menu 解释结果是否稳定落在预期 scene/fallback

4. `provider_completeness_guard`
   - 检查已发布 scene 是否具备 provider 或明确 fallback

## 9. 当前落地建议

后续所有 family 收口必须按固定顺序执行：

1. 先冻结 registry identity
2. 再对齐 canonical scene entry
3. 再检查 provider completeness
4. 最后验证 menu/action fallback 是否可解释

不允许继续反过来做：

- 先改 profile
- 再猜 registry
- 最后靠兼容链兜住

## 10. 临时判定

从本轮排查到当前实现链路看，系统应该正式采用：

> registry 定 identity，provider 定内容，merge/runtime 定编排，native menu/action 只保留为来源事实和兼容事实。

这是后端场景化从“能跑”进入“可治理”的第一条红线。
