# Semantic Page Contract Shape v1 (Freeze)

## Purpose
冻结 `semantic_page` 的最小稳定结构，作为后端统一契约出口的第一阶段基线。

## Required Top-Level Keys
- `semantic_page.model` (string)
- `semantic_page.view_type` (string)
- `semantic_page.layout` (string)
- `semantic_page.zones` (array)

## Allowed Zone Keys (v1)
- `header_zone`
- `summary_zone`
- `detail_zone`
- `relation_zone`
- `action_zone`
- `collaboration_zone`
- `insight_zone`
- `attachment_zone`

## Allowed Block Types (v1)
- `title_block`
- `status_block`
- `action_bar_block`
- `field_group_block`
- `notebook_block`
- `relation_table_block`
- `relation_card_block`
- `stat_button_block`
- `chatter_block`
- `attachment_block`
- `timeline_block`
- `risk_alert_block`
- `ai_recommendation_block`
- `next_action_block`

## Compatibility Policy
- 非破坏式新增：允许新增可选字段。
- 破坏性变更（删除字段、重命名 zone/block）必须升级版本。
- v1 guard 默认只校验最小必需结构与枚举合法性。
