# Codex Trace Usage v1

## Purpose
Observe Codex execution process output for debugging and replay. This is not a formal delivery artifact.

## Normal Usage
```bash
codex
```

## Trace Usage
```bash
bash scripts/ops/codex_trace_run.sh
```

## Verification Usage
```bash
bash scripts/ops/codex_trace_run.sh true
```

## Output Directory
```text
artifacts/codex_trace/YYYY-MM-DD/
```

## Notes
- Do not submit trace logs to Git.
- Do not use trace logs as release evidence.
- Use only for manual replay, debugging, and Codex behavior tuning.
- Do not integrate this wrapper into `verify.*`, `release.*`, or formal report flows.
