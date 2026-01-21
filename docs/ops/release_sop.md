# Release SOP (Stage → Gate → Tag → Release)

## 1) Stage + Evidence
- Run stage definitions for the target scope.
- Require `STAGE_RESULT: PASS` and evidence markers present.
- Collect reports in `out/stage_reports/` (`.md` + `.json`).

## 2) Gate
- Run `make ci.gate.tp08 DB=sc_demo`.
- Gate must pass before any merge.

## 3) Tag
- Use canonical, documented tag semantics only.
- If a legacy tag exists, document it as legacy and do not use it for release.

## 4) Release Index
- Update `docs/ops/releases/README.md` with:
  - tag, type, status, docs, verify commands.
- Commit the index update separately if required by SOP.

## 5) Merge + Push
- Merge to `main` only after gates pass.
- Push `main` and the release tag to origin.

## 6) Evidence Pack
- Include command outputs for gates, stages, tags, and pushes.
- Keep evidence in the release report or designated artifact.
