# Scene Contract 结构规范 v1

## 1. 文档目标

本文档定义 `Scene Contract` 的字段级结构、约束与兼容规则，作为：

- 场景编排层输出标准
- 前端通用渲染唯一输入标准
- 合约验证（shape/snapshot）基线

本规范与 `docs/architecture/scene_orchestration_layer_design_v1.md` 配套使用。

## 2. 设计边界

- 仅定义契约结构，不定义业务规则算法。
- 仅定义输出格式，不约束前端视觉风格。
- 编排层可扩展字段，但不得破坏本规范顶层稳定性。

## 3. 顶层结构

`Scene Contract` 顶层对象必须包含以下键：

```json
{
  "contract_version": "v1",
  "scene": {},
  "page": {},
  "nav_ref": {},
  "zones": [],
  "blocks": {},
  "actions": {},
  "permissions": {},
  "record": {},
  "extensions": {},
  "diagnostics": {}
}
```

## 4. 顶层字段定义

### 4.1 `contract_version`

- 类型：`string`
- 必填：是
- 约束：`v1`

### 4.2 `scene`

- 类型：`object`
- 必填：是
- 字段：
  - `scene_key: string`（必填）
  - `scene_type: string`（必填，示例：`detail`/`list`/`kanban`/`workspace`）
  - `page_goal: string`（可选）
  - `interaction_mode: string`（可选）
  - `layout_mode: string`（可选）
  - `scene_version: string`（可选）

### 4.3 `page`

- 类型：`object`
- 必填：是
- 字段：
  - `model: string`（必填）
  - `record_id: number | null`（可选）
  - `view_type: string`（必填）
  - `title_field: string`（可选）
  - `subtitle_fields: string[]`（可选）
  - `page_status: string`（可选，示例：`ready`/`empty`/`readonly`）

### 4.4 `nav_ref`

- 类型：`object`
- 必填：是（可为空对象）
- 作用：页面契约与壳层导航联动的轻量引用，不承载完整导航树。
- 字段：
  - `active_scene_key: string`（可选）
  - `active_menu_id: number | null`（可选）
  - `active_menu_key: string`（可选）
- 约束：禁止在 `nav_ref` 内输出完整导航树。

### 4.5 `zones`

- 类型：`array`
- 必填：是
- 元素结构：
  - `key: string`（必填，必须来自平台标准 zone）
  - `title: string`（可选）
  - `priority: number`（可选，越大越靠前）
  - `visible: boolean`（可选，默认 `true`）
  - `block_keys: string[]`（必填，对应 `blocks` 中的 key）

### 4.6 `blocks`

- 类型：`object`
- 必填：是
- 约束：以 block_key 为字典键。
- 单个 block 结构：
  - `key: string`（必填）
  - `type: string`（必填，必须映射平台标准 block type）
  - `title: string`（可选）
  - `priority: number`（可选）
  - `visible: boolean`（可选）
  - `state: string`（可选，示例：`ready`/`empty`/`error`）
  - `data_source: string`（可选）
  - `payload: object`（可选）
  - `actions: string[]`（可选，引用 `actions`）

### 4.7 `actions`

- 类型：`object`
- 必填：是
- 字段：
  - `primary_actions: ActionItem[]`
  - `secondary_actions: ActionItem[]`
  - `contextual_actions: ActionItem[]`
  - `danger_actions: ActionItem[]`
  - `recommended_actions: ActionItem[]`

`ActionItem` 结构：

- `key: string`（必填）
- `label: string`（必填）
- `intent: string`（必填）
- `enabled: boolean`（可选，默认 `true`）
- `reason: string`（可选，禁用原因）
- `params: object`（可选）

### 4.8 `permissions`

- 类型：`object`
- 必填：是
- 字段：
  - `can_read: boolean`（必填）
  - `can_edit: boolean`（必填）
  - `can_create: boolean`（必填）
  - `can_delete: boolean`（必填）
  - `disabled_actions: object`（可选，`action_key -> reason`）
  - `record_state_summary: object`（可选）

### 4.9 `record`

- 类型：`object`
- 必填：是
- 字段：
  - `id: number | null`（可选）
  - `data: object`（可选）
  - `summary: object`（可选）
  - `relations: object`（可选）

### 4.10 `extensions`

- 类型：`object`
- 必填：是（可为空对象）
- 字段（建议）：
  - `injected_blocks: string[]`
  - `injected_actions: string[]`
  - `providers: string[]`

### 4.11 `diagnostics`

- 类型：`object`
- 必填：是（可为空对象）
- 字段（建议）：
  - `trace_id: string`
  - `source_versions: object`
  - `build_pipeline: string[]`
  - `warnings: string[]`

## 5. 平台标准枚举（v1）

### 5.1 标准 zone

- `header_zone`
- `summary_zone`
- `detail_zone`
- `relation_zone`
- `action_zone`
- `collaboration_zone`
- `insight_zone`
- `attachment_zone`

### 5.2 标准 block type

- `title_block`
- `status_block`
- `action_bar_block`
- `stat_button_block`
- `field_group_block`
- `notebook_block`
- `relation_table_block`
- `relation_card_block`
- `relation_tab_block`
- `chatter_block`
- `activity_block`
- `attachment_block`
- `timeline_block`
- `ribbon_block`
- `risk_alert_block`
- `ai_recommendation_block`
- `next_action_block`
- `summary_metrics_block`

## 6. 兼容策略

### 6.1 向前兼容

- 新增字段必须为可选。
- 已有字段语义不得破坏。

### 6.2 版本升级

- 破坏性变更必须升级 `contract_version`。
- 同时提供迁移说明与验证脚本。

### 6.3 legacy 协议

- 允许并行保留 legacy contract。
- 前端默认仅消费 `Scene Contract v1` 主协议。

## 7. 校验要求

必须进入自动化校验链：

- `shape guard`：顶层和关键节点结构校验。
- `snapshot guard`：关键 scene 输出快照比对。
- `sample regression`：代表性 scene 回归。

## 8. 前后端责任边界

- 后端：输出完整且可执行的 `Scene Contract`。
- 前端：仅按 contract 渲染与交互，不进行场景意图猜测。

## 9. 示例（简化）

```json
{
  "contract_version": "v1",
  "scene": {
    "scene_key": "project.overview.manager",
    "scene_type": "detail",
    "layout_mode": "summary_detail_dual_column"
  },
  "page": {
    "model": "project.project",
    "record_id": 20,
    "view_type": "form"
  },
  "zones": [
    {"key": "summary_zone", "priority": 100, "block_keys": ["project_summary"]},
    {"key": "insight_zone", "priority": 90, "block_keys": ["project_risk"]}
  ],
  "blocks": {
    "project_summary": {
      "key": "project_summary",
      "type": "summary_metrics_block",
      "title": "项目摘要",
      "state": "ready"
    },
    "project_risk": {
      "key": "project_risk",
      "type": "risk_alert_block",
      "title": "风险提醒",
      "state": "ready"
    }
  },
  "actions": {
    "primary_actions": [{"key": "open_task", "label": "查看任务", "intent": "ui.contract"}],
    "secondary_actions": [],
    "contextual_actions": [],
    "danger_actions": [],
    "recommended_actions": []
  },
  "permissions": {
    "can_read": true,
    "can_edit": true,
    "can_create": false,
    "can_delete": false
  },
  "record": {"id": 20, "summary": {"name": "示例项目"}},
  "extensions": {},
  "diagnostics": {}
}
```

## 10. 一句话结论

`Scene Contract v1` 是前端唯一可消费页面协议；后端编排层必须输出稳定结构，前端不得再基于模型特判重组页面语义。
