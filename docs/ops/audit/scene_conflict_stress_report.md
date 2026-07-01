# Scene Conflict Stress Report

- dry_run_conflicts_count: 1
- import_conflicts_count: 1
- auto_degrade_triggered: False
- post_channel: stable
- rollback_ok: False
- error_count: 0
- warning_count: 5

## Errors

- none

## Warnings

- exported package has insufficient scenes; fallback to runtime system.init scenes
- scene.package.dry_run_import unavailable; fallback to synthetic conflict signal
- scene.package.import(rename_on_conflict) unavailable in current role
- auto_degrade not triggered in this environment
- scene.governance.rollback unavailable after conflict stress
