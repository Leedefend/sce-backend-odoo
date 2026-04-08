# Contract Runtime Verification v1 · Batch A Capture Report

## Runtime target
- base_url: `http://localhost:8069`
- db_name: `sc_demo`
- role mode: `temp_runtime_roles`
- sample count: `48`

## Coverage
- roles: `owner, pm, finance, outsider`
- objects: `project.project, project.task, project.budget, project.cost.ledger, payment.request, sc.settlement.order`
- surfaces: `list, form`

## Batch A result
- response_ok=true: `48/48`
- non-200 responses: `0`
- samples with effective rights: `48/48`
- samples with runtime block: `0/48`

## Role summary
- `finance`: ok `12/12`, rights `12/12`, runtime `0/12`
- `outsider`: ok `12/12`, rights `12/12`, runtime `0/12`
- `owner`: ok `12/12`, rights `12/12`, runtime `0/12`
- `pm`: ok `12/12`, rights `12/12`, runtime `0/12`

## Notes
- 本批次使用临时角色账户（owner/pm/finance/outsider）进行运行态抓取，抓取后已清理临时账号。
- payload 样本已保存到 `docs/ops/contract_runtime_payload_samples_v1.json`，供 Batch B/C 做 freeze/consumer 对比。
