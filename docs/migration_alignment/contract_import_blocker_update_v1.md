# Contract Import Blocker Update v1

Iteration: `ITER-2026-04-13-1840`

## Blocker Status

| Blocker from 1839 | Status after 1840 |
|---|---|
| No confirmed target legacy contract identity field | resolved |
| Partner exact match rate is 0 | still blocked |
| Only 146 rows map to known written project skeletons | still constrained |
| Tax and computed amount semantics not frozen | still blocked |
| Contract line source not identified | still blocked |
| `DEL=1` handling not implemented in importer | still blocked |
| Workflow state replay not frozen | still blocked |

## Updated Gate

Contract write remains `NO-GO`.

The model can now carry legacy contract identity/reference facts, but no contract row should be created until partner matching and safe-slice write rules are resolved.

## Next Recommended Batch

`ITER-2026-04-13-1841 合同 partner 主数据匹配与安全候选重算专项 v1`

Minimum requirements:

- build `FBF` / `CBF` counterparty text distinct table
- compare against current `res.partner`
- produce exact/fuzzy/manual partner match candidates
- decide whether to create partner master data first or defer contract write
- rerun safe candidate count using the new partner match table
