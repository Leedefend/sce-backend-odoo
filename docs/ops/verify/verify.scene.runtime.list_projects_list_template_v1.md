# verify.scene.runtime.list（projects.list）模板 v1

## 目标

验证 `projects.list` 是否完成以下运行时闭环：

1. 形成 `UI Base Contract`
2. 进入 `Scene Orchestrator`
3. 输出 `Scene-ready Contract`
4. 前端列表页仅消费 `Scene-ready` 子结构

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
  }' > /tmp/projects_list_system_init.json
```

## 断言清单（后端输出）

### A. `scene_ready_contract_v1` 存在

- `data.scene_ready_contract_v1` 非空
- `data.scene_ready_contract_v1.scenes` 包含 `projects.list`

### B. `UI Base -> Orchestrator` 输入存在

在 `projects.list` 条目中断言：

- `meta.ui_base_orchestrator_input` 存在
- 包含 7 类 fact：
  - `view_fact`
  - `field_fact`
  - `search_fact`
  - `action_fact`
  - `permission_fact`
  - `workflow_fact`
  - `validation_fact`

### C. `Scene-ready` 列表面存在

在 `projects.list` 条目中断言：

- `blocks` 存在并可解析列表字段
- `search_surface` 存在
- `permission_surface` 存在
- `action_surface` 存在
- `actions` 存在

## 前端消费断言（List）

页面：`ActionView`

- 列来源优先：`scene-ready.blocks[].fields`
- 排序来源优先：`scene-ready.search_surface.default_sort`
- 筛选来源优先：`scene-ready.search_surface.filters`
- 分组来源优先：`scene-ready.search_surface.group_by`
- 动作来源优先：`scene-ready.actions`

对应代码点：

- `frontend/apps/web/src/app/resolvers/sceneReadyResolver.ts`
- `frontend/apps/web/src/views/ActionView.vue`

## 建议自动化断言（jq 示例）

```bash
jq -e '
  .data.scene_ready_contract_v1.scenes
  | map(select(((.scene.key // .page.scene_key // "") == "projects.list")))
  | length > 0
' /tmp/projects_list_system_init.json

jq -e '
  .data.scene_ready_contract_v1.scenes
  | map(select(((.scene.key // .page.scene_key // "") == "projects.list")))[0]
  | (.meta.ui_base_orchestrator_input.view_fact != null)
    and (.meta.ui_base_orchestrator_input.field_fact != null)
    and (.meta.ui_base_orchestrator_input.search_fact != null)
    and (.meta.ui_base_orchestrator_input.action_fact != null)
    and (.meta.ui_base_orchestrator_input.permission_fact != null)
    and (.meta.ui_base_orchestrator_input.workflow_fact != null)
    and (.meta.ui_base_orchestrator_input.validation_fact != null)
' /tmp/projects_list_system_init.json

jq -e '
  .data.scene_ready_contract_v1.scenes
  | map(select(((.scene.key // .page.scene_key // "") == "projects.list")))[0]
  | (.blocks | type == "array")
    and (.search_surface | type == "object")
    and (.permission_surface | type == "object")
    and (.action_surface | type == "object")
    and (.actions | type == "array")
' /tmp/projects_list_system_init.json
```

## 结果判定

- 全部断言通过：`PASS verify.scene.runtime.list (projects.list)`
- 任一断言失败：标记 `FAIL` 并记录失败项（输入缺失 / 编排缺失 / 前端消费越界）

