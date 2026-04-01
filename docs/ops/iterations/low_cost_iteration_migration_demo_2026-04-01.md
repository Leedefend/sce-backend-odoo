# Low-Cost Iteration Migration Demo 2026-04-01

## 1. 原任务

- task: `agent_ops/tasks/ITER-2026-04-01-522.yaml`
- objective: screen remaining natural candidates on the config-admin governance line
- issue: the original task mixes candidate discovery, classification intent, and verification-style acceptance in one contract

## 2. 拆分后任务

- scan: `agent_ops/tasks/ITER-2026-04-01-522-A.yaml`
- screen: `agent_ops/tasks/ITER-2026-04-01-522-B.yaml`
- verify: `agent_ops/tasks/ITER-2026-04-01-522-C.yaml`

## 3. 每阶段输入与输出

### A. Scan

- input:
  - base task scope
  - low-cost limits
  - `agent_ops/templates/prompts/lead_scan.txt`
- output:
  - structured candidate list only
  - no more than 15 candidates
  - no conclusion

### B. Screen

- input:
  - `ITER-2026-04-01-522-A`
  - `agent_ops/templates/prompts/lead_screen.txt`
- output:
  - `next_candidate_family`
  - `family_scope`
  - `reason`

### C. Verify

- input:
  - `ITER-2026-04-01-522-B`
  - `agent_ops/templates/prompts/lead_verify.txt`
  - declared verification commands only
- output:
  - `PASS | FAIL | STOP`
  - `violations`
  - `decision`

## 4. 预计如何降低上下文消耗

- single-stage contracts prevent one session from carrying scan, reasoning, and verification together
- prompt templates replace repeated long-form operator prompts
- new-session enforcement prevents long context reuse across A/B/C
- bounded limits (`max_files`, `max_candidates`, `max_output_lines`) cap scan breadth and response size
- no repo-wide scan reduces unnecessary file loading and token waste
- verify-only final stage stops downstream re-analysis once the screen result exists

## 5. 使用方式

```bash
make task.split TASK=agent_ops/tasks/ITER-2026-04-01-522.yaml
make task.validate.low_cost TASK=agent_ops/tasks/ITER-2026-04-01-522-A.yaml
make task.validate.low_cost TASK=agent_ops/tasks/ITER-2026-04-01-522-B.yaml
make task.validate.low_cost TASK=agent_ops/tasks/ITER-2026-04-01-522-C.yaml
make task.run.low_cost TASK=ITER-2026-04-01-522
```
