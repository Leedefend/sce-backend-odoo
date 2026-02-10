# Phase 10 PR Split Plan

- Branch source: `codex/phase10-my-work-v1`
- Split strategy: `A` (core first, enhancements second)
- Goal: reduce review risk and keep rollback boundaries clear

## 1. PR-A (must merge first)

Title suggestion:

`feat(phase10): my-work v1 core with semantic actions and strict gate baseline`

Include:

- My Work core intents:
- `my.work.summary`
- `my.work.complete`
- `my.work.complete_batch`
- My Work frontend view behavior:
- filters/pagination/sorting
- batch complete and failed retry
- semantic execute envelope alignment (`execute_button`)
- strict gate baseline:
- `verify.portal.my_work_smoke.container`
- extension prerequisite guard/apply/ensure flow
- service-user baseline for my-work smoke (`svc_e2e_smoke`)
- evidence docs:
- `docs/ops/releases/current/phase_10_my_work_v1_evidence.md`

Do not include:

- usage analytics dashboard/report/export UX
- collaboration timeline/chatter enhancements
- extra UX polish outside core My Work/gate chain

## 2. PR-B (follow-up enhancements)

Title suggestion:

`feat(phase10): usage analytics and collaboration enhancements`

Include:

- usage tracking/report/export enhancements
- admin analytics UI wiring and filters
- collaboration timeline/chatter integration refinements
- non-core UX failure-state consistency enhancements

Depends on:

- PR-A merged

## 3. Validation Baseline

PR-A minimum:

```bash
make verify.frontend.typecheck.strict
make verify.frontend_api
make test MODULE=smart_construction_core TEST_TAGS=my_work_backend DB_NAME=sc_demo
make verify.portal.my_work_smoke.container DB_NAME=sc_demo E2E_LOGIN=svc_e2e_smoke E2E_PASSWORD=demo
```

PR-A merge-gate:

```bash
CODEX_MODE=gate DB_NAME=sc_demo E2E_LOGIN=svc_e2e_smoke E2E_PASSWORD=demo make gate.full
```

PR-B minimum:

```bash
make verify.frontend.typecheck.strict
make test MODULE=smart_construction_core TEST_TAGS=usage_backend DB_NAME=sc_demo
make test MODULE=smart_construction_core TEST_TAGS=capability_contract_backend DB_NAME=sc_demo
```

## 4. Reviewer Navigation

PR-A reviewer entry points:

- `addons/smart_construction_core/handlers/my_work.py`
- `frontend/apps/web/src/views/MyWorkView.vue`
- `scripts/verify/fe_my_work_smoke.js`
- `scripts/verify/extension_modules_guard.sh`
- `scripts/ops/apply_extension_modules.sh`
- `Makefile`
- `docs/ops/releases/current/phase_10_my_work_v1_evidence.md`

PR-B reviewer entry points:

- `addons/smart_construction_core/handlers/usage.py`
- `frontend/apps/web/src/views/UsageAnalyticsView.vue`
- `frontend/apps/web/src/views/ActionView.vue`
- `frontend/apps/web/src/views/HomeView.vue`
- `frontend/apps/web/src/views/RecordView.vue`

