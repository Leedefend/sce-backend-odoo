# App Shell Contract vs Page Scene Contract v1

## App Shell Contract（壳层）

- 输入：`system.init` 的全局聚合结果。
- 输出：全局导航与会话上下文（`nav`、`default_route`、`capabilities`、`role_surface`、`scene_governance_v1`）。
- 前端用途：启动、路由守卫、导航树、角色信息、治理监控。
- 不承载：页面字段布局、列表列、表单必填、动作编排。

## Page Scene Contract（页面场景）

- 输入：`scene_ready_contract_v1.scenes[*]` 的场景级条目。
- 输出：场景渲染负载（`page.zones`、`blocks`、`actions`、`search_surface`、`permission_surface`、`validation_surface`、`workflow_surface`）。
- 前端用途：页面渲染与交互。
- 不承载：登录身份、壳层导航树。

## 消费边界

- App Shell 组件只消费 App Shell Contract。
- 页面组件只消费 Page Scene Contract。
- 两者禁止混读：
  - 壳层不得解析 `blocks/fields`。
  - 页面不得反向读取原始 `nav` 来拼装页面结构。

