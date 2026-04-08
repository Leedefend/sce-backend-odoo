# Contract Runtime Remediation · Extended Capture Report v1

## Scope
- base_url: `http://localhost:8069`
- db_name: `sc_demo`
- sample_count: `52`
- surfaces: `action_open_edit, model_form_edit, payment_available_actions`

## Capture result
- response_ok: `49/52`
- `action_open_edit` samples: `24`
- `model_form_edit` samples: `24`
- `payment_available_actions` samples: `4`

## CRG coverage progress
- `CRG-001 can_create` hit count: `0`
- `CRG-002 can_edit` hit count: `0`
- `CRG-003 page_status` hit count: `0`
- `CRG-004 payment action surface` hit count: `1`

## Observation
- 通过扩展抓取已补到 payment action surface 运行态证据（CRG-004 命中）。
- runtime 字段（can_create/can_edit/page_status）在 `model_form_edit` 与 `action_open_edit` 仍未出现。
- 该结果说明需继续补抓非 `ui.contract op=model/action_open` 的 runtime 专用路径。
