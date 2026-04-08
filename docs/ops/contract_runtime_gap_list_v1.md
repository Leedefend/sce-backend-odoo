# Contract Runtime Gap List v1

## Gap baseline

| Gap ID | Field / Surface | Current finding | Impact | Classification |
|---|---|---|---|---|
| CRG-001 | `permissions.can_create` (`scene runtime extension`) | 现有运行时基线（`ui.contract op=model/action_open` + `system.init/page.contract`）未提供 `scene_contract_v1` 扩展分支；screen 已确认字段归属 extension-surface | 在当前 runtime baseline 下不作为根层必现项 | intentional-not-in-surface |
| CRG-002 | `permissions.can_edit` (`scene runtime extension`) | 同 CRG-001 | 同 CRG-001 | intentional-not-in-surface |
| CRG-003 | `runtime_page_status/page_status` (`scene runtime extension`) | 同 CRG-001，字段归属 `scene_contract_v1.diagnostics.consumer_runtime` | 在当前 runtime baseline 下不作为根层必现项 | intentional-not-in-surface |
| CRG-004 | `actions[].allowed/reason_code/execute_*` (`payment/settlement action-surface`) | payment dedicated action surface + settlement intent-ready contract action surface 均已观测（见 `contract_runtime_settlement_action_surface_compare_v1.md`） | 动作面对称证据链成立 | closed |

## Object/role impact notes
- 受影响对象：`payment.request` 与 `sc.settlement.order` 在 action/runtime 维度影响更明显。
- 受影响角色：四角色均受 runtime 字段缺失影响（非角色特例）。
- 角色差异现象主要出现在 rights 值层面，属于预期权限差异，不计为结构漂移。

## Remediation lanes

### Lane A: runtime-surface capture extension
- 扩展抓取目标调整为：仅针对 **`scene_contract_v1` 扩展分支** 进行补抓。
- 验收目标：在 extension-surface 可见样本中观测到 `can_create/can_edit/page_status`。
- 当前状态：`intentional-not-in-surface`（当前 runtime baseline 不暴露该扩展分支；若后续环境启用该分支，可重新开 lane 复核）。

### Lane B: action-surface capture extension (payment/settlement)
- 补抓 `payment.request.available_actions` / 对应 settlement action 面 payload。
- 验收目标：`allowed/reason_code/execute_intent/execute_params` 完整供给并与冻结面一致。
- 进度：`closed`（`ITER-2026-04-07-1316` 已完成 payment vs settlement 对称证据收口）。

### Lane C: freeze surface stratification
- 将冻结面拆分为：
  - `model-surface freeze`（已运行态验证）
  - `runtime/action-surface freeze`（待补抓验证）
- 验收目标：避免用单一路径样本对多表面冻结做过度结论。

## Exit criteria
- CRG-001~CRG-003 已在 extension-surface 口径下标注为 `intentional-not-in-surface`。
- CRG-004 已 `closed`。
- `contract_runtime_acceptance_v1.md` 升级为 full-pass（非 partial）。
