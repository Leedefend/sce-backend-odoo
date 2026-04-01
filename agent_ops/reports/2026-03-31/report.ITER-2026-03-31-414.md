# ITER-2026-03-31-414 Report

## Summary

- Audited the current repository path for customer post attachment and system-role attachment.
- Confirmed that the current repository has a clear persistence path for primary department only.
- Confirmed that the next attachment batch cannot proceed with certainty yet because the post field owner and the workbook system-role mapping target are not closed by repository facts.

## Changed Files

- `agent_ops/tasks/ITER-2026-03-31-414.yaml`
- `agent_ops/reports/2026-03-31/report.ITER-2026-03-31-414.md`
- `agent_ops/state/task_results/ITER-2026-03-31-414.json`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-31-414.yaml` -> PASS

## Repository Facts

### 1. Department attachment path is clear

Observed in:

- `addons/smart_enterprise_base/models/res_users.py`

Facts:

- `res.users` currently exposes:
  - `sc_department_id = fields.Many2one("hr.department", ...)`
  - `sc_manager_user_id = fields.Many2one("res.users", ...)`
- no extra-department persistence exists in the active user model

Conclusion:

- primary department persistence is real and implemented
- additional department persistence is still absent

### 2. Post attachment path is not implemented

Observed in:

- `addons/smart_enterprise_base/models/res_users.py`
- repo-wide search across:
  - `addons/smart_enterprise_base`
  - `addons/smart_construction_custom`
  - `addons/smart_construction_core`

Facts:

- no user-facing post field was found in active models:
  - no `hr.job`
  - no `job_id`
  - no `post_ids`
  - no equivalent custom post field on `res.users`
- the only place where `posts` appears is the README planning/spec text

Conclusion:

- the customer workbook `posts` column currently has no repository-backed persistence owner
- post attachment implementation would require first defining the owning model/field

### 3. System-role attachment is only partially clear

Observed in:

- `addons/smart_construction_custom/security/role_matrix_groups.xml`
- `addons/smart_construction_custom/models/security_policy.py`

Facts:

- real customer-facing role groups already exist:
  - `group_sc_role_owner`
  - `group_sc_role_pm`
  - `group_sc_role_finance`
  - `group_sc_role_executive`
  - `group_sc_role_config_admin`
- `apply_role_matrix()` already writes these groups to demo users by login
- workbook-origin system roles were frozen as:
  - `管理员角色`
  - `通用角色`
- repo facts do not provide an explicit mapping:
  - `管理员角色` -> which exact group set
  - `通用角色` -> which exact group set

Conclusion:

- the repository does contain real group targets
- but the workbook role labels are not yet bound to those targets by a confirmed mapping rule

## Outcome

This audit batch succeeded as an ownership check, but the next implementation
batch is not safe yet.

Closed facts:

- primary department owner is known
- real role groups exist

Still open:

- post persistence owner is missing
- workbook system-role labels are not yet mapped to explicit group targets

## Risk Analysis

- Classification: `PASS_WITH_RISK`
- Risk reason:
  - `post_attachment_owner_unclear`
  - `system_role_group_target_unclear`

This means the next batch must not directly write posts or attach workbook
system roles until those two ownership questions are resolved.

## Rollback

- `git restore agent_ops/tasks/ITER-2026-03-31-414.yaml`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`
- `git restore agent_ops/reports/2026-03-31/report.ITER-2026-03-31-414.md`
- `git restore agent_ops/state/task_results/ITER-2026-03-31-414.json`

## Next Suggestion

- Open a narrow governance batch to define:
  - the owning model/field for customer posts
  - the exact mapping from workbook labels:
    - `管理员角色`
    - `通用角色`
    to existing repository groups
- Only after those mappings are frozen should the bootstrap implementation continue.
