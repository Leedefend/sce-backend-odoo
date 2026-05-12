# Business Fact Source Field Coverage Acceptance v1

Status: `accepted`

Task: `ITER-2026-05-10-BUSINESS-FACT-SOURCE-FIELD-COVERAGE`

## Acceptance Principle

This iteration accepts migrated history by business fact coverage, not by
forcing legacy data to satisfy the new system's customer/supplier
classification rules.

The target is:

- carry all deterministic historical business facts into the new system;
- preserve old-source identifiers so facts can be traced back to the legacy
  database;
- use only old-source creator/time/amount/balance fields as factual evidence;
- treat Odoo import users, import timestamps, and technical accounts as
  technical metadata only;
- document blank creator/time fields from the old source as source coverage
  observations, not migration blockers.

Customer and supplier categories are upgraded system concepts derived from
business facts. They are useful for current operations, but they are not a
mandatory old-database fact shape.

## Current Evidence

Acceptance database:

`sc_acceptance_audit_20260510`

Classifier artifact:

`artifacts/business-fact-audit/sc_acceptance_audit_20260510_residual_source_classified/business_fact_residual_gap_classifier_v1.json`

Latest result:

| Check | Result |
| --- | --- |
| status | `PASS` |
| mode | `business_fact_source_field_coverage_classifier` |
| blocking source key counts | `{}` |
| contract amount missing total | `0` |
| contract receivable balance missing total | `0` |
| supplier contract entry source missing total | `0` |
| affected business subject count | `250` |
| old-source blank creator/time is blocker | `false` |

The affected business subject count is impact context only. It must not be
reported as a customer/supplier classification gap.

## Residual Interpretation

Remaining source-field observations are limited to blank fields in the old
source evidence, for example old payment execution, payment request,
historical supplier invoice, historical supplier contract, and historical
expense fact creator/time blanks.

These are objective historical-source observations:

- they must remain visible in evidence artifacts;
- they must not be filled from `OdooBot`, `admin`, `system`, import operators,
  or import timestamps;
- they must not block this round if the runtime source key is present and the
  legacy source evidence shows the source field itself is blank.

## Delivery Rule

This round is considered complete when historical business facts are carried and
traceable. Later iterations may improve user-facing customer/supplier
classification, supplier types, or business-rule validation, but those upgrades
must not rewrite unknown legacy facts into artificial certainty.

Future audit wording should use:

`业务事实源字段覆盖`

Do not use:

`有效残余伙伴缺口`

That old wording incorrectly implies that legacy data must already match the
new customer/supplier model.
