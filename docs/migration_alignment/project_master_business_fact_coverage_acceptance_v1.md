# Project Master Business Fact Coverage Acceptance v1

Status: `accepted`

Task: `ITER-2026-05-10-PROJECT-MASTER-FACT-COVERAGE`

## Acceptance Principle

Project master acceptance is based on historical project business facts and
source anchors. Old project data must not be forced to satisfy new-system
lifecycle, operation-strategy, visibility, or mandatory-field rules.

The target is:

- carry every legacy project master row as a project anchor;
- carry contract facts with a legacy project id as project-anchor evidence;
- preserve source identifiers so downstream facts can keep project continuity;
- treat old-source blank creator/time fields as coverage observations, not
  migration blockers;
- treat Odoo import users and import timestamps as technical metadata only.

## Current Evidence

Acceptance database:

`sc_acceptance_audit_20260510`

Classifier artifact:

`artifacts/business-fact-audit/sc_acceptance_audit_20260510_project_master_fact_coverage/project_master_business_fact_coverage_classifier_v1.json`

Latest result:

| Check | Result |
| --- | ---: |
| status | `PASS` |
| legacy project source rows | `755` |
| contract project business-fact anchors | `762` |
| contract anchors without project master source | `63` |
| all business-fact project anchors | `818` |
| replay payload project anchors | `818` |
| target project anchors | `818` |
| uncovered business-fact project anchors | `0` |
| contract anchors missing from payload | `0` |
| mapped raw project fields | `63` |
| raw fields with source values | `35` |
| fields with payload missing values | `0` |
| fields with target missing values | `0` |

The replay adapter now carries 20 non-visible contract-source project anchors as
historical business facts. These were previously deferred because they did not
pass a user-facing visible-income-contract filter, but that filter is not a
valid reason to drop historical project fact anchors.

The project master payload now also carries all 63 raw project table columns
through explicit target fields. Empty old-source columns remain empty evidence;
non-empty old-source values are required to appear in both the replay payload
and `project.project`.

## User Verification Surface

The project form includes a read-only `历史项目资料` page for acceptance
reconciliation. It exposes old-system project identifiers, organization,
classification, contacts, finance/tax fields, address, source creator/update
trace, and supplemental source text.

The project list and search views expose the core reconciliation keys:

- `旧系统项目编号`
- `旧系统项目ID`
- `旧系统公司`
- `旧系统项目经理`
- `旧系统阶段`
- `旧系统录入人`
- `旧系统录入时间`

Runtime view check on `sc_acceptance_audit_20260510`:

| Check | Result |
| --- | --- |
| form has `历史项目资料` page | `true` |
| form has old-source creator fields | `true` |
| list has old project code | `true` |
| search has old project code | `true` |
| old field labels | Chinese |

Browser acceptance on daily dev port `http://localhost:18081`:

| Check | Result |
| --- | --- |
| frontend/runtime DB | `sc_acceptance_audit_20260510` |
| login user | `wutao` / `吴涛` |
| action/menu | `action_id=506`, `menu_id=367` |
| project list has `旧系统项目编号` | `true` |
| form has `历史项目资料` tab | `true` |
| form shows sample old project code | `STJ-MYHSTLDCDPZGC-255` |
| form shows sample old project id | `00c73f013e234461883beac337e8d75d` |
| form shows sample old company | `四川保盛建设集团有限公司` |
| form shows sample old source time | `03/31/2020 14:42:08` |
| console errors | `0` |

Browser evidence:

`artifacts/project-legacy-fact-browser-acceptance/20260510T123010/summary.json`

Daily dev acceptance uses `.env.dev.audit` to lock Odoo to the dedicated audit
database while reusing the normal dev compose project and volumes. The nginx
dev proxy forwards the request DB instead of forcing `sc_demo`, so frontend
tokens and backend initialization remain on the same database.

## Runtime Write Evidence

Project anchor write on `sc_acceptance_audit_20260510`:

| Check | Result |
| --- | ---: |
| input rows | `818` |
| created rows | `15` |
| updated rows | `803` |
| post-write identity count | `818` |
| status | `PASS` |

Read-only postcheck:

| Check | Result |
| --- | ---: |
| payload rows | `818` |
| expected rows | `818` |
| matched project rows | `818` |
| visible contract unlinked rows | `0` |
| status | `PASS` |

## Residual Interpretation

The project source creator coverage remains an old-source observation:

- `source_creator_present`: `266`
- `source_creator_blank`: `489`
- `source_time_present`: `752`
- `source_time_blank`: `3`

Blank legacy creator/time fields must remain blank evidence, not be replaced by
`OdooBot`, `admin`, `system`, import operators, or import timestamps.

## Delivery Rule

This round is complete when the project business facts are carried and
traceable. Later iterations may improve project lifecycle, status, operating
strategy, or user-facing validation, but those upgrades must not rewrite
uncertain legacy facts into artificial certainty.
