# Agent Instructions (Iteration-Driven Mode)

---

## 0. Core Principle

This repository uses a **controlled continuous iteration model**.

The agent MUST:
- Execute tasks one iteration at a time
- Produce verifiable output for each iteration
- Stop automatically when risk or uncertainty is detected

---

## 1. Task-Driven Execution (MANDATORY)

Before any coding:

1. A valid task contract MUST exist under:
   agent_ops/tasks/*.yaml

2. The agent MUST:
   - Load the task contract
   - Respect allowed / forbidden paths
   - Follow change rules
   - Execute acceptance commands

❌ If no task contract → STOP

---

## 2. Iteration Loop (Agent Loop)

Each iteration MUST follow:

1. Plan
   - Identify Layer Target / Module / Reason

2. Implement
   - Only modify allowed paths

3. Verify
   - Run all required `make verify.*` commands

4. Report
   - Generate iteration report:
     - changed files
     - verification result
     - risk summary
     - next suggestion

5. Decide
   - PASS → continue next task
   - PASS_WITH_RISK → STOP
   - FAIL → STOP

---

## 3. Mandatory Preflight (Before Any Edit)

Always run:

- `pwd`
- `git rev-parse --show-toplevel`
- `git branch --show-current`
- `git status --short`

---

## 4. Execution Policy

- Must follow:
  - `docs/ops/codex_execution_allowlist.md`
  - `docs/ops/codex_workspace_execution_rules.md`

- Allowed branches:
  - feat/*
  - feature/*
  - codex/*
  - experiment/*

- Forbidden:
  - main / master / release/* direct modification

---

## 5. Architecture Guard (MANDATORY)

Before coding:

- Read:
  - `ARCHITECTURE_GUARD.md`
  - `docs/architecture/ai_development_guard.md`

Must declare:

- Layer Target
- Module
- Reason

---

## 6. Risk & Stop Conditions (CRITICAL)

The agent MUST STOP immediately if:

1. Any forbidden path is modified
2. Any of the following files are touched:
   - security/**
   - record_rules/**
   - ir.model.access.csv
   - *payment*
   - *settlement*
   - *account*
   - __manifest__.py
3. Any `make verify.*` fails
4. Contract structure changes (field rename/remove)
5. Diff exceeds safe size threshold
6. Task cannot be completed with certainty

---

## 7. Allowed Change Rules

- Prefer additive changes only
- Do NOT modify:
  - core business facts
  - financial semantics
  - ACL / record rules

---

## 8. Reporting Requirement

Each iteration MUST produce:

- Summary of change
- Verification result
- Risk analysis
- Rollback suggestion
- Next iteration suggestion

---

## 9. Continuous Iteration Mode

The agent MAY continue automatically ONLY IF:

- Last iteration result = PASS
- No risk triggered
- Next task is low-risk

Otherwise → STOP

---

## 10. Priority Strategy

Always prioritize:

1. User-visible outcome
2. Read-only extension
3. Verification completeness

Avoid:

- premature architecture abstraction
- cross-module refactor
- schema change

---