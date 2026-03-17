# Frontend Direct Base Contract Usage Audit v1

## 审计范围

- `frontend/apps/web/src/views/ActionView.vue`
- `frontend/apps/web/src/pages/ContractFormPage.vue`
- `frontend/apps/web/src/app/resolvers/sceneRegistry.ts`
- `frontend/apps/web/src/app/resolvers/sceneReadyResolver.ts`

## 发现

### A. 已完成收口（本轮）

- 列表页过滤器/分组/动作/列优先消费 scene-ready：
  - `search_surface.filters`
  - `search_surface.group_by`
  - `actions`
  - `blocks[].fields`
- 表单页场景校验必填优先消费 scene-ready：
  - `validation_surface.required_fields`

### B. 仍存在的历史直读（待后续）

- `ActionView.vue` 仍保留对动作契约（`actionContract.views/search/permissions`）的回退逻辑。
- `ContractFormPage.vue` 的字段布局仍以表单契约为主（scene-ready 主要用于校验增强）。

## 收口规则

- 主线路径：页面先读 `sceneReadyResolver`。
- 兼容路径：旧契约仅作为 fallback，不作为主数据源。

## 下一步

- 把表单 `layout/actions/editability` 全量迁移到 `formSceneResolver`。
- 清理 `ActionView` 对 `ui_contract.views.*` 的结构主依赖。

