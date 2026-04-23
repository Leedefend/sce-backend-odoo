# Project Stage Policy Final v1

## Import Decision

For normalized project import, write lifecycle first, then map to stage:

```text
source facts -> lifecycle_state -> stage_id
```

Do not write `stage_id` as independent truth.

## Final Source Rule

| Source condition | lifecycle_state | stage_id |
| --- | --- | --- |
| `IS_COMPLETE_PROJECT` indicates completed | `done` | 竣工 |
| has approved business execution facts | `in_progress` | 在建 |
| `CONTRACT_STATUS` / `QYZT` indicates signed only | `draft` for current v1, pending later signed-state gate | 筹备中 |
| all other records | `draft` | 筹备中 |

## Important Qualification

The user-provided semantic label says `CONTRACT_STATUS/QYZT -> 已签约`. Current
runtime project lifecycle does not yet define a dedicated `signed` lifecycle
state or `待启动` stage. Therefore v1 must not invent a hidden state.

If signed-but-not-started is a required project truth, open a new state extension
gate before import expansion.

## Current 30-Row Trial

The 30-row create-only trial did not write normalized lifecycle from legacy
signals. Odoo/system default produced:

```text
lifecycle_state = draft
stage_id = 筹备中
```

This remains acceptable only for first-round skeleton records until a normalized
legacy lifecycle conversion table is approved.
