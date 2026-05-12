# Fresh DB Project Anchor Replay Adapter Report v1

Status: PASS

Task: `ITER-2026-05-07-FRESH-DB-REPLAY-PROJECT-ANCHOR-CONSOLIDATED`

## Scope

Build a no-DB consolidated replay payload for project anchors from the project
master source and visible contract-fact project anchors. This batch does not
execute project write scripts and does not touch a database.

## Result

- project master source rows: `755`
- project master contract-enriched rows: `1`
- contract visible project anchor rows: `43`
- contract business-fact project anchor rows: `20`
- non-visible contract project anchor observations: `20`
- non-visible contract project anchor amount: `43266877.41`
- replay payload rows: `818`
- duplicate replay identities: `0`
- raw source misses: `0`
- deleted source rows in payload: `61`
- DB writes: `0`

## Source Lanes

```json
{
  "contract_project_business_fact_anchor": 20,
  "contract_visible_project_anchor": 43,
  "project_master": 754,
  "project_master_contract_enriched": 1
}
```

## Operation Strategy

```json
{
  "direct": 36,
  "joint": 780,
  "unspecified": 2
}
```

## Stage Counts

```json
{
  "unknown": 818
}
```

## Decision

`project_anchor_replay_payload_ready`

## Next

run unified project anchor replay write before dependent fact replay
