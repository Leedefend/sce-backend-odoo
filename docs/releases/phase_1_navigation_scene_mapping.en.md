# SCEMS v1.0 Phase 1: Main Navigation to Scene Mapping

## 1. Mapping Objective
Freeze V1 main navigation onto the `construction_pm_v1` canonical scene code set as release baseline.

## 2. Target Mapping (V1)

| Main Nav | Target Scene Code | Current Status | Notes |
|---|---|---|---|
| My Work | `my_work.workspace` | Available | stable entry |
| Project Ledger | `projects.ledger` | Available | linked to management console |
| Project Management | `project.management` | Available | core console scene |
| Contract Management | `contracts.workspace` | Implemented (minimum usable) | keep transitional deep-link via `contract.center` |
| Cost Control | `cost.analysis` | Implemented (minimum usable) | keep transitional deep-link via `cost.*` scenes |
| Fund Management | `finance.workspace` | Implemented (minimum usable) | keep transitional deep-link via `finance.center` |
| Risk Alerts | `risk.center` | Implemented (minimum usable) | keep transitional deep-link via `risk.monitor` |

## 3. Policy Landing
- `docs/product/delivery/v1/construction_pm_v1_scene_surface_policy.json` now locks `construction_pm_v1.nav_allowlist` to the 7 target items above.
- `config.*` and `data.*` are removed from deep-link allowlist, matching the non-core exclusion policy.

## 4. Next Actions (Phase 2 bridge)
- Implement scene definitions/contracts for `contracts.workspace`, `cost.analysis`, `finance.workspace`, and `risk.center`.
- Keep temporary deep-link fallback until those scenes are fully delivered.
