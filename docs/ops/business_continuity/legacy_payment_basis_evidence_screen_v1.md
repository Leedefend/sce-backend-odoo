# Legacy Payment Basis Evidence Screen v1

## Scope

- Database: `sc_demo`
- Mode: read-only legacy evidence screen
- Target: remaining `payment.request` records with empty `contract_id`
- No payment, contract, settlement, ledger, account, ACL, manifest, frontend, or
  migration records were changed.

## Architecture Decision

- Layer Target: Business Fact Screening
- Backend sub-layer: business-fact layer
- Reason: whether a payment is contract-basis or enterprise daily expense is a
  business fact from the old system. It must be classified before any replay or
  write batch.

## Source Evidence

### Existing Migration Screens

- `C_ZFSQGL` outflow request:
  - raw rows: `13646`
  - loadable candidates: `12284`
  - source contract field: `f_GYSHTID`
  - contract reference is explicitly optional in the asset generator.
- `C_ZFSQGL_CB` outflow request lines:
  - raw rows: `17413`
  - loadable line facts: `15917`
  - contract evidence fields: `legacy_supplier_contract_id`,
    `source_contract_no`, and resolved line `contract_id`.
- `T_FK_Supplier` actual outflow:
  - raw rows: `13629`
  - loadable candidates: `12463`
  - `f_HTID` / supplier-contract presence for loadable rows: `0`
  - source request anchor `f_ZFSQGLId` is optional.

Interpretation:

The old system does not make every payment a direct contract payment. Actual
outflow facts can exist without a supplier contract and may only refer to an
outflow request. Some outflow requests and lines carry contract evidence; others
are valid non-contract spending or lack deterministic contract evidence.

## Remaining Missing-Contract Population

| Source class | Count |
| --- | ---: |
| `legacy_actual_outflow_sc_*` actual outflow | 10377 |
| `legacy_outflow_sc_*` outflow request | 7617 |
| Other external IDs, mostly receipt/income carriers | 2686 |

Total current missing `contract_id` rows remain `17994`, but this includes
non-pay receipt carriers and different legacy source families. These must not be
handled by one contract-link rule.

## Outflow Request Line Evidence

For remaining missing-contract rows:

| Classification | Count | Decision |
| --- | ---: | --- |
| No detail lines | 13111 | do not force contract |
| Detail exact-one linked contract | 2744 | deterministic contract-basis candidate |
| Detail multiple linked contracts | 143 | no parent contract write; keep line-level evidence |
| Detail single legacy contract ID unresolved | 1731 | needs supplier-contract asset/resolution screen |
| Detail multiple legacy IDs | 228 | no parent contract write |
| Detail without contract evidence | 37 | non-contract / insufficient evidence |

Line type evidence:

| Source line type | Rows |
| --- | ---: |
| 发票 | 5369 |
| 供货合同 | 2250 |
| 合同 | 843 |
| 扣款 | 40 |
| 分包合同 | 2 |
| 租赁合同 | 1 |

## Actual Outflow Through Source Request

Actual outflow source table `T_FK_Supplier` does not directly carry supplier
contract evidence for loadable rows. The only safe path is:

```text
actual outflow -> source outflow request -> request line contract evidence
```

Classification for missing-contract actual outflow rows:

| Classification | Count | Decision |
| --- | ---: | --- |
| Source request line exact-one contract | 2715 | deterministic inherited contract-basis candidate |
| Source request already has contract | 28 | deterministic inherited contract-basis candidate |
| Source request line multiple contracts | 146 | no parent contract write |
| Source request has no contract evidence | 2009 | daily/non-contract or insufficient contract evidence |
| Request ref but loaded request not found | 2621 | investigate source mapping before write |
| Request unresolved | 112 | no write |
| Request empty | 60 | no write |

## Outflow Request Header Evidence

For missing-contract outflow request rows:

| Classification | Count | Decision |
| --- | ---: | --- |
| Header contract empty, no detail | 2734 | daily/non-contract or insufficient evidence |
| Detail exact-one contract | 2744 | deterministic contract-basis candidate |
| Detail no contract and header empty | 1996 | daily/non-contract or insufficient evidence |
| Detail multiple contracts | 143 | no parent contract write |

## Receipt/Income Carriers

`2686` missing-contract rows are under other external-id families, mostly
`legacy_receipt_sc_*`. These are not payment outflow contract-link candidates
and must be handled under receipt/income continuity rules.

## Decision

The owner's business judgment is confirmed by legacy evidence:

- Some payments are contract-basis and have deterministic contract evidence.
- Some payments are enterprise daily expenses or non-contract spending.
- Actual outflow rows do not directly require a supplier contract in the old
  source.
- A missing `contract_id` is not automatically a defect.

## Eligible Next Write Rules

A future high-risk write/replay batch may be considered only for deterministic
contract-basis candidates:

- outflow request with exact-one resolved line `contract_id`: `2744`
- actual outflow whose source request has exact-one line contract: `2715`
- actual outflow whose source request already has `contract_id`: `28`

Do not write parent `contract_id` when:

- the source line has multiple contracts
- only unresolved legacy supplier contract IDs exist
- no detail/header contract evidence exists
- the row belongs to receipt/income carriers

## Next Required Screen

Before writing the `1731` rows with a single unresolved
`legacy_supplier_contract_id`, screen supplier-contract asset/resolution
coverage:

- whether the old supplier contract exists in `T_GYSHT_INFO`
- whether it is imported as `construction.contract`
- whether project/partner/direction match the payment request
- whether exactly one target contract can be resolved
