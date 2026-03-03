# UI Convergence v0.1 Page Intents

## Scope
- Branch: `feat/ui-user-centric-convergence-v0_1`
- Goal: user-first convergence without backend contract changes.

## Page Intents
- Workbench (`HomeView`): 优先处理风险/审批，掌控经营状态。
- My Work (`MyWorkView`): 聚合待办并提供可执行入口。
- Project Detail (`RecordView`): 判断项目是否可控，锁定下一步动作。
- Risk Cockpit / Risk List (`ActionView` risk surfaces): 发现高风险并完成分派/关闭/审批闭环。
- Contracts (`ActionView` contract surfaces): 掌控合同执行、付款与变更风险。
- Cost Ledger (`ActionView` cost surfaces): 判断是否超支、锁定超支来源与处置动作。

## Code Anchors
- `frontend/apps/web/src/views/HomeView.vue` has `Page intent` comment.
- `frontend/apps/web/src/views/MyWorkView.vue` has `Page intent` comment.
- `frontend/apps/web/src/views/RecordView.vue` has `Page intent` comment.
- `frontend/apps/web/src/views/ActionView.vue` has `Page intent` comment for list/action surfaces.
