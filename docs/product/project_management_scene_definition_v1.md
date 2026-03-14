# Project Management Scene Definition v1.1

## 1. Scene Identity
- Scene key: `project.management`
- Page key: `project.management.dashboard`
- Product label: 项目驾驶舱

## 2. User and Goal
- Core users:
  - 项目经理（PM）
  - 分管领导（executive/read focus）
  - 项目经营/财务协同角色（capability-pruned）
- Product goal:
  - 状态判断 + 动作入口 + 风险识别

## 3. Zone and Block Semantics
- `zone.header` -> `block.project.header`
- `zone.metrics` -> `block.project.metrics`
- `zone.progress` -> `block.project.progress`
- `zone.contract` -> `block.project.contract`
- `zone.cost` -> `block.project.cost`
- `zone.finance` -> `block.project.finance`
- `zone.risk` -> `block.project.risk`

## 4. Route Semantics
- Primary route context protocol:
  - `/s/project.management?project_id=<id>`
- Route layer behavior:
  - resolve scene entry
  - extract and forward `project_id`
  - do not perform business aggregation

## 5. Context Semantics
- Fallback resolution order:
  1. route query `project_id`
  2. action/context payload `project_id`
  3. user default/current project resolver
  4. stable empty-state dashboard response

## 6. v1 Scope
- Included:
  - scene/page/zone/block orchestration
  - stable block contracts for v1 block types
  - project_id-aware dashboard aggregation
- Excluded:
  - frontend page refactor
  - workflow redesign
  - model schema migration

## 7. Action Entry Strategy
- v1 strategy:
  - use block-level quick actions in header / finance / risk blocks
  - standalone `next-actions` block can be introduced in v1.1+

## 8. Data Contract Principle
- Every block must return a stable typed payload.
- Backend owns block payload semantics and visibility state.
- Frontend must not infer business fields or permission logic.
- Empty/error/permission-denied states must be representable in block contract.
