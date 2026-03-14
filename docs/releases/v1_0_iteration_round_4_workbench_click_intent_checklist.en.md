# SCEMS v1.0 Round 4 Workbench Click-to-Intent Checklist

## 1. Purpose

This checklist turns “product feel” into verifiable facts:

- whether click actions trigger expected intents,
- whether telemetry stays non-blocking,
- whether users can one-hop into business processing pages.

## 2. Primary Workbench Flow (User View)

### 2.1 First-screen loading

1. Open workbench route (`/` or `/s/portal.dashboard`);
2. load initialization via `system.init`;
3. render `workspace_home` (`hero/today_actions/risk/metrics`);
4. emit `workspace.view` (`telemetry.track`, non-blocking).

### 2.2 Action click flow

1. Click a Today Action card:
   - emit `workspace.enter_click` (`telemetry.track`),
   - navigate to target scene (then `ui.contract` / `load_view` / `api.data`).
2. Click a Risk action:
   - emit `workspace.risk_action_click` (`telemetry.track`),
   - navigate to risk center or related business page.

### 2.3 Hero quick actions

- Open landing / My Work / navigation actions:
  - emit `workspace.nav_click` (`telemetry.track`),
  - navigate to target path.

## 3. Click-to-Intent Matrix

| UI Action | Expected Event | Expected Intent | Blocking |
| --- | --- | --- | --- |
| enter workbench | `workspace.view` | `telemetry.track` | no |
| click today action | `workspace.enter_click` | `telemetry.track` | no |
| action navigation result | `workspace.enter_result` | `telemetry.track` | no |
| click risk action | `workspace.risk_action_click` | `telemetry.track` | no |
| open landing/my-work | `workspace.nav_click` | `telemetry.track` | no |
| enter business page | - | `ui.contract/load_view/api.data` | yes (business path) |

## 4. 10-Second / 30-Second Product Acceptance

### 10-second check

- users immediately see “today actions + risk alerts”,
- users can tell what to do first,
- no debug-field noise in default view.

### 30-second check

- at least one one-hop action works,
- risk actions can reach risk center,
- when data is thin, page shows ownership/demo-assignment hint.

## 5. Minimal Regression

- `make verify.frontend.typecheck.strict`
- `make verify.frontend.build`
- `make verify.phase_next.evidence.bundle ENV=test ENV_FILE=.env.prod.sim DB_NAME=sc_prod_sim E2E_BASE_URL=http://localhost:18069`
- `make verify.workbench.extraction_hit_rate.report ENV=test ENV_FILE=.env.prod.sim DB_NAME=sc_prod_sim E2E_BASE_URL=http://localhost:18069`
