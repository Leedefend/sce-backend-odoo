# New System Approval Business Fact Usability Judgment v1

Status: `FROZEN_JUDGMENT`

## Overall judgment

The new approval mechanism is technically installed and partially wired, but
its business facts are not currently usable as a reliable migration target.

Use it for future runtime approval only after approval definitions, reviewer
visibility, callback behavior, and smoke tests are completed. Do not use it to
absorb legacy approval history.

Short form:

```text
framework_installed_but_business_fact_unready
```

## Current database facts

Database: `sc_demo`

Installed modules:

| Module | State |
|---|---|
| `base_tier_validation` | installed |
| `base_tier_validation_server_action` | installed |
| `smart_construction_core` | installed |

Runtime fact counts:

| Fact | Count |
|---|---:|
| `tier.definition` | 0 |
| `tier.review` | 0 |
| `payment.request` | 110 |

Payment request state distribution:

| State | validation_status | Count |
|---|---|---:|
| `approved` | `no` | 19 |
| `done` | `no` | 19 |
| `done` | `validated` | 22 |
| `draft` | `no` | 50 |

Every sampled `payment.request` has `review_count = 0` when joined to
`tier.review`. This means current payment approval status is not backed by
visible `tier.review` rows in the runtime database.

## Business fact usability

### What is technically available

`base_tier_validation` can represent these runtime facts:

| Runtime fact | Carrier |
|---|---|
| approval rule | `tier.definition` |
| target document | `tier.review.model` + `tier.review.res_id` |
| reviewer identity | `reviewer_id`, `reviewer_group_id`, computed `reviewer_ids` |
| review sequence | `tier.review.sequence` |
| review status | `waiting`, `pending`, `approved`, `rejected` |
| approving user | `done_by` |
| reviewed time | `reviewed_date` |
| reviewer comment | `comment` |

`payment.request` is wired to the approval framework:

- it inherits `tier.validation`
- `action_submit()` calls `request_validation()`
- approval and rejection server actions call:
  - `action_on_tier_approved()`
  - `action_on_tier_rejected()`
- `validation_status` gates later payment completion behavior

### What is not currently available

The business approval runtime has no configured rules:

- no `tier.definition`
- no reviewer assignment facts
- no active domain rules
- no approval sequences
- no post-approve / post-reject definition bindings in data
- no `tier.review` rows proving current approval history

Therefore the current database does not yet provide a complete approval fact
chain from:

```text
business document -> approval definition -> reviewer -> review decision -> callback result
```

## Usability gaps

### 1. No approval definitions

Without `tier.definition`, `request_validation()` has nothing to instantiate.
Submitting a payment request can only become meaningful after business approval
rules are configured or seeded.

### 2. No approval review rows

`tier.review` is empty. This means there is no current new-system evidence for:

- pending approvals
- completed approval decisions
- reviewer identities
- approval comments
- reviewed timestamps

### 3. Existing `validation_status` is not self-sufficient

There are `payment.request` records with `validation_status = validated` and no
matching `tier.review` rows. That status alone is not enough audit evidence.
It may be stale, imported, demo-derived, or produced by a path that did not
leave current review rows.

For migration decisions, `validation_status` must not be treated as a complete
approval business fact unless backed by review rows or another durable audit
carrier.

### 4. Reviewer entry is incomplete for group approval

The current action for payment request approvals filters:

```text
[('reviewer_id','=',uid), ('status','in',('waiting','pending')), ('model','=','payment.request')]
```

But `base_tier_validation` supports group reviewers through
`reviewer_group_id` and computed `reviewer_ids`. A group-based approval may not
be visible in this action if it only checks `reviewer_id`.

### 5. Runtime callbacks are not neutral import paths

The approval server action extension can run post-approve and post-reject
callbacks. For `payment.request`, those callbacks change business state and
write audit transitions.

This is useful for live approval, but unsafe for importing old approval rows.
Legacy approvals must not trigger these callbacks.

## Migration implication

Do not map legacy `S_Execute_Approval` rows into `tier.review`.

Reasons:

- `tier.review` is a live approval runtime carrier, not a neutral archive.
- It requires configured definitions and reviewer semantics.
- It can trigger callbacks that mutate `payment.request`.
- It cannot preserve all legacy workflow setup, step, and source identifiers
  without overloading runtime fields.
- The current database has no working approval fact chain to validate against.

Legacy approvals should stay on the historical approval audit lane defined in:

```text
docs/migration_alignment/frozen/legacy_workflow_approval_assetization_solution_v1.md
```

## Approved target use

Use `base_tier_validation` for future new-system approvals after configuration
and smoke validation.

Use a separate historical carrier for old approvals:

```text
sc.legacy.workflow.audit
```

The two lanes should be related only at the business document display/audit
level. They should not share runtime state.

## Required gates

Before declaring new-system approval business facts usable, complete these
gates:

1. Seed or configure `tier.definition` for `payment.request`.
2. Bind explicit post-approve and post-reject actions to the definitions.
3. Fix reviewer visibility so group-based reviewers can see pending approvals.
4. Run an end-to-end smoke:
   - create payment request
   - submit
   - generate `tier.review`
   - approve as reviewer
   - verify `payment.request.state`
   - verify `validation_status`
   - verify `done_by`, `reviewed_date`, and comment/audit evidence
5. Prove that importing historical audit assets does not create or mutate
   `tier.review`.

## Current classification

| Dimension | Judgment |
|---|---|
| module installation | usable |
| payment request code wiring | partially usable |
| approval rule configuration | not usable |
| runtime approval facts | not usable |
| reviewer UI/action coverage | incomplete |
| migration target for old approvals | not usable |
| future runtime approval foundation | usable after gates |

## Final decision

`new_approval_runtime_not_ready_as_business_fact_source`

The migration mainline should continue with a separate historical approval
audit asset lane. New-system approval should become a later product hardening
batch, not a dependency for legacy approval history migration.
