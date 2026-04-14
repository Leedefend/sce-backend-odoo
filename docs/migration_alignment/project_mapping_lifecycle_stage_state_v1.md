# Project Lifecycle / Stage / State Mapping v1

## Source Summary

| Legacy Field | Non-Empty Rows | Unique Values |
| --- | ---: | --- |
| `XMJDID` | 0 | none |
| `XMJD` | 0 | none |
| `STATE` | 147 | `0` |
| `IS_COMPLETE_PROJECT` | 481 | `否`, `是` |
| `DEL` | 752 | `0`, `1` |

## Current Runtime Stage Candidates

| Stage | Sequence |
| --- | ---: |
| `筹备中` | 5 |
| `在建` | 10 |
| `停工` | 20 |
| `竣工` | 30 |
| `结算中` | 40 |
| `保修期` | 50 |
| `关闭` | 60 |

## Dry-Run Mapping

| Legacy Signal | Rows | Candidate Target | Mapping Type | Confidence | Manual Confirm |
| --- | ---: | --- | --- | --- | --- |
| `XMJDID` empty | 755 | `legacy_stage_id` empty | direct | high | no |
| `XMJD` empty | 755 | `legacy_stage_name` empty | direct | high | no |
| `STATE=0` | 147 | `legacy_state='0'` | direct | high | no |
| `STATE=0` | 147 | candidate `lifecycle_state='draft'` or current default | dictionary | low | yes |
| `IS_COMPLETE_PROJECT=否` | 466 | no normalized target yet | defer | none | yes |
| `IS_COMPLETE_PROJECT=是` | 15 | candidate `lifecycle_state='done'` or `closed` | dictionary | low | yes |
| `DEL=0` | 691 | candidate active record | defer | medium | yes |
| `DEL=1` | 61 | candidate archived/inactive record | defer | low | yes |

## Coverage

| Metric | Value |
| --- | ---: |
| raw legacy state preservation | 147 / 147 = 100.00% |
| normalized lifecycle/stage automatic coverage | 0 / 755 = 0.00% |
| rows requiring lifecycle/delete confirmation | 542 |

## Decision

First import can preserve raw fields (`legacy_stage_id`, `legacy_stage_name`,
`legacy_state`) and rely on current default lifecycle behavior. It should not
auto-write `stage_id`, `lifecycle_state`, or `active` from `STATE`,
`IS_COMPLETE_PROJECT`, or `DEL` until a lifecycle conversion table is approved.
