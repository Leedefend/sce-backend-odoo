# Residual Legacy Contract Source Screen v1

## Scope

- Database: `sc_demo` plus read-only `LegacyDb`
- Mode: read-only screen
- Target: the `1556` legacy supplier contract IDs that are referenced by
  imported payment request lines but are missing from the target
  `construction.contract` records and the current supplier-contract manifest
- No payment, contract, settlement, ledger, account, ACL, manifest, frontend, or
  migration records were changed.

## Architecture Decision

- Layer Target: Business Fact Screening
- Backend sub-layer: business-fact layer
- Reason: whether a legacy ID is a real old contract primary key is business
  truth. It cannot be repaired by frontend rendering or scene orchestration.

## Strict Input

The screen first rebuilt the prior unresolved slice:

| Metric | Count |
| --- | ---: |
| Payment-line single legacy contract IDs before manifest filtering | 1950 |
| Payment requests carrying a single legacy contract ID before manifest filtering | 2224 |
| Supplier-contract manifest IDs | 5301 |
| Strict IDs missing from supplier-contract manifest | 1556 |

This strict set matches the unresolved supplier-contract-ID population from the
previous screen.

## Contract Source Table Resolution

Direct source-table lookup:

| Source table / rule | Unique IDs |
| --- | ---: |
| Input unique IDs | 1556 |
| `T_GYSHT_INFO.Id` direct match | 1 |
| `T_GYSHT_INFO.Id` active-like match | 1 |
| `T_GYSHT_INFO.Id` deleted/scrapped match | 0 |
| `T_CGHT_INFO.Id` direct match | 0 |
| `T_CGHT_INFO.Id` active-like match | 0 |
| `T_CGHT_INFO.Id` deleted match | 0 |
| No direct match in either contract source table | 1555 |

The only direct `T_GYSHT_INFO` match is:

| Legacy ID | Contract No | Document No | Supplier | Amount | Deleted |
| --- | --- | --- | --- | ---: | --- |
| `87b694dc710145058c9334a0158c20be` | `GYSHT-20230510-002` | `PZH2023-39-005-230510（1）` | `雷勤英` | 147812.7000 | 0 |

That row is not enough to promote the whole residual set. It should be handled
later as a narrow manifest-gap case only if project, supplier, amount, and
direction compatibility all pass.

## Where The IDs Actually Appear

The unresolved IDs mostly appear as payment-line relationship values, not as
contract master keys:

| Old field | Rows | Unique IDs |
| --- | ---: | ---: |
| `C_ZFSQGL_CB.GLYWID` | 1880 | 1543 |
| `C_ZFSQGL.f_GYSHTID` | 0 | 0 |
| `T_FK_Supplier.f_HTID` | 0 | 0 |
| `T_FK_Supplier.GLYWID` | 0 | 0 |
| `T_GYSHT_INFO.GLYHTID` | 0 | 0 |
| `T_CGHT_INFO.GLYHTID` | 0 | 0 |

This means the old payment-line `GLYWID` field is not a reliable synonym for
`supplier contract ID` in this residual population.

## Business Evidence Split

Document prefixes from the matched `C_ZFSQGL_CB.GLYWID` rows:

| Prefix | Rows | Unique IDs |
| --- | ---: | ---: |
| `FPJJD` | 1043 | 804 |
| `ZYFPJJD` | 803 | 712 |
| `KKD` | 17 | 17 |
| `ZLHTJX` | 7 | 6 |
| `BZHT` | 6 | 2 |
| `FBHT` | 2 | 1 |
| `GYSHT` | 2 | 1 |

Counterparty and contract-number text:

| Evidence | Rows | Unique IDs |
| --- | ---: | ---: |
| Blank counterparty text | 1018 | 806 |
| Has counterparty text | 862 | 751 |
| Blank contract-number text | 1878 | 1542 |
| Has contract-number text | 2 | 1 |

Only one ID has contract-number text in the line relationship data:

| Legacy ID | Line document | Counterparty text | Contract no text | Line amount | Paid amount |
| --- | --- | --- | --- | ---: | ---: |
| `e03ddff03da54b328b1032f9daad3dc7` | `FBHT-20200930-001` | `四川华亚智优科技有限公司` | `XDXX2020-017-036-0930` | 1000000.0000 | 50000.0000 |

This is still text evidence, not an exact contract source-table key.

## Interpretation

The residual `legacy_supplier_contract_id` values on payment lines are mostly
not old supplier-contract or purchase-contract primary keys.

They are old payment-line business relationship IDs, invoice/payment settlement
document references, or other related-business anchors. Treating them as
`construction.contract.legacy_contract_id` would fabricate contract facts.

## Decision

Stop before write for this residual group.

Do not replay `payment.request.contract_id` from these `1556` unresolved legacy
IDs.

## Business Continuity Impact

This supports the current business rule:

- Payments can continue without a mandatory settlement or contract when the old
  business fact is a daily expense, invoice payment, deduction, or other
  non-contract outflow.
- Contract-basis payments should only be linked when an exact old contract fact
  is already resolved or can be proven by a dedicated, deterministic replay
  rule.

## Replay Eligibility

The residual `1556` ID group is not replay-eligible.

Future write eligibility remains limited to the earlier deterministic
contract-basis candidates:

- outflow request with exact-one resolved line `contract_id`: `2744`
- actual outflow whose source request has exact-one line contract: `2715`
- actual outflow whose source request already has `contract_id`: `28`

The single `T_GYSHT_INFO.Id` direct match and the single line contract-number
text case require a separate narrow screen before any replay decision.
