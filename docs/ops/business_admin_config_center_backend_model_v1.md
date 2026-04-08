# 业务管理员可视化配置中心 v1 · Phase 2 后端配置模型设计

## 1. 设计目标

在不改业务事实层的前提下，定义可落地的最小配置治理模型，支持：
- 系统参数可管理
- 角色入口可配置
- 首页区块可配置

本阶段仅输出模型设计基线，不实施业务代码改造。

## 2. 设计原则

- 配置层不拥有业务真相，仅承载治理参数。
- 配置层不绕过权限系统，入口显隐不改变后端授权结果。
- 配置输出必须可审计、可回滚、可禁用。
- 配置对 contract 的影响必须是 non-breaking、可选扩展。

## 3. 最小配置治理模型

## 3.1 `config.item`（系统参数/配置项）

用途：管理白名单参数，例如默认列表页尺寸、默认入口、显示文案开关。

建议字段：
- `key`（唯一键）
- `category`（分类：runtime/display/navigation）
- `value_type`（string/int/bool/json）
- `value_payload`（配置值）
- `scope_type`（global/company/role）
- `scope_ref`（作用域引用）
- `is_enabled`
- `effective_from` / `effective_to`
- `version`

治理约束：
- `key` 必须来自白名单。
- 禁止配置会影响业务权限判定、金额规则、审批规则的关键逻辑。

## 3.2 `config.role.entry`（业务角色入口配置）

用途：为业务角色管理入口可见性与顺序。

建议字段：
- `role_code`
- `entry_code`
- `entry_label_override`（可选）
- `entry_target_type`（action/scene/url）
- `entry_target_ref`
- `is_visible`
- `display_order`
- `company_id`（可选公司作用域）
- `is_enabled`

治理约束：
- 入口配置仅影响导航可发现性。
- 真实访问仍受后端 ACL/rule/capability 控制。

## 3.3 `config.home.block`（首页/区块配置）

用途：管理首页区块启用、排序、分组和默认展开态。

建议字段：
- `home_surface_code`（例如 my_work/project_dashboard）
- `block_code`
- `group_code`
- `display_order`
- `is_visible`
- `default_collapsed`
- `render_hint`（可选：compact/standard）
- `company_id` / `role_code`（可选作用域）
- `is_enabled`

治理约束：
- 仅控制呈现，不改区块业务数据语义。
- 不允许通过配置替换区块业务查询逻辑。

## 4. 审计与发布字段（三模型共用）

必备审计字段：
- `created_by`
- `updated_by`
- `created_at`
- `updated_at`
- `change_ticket`
- `change_note`
- `publish_state`（draft/active/retired）

建议发布机制：
- 草稿保存 -> 校验 -> 激活发布 -> 版本追踪。
- 发布失败支持回滚到上一版本。

## 5. 配置结果与契约联动边界

## 5.1 可进入 contract 的配置结果（可选扩展）

- 导航可见入口集合（按角色/公司作用域）
- 首页区块排序与显隐建议
- 文案覆盖提示（非业务字段）

要求：
- 仅作为扩展字段输出，不能破坏既有冻结 surface。
- 新字段需走独立契约验收批次再冻结。

## 5.2 仅作用后端参数的配置结果

- 默认分页大小
- 默认排序偏好
- 默认首页布局偏好

要求：
- 不进入核心业务 contract。
- 仅影响系统行为参数，不影响权限和业务真相。

## 6. 与后续阶段的接口

- 给 Phase 3（前端壳层）的输入：
  - 三模型列表/表单字段清单
  - 审计字段展示要求
  - 发布状态与版本展示要求
- 给 Phase 4（契约联动预案）的输入：
  - 可选扩展字段候选清单
  - backend-only 参数清单

## 7. 本阶段结论

- `PASS`（设计阶段）：后端最小配置治理模型已成型，边界清晰。
- 下一步应进入前端壳层结构设计（列表/表单承载，不做低代码引擎）。
