# Project Write Trial Next Gate v1

## Decision

| Question | Decision |
| --- | --- |
| 当前是否允许真实回滚 | Not in this batch. Technically ready, but requires a separate explicit delete authorization batch. |
| 当前是否允许扩大 create-only 样本 | Not yet. Expansion remains blocked until default `stage_id` behavior is manually accepted or handled. |
| 下一轮方向 | Default `stage_id` policy confirmation, then either real rollback authorization or bounded create-only expansion. |

## Evidence

| Metric | Value |
| --- | ---: |
| rollback dry-run status | `ROLLBACK_READY` |
| total_targets | 30 |
| matched_rows | 30 |
| missing_rows | 0 |
| duplicate_matches | 0 |
| out_of_scope_matches | 0 |
| stage_id_all_same | true |
| default stage | `5 / 筹备中` |

## Real Rollback Gate

Real rollback is allowed only after:

1. a new task contract explicitly authorizes deletion;
2. rollback dry-run is rerun and still returns `ROLLBACK_READY`;
3. target count remains exactly 30;
4. no missing, duplicate, or out-of-scope records are found;
5. deletion remains scoped only by `legacy_project_id`;
6. no related company, partner, user, contract, payment, supplier, tax, bank,
   cost, settlement, or attachment records are touched.

## Expansion Gate

Create-only expansion is blocked until:

1. manual review accepts `stage_id=5 / 筹备中` as the default skeleton stage, or a
   replacement stage policy is approved;
2. rollback dry-run remains reproducible;
3. the existing 30 write-trial records are accepted as usable skeleton data;
4. a new bounded sample size is declared;
5. the next task remains create-only and safe-slice-only.

## Current Recommendation

Next round should be the default `stage_id` policy confirmation. If business
accepts `筹备中` as the first-round skeleton default, proceed to bounded
create-only sample expansion. If not, open a stage-policy gate before any
additional import.
