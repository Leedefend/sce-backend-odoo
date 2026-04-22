# FE Compat Record Live Ingress Reverify EM

## Goal

Re-verify against the current running frontend whether a real legacy
`/compat/record/...` URL still acts as a valid ingress path after login,
compared with the standard `/r/:model/:id` route.

## Verification

1. `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-21-FE-COMPAT-RECORD-LIVE-INGRESS-REVERIFY-EM.yaml`
   - PASS
2. Live Playwright probe against `BASE_URL=http://127.0.0.1:5174`, `DB_NAME=sc_demo`, `E2E_LOGIN=wutao`, `E2E_PASSWORD=demo`
   - PASS
   - artifacts: `artifacts/codex/live-compat-record-ingress-reverify/20260421T051830Z`
3. `git diff --check -- agent_ops/tasks/ITER-2026-04-21-FE-COMPAT-RECORD-LIVE-INGRESS-REVERIFY-EM.yaml docs/verify/fe_compat_record_live_ingress_reverify_em_v1.md docs/ops/iterations/delivery_context_switch_log_v1.md`
   - PASS

## Live Result

- Standard route probe:
  - href: `http://127.0.0.1:5174/s/project.management`
  - pathname: `/s/project.management`
  - title: `系统 - 智能施工企业管理平台`
  - text_length: `1227`
  - no error panel
- Compat route probe:
  - href: `http://127.0.0.1:5174/compat/record/sc.legacy.financing.loan.fact/53?menu_id=405&action_id=599`
  - pathname: `/compat/record/sc.legacy.financing.loan.fact/53`
  - title: `系统 - 智能施工企业管理平台`
  - text_length: `3532`
  - no error panel

## Decision

This refreshes the earlier live-ingress evidence. The running frontend still
accepts a real legacy `/compat/record/...` URL as a valid user ingress. In the
current runtime, the standard `/r/...` path has already converged onto a scene
route, but the legacy compat route still enters and remains on the compat route
shape without rendering an error panel. Therefore `compat-record` bridge
retirement is still not currently safe without a separate saved-link or legacy
ingress retirement program.
