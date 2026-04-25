## Summary

- Preserves provider-supplied `action_xmlid` / `menu_xmlid` when reconciling scene targets with registry rows.
- Prevents stale registry `action_id` / `menu_id` values from overwriting recovered XMLID identity.
- Adds a regression test covering stale registry numeric target drift.

## Architecture Impact

- Platform Layer change scoped to scene provider target reconciliation.
- No changes to public intent names, startup chain, route semantics, or frontend consumers.
- Keeps XMLID as the stable cross-database identity source when provider recovery has supplied it.

## Layer Target

- Platform Layer: `addons/smart_core`

## Affected Modules

- `addons/smart_core/core/scene_provider.py`
- `addons/smart_core/tests/test_scene_provider_target_identity_merge.py`

## Reason

Fix review finding P1: provider target identity was recovered and hydrated, then immediately discarded by a later registry target overwrite when registry rows still carried stale numeric IDs.

## Verification

```bash
python3 addons/smart_core/tests/test_scene_provider_target_identity_merge.py
```

Result:

```text
Ran 2 tests in 0.001s
OK
```

## Commit

- `adf01925 fix(scene): preserve provider target identity`
