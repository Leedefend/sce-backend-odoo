# Contract Surface 规范 v1

## 1. Surface 类型

1. `native`
- 定义：解析层原生结构面，最大程度保真。
- 用途：解析诊断、结构对照、治理回归分析。

2. `user`（governed）
- 定义：面向用户消费的治理面。
- 用途：前端默认渲染。

3. `hud`（governed + debug）
- 定义：调试诊断治理面。
- 用途：开发排障、可观测性增强。

## 2. 必备元字段

所有生产 contract 必须包含：
- `contract_surface`
- `render_mode`
- `source_mode`
- `governed_from_native`
- `surface_mapping`

约束：
- `native`:
  - `render_mode=native`
  - `governed_from_native=false`
- `user/hud`:
  - `render_mode=governed`
  - `governed_from_native=true`

## 3. mapping 证据格式

`surface_mapping.native_to_governed` 至少包含：
- `fields`
- `layout_fields`
- `layout_nodes`
- `buttons`
- `header_buttons`
- `stat_buttons`
- `field_modifiers`

每项包含：
- `native_count` (int)
- `governed_count` (int)
- `removed` (list)
- `added` (list)
- `reordered` (bool)

## 4. 前后端消费约束

### 4.1 后端
- 统一通过 `apply_contract_governance` 输出 surface 元信息与映射证据。
- 不允许旁路 handler 生产主链契约。

### 4.2 前端
- 默认消费 `surface=user`。
- 允许调试切换：
  - `?surface=native`
  - `?surface=hud`
- 调试面必须显示 surface 元字段，避免猜测契约语义。

## 5. Guard 对应关系

1. `verify.contract.native_integrity_guard`
- 验证 native 面结构完整与元字段一致性。

2. `verify.contract.governed_policy_guard`
- 验证 user 面治理政策与元字段一致性。

3. `verify.contract.surface_mapping_guard`
- 验证 mapping 结构完整与 surface 对齐。

4. `verify.project.form.contract.surface.guard`
- 验证核心业务模型（project form）跨 surface 行为稳定。

