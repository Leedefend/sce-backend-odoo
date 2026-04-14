# Project member neutral pair consolidation v1

Status: PAIR_CONSOLIDATION_RULE_READY  
Iteration: `ITER-2026-04-14-0030ZA`

## Positioning

`sc.project.member.staging` is an evidence layer.

The consolidated pair is a readonly governance projection over that evidence
layer. It is not a new business fact table and is not a replacement for
`project.responsibility`.

## Pair Key

The pair key is:

```text
project_id + user_id
```

One consolidated pair represents the governance reading of all neutral evidence
rows that share the same `project_id/user_id`.

## Evidence To Pair Relationship

Relationship:

```text
one consolidated pair -> many neutral evidence rows
```

The pair is the parent governance reading. Evidence rows remain the child
source records and preserve `legacy_member_id`, `legacy_project_id`,
`legacy_user_ref`, `import_batch`, `evidence`, and `notes`.

## Readonly Pair Fields

The minimum readonly pair output should include:

- `pair_key`;
- `project_id`;
- `user_id`;
- `evidence_count`;
- `role_fact_status_summary`;
- `batch_list`;
- `duplicate_evidence`;
- `first_neutral_id`;
- `last_neutral_id`.

## Consumer Rule

Future human review, statistics, and promotion candidate checks should read the
consolidated pair projection first.

Raw evidence rows must not be consumed as formal member responsibility semantics.
They remain traceability records under the pair.

## Current Profile

The readonly profile reports:

| Item | Count |
| --- | ---: |
| total evidence rows | 534 |
| total distinct pairs | 362 |
| duplicate pair count | 120 |
| max evidence per pair | 5 |
