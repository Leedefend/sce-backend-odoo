# ITER-2026-04-01-591

- status: PASS
- mode: screen
- layer_target: Frontend Layer
- module: record-view HUD continuity screen
- priority_lane: P1_core_usability
- risk: low

## Decision

- PASS
- next bounded record-view continuity slice is `contract-status prominence ordering`
- keep HUD field set unchanged; only adjust ordering so contract health stays near top continuity signals

## Reason

- key continuity signals are already front-loaded by `589`
- contract status (`契约动作数`、`契约限制数`、`契约可读`、`契约告警数`、`契约降级`) still sits after filter/group context
- for quick decision continuity in record-view, contract health should be visible before deeper filter/group metadata

## Next Iteration Suggestion

- open a bounded P1 implementation batch limited to `useActionViewHudEntriesRuntime.ts` and move contract-status entries ahead of filter/group sections
