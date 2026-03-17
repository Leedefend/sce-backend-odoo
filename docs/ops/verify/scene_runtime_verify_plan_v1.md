# Scene Runtime Verify Plan v1

## 新增验证项

- `verify.scene.runtime.list`
- `verify.scene.runtime.form`
- `verify.scene.runtime.workspace`

## 验证链路

1. 请求 `intent=system.init`。
2. 验证服务端存在 `ui_base_orchestrator_input`（scene meta）。
3. 验证 Scene Orchestrator 输出 `scene_ready_contract_v1`。
4. 验证前端页面通过 `sceneReadyResolver` 消费 `scene_ready` 子结构。

## 样板场景验收

### `projects.list`

- 断言存在 `search_surface`、`action_surface`、`permission_surface`。
- 断言前端列表列、过滤器、分组、动作来自 scene-ready 优先路径。

### `projects.intake`

- 断言存在 `validation_surface`、`workflow_surface`、`permission_surface`。
- 断言前端必填校验来自 scene-ready。

## 验证证据建议

- 后端：`scene_ready_contract_v1.scenes[*].meta.compile_pipeline`
- 前端：`ActionView.vue` 与 `ContractFormPage.vue` 的 resolver 调用路径

