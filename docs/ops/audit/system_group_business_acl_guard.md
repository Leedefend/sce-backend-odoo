# System Group Business ACL Guard

- status: PASS
- scanned_file_count: 5
- scanned_row_count: 198
- violation_count: 0

## Rule

- Forbid direct `base.group_system` ACL on `model_sc_*` business models.
- Use SC capability groups as ACL bindings, then map system role via implied groups.
