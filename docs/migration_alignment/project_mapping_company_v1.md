# Project Company Mapping v1

## Source Summary

- Rows scanned: 755
- Unique legacy company IDs: 8
- Unique legacy company names: 7
- Runtime candidates from `res.company`: `My Company`, `四川保盛建设集团有限公司`

## Mapping Table

| Legacy Company ID | Legacy Company Name | Rows | Candidate | Match Mode | Confidence | Manual Confirm |
| --- | --- | ---: | --- | --- | --- | --- |
| `1` | `四川保盛建设集团有限公司` | 569 | `res.company(2) 四川保盛建设集团有限公司` | exact | high | no |
| `141` | `四川保盛建设集团有限公司` | 90 | `res.company(2) 四川保盛建设集团有限公司` | exact | high | yes, because two legacy IDs collapse to one company |
| `570` | `保盛重庆分公司` | 52 | none | dictionary | none | yes |
| `565` | `保盛新疆分公司` | 23 | none | dictionary | none | yes |
| `571` | `保盛绵阳分公司` | 15 | none | dictionary | none | yes |
| `567` | `保盛西藏分公司` | 3 | none | dictionary | none | yes |
| `572` | `保盛广元分公司` | 2 | none | dictionary | none | yes |
| `608` | `项目实施分公司` | 1 | none | dictionary | none | yes |

## Coverage

| Metric | Value |
| --- | ---: |
| exact matched rows | 659 / 755 = 87.28% |
| exact matched unique names | 1 / 7 = 14.29% |
| exact matched unique ID/name pairs | 2 / 8 = 25.00% |
| unresolved rows | 96 |
| unresolved unique ID/name pairs | 6 |

## Uncovered Values

- `570 / 保盛重庆分公司`
- `565 / 保盛新疆分公司`
- `571 / 保盛绵阳分公司`
- `567 / 保盛西藏分公司`
- `572 / 保盛广元分公司`
- `608 / 项目实施分公司`

## Import Readiness

Do not write `company_id` automatically for unresolved branch companies. First
import can preserve `legacy_company_id` and `legacy_company_name`; automatic
`company_id` write is safe only for exact matches after accepting that legacy
IDs `1` and `141` both point to the same current company.
