# Complexity Budget Policy

This policy defines the first v1.1 limits for code-size governance. The initial phase is report-first: large files are identified and assigned before hard blocking begins.

## File Size Budget

| Category | Warning | Requires Split Plan |
| --- | ---: | ---: |
| Python source | 800 lines | 1500 lines |
| JavaScript/TypeScript/Vue source | 800 lines | 1500 lines |
| XML data/view file | 1200 lines | 2500 lines |
| Shell script | 250 lines | 500 lines |
| Makefile fragment | 300 lines | 600 lines |

## Method and Function Budget

| Category | Warning | Requires Refactor Plan |
| --- | ---: | ---: |
| Python function/method | 80 lines | 150 lines |
| JavaScript/TypeScript function | 80 lines | 150 lines |
| Vue component setup block | 250 lines | 500 lines |

## Governance Rules

- Files above the split-plan threshold must have an owner and a decomposition direction.
- Large files may be changed for defects, but unrelated additions should move to a smaller owned module.
- New files should stay below the warning threshold unless an ADR explains why.
- The root `Makefile` should keep stable user-facing entries and delegate implementation details to scripts or included fragments over time.
- Generated files are exempt only if the generator is owned and freshness is checked.

## First Enforcement Step

During v1.1 convergence:

1. Generate and review a large-file report.
2. Assign owners to split-plan files.
3. Convert repeated Makefile bodies into scripts or included fragments.
4. Add hard CI limits only after the current baseline has an approved exception list.

## P0 Debt Lock

The first hard limit is active for the P0 split-plan files listed in
`complexity_baseline_lock.json`.

- Current line counts are ceilings, not targets.
- Reductions are accepted without changing the baseline.
- Increases fail `make ci` through `architecture.complexity_baseline_lock`.
- Raising a ceiling requires an explicit architecture review because it means a known split-plan file is absorbing new responsibility.
