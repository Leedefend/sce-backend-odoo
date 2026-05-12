# Frontend Design System v1（跨端统一）

## Layer Target
- Frontend Layer

## Module
- `frontend/packages/design-tokens`

## Reason
- 建立契约驱动前端的统一样式系统，支撑 web/mobile/mini 多端一致。

## 四层结构
1. Primitives（原子值）
2. Semantic Tokens（语义令牌）
3. Component Tokens（组件令牌）
4. Runtime Adaptation（主题/终端/密度）

## 语义状态映射（必须）
- `capability_state=allow -> state.success`
- `capability_state=readonly -> text.secondary`
- `capability_state=deny -> state.danger`
- `capability_state=pending -> state.warning`
- `capability_state=coming_soon -> state.info`

## 治理规则
- 页面禁止直接写硬编码颜色。
- 业务样式只允许消费 semantic/component tokens。
- 新增契约状态必须先补 token 映射再上线。

## 交付物
- Token 源文件（json）
- 生成脚本（css variables + ts const）
- 多端平台覆盖（web/mobile）
