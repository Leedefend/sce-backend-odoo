# Project Partner Match v1

## Source Summary

| Legacy Field | Non-Empty Rows | Unique Values |
| --- | ---: | --- |
| `OWNERSUNIT` | 0 | none |
| `OWNERSCONTACT` | 0 | none |
| `SUPERVISIONUNIT` | 0 | none |
| `SUPERVISORYENGINEER` | 0 | none |

Company mapping from `COMPANYNAME` is covered separately in
`project_mapping_company_v1.md`.

## Runtime Partner Candidate Sample

Current `sc_demo` company partners include:

- `四川保盛建设集团有限公司`
- `Demo-业主单位`
- `演示业主 · 城市建设集团`
- `城市建设投资集团`
- `德阳市某产业发展有限公司（示例）`

## Match Table

| Source Field | Source Text | Rows | Candidate Partner | Match Mode | Confidence | Manual Confirm |
| --- | --- | ---: | --- | --- | --- | --- |
| `OWNERSUNIT` | none | 0 | none | text_match | N/A | no source value |
| `OWNERSCONTACT` | none | 0 | none | text_match | N/A | no source value |
| `SUPERVISIONUNIT` | none | 0 | none | text_match | N/A | no source value |
| `SUPERVISORYENGINEER` | none | 0 | none | text_match | N/A | no source value |

## Success Rate

| Metric | Value |
| --- | ---: |
| matchable unique source texts | 0 |
| exact matched unique texts | N/A |
| matched rows | N/A |

## Decision

There is no owner/supervision text to match in this CSV export. First import can
preserve empty text fields and should not auto-create or link owner/supervision
partners from these columns.
