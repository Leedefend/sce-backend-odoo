# Scene Entry Semantics v1

状态：Draft Governance Freeze  
适用范围：scene canonical entry、native entry、compatibility fallback

## 1. 文档目标

本文件用于冻结：

- scene 的正式入口语义
- 原生菜单入口与 scene 工作入口的关系
- compatibility fallback 的解释规则

核心目标：

> 允许 native entry 与 scene work entry 并存，但禁止它们在语义上互相替代、互相污染。

## 2. 两类入口必须显式区分

### 2.1 Native Entry

定义：

- 来自 Odoo 原生 menu/action 的入口
- 反映原生系统组织方式

用途：

- 原生兼容入口
- source fact
- 无 scene identity 时的 fallback 来源

它不是：

- scene 的正式产品入口

### 2.2 Scene Work Entry

定义：

- 面向用户工作的正式编排入口
- 由 scene registry authority 明确指定

用途：

- 产品正式入口
- scene-first 导航
- startup/default_route/role landing/workbench entry 的权威来源

## 3. 语义规则

### 3.1 允许不一致

native entry 与 scene work entry 允许不一致。

示例：

- 菜单原生绑定 `action_payment_request`
- scene canonical entry 定义为 `action_payment_request_my`

这是合法状态，只要：

- registry 已明确冻结 canonical entry
- menu interpreter 能解释 fallback
- diagnostics 能说明采用了哪条路径

### 3.2 冲突裁决

当 native entry 与 scene work entry 冲突时：

- scene work entry 优先
- native entry 降级为 compatibility/source fact

### 3.3 对前端的含义

前端应消费：

- canonical scene route
- formal entry_target

前端不应自行根据原生 action 猜哪个入口更“正式”。

## 4. 规范字段

每个已发布 scene 至少应能解释以下概念：

- `canonical_route`
- `canonical_action_xmlid`
- `native_action_xmlid`
- `compatibility_target`
- `entry_semantic`

其中：

- `entry_semantic`
  - `native`
  - `scene_work`
  - `hybrid`

- `compatibility_target`
  - scene 不能完全解释时允许退回的原生/兼容入口

## 5. 典型模式

### 5.1 完整 scene-first

- native menu 可存在
- canonical route 明确为 `/s/<scene>`
- registry 有稳定 `action_xmlid/menu_xmlid/model/view_type`

### 5.2 Scene work + native fallback

- canonical route 为 `/s/<scene>`
- native action 仍保留
- menu 解释器在 identity 足够时给 scene
- identity 不足时给 compatibility/native

### 5.3 Native-only transitional

- 仅允许在 scene identity 未冻结前临时存在
- 必须可观测
- 必须有 family 收口计划

## 6. 当前仓库里的典型冲突类型

### 6.1 原生菜单默认绑定 vs scene canonical entry

常见于：

- `finance.center`
- `finance.payment_requests`
- `payments.approval`

### 6.2 profile/layout/capability payload 比 registry 更早演化

症状：

- profile 里 action 已切到用户工作入口
- registry 仍保留旧 action

### 6.3 menu/action 正确，但 canonical route 未冻结

症状：

- 解释链能推出 scene
- 但 route/fallback 仍呈现漂移

## 7. 实施准则

后续每个 family 收口时，必须按以下顺序做：

1. 判定 canonical scene entry
2. registry 冻结 canonical action/route
3. 检查 native menu/action 是否仅作为 compatibility/source fact
4. provider / profile / capability payload 与 registry 对齐
5. menu interpreter 输出可解释的 fallback

## 8. 不允许的做法

- 用 profile/layout/default payload 偷偷重定义 canonical entry
- 用前端行为反推 scene canonical entry
- 让 native menu/action 反向覆盖 registry 结论
- 一个 scene 同时存在两个 canonical entry 且无明确 semantic split

## 9. 临时结论

当前系统应正式接受：

> native entry 是系统原生入口，scene work entry 是产品正式入口。  
> 两者允许不一致；不一致时，以 scene canonical entry 为准，以 native entry 为 compatibility fact。
