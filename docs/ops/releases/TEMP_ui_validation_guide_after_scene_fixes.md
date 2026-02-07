# TEMP UI Validation Guide After Scene Fixes

Last updated: 2026-02-06
Scope: R0 + Scene target systematic fixes

## 1) Start Frontend

```bash
cd /mnt/e/sc-backend-odoo
make fe.dev
```

Open frontend (usually `http://localhost:5174`).

## 2) Validate First-Login Path (R0)

- Go to `/login` and sign in with a test account.
- Expected:
  - Redirect to `/s/projects.list`
  - No workbench landing
  - No blank page

## 3) Validate Directory Menu Auto-Drilldown (R0-1)

- Click a parent menu node that is directory-like (no direct action).
- Expected:
  - Auto-redirect to first reachable child (`/a/:id` or `/s/:sceneKey`)
  - Must NOT land on `/workbench?...reason=NAV_MENU_NO_ACTION`

## 4) Validate Core Scenes Openability (Systematic Fix)

Open these routes directly:

- `/s/projects.list`
- `/s/projects.ledger`
- `/s/projects.intake`

Expected for all three:

- Open a meaningful page (list/form/action)
- Do NOT land on `Navigation unavailable`
- Do NOT show `Unknown` reason

## 5) Validate Workbench Is Exception-Only (R0-2)

- Manually open an invalid route/scene (e.g. unknown scene key).
- Expected:
  - Workbench/exception page appears only in this abnormal case
  - Exit actions are available (`Back to home`, `Open menu`)

## 6) If Any Fallback Still Happens

Capture and check quickly:

1. Full URL (including query string)
2. Browser Network -> `app.init` response
3. In `scenes[]`, check the scene `target` contains executable fields (`action_id` / `model` / `route`)

Interpretation:

- Scene has valid target but still falls back -> frontend resolver/path issue
- Scene missing executable target -> runtime contract not refreshed / stale data

## 7) Optional CLI Guards

```bash
node scripts/verify/fe_menu_no_action_smoke.js
node scripts/verify/fe_scene_registry_coerce_smoke.js
node scripts/verify/fe_scene_core_openable_guard.js
```

Expected: all PASS.
