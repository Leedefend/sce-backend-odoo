# FE Compat Record Live Ingress Verify DZ

## Goal

Verify against the live running frontend whether a real legacy
`/compat/record/...` URL still acts as a valid ingress path after login,
compared with the standard `/r/:model/:id` route.

## Verification

1. `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-21-FE-COMPAT-RECORD-LIVE-INGRESS-VERIFY-DZ.yaml`
   - PASS
2. Live Playwright probe against `BASE_URL=http://127.0.0.1:5174`, `DB_NAME=sc_demo`, `E2E_LOGIN=wutao`, `E2E_PASSWORD=demo`
   - PASS
   - artifacts: `artifacts/codex/live-compat-record-ingress-probe/20260420T181213Z`
3. `git diff --check -- agent_ops/tasks/ITER-2026-04-21-FE-COMPAT-RECORD-LIVE-INGRESS-VERIFY-DZ.yaml docs/verify/fe_compat_record_live_ingress_verify_dz_v1.md docs/ops/iterations/delivery_context_switch_log_v1.md`
   - PASS

## Live Result

- Standard route probe:
  - href: `http://127.0.0.1:5174/r/sc.legacy.financing.loan.fact/53?menu_id=405&action_id=599`
  - pathname: `/r/sc.legacy.financing.loan.fact/53`
  - title: `系统 - 智能施工企业管理平台`
  - text_length: `319`
  - no error panel
- Compat route probe:
  - href: `http://127.0.0.1:5174/compat/record/sc.legacy.financing.loan.fact/53?menu_id=405&action_id=599`
  - pathname: `/compat/record/sc.legacy.financing.loan.fact/53`
  - title: `系统 - 智能施工企业管理平台`
  - text_length: `319`
  - no error panel

## Decision

This removes the earlier retirement uncertainty. The running frontend still
accepts a real legacy `/compat/record/...` URL as a valid user ingress, and it
behaves equivalently to the standard `/r/:model/:id` entry for the verified
detail page. Therefore `compat-record` bridge retirement is not currently safe
for real usability, and the correct conclusion is to keep the bridge in place
until legacy saved URLs or external metadata ingress are explicitly retired.
