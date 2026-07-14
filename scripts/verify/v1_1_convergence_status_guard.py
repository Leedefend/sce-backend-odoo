#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STATUS = ROOT / "docs/engineering_convergence/phase0_phase1_status.md"
P0_PLAN = ROOT / "docs/engineering_convergence/p0_split_plan_execution.md"
RISK = ROOT / "docs/engineering_convergence/engineering_risk_ledger.md"
PLAN = ROOT / "docs/engineering_convergence/v1_1_execution_plan.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.is_file() else ""


def main() -> int:
    errors: list[str] = []
    status = _read(STATUS)
    p0_plan = _read(P0_PLAN)
    risk = _read(RISK)
    plan = _read(PLAN)

    for path, text in [
        (STATUS, status),
        (P0_PLAN, p0_plan),
        (RISK, risk),
        (PLAN, plan),
    ]:
        if not text:
            errors.append(f"missing convergence doc: {path.relative_to(ROOT)}")

    for token in [
        "Mainline checkpoint: `7d2f86ec973594d8919474a1f075c0672e557b65`",
        "P4-P0-01 Makefile split",
        "P4-P0-02 Business config surface split",
        "P4-P0-03 Contract form route shell split",
        "Contract governance responsibility baseline",
        "UI contract v2 responsibility baseline",
        "Latest `origin/main` commit `7d2f86ec973594d8919474a1f075c0672e557b65` remote quality gate",
        "Needs workflow run evidence",
        "Core amount calculation tests",
        "Permission and project-isolation verification",
        "Backup and filestore restore drill",
        "Performance baseline",
        "Controlled pilot readiness",
    ]:
        if token not in status:
            errors.append(f"phase0_phase1_status.md missing token: {token}")
    if "Start P4-P0-01" in status:
        errors.append("phase0_phase1_status.md must not point next execution focus at P4-P0-01")

    for token in [
        "The original P4-P0-01, P4-P0-02, and P4-P0-03 sequence has completed on",
        "`Makefile` is 272 lines",
        "`BusinessConfigSurfaceView.vue` is 1486 lines",
        "`ContractFormPage.vue` is 5939 lines",
        "PR `#1052` merged as `b9d9e8cf`",
        "PR `#1053` merged as `815697e`",
        "latest `origin/main` workflow-run evidence still needs to be attached",
    ]:
        if token not in p0_plan:
            errors.append(f"p0_split_plan_execution.md missing token: {token}")

    for token in [
        "| ID | Risk | Level | Owner | Due | Mitigation | Status | Evidence |",
        "| R-001 |",
        "| R-012 |",
        "Closed",
        "Mitigated; still needs",
        "Open",
        "RPO/RTO",
        "performance baseline report",
        "Pilot runbook",
    ]:
        if token not in risk:
            errors.append(f"engineering_risk_ledger.md missing token: {token}")

    for token in [
        "## Current Checkpoint",
        "7d2f86ec973594d8919474a1f075c0672e557b65",
        "core amount calculation tests",
        "permission and project-isolation verification",
        "workflow-run evidence",
    ]:
        if token not in plan:
            errors.append(f"v1_1_execution_plan.md missing token: {token}")

    if errors:
        print("[v1_1_convergence_status_guard] FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[v1_1_convergence_status_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
