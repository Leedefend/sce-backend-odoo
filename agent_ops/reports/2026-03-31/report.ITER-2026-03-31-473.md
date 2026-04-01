# ITER-2026-03-31-473

## Summary
- 收窄了两个代表性 action 的可见性，使其与真实写权一致
- 结果为 `PASS`
- `PM` 不再看到无写权的 `payment_request_my`，`finance` 不再看到无写权的 `project_progress_entry`

## Changed Files
- [action_groups_patch.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_core/security/action_groups_patch.xml)
- [test_business_admin_authority_path.py](/mnt/e/sc-backend-odoo/addons/smart_construction_custom/tests/test_business_admin_authority_path.py)
- [ITER-2026-03-31-473.yaml](/mnt/e/sc-backend-odoo/agent_ops/tasks/ITER-2026-03-31-473.yaml)
- [report.ITER-2026-03-31-473.md](/mnt/e/sc-backend-odoo/agent_ops/reports/2026-03-31/report.ITER-2026-03-31-473.md)
- [ITER-2026-03-31-473.json](/mnt/e/sc-backend-odoo/agent_ops/state/task_results/ITER-2026-03-31-473.json)
- [delivery_context_switch_log_v1.md](/mnt/e/sc-backend-odoo/docs/ops/iterations/delivery_context_switch_log_v1.md)

## Verification
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-31-473.yaml` → `PASS`
- `make verify.smart_core` → `PASS`
- `make mod.upgrade CODEX_NEED_UPGRADE=1 MODULE=smart_construction_core DB_NAME=sc_odoo` → `PASS`
- runtime audit on `sc_odoo` confirms:
  - `PM / hujun`
    - `payment_request_my = False`
    - `payment_request_write = False`
    - `project_progress_entry = True`
    - `project_progress_entry_write = True`
  - `finance / jiangyijiao`
    - `payment_request_my = True`
    - `payment_request_write = True`
    - `project_progress_entry = False`
    - `project_progress_entry_write = False`
  - `executive / wutao`
    - `payment_request_my = True`
    - `project_progress_entry = True`
  - `business_admin / admin`
    - `payment_request_my = True`
    - `project_progress_entry = True`

## Implementation
- [action_groups_patch.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_core/security/action_groups_patch.xml)
  - added an explicit patch for `action_payment_request_my` using `[(6, 0, ...)]` so the action is limited to `finance_user + finance_manager`
  - changed `action_project_progress_entry` to `[(6, 0, ...)]` so the action is limited to `cost_user + cost_manager`
  - this removes the prior residual where inherited base groups left the action visible to non-writers
- [test_business_admin_authority_path.py](/mnt/e/sc-backend-odoo/addons/smart_construction_custom/tests/test_business_admin_authority_path.py)
  - added a regression assertion that `action_payment_request_my` excludes `finance_read`
  - added a regression assertion that `action_project_progress_entry` excludes `cost_read`

## Risk
- 结果：`PASS`
- 观察项：
  - 本批只收窄 action 可见性，没有扩大任何角色权力
  - `executive` 与 `business_admin` 的代表性写/审路径保持不变
  - 升级期间仍出现既有非阻断 warning：
    - `smart_scene` manifest 缺 `license`
    - `smart_construction_custom` README docutils 缩进 warning

## Rollback
- rerun `make mod.upgrade CODEX_NEED_UPGRADE=1 MODULE=smart_construction_core DB_NAME=sc_odoo`
- `git restore addons/smart_construction_core/security/action_groups_patch.xml`
- `git restore addons/smart_construction_custom/tests/test_business_admin_authority_path.py`
- `git restore agent_ops/tasks/ITER-2026-03-31-473.yaml`
- `git restore agent_ops/reports/2026-03-31/report.ITER-2026-03-31-473.md`
- `git restore agent_ops/state/task_results/ITER-2026-03-31-473.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next
- 代表性写路径残差已经收口
- 下一步可回到四川保盛更细粒度业务流程验收，继续看是否还有非代表性入口残差
