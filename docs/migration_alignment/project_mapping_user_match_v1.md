# Project User Name Match v1

## Source Summary

| Legacy Field | Non-Empty Rows | Unique Values |
| --- | ---: | --- |
| `PROJECTMANAGER` | 0 | none |
| `TECHNICALRESPONSIBILITY` | 0 | none |
| `XQRGZR` | 0 | none |
| `XQRGZXZR` | 0 | none |

The export does include audit names such as `LRR` and `XGR`, but those fields
are deferred as audit metadata and are not project responsibility assignments in
this batch.

## Runtime User Candidate Sample

Current `sc_demo` contains active users such as `吴涛`, `杨德胜`, `李林旭`,
`李娜`, `张文翠`, `李俭锋`, `叶凌越`, `李德学`, `陈帅`, `肖辉玖`, `罗萌`,
and `胡俊`, plus test/demo users.

## Match Table

| Source Field | Source Name | Rows | Candidate User | Match Mode | Confidence | Manual Confirm |
| --- | --- | ---: | --- | --- | --- | --- |
| `PROJECTMANAGER` | none | 0 | none | text_match | N/A | no source value |
| `TECHNICALRESPONSIBILITY` | none | 0 | none | text_match | N/A | no source value |
| `XQRGZR` | none | 0 | none | text_match | N/A | no source value |
| `XQRGZXZR` | none | 0 | none | text_match | N/A | no source value |

## Success Rate

| Metric | Value |
| --- | ---: |
| matchable unique source names | 0 |
| exact matched unique names | N/A |
| matched rows | N/A |

## Decision

First import should preserve raw manager/technical responsibility fields when
present in future exports, but this CSV has no project-responsibility source
names to map. Do not auto-write `project_manager_user_id` or
`technical_lead_user_id` from this export.
