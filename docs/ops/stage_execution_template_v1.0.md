# Stage Execution Template v1.0

Use this template for stage/sprint execution reports.
Copy the sections and fill in the evidence blocks.

## Branch + SHA
- Branch:
- SHA:

## Git Diff / Files Changed
- `git show --name-status -1`

## Commands Executed (PASS/FAIL)
- `make codex.preflight DB=...`:
- `make ci.gate.tp08 DB=sc_demo`:
- `make p2.smoke DB=...` or `make p3.smoke DB=...`:
- `make p3.audit DB=...` (if applicable):

## Evidence Blocks
- tp08 tail:
```
<paste tail with [GATE][PASS]>
```
- smoke tail:
```
<paste tail with RESULT: PASS>
```
- git status:
```
<paste `git status` or `git status --porcelain`>
```

## Release Actions (Optional)
- Tag:
- Merge:
- Release index:
