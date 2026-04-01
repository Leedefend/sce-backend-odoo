# ITER-2026-03-31-403 Report

## Summary

- Converted the confirmed customer rules into a structured enterprise draft.
- Split the structure into four layers:
  - enterprise
  - departments
  - enterprise-specific posts
  - system roles
- Added the special treatment rule for `项目部`.

## Changed Files

- `agent_ops/tasks/ITER-2026-03-31-403.yaml`
- `agent_ops/reports/2026-03-31/report.ITER-2026-03-31-403.md`
- `agent_ops/state/task_results/ITER-2026-03-31-403.json`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-31-403.yaml` -> PASS

## Confirmed Enterprise Draft

### 1. Enterprise

- enterprise_name: `四川保盛建设集团有限公司`

### 2. Formal departments

Confirmed as formal system departments:

- `经营部`
- `工程部`
- `财务部`
- `行政部`
- `成控部`
- `项目部`

Excluded from formal department set:

- `公司员工`

Reason:

- this is treated as a generic employee bucket, not a formal business
  department

### 3. Enterprise-specific posts

Confirmed as post-level entities rather than departments:

- `董事长`
- `总经理`
- `副总经理`
- `项目负责人`
- `临时项目负责人`
- `财务经理`
- `财务助理`

Normalization rule:

- `董事长1` -> `董事长`

### 4. System roles

Confirmed as system-role layer rather than enterprise post layer:

- `管理员角色`
- `通用角色`

Reason:

- these are system-side permission labels
- they should not be treated as enterprise org posts

## Special Project Department Rule

`项目部` should remain a formal department in the system.

The confirmed handling rule is:

- some personnel belong only to `项目部`
- some scenarios require project-department personnel to be accounted for
  independently

This means `项目部` is not only an organizational placeholder. It must be
treated as a real department node with possible independent accounting or
project-oriented ownership semantics.

Current implication for later system mapping:

- `项目部` must be retained in the organization tree
- it must support personnel assignment
- later iterations should allow project-linked members to remain under
  `项目部` without forcing reassignment into another functional department

## Recommended Structured Output For Next Mapping Step

### Department table draft

- `经营部`
- `工程部`
- `财务部`
- `行政部`
- `成控部`
- `项目部`

### Post table draft

- `董事长`
- `总经理`
- `副总经理`
- `项目负责人`
- `临时项目负责人`
- `财务经理`
- `财务助理`

### System role table draft

- `管理员角色`
- `通用角色`

### Explicit exclusions

- `公司员工`
  - keep as employee bucket / generic membership label
  - do not import as department

## Main Conclusion

The customer structure can now be described clearly as:

- one enterprise
- six formal departments
- seven enterprise-specific posts
- two system roles
- one special rule:
  - `项目部` stays as a formal department and may later require independent
    project-side accounting treatment

This is sufficient to start the next data-mapping pass without re-reading the
original workbook semantics.

## Risk Analysis

- Risk remained low because this batch was audit-only.
- No module implementation was changed.
- The main residual unknown is not structure any more, but user-to-department
  and user-to-post mapping at record level.

## Rollback

- `git restore agent_ops/tasks/ITER-2026-03-31-403.yaml`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`
- `git restore agent_ops/reports/2026-03-31/report.ITER-2026-03-31-403.md`
- `git restore agent_ops/state/task_results/ITER-2026-03-31-403.json`

## Next Suggestion

- Next, map user records into:
  - department
  - post
  - system role
- especially identify which users are pure `项目部` members and which users also
  belong to functional departments.
