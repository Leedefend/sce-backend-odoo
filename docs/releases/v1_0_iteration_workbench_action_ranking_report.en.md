# v1.0 Workbench Action Ranking and Hit-Rate Report (Current Round)

## 1. Goal

Without changing permission/governance/delivery core mechanisms, this round adds explainable business-first ranking for `today_actions` and `risk.actions`:

- business actions over capability fallback,
- overdue/near-due actions first,
- high-risk semantics first,
- pending volume as secondary weight.

## 2. Implementation Summary

Core implementation file:

- `addons/smart_core/core/workspace_home_contract_builder.py`

Added capabilities:

- `_urgency_score(...)`: unified urgency scoring;
- `_build_today_actions(...)`: ordering by `urgency_score` + business-source priority;
- `_build_risk_actions(...)`: urgency-sorted risk actions with `urgent/danger` semantics;
- `diagnostics.extraction_stats`: business-hit vs fallback counters.

## 3. Ranking Rules (current)

Action score combines:

1. Severity keywords (`critical/urgent/overdue/严重/紧急/逾期`)
2. Deadline urgency (`due_date/deadline/planned_date/date_deadline`)
   - overdue > due within 24h > due within 3 days > due within 7 days
3. Pending volume (`count/pending_count`)
4. Source priority (business > capability fallback)

## 4. Hit-Rate Output Fields

Current contract outputs:

- `diagnostics.extraction_stats.business_collections`
- `diagnostics.extraction_stats.business_rows_total`
- `diagnostics.extraction_stats.today_actions_business`
- `diagnostics.extraction_stats.today_actions_fallback`
- `diagnostics.extraction_stats.risk_actions_business`
- `diagnostics.extraction_stats.risk_actions_fallback`

These are for role/environment comparison and should not appear in user main view.

## 5. Validation Suggestions

1. Verify first-screen action order reflects urgency.
2. Check `diagnostics.extraction_stats` via HUD/contract export.
3. Verify fallback path keeps page non-empty when business data is missing.

## 6. Next Round

1. Add impact dimensions (financial/project impact).
2. Introduce role-specific thresholds (PM/Finance/Owner).
3. Freeze as standalone `action_ranking_policy_v1` spec.

