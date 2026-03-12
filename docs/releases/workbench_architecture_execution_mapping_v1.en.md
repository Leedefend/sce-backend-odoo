# Workbench Architecture Baseline Execution Mapping (v1)

## 1. Purpose

Map `workbench_architecture_calibration_v1` rules to concrete code locations and verification commands for direct iteration execution.

---

## 2. Rule → Code Mapping

### R1: `page_orchestration_v1` is primary protocol

- Rule: `page_orchestration_v1` must be primary; legacy is compatibility only.
- Code:
  - `addons/smart_core/core/workspace_home_contract_builder.py`
  - Fields: `contract_protocol.primary` / `contract_protocol.legacy`
- Verification:
  - Contract payload contains `contract_protocol.primary=page_orchestration_v1`

### R2: Four-zone freeze (hero/today_focus/analysis/quick_entries)

- Rule: no fifth primary zone.
- Code:
  - `addons/smart_core/core/workspace_home_data_provider.py`
  - Function: `build_v1_zones`
- Verification:
  - Browser console prints `workspaceHome.page_orchestration_v1.zones`
  - Only four primary zone keys exist

### R3: `today_actions` business-first, capability fallback second

- Rule: business actions first, fallback only when business data is insufficient.
- Code:
  - `addons/smart_core/core/workspace_home_contract_builder.py`
  - Functions: `_build_business_today_actions` / `_build_capability_today_actions` / `_build_today_actions`
- Verification:
  - `diagnostics.extraction_stats.today_actions_business > 0` implies business-first list

### R4: `risk.actions` business-first, capability fallback second

- Rule: risk actions should primarily come from business risk sources.
- Code:
  - `addons/smart_core/core/workspace_home_contract_builder.py`
  - Function: `_build_risk_actions`
- Verification:
  - `diagnostics.extraction_stats.risk_actions_business`

### R5: KPI layering (business vs platform)

- Rule: `metrics` must not mix platform capability counts; platform counts go to `platform_metrics`.
- Code:
  - `addons/smart_core/core/workspace_home_contract_builder.py`
  - Function: `_build_metric_sets`
- Verification:
  - Contract includes both `metrics` and `platform_metrics`

### R6: Debug-field layering

- Rule: no debug terms in user main view; diagnostics stay in `diagnostics`.
- Code:
  - `addons/smart_core/core/workspace_home_contract_builder.py`
  - Field: `diagnostics.*`
- Verification:
  - Main view does not expose technical terms like `result_summary/active_filters`

### R7: Explainable action ranking

- Rule: rank by severity + urgency + pending volume + source priority.
- Code:
  - `addons/smart_core/core/workspace_home_contract_builder.py`
  - Function: `_urgency_score`
  - Field: `diagnostics.action_ranking_policy`
- Verification:
  - Overdue/urgent items appear before normal items

### R8: Backend/frontend responsibility boundary

- Rule: backend defines semantics/ranking; frontend does not rewrite business priority.
- Code:
  - Backend: `workspace_home_contract_builder.py`
  - Frontend: `frontend/apps/web/src/components/page/PageRenderer.vue` (priority rendering only)
- Verification:
  - No extra business-priority sorting branch in frontend

---

## 3. Verification Command Mapping

- `make verify.frontend.build`
- `make verify.frontend.typecheck.strict`
- `make verify.project.dashboard.contract`
- `make verify.phase_next.evidence.bundle`

Recommended environment:

- `ENV=test`
- `ENV_FILE=.env.prod.sim`
- `COMPOSE_FILES='-f docker-compose.yml -f docker-compose.prod-sim.yml'`

---

## 4. Direct Iteration Backlog (next batch)

### P0 (immediate)

1. Implement role-based ranking parameters (PM/Finance/Owner).
2. Add impact factors (financial/project impact) into `today_actions` ranking.
3. Add HUD switch for `diagnostics.extraction_stats` visualization.

### P1 (next)

1. Publish weekly extraction hit-rate report by role/tenant/environment.
2. Freeze `action_ranking_policy_v1` and include in regression checks.

---

## 5. Execution Conclusion

Direct iteration is now ready:

- baseline is frozen,
- rules are mapped to concrete code locations,
- verification chain is explicit,
- P0 tasks are ready for immediate implementation.

