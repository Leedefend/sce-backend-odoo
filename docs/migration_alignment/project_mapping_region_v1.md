# Project Region Mapping v1

## Source Summary

| Legacy Field | Non-Empty Rows | Unique Values |
| --- | ---: | --- |
| `SSDQID` | 0 | none |
| `SSDQ` | 0 | none |

## Mapping Table

| Legacy Region ID | Legacy Region Name | Rows | Candidate | Match Mode | Confidence | Manual Confirm |
| --- | --- | ---: | --- | --- | --- | --- |
| empty | empty | 755 | none | defer | none | no source value in this export |

## Coverage

| Metric | Value |
| --- | ---: |
| source non-empty rows | 0 / 755 = 0.00% |
| dictionary mapped rows | N/A |
| unresolved rows caused by actual region values | 0 |

## Decision

No region dictionary can be derived from this CSV export because both region
columns are empty. First import may leave `legacy_region_id` and
`legacy_region_name` empty. Region is not a blocker for first-round project
import.
