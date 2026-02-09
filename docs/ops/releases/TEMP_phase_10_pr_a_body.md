# PR-A: Phase 10 My Work Core + Gate Baseline

## Summary

This PR delivers the Phase 10 core interaction baseline:

- My Work unified entry (`my.work.summary`, `my.work.complete`, `my.work.complete_batch`)
- semantic action envelope alignment (`execute_button`)
- server-driven filters/sorting/pagination for My Work
- strict gate integration with my-work smoke and extension prereq guard
- service smoke user baseline (`svc_e2e_smoke`) for My Work smoke

Owner-specific scenes are intentionally excluded.

## Why

This is the merge-safe core that users need daily and that CI/gate can reliably enforce.
Enhancement scope (usage analytics/collaboration polish) is intentionally deferred to PR-B.

## Scope

Included:

- My Work contract and behavior
- completion/batch completion with structured failure taxonomy
- strict gate checks and prereq guard chain
- evidence and release docs for reviewer/audit

Excluded:

- owner scene flows (`T10.4.x`)
- extended analytics/collaboration refinements (PR-B)

## Contract Changes

- `my.work.summary`:
- status taxonomy: `READY | EMPTY | FILTER_EMPTY`
- filters: `section/source/reason_code/search`
- pagination: `page/page_size/total_pages`
- sorting: `sort_by/sort_dir`
- `my.work.complete` / `my.work.complete_batch`:
- normalized failure fields:
- `reason_code`
- `retryable`
- `error_category`
- `suggested_action`

## Gate and Verification

Primary strict gate command:

```bash
CODEX_MODE=gate DB_NAME=sc_demo E2E_LOGIN=svc_e2e_smoke E2E_PASSWORD=demo make gate.full
```

Focused checks:

```bash
make verify.portal.my_work_smoke.container DB_NAME=sc_demo E2E_LOGIN=svc_e2e_smoke E2E_PASSWORD=demo
make verify.extension_modules.guard DB_NAME=sc_demo
```

## Evidence

- `docs/ops/releases/phase_10_my_work_v1_evidence.md`
- `docs/ops/releases/TEMP_phase_10_branch_full_summary.md`

## Rollback / Safety

- emergency local degrade only:

```bash
SC_GATE_STRICT=0 make gate.full DB_NAME=sc_demo
```

- extension prereq remediation:

```bash
make policy.ensure.extension_modules DB_NAME=sc_demo
make restart
```

