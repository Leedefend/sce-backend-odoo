# Contract Runtime Surface Classification Screen v1

## Screen target
- 对象：`CRG-001/002/003`
- 问题：`can_create/can_edit/page_status` 在多条运行时抓取路径均未命中，需先判定字段应归属哪个 contract surface。

## Evidence base
- 前端消费来源（不是 `page.contract` 直接字段）：
  - `frontend/apps/web/src/pages/ContractFormPage.vue:406`
  - `frontend/apps/web/src/pages/ContractFormPage.vue:407`
  - `frontend/apps/web/src/pages/ContractFormPage.vue:422`
  - `frontend/apps/web/src/pages/ContractFormPage.vue:498`
  - `frontend/apps/web/src/pages/ContractFormPage.vue:499`
- 已完成抓取结果：
  - `docs/ops/contract_runtime_extended_capture_report_v1.md`
  - `docs/ops/contract_runtime_dedicated_capture_report_v1.md`

## Classification result
| Gap | Field | Classified owner surface | Rationale |
|---|---|---|---|
| CRG-001 | `can_create` | `ui.contract` payload extension: `scene_contract_v1.permissions` | 前端读取路径明确来自 `contract.scene_contract_v1.permissions.can_create`，不是 `permissions.effective.rights.create`。 |
| CRG-002 | `can_edit` | `ui.contract` payload extension: `scene_contract_v1.permissions` | 同上，前端写入门禁读取 `can_edit`。 |
| CRG-003 | `runtime_page_status/page_status` | `ui.contract` payload extension: `scene_contract_v1.diagnostics.consumer_runtime` | 前端读取 `scene_contract_v1.diagnostics.consumer_runtime.runtime_page_status/page_status`。 |

## Screen judgment
- 结论：`classification resolved`
- 判定：CRG-001/002/003 不属于当前“model-surface 基础冻结字段”；其正确归属是 **scene runtime extension surface**（挂载于 `ui.contract` 的 `scene_contract_v1` 分支）。
- 当前零命中的根因更可能是：当前样本环境未供应 `scene_contract_v1` 分支，而非字段本体应存在于 `page.contract/system.init` 根层。

## Next executable low-risk step
- 启动文档修订批次（no-code）：
  1. 将 `contract_freeze_surface_v1.md` 按 `model-surface` / `scene-runtime-extension-surface` 分层。
  2. 将 CRG-001/002/003 从“通用 runtime 冻结必选”改为“scene runtime extension 冻结项（条件性）”。
  3. 在 `contract_runtime_gap_list_v1.md` 中把 CRG-001/002/003 状态从“capture missing”改为“surface-conditional pending env supply”。
