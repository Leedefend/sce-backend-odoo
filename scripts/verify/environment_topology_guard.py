#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

FILES = {
    "makefile": ROOT / "Makefile",
    "environment_tiers": ROOT / "docs/ops/environment_tiers_unified_runbook_v1.md",
    "daily_policy": ROOT / "docs/ops/daily_dev_runtime_repo_policy_v1.md",
    "production_deployment": ROOT / "docs/ops/production_deployment_runbook_v1.md",
    "production_upgrade": ROOT / "docs/ops/production_upgrade_standard_v1.md",
}

REQUIRED_TOKENS = {
    "environment_tiers": (
        "| Daily dev | `sc-root` | `/opt/projects/repos/sce-backend-odoo` | `dev` | `.env.dev` | `sc_demo` |",
        "| Production | `sc-prod` | `/opt/sce/production/sce-backend-odoo` | `prod` | `.env.prod` | `sc_prod` |",
        "The daily development runtime repository is the only deployable `dev` working tree.",
        "Production code authority is `main` or a frozen release package applied under `/opt/sce/production/sce-backend-odoo`.",
        "Do not deploy from scratch worktrees or archived runtime directories.",
        "make verify.daily_dev.runtime_repo.clean",
        "make release.daily_dev.acceptance.publish",
        "ACCEPTANCE_BASE_URL=http://127.0.0.1:18081",
        "ACCEPTANCE_LOGIN=wutao",
        "ACCEPTANCE_PASSWORD",
        "ACCEPTANCE_NAV_MIN_ACTIONS=60",
        "ACCEPTANCE_NAV_MAX_ACTIONS=70",
        "ACCEPTANCE_NAV_FORBIDDEN_LABELS=用户核对菜单,用户数据验收,用户验收,直营项目系统菜单",
        "ACCEPTANCE_PROBE_OUTPUT=artifacts/backend/dev_acceptance_release_probe.json",
        "FRONTEND_DIST_DIR=./frontend/apps/web/dist-dev",
        "VITE_BUILD_MODE",
        "VITE_PLATFORM_ADMIN_DB",
        "VITE_API_BASE_URL",
        "make verify.production_git.authority.guard",
    ),
    "daily_policy": (
        "- Host alias: `sc-root`",
        "- Path: `/opt/projects/repos/sce-backend-odoo`",
        "`ENV=dev`, `.env.dev`, and `DB_NAME=sc_demo`",
        "ENV=dev ENV_FILE=.env.dev DB_NAME=sc_demo make verify.daily_dev.runtime_repo.clean",
        "Do not apply scratch",
        "changes directly to the runtime repository.",
    ),
    "production_deployment": (
        "- 目标环境：`ENV=prod`",
        "- 标准数据库：`sc_prod`",
        "生产发布链路规范：`docs/ops/production_release_flow_standard_v1.md`",
        "ENV=prod ENV_FILE=.env.prod DB_NAME=sc_prod",
    ),
    "production_upgrade": (
        "cd /opt/sce/production/sce-backend-odoo",
        "生产 Git 权威对齐",
        "生产目录不是 Git 工作区时，不允许 `git pull`",
        "`make verify.production_git.authority.guard`",
        "rsync -av --relative $(cat changed_files.txt) /opt/sce/production/sce-backend-odoo/",
    ),
    "makefile": (
        ".PHONY: check-compose-project check.compose.project check-compose-env check-external-addons check-odoo-conf diag.project gate.compose.config env.print.db env.matrix.check verify.environment.topology.guard verify.daily_dev.runtime_repo.clean verify.daily_dev.acceptance.env.guard",
        "python3 scripts/verify/environment_topology_guard.py",
        "verify.environment.topology.guard:",
        "verify.daily_dev.runtime_repo.clean:",
        "verify.daily_dev.acceptance.env.guard:",
        "python3 scripts/verify/daily_dev_acceptance_env_guard.py",
        "release.daily_dev.acceptance.publish: guard.prod.forbid verify.daily_dev.acceptance.env.guard env.matrix.check verify.daily_dev.runtime_repo.clean release.dev.acceptance.publish",
        "bash scripts/ops/daily_dev_runtime_repo_guard.sh",
        ".PHONY: verify.production_git.authority.guard",
    ),
}


def _read(path: Path, errors: list[str]) -> str:
    if not path.is_file():
        errors.append(f"missing file: {path.relative_to(ROOT).as_posix()}")
        return ""
    return path.read_text(encoding="utf-8")


def main() -> int:
    errors: list[str] = []
    contents = {label: _read(path, errors) for label, path in FILES.items()}
    for label, tokens in REQUIRED_TOKENS.items():
        text = contents.get(label, "")
        for token in tokens:
            if token not in text:
                errors.append(f"{label}: missing token: {token}")

    if errors:
        print("[environment_topology_guard] FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[environment_topology_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
