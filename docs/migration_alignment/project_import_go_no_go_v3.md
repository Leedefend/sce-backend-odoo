# Project Import GO/NO-GO v3

## Decision

- GO: continue to a non-write first-create rehearsal for the same 30-row safe
  sample, or prepare a write-mode design gate for create-only skeleton import.
- NO-GO: do not run upsert/update-mode write import against `sc_demo` yet.

## Evidence

| Check | Result |
| --- | ---: |
| target database | `sc_demo` |
| target identity export | PASS |
| target identity rows | 0 |
| sample rows | 30 |
| safe-slice fields | 22 |
| create | 30 |
| update | 0 |
| error rows | 0 |
| header errors | 0 |
| no DB write during dry-run | PASS |

## Interpretation

The target database has no exported `legacy_project_id` identities, so the
dry-run correctly classifies all 30 sample rows as `create`.

This result is acceptable only if `sc_demo` is the intended empty target for the
first project skeleton import. It is not sufficient for an update/upsert import
because no target identity match was available.

## GO Scope

Allowed next steps:

- Run a stricter non-write create-only rehearsal with negative samples.
- Prepare a dedicated write-mode design gate for 30-row skeleton create import.
- If update behavior is required, seed or select a target database that already
  has project skeletons with `legacy_project_id`, then rerun the target-identity
  rehearsal before any write import.

## NO-GO Scope

Do not proceed to upsert/update write import until:

- target identity export contains reviewed `legacy_project_id` values, or
- the batch is explicitly re-scoped as create-only import into an empty target.

Do not include company, specialty, lifecycle/state, user, partner, contract,
payment, supplier, tax, bank, cost, or attachment write mapping in the next
project skeleton batch.

## Current Conclusion

The project skeleton importer is ready for a create-only write-mode design gate
for `sc_demo`, not for general upsert/update write import.
