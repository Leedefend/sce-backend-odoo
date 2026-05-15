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

## Web 产品化令牌基线
- surface：`page` / `panel` / `panel_muted` / `subtle` / `input` / `hover` / `overlay` / `interactive`
- border：`default` / `strong` / `subtle` / `interactive`
- focus：`ring`
- shadow：`panel` / `popover` / `modal`
- state：每个状态必须同时具备 base / bg / border / text 语义令牌
- component：`button` / `panel` / `card` / `toolbar` / `input` / `table` / `dialog` / `badge` / `tag`

## 治理规则
- 页面禁止直接写硬编码颜色。
- 业务样式只允许消费 semantic/component tokens。
- 新增契约状态必须先补 token 映射再上线。
- `frontend/apps/web/src/styles/design-system.css` 只能桥接 semantic/component tokens，不新增裸色值。
- `make verify.frontend.style_system.guard` 必须保持硬编码颜色基线不回升。

## 当前基线
- `frontend/apps/web/src` 硬编码颜色引用上限：`512`
- 该上限只允许在 token 化迁移后下调，不允许上调。

## Web 产品模式库
- `sc-page` / `sc-page-surface`：页面底色与文字基线。
- `sc-panel` / `sc-panel-flat`：面板和低阴影容器。
- `sc-toolbar` / `sc-action-group`：工具栏与动作组。
- `sc-form` / `sc-form-label` / `sc-field` / `sc-input` / `sc-search`：表单与输入控件。
- `sc-list` / `sc-list-item` / `sc-table-shell`：列表与表格外壳。
- `sc-btn` / `sc-btn-primary` / `sc-btn-ghost` / `sc-btn-sm`：按钮状态。
- `sc-tag` / `sc-badge` / `sc-badge-info` / `sc-badge-danger`：标签和徽标。
- `sc-alert` / `sc-alert-info` / `sc-alert-danger` / `sc-empty` / `sc-dialog`：反馈、空态和弹层。


## 交付物
- Token 源文件（json）
- 生成脚本（css variables + ts const）
- 多端平台覆盖（web/mobile）
