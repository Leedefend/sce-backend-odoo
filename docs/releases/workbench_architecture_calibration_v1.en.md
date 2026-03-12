# SCEMS Workbench Architecture Calibration (Frozen Baseline v1 · 2026-03-12)

## 1. Why calibrate now

The workbench has moved from visual iteration to semantic protocol governance. The main challenge is no longer UI styling but:

- whether first-screen narrative consistently stays action-first,
- whether protocol ownership remains stable (v1 primary, legacy compatibility),
- whether business data and platform diagnostics stay fully separated.

Conclusion: semantic stability must now take priority over visual polishing.

---

## 2. Workbench positioning (single source of truth)

The only positioning is:

> **Business Action Hub**

The workbench must answer three questions:

1. What should be handled first today? (Action)
2. Which risks impact target delivery? (Alert)
3. Is operational status drifting from plan? (Status)

---

## 3. Prohibited patterns (hard constraints)

The workbench must not:

1. expose raw capability-registry counts as primary business KPIs,
2. expose diagnostics/debug/raw meta fields in user main view,
3. expose protocol internals such as `scene_key/section_key/source_kind`,
4. replace action narrative with feature-group summaries,
5. allow `quick_entries` to overtake `today_focus` priority,
6. carry new semantics through legacy protocol,
7. override backend contract ordering with ad-hoc frontend ordering.

---

## 4. Target page model (four-zone freeze)

The homepage shell is frozen to four zones:

1. `today_focus` (primary)
   - `today_actions`
   - `risk_alert_panel`
2. `analysis`
   - business KPIs + progress summary
3. `quick_entries`
   - common entry points (secondary)
4. `hero`
   - role and landing summary (supporting)

No fifth primary zone is allowed.

---

## 5. Protocol and compatibility policy

### 5.1 Primary protocol

- `page_orchestration_v1` is the only primary protocol.

### 5.2 Compatibility protocol

- `page_orchestration` is retained for legacy compatibility only.
- New semantics must not be implemented in legacy-only fields.

### 5.3 Mandatory contract self-description

- `contract_protocol.primary=page_orchestration_v1`
- `contract_protocol.legacy.status=compatibility`

---

## 6. Data-priority policy

### 6.1 Actions and risks: business-first, capability-fallback

- `today_actions`: business actions first (tasks/approvals/risks/payments),
- `risk.actions`: real risk actions first,
- capability fallback only when business data is insufficient.

### 6.2 KPI naming and source layering

| Field | Type | Source | User first-screen visibility | Notes |
| --- | --- | --- | --- | --- |
| `today_actions` | action list | business / fallback | Yes | Primary narrative |
| `risk.actions` | alert list | business / fallback | Yes | Primary narrative |
| `metrics.*` | business metric | business only | Yes | No capability-based pseudo business KPIs |
| `platform_metrics.*` | platform metric | capability registry | No | Ops/HUD only |
| `diagnostics.extraction_stats` | diagnostic | extraction pipeline | No | Diagnostics only |
| `diagnostics.action_ranking_policy` | diagnostic | ranking engine | No | Diagnostics only |

### 6.3 Fallback semantic policy

When fallback is triggered due to missing business data:

1. user main view must not show pseudo operational percentages,
2. weak first-screen hint is allowed (e.g. “Business data unavailable; showing ready entries”),
3. `diagnostics` must include `source_kind/fallback_reason/extraction_hit_rate`,
4. fallback must not be presented as real business outcomes.

---

## 7. Action ranking policy (Action Ranking v1)

`today_actions` ordering must use explainable multi-factor ranking:

1. severity (`critical/urgent/overdue`),
2. time urgency (overdue > within 24h > within 3 days > within 7 days),
3. pending volume (`count/pending_count`),
4. source priority (business > capability fallback).

Policy must be externally observable via:

- `diagnostics.action_ranking_policy`
- `diagnostics.extraction_stats`

---

## 8. Role-template strategy (frozen)

### PM (Project Manager)

- `today_actions` highest
- `risk_alert_panel` second
- `analysis` third
- `quick_entries` fourth

### Finance

- `today_actions` and `analysis` balanced
- risk priorities emphasize payment/settlement
- finance/contract entries rank higher in `quick_entries`

### Owner / Executive

- `risk_alert_panel` and `analysis` highest
- `today_actions` simplified
- `quick_entries` further deprioritized

---

## 9. Backend vs frontend responsibilities

### Backend (contract responsibility)

- semantic structure and orchestration,
- source priority and degradation strategy,
- KPI layering and diagnostics,
- action ranking policy declaration.

### Frontend (renderer responsibility)

- strict contract rendering,
- interaction and navigation execution,
- no ad-hoc override of backend ranking semantics.

---

## 10. Release acceptance criteria

### 10-second criterion

- first screen must show “Today Actions + System Alerts”,
- users can identify immediate next actions without explanation.

### 30-second criterion

- at least one action is directly executable,
- risk-status relationship is understandable quickly,
- no technical-field leakage in user main view.

### Protocol criterion

- `page_orchestration_v1` stable as primary,
- legacy stays compatibility-only.

---

## 11. Next-phase actions

1. freeze `action_ranking_policy_v1` with snapshot baseline,
2. parameterize role templates (PM/Finance/Owner),
3. publish weekly extraction hit-rate report (by role/tenant/environment),
4. standardize HUD/diagnostics outputs to block debug leakage,
5. include workbench contract snapshot in pre-release minimal regression.

---

## 12. One-line conclusion

> The next milestone is not “a prettier homepage”, but stabilizing “action-first, risk-first, business-first” into a verifiable, evolvable, and governable platform semantic protocol.

