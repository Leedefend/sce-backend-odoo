# ITER-2026-04-10-1811 Report

## Batch
- Batch: `FORM-Collaboration-RCA-1`
- Mode: `implement`
- Stage: `business-fact to consumer full-path fix`

## Architecture declaration
- Layer Target: `Backend semantic layer + Frontend contract-consumer runtime`
- Module: `v2 chatter/attachments detection + collaboration visibility gating`
- Module Ownership: `addons/smart_core + frontend/apps/web`
- Kernel or Scenario: `scenario`
- Reason: 全路径核实后确认消息/附件缺失由后端探测口径过窄与前端门控叠加造成。

## Full-path verification
- 业务事实层：`project.project` 原生 form XML 含 `oe_chatter`（运行时核验）。
- 契约层：v2 `_fill_chatter_attachment_surface` 仅识别有限节点，漏判 `oe_chatter` / widget 场景。
- 消费层：`showCollaborationZoneBlock` 仍受 `preferNativeFormSurface` 限制，align 模式下可被拦截。

## Change summary
- 后端：`addons/smart_core/v2/services/ui_contract_service.py`
  - `_fill_chatter_attachment_surface` 增加 layout 节点探测：
    - `attributes.class` 包含 `oe_chatter` / `oe_attachment_box`
    - widget 识别 `mail_thread/mail_activity/mail_followers/many2many_binary/binary`
  - 附件启用条件加入 `has_attachment_node`。
- 前端：`frontend/apps/web/src/pages/ContractFormPage.vue`
  - `semanticHasChatter/semanticHasAttachments` 增加回退：从 `views.form.chatter.enabled` / `views.form.attachments.enabled` 推导。
  - `showCollaborationZoneBlock` 放开 align 模式下的 native 门控，避免误隐藏。

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-10-1811.yaml` → `PASS`
- `rg -n "_fill_chatter_attachment_surface|oe_chatter|many2many_binary|has_attachment_node" addons/smart_core/v2/services/ui_contract_service.py` → `PASS`
- `rg -n "semanticHasChatter|semanticHasAttachments|showCollaborationZoneBlock|allowInAlign" frontend/apps/web/src/pages/ContractFormPage.vue` → `PASS`
- `make restart` → `PASS`
- `make frontend.restart` → `PASS`

## Risk analysis
- 结论：`PASS`
- 风险级别：`medium-low`
- 风险说明：仅恢复协作区语义识别与显示门控，不涉及 ACL/业务事实改动。

## Rollback suggestion
- `git restore addons/smart_core/v2/services/ui_contract_service.py frontend/apps/web/src/pages/ContractFormPage.vue`

## Next suggestion
- 刷新同一页面，确认“协作区：讨论区/附件区”恢复。
- 如需“可点击入口”（消息流、附件列表），进入下一轮实现。
