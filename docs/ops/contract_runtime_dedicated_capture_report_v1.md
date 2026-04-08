# Contract Runtime Remediation · Dedicated Capture Report v1

## Scope
- base_url: `http://localhost:8069`
- db_name: `sc_demo`
- sample_count: `40`
- surfaces: `page.contract, system.init`

## Capture result
- response_ok: `12/40`
- `page.contract` samples: `32`
- `system.init` samples: `8`

## CRG-001/002/003 progress
- `CRG-001 can_create` hits: `0`
- `CRG-002 can_edit` hits: `0`
- `CRG-003 page_status` hits: `0`

## Assessment
- 在 `system.init` + `page.contract` 专用路径下，未观测到 CRG-001/002/003 目标字段。
- 这说明当前运行时入口与冻结字段定义可能存在“表面口径不一致”。
- 进入下一步前需先做 screen：明确这些字段应属于哪个 contract surface，再决定补抓还是调整冻结分层。
