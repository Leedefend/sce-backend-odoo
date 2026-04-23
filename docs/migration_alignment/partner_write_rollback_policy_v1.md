# Partner Write Rollback Policy v1

Iteration: `ITER-2026-04-13-1852`

## Rollback Target

Rollback objects must be locked only by:

- `legacy_partner_source`
- `legacy_partner_id`

For the strong-evidence partner slice:

- `legacy_partner_source = cooperat_company`
- `legacy_partner_id = T_Base_CooperatCompany.Id`

Rollback must not use name, credit code, tax number, company text, or contract text as a delete key.

## Required Rollback Artifacts

Any future write batch must produce a rollback target list containing:

- run id
- Odoo `res.partner.id`
- `legacy_partner_source`
- `legacy_partner_id`
- partner name
- `legacy_source_evidence`
- created timestamp if available
- write action result

## Rollback Dry-Run Requirements

Before any real delete:

1. Run a rollback dry-run script.
2. Confirm every target legacy identity resolves to exactly one `res.partner`.
3. Confirm there are no duplicate legacy identity matches.
4. Confirm no out-of-scope partner is matched.
5. Confirm all targets were created by the sample write batch.
6. Emit machine-readable result JSON.
7. Emit a human-readable rollback dry-run report.

## Real Rollback Requirements

Real rollback is not authorized by this document.

A future rollback execution batch must have:

- explicit task contract,
- explicit user authorization,
- exact rollback target list,
- rollback dry-run `PASS`,
- post-delete readonly verification.

## No-Delete Rule

No partner delete is allowed in this or the next planning batch.

Deleting by partner name is forbidden because the old system has duplicate and cross-source names.

Deleting by credit code or tax number is forbidden for this slice because coverage is too sparse.

## Decision

The rollback design is feasible if and only if the write batch stores `legacy_partner_source + legacy_partner_id` on every created row.
