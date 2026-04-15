# Upgrade Warning Cleanup v1

Status: PASS
Date: 2026-04-15

## Scope

This checkpoint cleans actionable warnings observed during
`smart_construction_core` module upgrade after the legacy fact usability batch.

## Warning Disposition

Resolved:

- Project create views emitted Odoo alert accessibility warnings.
  - Fixed by adding `role="status"` to the informational alert blocks in
    `addons/smart_construction_core/views/core/project_views.xml`.
- Odoo reported missing ACL rows for helper models.
  - Added scoped ACL rows in
    `addons/smart_construction_core/security/ir.model.access.csv`.
  - `sc.project.member.staging`: project read, read-only.
  - `sc.contract.recon.summary`: finance read, read-only.
  - `project.quick.create.wizard`: project user wizard access.
- `smart_construction_custom` README triggered docutils unexpected indentation.
  - Normalized the nested list indentation in
    `addons/smart_construction_custom/README.md`.
- `smart_core` startup success messages were logged at warning level.
  - Downgraded the two module-load success messages to info level.

Resolved after explicit authorization:

- `smart_scene` manifest was missing a `license` key.
  - Added explicit `LGPL-3` metadata in
    `addons/smart_scene/__manifest__.py`.
  - Scope was limited to license metadata only.

## Verification

Commands run:

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-15-UPGRADE-WARNING-CLEANUP.yaml`
- CSV duplicate-id and required ACL assertion.
- XML parse assertion for `project_views.xml`.
- `CODEX_NEED_UPGRADE=1 CODEX_MODULES=smart_construction_core make mod.upgrade MODULE=smart_construction_core`

Result:

- Task validation: PASS.
- Static assertions: PASS.
- Module upgrade: PASS.
- Cleared warning classes:
  - alert accessibility warning.
  - missing ACL warning.
  - docutils unexpected indentation warning.
  - smart_core startup success warning logs.
- Remaining warning classes: none detected in the refreshed upgrade log.

Runtime log:

- `.runtime_reports/upgrade_warning_cleanup_v1.log`

## Rollback

Rollback is limited to reverting:

- alert `role` attributes in `project_views.xml`.
- the three additive ACL CSV rows.
- the README indentation normalization.
- the two `smart_core` startup logger level changes.
