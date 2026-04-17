# Business Topic Replay Layer v1

## Purpose
Provide a topic-level replay entry for old business data alignment.

This layer turns one-off deterministic synchronization scripts into a replayable
business topic:

```text
legacy data loaded
→ topic replay plan/check/write
→ per-step logs
→ result.json
→ operational verification
```

## Command

Plan only:

```bash
python3 scripts/migration/replay_business_topic.py \
  --topic imported_business_continuity_v1 \
  --db sc_demo \
  --mode plan
```

Check mode:

```bash
python3 scripts/migration/replay_business_topic.py \
  --topic imported_business_continuity_v1 \
  --db sc_demo \
  --mode check
```

Write mode:

```bash
python3 scripts/migration/replay_business_topic.py \
  --topic imported_business_continuity_v1 \
  --db sc_demo \
  --mode write
```

## Artifacts
Each run writes to:

```text
artifacts/migration/replay/<topic>/<run_id>/
```

The directory contains:

- one log file per step
- check/write logs for Odoo sync steps
- `result.json`

## Guarantees
- Existing sync scripts remain the source of business-fact truth.
- Replay orchestration does not fabricate business facts.
- `write` mode runs `check` before each write-capable step.
- Replay stops on the first failed step.
- `check` mode can be used safely as a topic-level dry run.

## Current Topic Result
The initial check-mode validation passed for `imported_business_continuity_v1`
against `sc_demo`.

Validation artifact:

```text
artifacts/migration/replay/imported_business_continuity_v1/validation_check_v2/result.json
```

All six topic steps passed:

- `project_continuity`
- `contract_continuity`
- `payment_downstream_fact_screen`
- `payment_done_fact`
- `payment_linkage_fact`
- `operational_verify`

## Replay Stability Note
Contract continuity now excludes payment links that were inferred by the later
payment-linkage replay step when the rollback CSV is present. This prevents a
post-topic replay from feeding inferred payment links back into the historical
contract evidence count.
