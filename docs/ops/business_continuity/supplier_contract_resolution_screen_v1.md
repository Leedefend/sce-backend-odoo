# Supplier Contract Resolution Screen v1

## Scope

- Database: `sc_demo`
- Mode: read-only screen
- Target: imported payment request lines with a single unresolved
  `legacy_supplier_contract_id`
- No payment, contract, settlement, ledger, account, ACL, manifest, frontend, or
  migration records were changed.

## Architecture Decision

- Layer Target: Business Fact Screening
- Backend sub-layer: business-fact layer
- Reason: resolving a legacy supplier contract ID into a target
  `construction.contract` is business-fact evidence. It must be screened before
  any contract linkage replay.

## Input Population

From `legacy_payment_basis_evidence_screen_v1`:

- payment requests with a single unresolved `legacy_supplier_contract_id`: `1731`
- unique old supplier contract IDs in that slice: `1556`
- state split:
  - `done`: `1719`
  - `draft`: `12`

## Target DB Resolution

Rule:

```text
construction.contract.legacy_contract_id == payment.request.line.legacy_supplier_contract_id
```

Result:

| Classification | Payment Requests |
| --- | ---: |
| Target contract exact match and compatible | 0 |
| Target contract missing | 1731 |
| Target contract duplicate | 0 |

There are also no matching `ir.model.data` entries under:

```text
migration_assets.legacy_supplier_contract_sc_<legacy_supplier_contract_id>
```

## Manifest Resolution

Compared the `1556` unique old supplier contract IDs against:

```text
migration_assets/manifest/supplier_contract_external_id_manifest_v1.json
```

Result:

| Classification | Unique IDs | Payment refs |
| --- | ---: | ---: |
| Manifest loadable match | 0 | 0 |
| Manifest blocked match | 0 | 0 |
| Missing from manifest | 1556 | 1731 |

## Interpretation

The `1731` records are not currently resolvable by the target database and are
not covered by the existing supplier contract asset manifest.

This is not a simple module-upgrade or asset-load gap. The source
`legacy_supplier_contract_id` values on these payment lines appear to point to a
supplier-contract population outside the already generated
`supplier_contract_sc_v1` manifest.

## Decision

Stop before write.

Do not update parent `payment.request.contract_id` for these `1731` rows under
the current evidence.

## Next Required Screen

Open a residual legacy contract-source screen for these old IDs:

- check whether the IDs exist in `T_GYSHT_INFO`
- check whether they instead belong to another supplier/purchase contract table
  such as residual `T_CGHT_INFO`
- check whether they are historical deleted/blocked contracts
- only if an exact target `construction.contract` can be created or resolved
  with project, partner, and direction compatibility should a later high-risk
  replay be considered

## Current Write Eligibility

Eligible for a future dedicated write batch remains limited to previously
resolved deterministic candidates:

- outflow request with exact-one resolved line `contract_id`: `2744`
- actual outflow whose source request has exact-one line contract: `2715`
- actual outflow whose source request already has `contract_id`: `28`

The `1731` unresolved supplier-contract-ID records are not write-eligible yet.
