# Current Response Contract Gap Audit v1

## 审计对象

- 接口：`intent=system.init`
- 关注范围：顶层响应字段的三层归属与混层风险。

## 顶层字段归属

| 字段 | 归属层 | 说明 | 结论 |
| --- | --- | --- | --- |
| `nav` | App Shell | 壳层导航契约 | 保留 |
| `default_route` | App Shell | 壳层默认路由 | 保留 |
| `capabilities` | App Shell | 全局能力 | 保留 |
| `role_surface` | App Shell | 角色落点 | 保留 |
| `workspace_home` | Page Scene（workspace） | 已是页面编排载荷 | 保留 |
| `page_contracts` | Page Scene | 页面级文案/节区编排 | 保留 |
| `scene_ready_contract_v1` | Scene-ready | 场景可渲染契约 | 主消费入口 |
| `scene_governance_v1` | App Shell/Governance | 治理与诊断 | 壳层消费 |
| `scenes` | 混层（历史遗留） | 旧 scene 行数据，含 profile 与 target 混合 | 逐步降级为内部字段 |
| `scene_version/schema_version/scene_channel` | App Shell Meta | 版本控制 | 保留 |

## Base Contract / App Shell / Scene-ready 雏形识别

- Base Contract（输入层）：`scenes[*].ui_base_contract`（服务端内部绑定，不再下发前端）。
- App Shell：`nav/default_route/capabilities/role_surface`。
- Scene-ready 雏形：`scene_ready_contract_v1.scenes[*].{blocks/actions/search_surface/...}`。

## 混层问题与迁移要求

- 混层字段：`scenes[*].list_profile`、`scenes[*].filters`、`scenes[*].access` 与 `scene_ready` 并存。
- 必须迁移出前端直接消费：
  - `ui.contract.views.*`
  - `ui.contract.search`
  - `ui.contract.permissions`
  - `scenes[*].list_profile`（改为 `scene_ready` 导出结果）

