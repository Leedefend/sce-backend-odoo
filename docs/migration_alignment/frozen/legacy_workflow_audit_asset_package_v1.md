# Legacy Workflow Audit Asset Package v1

Status: `PASS`

## Scope

This batch generated replayable XML assets for legacy approval history from
`S_Execute_Approval` into the neutral historical audit carrier:

```text
sc.legacy.workflow.audit
```

It does not generate `tier.review`, `tier.definition`, runtime workflow
instances, workitems, or logs.

## Result

| Metric | Value |
|---|---:|
| source rows | 163245 |
| XML audit records | 79702 |
| blocked rows | 83543 |
| matched target records | 29932 |
| DB writes | 0 |
| Odoo shell | false |

## Lane Coverage

| Target lane | Rows |
|---|---:|
| outflow_request | 45693 |
| supplier_contract | 13281 |
| receipt | 8556 |
| actual_outflow | 6088 |
| contract | 6084 |

## Generated Assets

```text
migration_assets/30_relation/legacy_workflow_audit/legacy_workflow_audit_v1.xml
migration_assets/manifest/legacy_workflow_audit_external_id_manifest_v1.json
migration_assets/manifest/legacy_workflow_audit_validation_manifest_v1.json
migration_assets/manifest/legacy_workflow_audit_asset_manifest_v1.json
```

Catalog registration:

```text
legacy_workflow_audit_sc_v1
```

The migration asset bus now verifies `18` packages.

## Boundary

Included:

- historical approval actor id/name
- old approval timestamp and receive timestamp
- old approval note
- old source status and back type as raw facts
- old step/template identifiers and labels
- target model and target external id

Excluded:

- `tier.review`
- `tier.definition`
- `sc.workflow.instance`
- `sc.workflow.workitem`
- `sc.workflow.log`
- target business state mutation
- database integer id references

## Verification

Commands passed:

```bash
python3 scripts/migration/legacy_workflow_audit_asset_generator.py --asset-root migration_assets --check
python3 scripts/migration/legacy_workflow_audit_asset_verify.py --asset-root migration_assets --lane legacy_workflow_audit --check
python3 scripts/migration/migration_asset_catalog_verify.py --asset-root migration_assets --catalog migration_assets/manifest/migration_asset_catalog_v1.json --check
python3 scripts/migration/migration_asset_bus.py --verify-only --check
```

## Remaining Blockers

`83543` rows remain blocked because their target business records are not yet
assetized or not yet loadable. They should not be forced into the audit asset
lane until the corresponding business lane exists or is explicitly discarded.

## Next Step

Continue existing business fact assetization by analyzing the blocked approval
rows' target business families. Prioritize lanes that unlock the largest
remaining approval history without weakening the rule that historical approval
facts must anchor to a concrete business document.
