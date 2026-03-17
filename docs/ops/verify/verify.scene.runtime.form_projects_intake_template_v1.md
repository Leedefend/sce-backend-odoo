# verify.scene.runtime.form（projects.intake）模板 v1

## 目标

验证 `projects.intake` 是否完成以下运行时闭环：

1. 形成 `UI Base Contract`
2. 进入 `Scene Orchestrator`
3. 输出 `Scene-ready Contract`
4. 前端仅消费 `Scene-ready` 表单子结构

## 前置条件

- 当前分支为合规开发分支（`feat/*|feature/*|codex/*|experiment/*`）。
- 服务已可响应 `intent=system.init`。
- 登录态 token 可用于调用 intent API。

## 请求样例（system.init）

```bash
curl -sS -X POST "$BASE_URL/api/v1/intent" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "intent": "system.init",
    "params": {
      "surface": "user"
    }
  }' > /tmp/projects_intake_system_init.json
```

## 断言清单（后端输出）

### A. `scene_ready_contract_v1` 存在

- `data.scene_ready_contract_v1` 非空
- `data.scene_ready_contract_v1.scenes` 包含 `projects.intake`

### B. `UI Base -> Orchestrator` 输入存在

在 `projects.intake` 条目中断言：

- `meta.ui_base_orchestrator_input` 存在
- 包含 7 类 fact：
  - `view_fact`
  - `field_fact`
  - `search_fact`
  - `action_fact`
  - `permission_fact`
  - `workflow_fact`
  - `validation_fact`

### C. `Scene-ready` 表单面存在

在 `projects.intake` 条目中断言：

- `validation_surface.required_fields` 存在
- `permission_surface` 存在
- `workflow_surface` 存在
- `actions` 存在
- `next_scene`/`next_scene_route` 存在（可来自 provider/policy/runtime）

## 前端消费断言（Form）

页面：`ContractFormPage`

- 必填校验来源：`sceneReadyResolver.resolveFormSceneReady(...).requiredFields`
- 动作来源优先级：`scene-ready.actions` > legacy contract buttons/toolbar
- 创建成功跳转来源：`scene-ready.next_scene_route`（缺省回退既有路径）

对应代码点：

- `frontend/apps/web/src/app/resolvers/sceneReadyResolver.ts`
- `frontend/apps/web/src/pages/ContractFormPage.vue`

## 建议自动化断言（jq 示例）

```bash
jq -e '
  .data.scene_ready_contract_v1.scenes
  | map(select(((.scene.key // .page.scene_key // "") == "projects.intake")))
  | length > 0
' /tmp/projects_intake_system_init.json

jq -e '
  .data.scene_ready_contract_v1.scenes
  | map(select(((.scene.key // .page.scene_key // "") == "projects.intake")))[0]
  | (.meta.ui_base_orchestrator_input.view_fact != null)
    and (.meta.ui_base_orchestrator_input.field_fact != null)
    and (.meta.ui_base_orchestrator_input.search_fact != null)
    and (.meta.ui_base_orchestrator_input.action_fact != null)
    and (.meta.ui_base_orchestrator_input.permission_fact != null)
    and (.meta.ui_base_orchestrator_input.workflow_fact != null)
    and (.meta.ui_base_orchestrator_input.validation_fact != null)
' /tmp/projects_intake_system_init.json

jq -e '
  .data.scene_ready_contract_v1.scenes
  | map(select(((.scene.key // .page.scene_key // "") == "projects.intake")))[0]
  | (.validation_surface.required_fields | type == "array")
    and (.permission_surface | type == "object")
    and (.workflow_surface | type == "object")
    and (.actions | type == "array")
    and (((.next_scene // "") != "") or ((.next_scene_route // "") != ""))
' /tmp/projects_intake_system_init.json
```

## 结果判定

- 全部断言通过：`PASS verify.scene.runtime.form (projects.intake)`
- 任一断言失败：标记 `FAIL` 并记录失败项（输入缺失 / 编排缺失 / 前端消费越界）

