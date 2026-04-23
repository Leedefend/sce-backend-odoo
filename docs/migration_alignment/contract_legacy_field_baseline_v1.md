# Contract Legacy Field Baseline v1

Iteration: `ITER-2026-04-13-1838`

Source: `tmp/raw/contract/contract.csv`

Rows: 1694

Fields: 146

## High-Value Legacy Fields

| Field | Meaning inferred from source | Non-empty rows | First-round handling |
|---|---|---:|---|
| `Id` | legacy contract primary id | 1694 | identity candidate |
| `DJBH` | old document number | 1694 | identity/reference candidate |
| `XMID` | old project id | 1694 | project relation key, requires mapping |
| `f_XMMC` | old project name | 1694 | reference text only |
| `f_XMJL` | project manager name | 244 | defer or text match |
| `f_GCXZ` | business nature/project mode | 1611 | dictionary mapping |
| `f_HTDLRQ` | contract date/signing date candidate | 1669 | date candidate |
| `f_GCDZ` | project/contract address | 1381 | text candidate |
| `f_GCNR` | work content | 974 | long text candidate |
| `f_GCKGRQ` | start date candidate | 329 | date candidate |
| `JGRQ` | finish date candidate | 321 | date candidate |
| `GCYSZJ` | contract budget/original amount candidate | 1651 | amount candidate |
| `HTBH` | contract number/code | 1694 | reference/code candidate, not unique enough alone |
| `HTBT` | contract title/subject | 1663 | subject candidate |
| `FBF` | employer/issuer party text | 1628 | partner text match |
| `CBF` | contractor party text | 1600 | partner text match |
| `HTLX` | contract category/type text | 865 | dictionary mapping |
| `LX` | old module/type source | 867 | reference/source marker |
| `D_SCBSJS_HTJGFS` | price model text | 108 | dictionary/text candidate |
| `D_SCBSJS_SFGD` | archive/fixed marker candidate | 1653 | boolean/text candidate |
| `DEL` | old deletion marker | 967 | reject/filter candidate |
| `PID` | old external numeric id/root marker | 1694 | reference identity candidate |
| `f_WBHTBH` | old external contract number | 867 | identity/reference candidate |
| `XMBM` | project code | 2 | weak reference only |
| `HTYDFKFS` | payment terms / contract payment method text | 1540 | long text, not first-write safe |
| `f_FJ` | attachment reference | 1694 | attachment reference only |

## Distinct Value Baseline

| Field | Top values |
|---|---|
| `SJBMC` | `外部合同管理=867`, empty=827 |
| `DJZT` | `2=1484`, `0=118`, empty=41, `1=32`, `-1=19` |
| `f_GCXZ` | `联营=1580`, empty=83, `自营=31` |
| `HTLX` | empty=829, `房建工程=326`, `劳务工程=158`, `专业分包=128`, `消防工程=68`, `市政工程=63`, `装修装饰=52` |
| `LX` | `外部合同管理(新)=867`, empty=827 |
| `D_SCBSJS_HTJGFS` | empty=1586, `固定单价合同=62`, `固定总价合同=46` |
| `D_SCBSJS_SFGD` | `是=1479`, `否=174`, empty=41 |
| `DEL` | `0=902`, empty=727, `1=65` |

## Identity Baseline

| Candidate | Non-empty unique values | Duplicate value count | Conclusion |
|---|---:|---:|---|
| `Id` | 1694 | 0 | best legacy identity |
| `DJBH` | 1693 | 1 | useful reference, not sole upsert key |
| `HTBH` | 1611 | 40 | not safe as sole identity |
| `PID` | 828 | 1 | mixed source marker, not sole identity |
| `f_WBHTBH` | 867 | 0 | useful external reference for subset |

## Project Relation Baseline

`XMID` is populated on all 1694 rows.

Against raw project export `tmp/raw/project/project.csv`:

- raw project IDs: 755
- contract rows whose `XMID` matches raw project `ID`: 1606
- unique matching project IDs: 699

Against known written project skeleton artifact IDs:

- known written project IDs from artifacts: 130
- contract `XMID` matches known written project IDs: 121

Conclusion: contract import cannot run independently. It must follow a project mapping gate and can only write rows whose `XMID` maps to an existing `project.project.legacy_project_id`.
