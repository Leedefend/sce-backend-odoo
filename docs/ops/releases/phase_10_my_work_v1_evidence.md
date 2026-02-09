# Phase 10 My Work v1 Evidence

- Branch: `codex/phase10-my-work-v1`
- Scope: Phase 10 user interaction productization except owner-specific scenes (`T10.4.x` excluded)
- Delivery shape: PR-A core (My Work + semantic actions + gate prerequisites)

## 1. Included Scope

- `T10.3.1` My Work unified entry:
- `my.work.summary`
- `my.work.complete`
- `my.work.complete_batch`
- `T10.2.3` semantic action envelope:
- `execute_button` returns standardized success/failure structure
- `T10.2.1` list interaction baseline:
- server-side search/filter/sort/pagination contract consumed by frontend
- Gate strict hardening:
- `verify.portal.my_work_smoke.container` in strict gate path
- extension module prerequisite guard before My Work smoke

## 2. Excluded Scope

- Owner-specific scenes and owner confirmation flows (`T10.4.1`, `T10.4.2`)
- Product analytics and collaboration enhancements intended for PR-B split

## 3. Contract Evidence (Core)

### 3.1 `my.work.summary`

- Status taxonomy:
- `READY`
- `EMPTY`
- `FILTER_EMPTY`
- Filter contract:
- `section`, `source`, `reason_code`, `search`
- `page`, `page_size`, `total_pages`
- `sort_by`, `sort_dir`
- Facets contract:
- source/reason/section counts available in response

### 3.2 Completion intents

- `my.work.complete` and `my.work.complete_batch` return structured outcomes
- Failure taxonomy includes:
- `reason_code`
- `retryable`
- `error_category`
- `suggested_action`

### 3.3 Semantic execute envelope

- UI actions use semantic response contract (not raw method exposure)
- Response is normalized into user-level success/failure payload

## 4. Gate and Verify Chain

Canonical strict gate command (service smoke user):

```bash
CODEX_MODE=gate DB_NAME=sc_demo E2E_LOGIN=svc_e2e_smoke E2E_PASSWORD=demo make gate.full
```

Core checks in strict path include:

- `verify.menu.scene_resolve.container`
- `verify.portal.scene_warnings_guard.container`
- `verify.portal.scene_warnings_limit.container`
- `verify.portal.act_url_missing_scene_report.container`
- `verify.portal.my_work_smoke.container`

Direct smoke command:

```bash
make verify.portal.my_work_smoke.container DB_NAME=sc_demo E2E_LOGIN=svc_e2e_smoke E2E_PASSWORD=demo
```

## 5. Extension Prerequisite Guard

- Guard target: `verify.extension_modules.guard`
- Behavior:
- validates `ir_config_parameter.key = sc.core.extension_modules`
- fails if `smart_construction_core` is missing
- emits remediation hint and restart hint

Apply target:

- `policy.apply.extension_modules`
- upserts `smart_construction_core` into `sc.core.extension_modules`
- requires explicit restart to reload extension loader cache

Ensure target:

- `policy.ensure.extension_modules`
- guard-first flow
- optional auto-heal only when `AUTO_FIX_EXTENSION_MODULES=1`

## 6. Artifacts and Auditability

Expected artifact families:

- My Work smoke:
- `artifacts/codex/my-work-smoke-v10_2/<timestamp>/summary.md`
- `.../my_work_page1_desc.log`
- `.../my_work_page2_asc.log`
- Extension guard output in gate/verify logs
- Backend test logs for:
- `my_work_backend`
- `usage_backend`
- `capability_contract_backend`

## 7. Rollback / Degrade Controls

- Soft degrade strict checks for emergency local iteration only:

```bash
SC_GATE_STRICT=0 make gate.full DB_NAME=sc_demo
```

- Keep strict gate enabled for merge readiness.
- If extension prereq fails, run:

```bash
make policy.ensure.extension_modules DB_NAME=sc_demo
make restart
```

## 8. Service User Baseline

- Canonical smoke user: `svc_e2e_smoke`
- My Work smoke fallback now defaults to `svc_e2e_smoke` when `E2E_LOGIN` is not provided.
- Demo walkthrough account `demo_pm` remains for manual UI walkthroughs, not gate baseline.
