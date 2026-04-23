# Partner Cross-Source Manual Decision Template v1

Iteration: `ITER-2026-04-13-1859`

## Purpose

Provide a manual decision template for the 8 partner cross-source conflict rows.

This template is intentionally blank for final decision fields.

## Template

Path:

- `artifacts/migration/partner_cross_source_manual_decision_template_v1.csv`

Decision fields to fill manually:

- `selected_source`;
- `selected_legacy_id`;
- `rejected_source`;
- `losing_source_as_supplement`;
- `decision_status`;
- `decision_reason`;
- `reviewer`;
- `reviewed_at`;
- `write_eligible_after_review`.

## Guard

The agent must not fill these fields without an explicit manual decision source.

Allowed values should be decided in a later manual-review batch:

- `selected_source`: `company`, `supplier`, or `defer`;
- `losing_source_as_supplement`: `yes`, `no`, or `defer`;
- `decision_status`: `approved`, `rejected`, or `defer`;
- `write_eligible_after_review`: `yes`, `no`, or `defer`.

## Current State

- rows: 8;
- final source decisions: 0;
- database writes: 0;
- partner creates: 0;
- partner updates: 0.
