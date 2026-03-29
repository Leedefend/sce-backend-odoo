## Summary

- added a reusable live gap-matrix audit for generic list/detail pages in [list_detail_gap_audit.py](/mnt/e/sc-backend-odoo/agent_ops/scripts/list_detail_gap_audit.py)
- reran the audit against the live local backend instead of stale snapshots
- current live conclusion:
  - detail scope: no gap detected in the audited structure/consumer slice
  - list scope: backend still lacks `search.saved_filters`; current frontend list consumers already cover the rest of the audited list surface

## Changed Files

- `agent_ops/tasks/ITER-2026-03-29-229.yaml`
- `agent_ops/scripts/list_detail_gap_audit.py`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-29-229.yaml`
- `python3 -m py_compile agent_ops/scripts/list_detail_gap_audit.py`
- `bash -lc 'export E2E_BASE_URL=http://127.0.0.1:8070; python3 agent_ops/scripts/list_detail_gap_audit.py --db sc_demo --login sc_fx_pm --password prod_like --list-view frontend/apps/web/src/views/ActionView.vue --list-page frontend/apps/web/src/pages/ListPage.vue --detail-page frontend/apps/web/src/pages/ContractFormPage.vue --detail-runtime frontend/apps/web/src/app/runtime/detailLayoutRuntime.ts --expect-status PASS'`

## Risk

- low-risk audit batch
- no frontend or backend product code changed
- live backend facts were used to avoid snapshot drift

## Rollback

- run the `git restore ...` command listed in `agent_ops/tasks/ITER-2026-03-29-229.yaml`

## Next Suggestion

- stop detail-page structure work for now, because the audited detail slice is already aligned at the fact/consumer level
- reopen list work only if `search.saved_filters` is important enough to justify a backend fact-completeness batch
