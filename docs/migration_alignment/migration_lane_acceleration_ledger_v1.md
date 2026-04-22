# Migration lane acceleration ledger v1

Status: PLAN_READY
Iteration: `ITER-2026-04-14-MIG-FAST-LEDGER`

## Purpose

Close the current migration branch state into a single ledger before resuming
the frozen main line. This prevents each later batch from re-reading the whole
delivery log to decide whether a lane can move.

## Global rules

- Current validation database: `sc_demo`.
- Formal rebuild target: a new future database, not an in-place rebuild of
  `sc_demo`.
- Frozen lane order remains:
  `project -> partner -> project_member -> contract -> receipt -> payment/settlement -> file index -> file binary`.
- One write batch may touch only one lane and one target model family.
- Every write must have a rollback target list keyed by the same legacy identity
  used for idempotency.
- Payment, settlement, account, ACL, record rule, security, and manifest domains
  remain stopped unless a dedicated high-risk task line is opened.

## Lane ledger

| Lane | Current validation state | Current promotion state | Next allowed stage | Acceleration decision |
| --- | --- | --- | --- | --- |
| `project` | 755 rows materialized and post-write reviewed | Baseline frozen | Downstream consumption only | Do not expand. Only open correction batches if project facts are proven wrong. |
| `partner` | 100-row safe-slice create-only write reviewed as `ROLLBACK_READY` | L3 bounded-write evidence exists | L4 candidate promotion | Resume main line here. Generate full no-DB decision, then expand by reviewable slices. |
| `project_member_neutral` | 534 evidence rows in `sc.project.member.staging`; no permission semantics | L3 neutral evidence carrier evidence exists | More neutral evidence slices only | May continue after partner L4 plan, but must stay separate from responsibility writes. |
| `project_member_responsibility` | 3 `manager` sample rows written and impact-reviewed; rollback eligible | Sample evidence only | Hold / rollback / separately authorized expansion | Keep as observation sample for now. Do not expand without role-source rule and legal role-key gate. |
| `contract` | 12 header rows written and post-write reviewed as `ROLLBACK_READY` | L3 header sample evidence exists | Contract full no-DB classification after partner baseline | Do not expand until partner L4 candidate output is stable. |
| `receipt` | Stopped | Not promoted | No movement | Wait for contract readiness. |
| `payment / settlement` | Stopped high-risk financial domain | Not promoted | No movement | Dedicated boundary and financial semantics task required. |
| `file index` | Stopped | Not promoted | No movement | Wait for business identity lanes. |
| `file binary` | Stopped | Not promoted | No movement | Wait for file index validation. |

## Branch closure decision

The `project_member` responsibility branch is not the main migration line. Its
three-row `manager` sample is reviewable and rollback eligible, but it does not
authorize further responsibility expansion. The branch remains closed until one
of these happens in a dedicated task:

- rollback is explicitly requested;
- a verified role-source rule maps legacy project-member evidence to existing
  legal role keys;
- business approval explicitly authorizes a bounded expansion using an existing
  legal `project.responsibility.role_key`.

Neutral project-member evidence may continue independently because it writes to
`sc.project.member.staging` and does not grant authority or responsibility.

## Main-line acceleration target

The next executable main-line target is partner L4 candidate promotion:

1. Run partner no-DB full decision using the existing importer shape.
2. Freeze safe candidates and blockers in machine-readable outputs.
3. Execute bounded partner slices only after each slice has a rollback target
   and immediate readonly post-write review.
4. Promote to L4 only after repeatable dry-run plus at least one reviewed
   bounded write proves idempotency and rollback selection.

## Stop conditions

- Any non-partner model write during partner promotion.
- Any update/upsert to partner records before a dedicated update policy exists.
- Duplicate `legacy_partner_source + legacy_partner_id`.
- Rollback target selection not exactly matching the current write slice.
- Any request to touch payment, settlement, account, ACL, security, manifest, or
  record rules.
