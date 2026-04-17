# Payment Linkage Fact Screen v1

## Scope
- Database: `sc_demo`
- Mode: read-only screen
- Target: imported `payment.request` company and contract linkage completeness.
- No payment, ledger, contract, settlement, accounting, or workflow records were mutated.

## Architecture Decision
- Layer Target: Payment business-fact linkage screen
- Backend sub-layer: business-fact layer
- Reason: `company_id` and `contract_id` are backend-owned business facts and must be recovered from deterministic source facts before frontend or scene behavior is considered.

## Base Facts
- Payment requests: 30102
- Missing `company_id`: 30102
- Missing `contract_id`: 28299
- Missing `project_id`: 0
- Missing `partner_id`: 0
- Already linked to contract: 1803

## Source Manifest Evidence
- Pay manifest loadable rows: 12284
- Pay rows with explicit contract external id: 0
- Pay rows with empty contract reference: 12284
- Receive manifest loadable rows: 5355
- Receive rows with explicit contract external id: 1803
- Receive rows with unresolved legacy contract id: 22
- Receive rows with empty contract reference: 3530

## Deterministic Link Rules

### Rule A: Existing Contract -> Company
If `payment_request.contract_id` already exists and the linked contract has `company_id`, then payment `company_id` can be copied from the contract.

Result:
- Candidate company updates: 1803
- Existing linked contracts missing company: 0

### Rule B: Unique Project + Partner + Direction Contract
If a payment request has no `contract_id`, use:

- payment `type=pay` -> contract `type=in`
- payment `type=receive` -> contract `type=out`
- same `project_id`
- same `partner_id`
- exactly one matching contract

Result:
- Missing-contract unique candidates: 10305
- Company derivable from those unique candidates: 10305

### Rejected Rules
- Do not infer contract by amount similarity.
- Do not infer contract by name/text similarity.
- Do not choose among multiple matching contracts.
- Do not use project company as a fallback because linked projects currently have no company.

## Candidate Classification

| Class | Count | Decision |
| --- | ---: | --- |
| Existing contract can provide company | 1803 | deterministic write candidate |
| Missing contract has unique project/partner/direction contract | 10305 | deterministic write candidate |
| Missing contract has multiple candidates | 6746 | stop, needs stronger source fact |
| Missing contract has no candidate | 11248 | stop, no deterministic contract fact |

## State Split

| State | Total | Unique Candidate | Ambiguous | No Candidate |
| --- | ---: | ---: | ---: | ---: |
| `done / validated` | 12194 | 4638 | 3185 | 4371 |
| `draft / no` | 17908 | 5667 | 3561 | 6877 |

## Write Recommendation

Open a dedicated high-risk write batch for deterministic candidates only:

- update `company_id` for 1803 records from existing linked contracts
- update `contract_id` and `company_id` for 10305 records from the unique candidate rule
- total company updates expected: 12108
- total contract updates expected: 10305
- do not touch the 6746 ambiguous records
- do not touch the 11248 no-candidate records
- do not touch settlement or accounting records
- produce rollback snapshot before write

## Result
PASS. Deterministic payment linkage write batch is eligible.
