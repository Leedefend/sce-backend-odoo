# Project Business Nature / Environment Mapping v1

## Source Summary

| Field | Values |
| --- | --- |
| `NATURE` | `联营` 722 rows; `自营` 30 rows; empty 3 rows |
| `PROJECT_ENV` | `正式项目` 487 rows; `测试项目` 1 row; empty 267 rows |
| `PRICE_METHOD` | `1` 611 rows; `0` 144 rows |

## Mapping Table

| Legacy Field | Value | Rows | Target | Mapping Type | Confidence | Manual Confirm |
| --- | --- | ---: | --- | --- | --- | --- |
| `NATURE` | `联营` | 722 | `business_nature='联营'` | direct | high | no |
| `NATURE` | `自营` | 30 | `business_nature='自营'` | direct | high | no |
| `NATURE` | empty | 3 | empty | direct | high | no |
| `PROJECT_ENV` | `正式项目` | 487 | `project_environment='正式项目'` | direct | high | no |
| `PROJECT_ENV` | `测试项目` | 1 | `project_environment='测试项目'` | direct | high | yes, decide whether to exclude test data |
| `PROJECT_ENV` | empty | 267 | empty | direct | high | no |
| `PRICE_METHOD` | `1` | 611 | `legacy_price_method='1'` | direct | high | no |
| `PRICE_METHOD` | `0` | 144 | `legacy_price_method='0'` | direct | high | no |

## Optional Normalization Candidates

| Source | Candidate Normalization | Mapping Type | Confidence | Manual Confirm |
| --- | --- | --- | --- | --- |
| `NATURE=联营` | business nature class `joint_operation` | dictionary | medium | yes |
| `NATURE=自营` | business nature class `self_operated` | dictionary | medium | yes |
| `PROJECT_ENV=正式项目` | import include by default | dictionary | medium | yes |
| `PROJECT_ENV=测试项目` | import exclude or mark test | dictionary | low | yes |

## Coverage

Raw preservation coverage is 755 / 755 = 100.00% for these three fields. No
normalized dictionary write should be performed until a later policy decision.
