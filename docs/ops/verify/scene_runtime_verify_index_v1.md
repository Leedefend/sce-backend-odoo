# Scene Runtime Verify Index v1

## 目标

为 P0 样板场景提供统一验证入口，支持“独立提交、连续迭代”的交付节奏。

## 验证模板目录

- `verify.scene.runtime.list`：`docs/ops/verify/verify.scene.runtime.list_projects_list_template_v1.md`
- `verify.scene.runtime.form`：`docs/ops/verify/verify.scene.runtime.form_projects_intake_template_v1.md`
- `verify.scene.runtime.workspace`：`docs/ops/verify/scene_runtime_verify_plan_v1.md`（workspace 子项）

## 连续迭代提交序列（建议）

- 执行手册：`docs/ops/iterations/scene_runtime_commit_playbook_v1.md`

### Iteration A：契约边界与输入标准

- 范围：三层边界文档 + UI Base Schema + 差异审计。
- 验收：文档齐备，边界可追溯。

### Iteration B：后端编排主链

- 范围：UI Base Adapter + Scene-ready 构建接入 + next scene 显式输出。
- 验收：`scene_ready_contract_v1` 含 `ui_base_orchestrator_input` 与 `next_scene`。

### Iteration C：前端消费收口

- 范围：`sceneReadyResolver` + `ActionView`/`ContractFormPage` scene-ready 优先消费。
- 验收：列表/表单主线优先读 scene-ready，旧契约仅 fallback。

### Iteration D：行业落地与样板验证

- 范围：行业 Profile/Policy/Provider 三件套 + 样板场景 + runtime verify 模板。
- 验收：`projects.list`、`projects.intake` 闭环模板可执行。

## 提交原则

- 每个 Iteration 可单独提交与回滚。
- 每个 Iteration 必须附带对应验证模板或断言证据。
- 未通过模板断言的 Iteration 不进入下一轮。
