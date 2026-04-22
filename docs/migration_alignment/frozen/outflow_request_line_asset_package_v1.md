# Outflow Request Line Asset Package v1

Status: frozen checkpoint

## Scope

This checkpoint materializes legacy `C_ZFSQGL_CB` outflow request line facts as
a replayable repository asset package for `payment.request.line`.

This batch does not import the XML into any Odoo database.

## Result

- asset package: `outflow_request_line_sc_v1`
- source table: `C_ZFSQGL_CB`
- target model: `payment.request.line`
- raw rows: `17413`
- loadable records: `15917`
- blocked records: `1496`
- DB writes: `0`
- Odoo shell: `false`

## Assets

- XML: `migration_assets/20_business/outflow_request_line/outflow_request_line_v1.xml`
- external id manifest: `migration_assets/manifest/outflow_request_line_external_id_manifest_v1.json`
- validation manifest: `migration_assets/manifest/outflow_request_line_validation_manifest_v1.json`
- asset manifest: `migration_assets/manifest/outflow_request_line_asset_manifest_v1.json`

## Business Boundary

Included:

- stable legacy line identity
- parent outflow request anchor
- positive line amount
- optional supplier contract anchor when it resolves
- legacy trace fields for paid-before, remaining, and current-pay amounts

Excluded:

- payment ledger truth
- settlement truth
- accounting truth
- workflow state claims

The line package depends on `outflow_request_sc_v1` and
`supplier_contract_sc_v1`. It must not be replayed before its parent request
anchors exist.

## Verification

- package generator: `PASS`
- package verifier: `PASS`
- migration asset catalog verifier: `PASS`
- migration asset bus verify-only: `PASS`
