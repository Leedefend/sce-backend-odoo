#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]


def _run(args: list[str], *, timeout: int = 15) -> tuple[int, str, str]:
    proc = subprocess.run(
        args,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def _git(args: list[str], *, timeout: int = 15) -> tuple[int, str, str]:
    return _run(["git", *args], timeout=timeout)


def _bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name, "").strip().lower()
    if not value:
        return default
    return value in {"1", "true", "yes", "on"}


def main() -> int:
    expected_branch = os.getenv("PRODUCTION_GIT_AUTHORITY_BRANCH", "main").strip() or "main"
    expected_remote = os.getenv("PRODUCTION_GIT_AUTHORITY_REMOTE", "origin").strip() or "origin"
    require_remote_auth = _bool_env("PRODUCTION_GIT_AUTHORITY_REQUIRE_REMOTE", True)
    require_env_skip_worktree = _bool_env("PRODUCTION_GIT_AUTHORITY_REQUIRE_ENV_SKIP", False)
    allowed_env_file = os.getenv("PRODUCTION_GIT_AUTHORITY_ENV_FILE", ".env.prod").strip()

    errors: list[str] = []
    warnings: list[str] = []
    evidence: dict[str, object] = {
        "guard": "production_git_authority_guard",
        "schema_version": "1.0",
        "expected_branch": expected_branch,
        "expected_remote": expected_remote,
        "require_remote_auth": require_remote_auth,
        "require_env_skip_worktree": require_env_skip_worktree,
        "allowed_env_file": allowed_env_file,
    }

    rc, inside, err = _git(["rev-parse", "--is-inside-work-tree"])
    evidence["inside_work_tree"] = inside
    if rc != 0 or inside != "true":
        errors.append(f"not a git work tree: {err or inside}")
        print(json.dumps({**evidence, "errors": errors}, ensure_ascii=False, indent=2))
        print("[production_git_authority_guard] FAIL")
        return 2

    rc, branch, err = _git(["rev-parse", "--abbrev-ref", "HEAD"])
    evidence["branch"] = branch
    if rc != 0:
        errors.append(f"cannot read current branch: {err}")
    elif branch != expected_branch:
        errors.append(f"branch mismatch: expected {expected_branch}, got {branch}")

    rc, head, err = _git(["rev-parse", "HEAD"])
    evidence["head"] = head
    if rc != 0:
        errors.append(f"cannot read HEAD: {err}")

    remote_ref = f"refs/remotes/{expected_remote}/{expected_branch}"
    rc, remote_head, err = _git(["rev-parse", remote_ref])
    evidence["remote_ref"] = remote_ref
    evidence["remote_head"] = remote_head
    if rc != 0:
        errors.append(f"cannot read remote tracking ref {remote_ref}: {err}")
    elif head and remote_head != head:
        errors.append(f"HEAD differs from {remote_ref}: head={head} remote={remote_head}")

    rc, status, err = _git(["status", "--porcelain"])
    evidence["status_porcelain"] = status
    if rc != 0:
        errors.append(f"cannot read git status: {err}")
    elif status:
        errors.append("git work tree is not clean")

    if allowed_env_file:
        rc, env_marker, err = _git(["ls-files", "-v", "--", allowed_env_file])
        evidence["env_file_marker"] = env_marker
        if rc == 0 and env_marker:
            marker = env_marker.split(" ", 1)[0]
            evidence["env_file_skip_worktree"] = marker == "S"
            if require_env_skip_worktree and marker != "S":
                errors.append(f"{allowed_env_file} must be marked skip-worktree in production")
        elif require_env_skip_worktree:
            errors.append(f"{allowed_env_file} is not tracked or cannot be inspected: {err}")

    rc, remote_url, err = _git(["remote", "get-url", expected_remote])
    evidence["remote_url"] = remote_url
    if rc != 0:
        errors.append(f"cannot read remote url for {expected_remote}: {err}")

    rc, ls_remote, err = _git(
        ["ls-remote", "--heads", expected_remote, expected_branch],
        timeout=int(os.getenv("PRODUCTION_GIT_AUTHORITY_REMOTE_TIMEOUT", "20")),
    )
    evidence["remote_auth_ok"] = rc == 0
    evidence["remote_auth_output"] = ls_remote[:240]
    if rc != 0:
        message = f"remote auth/fetch check failed for {expected_remote}/{expected_branch}: {err or ls_remote}"
        if require_remote_auth:
            errors.append(message)
        else:
            warnings.append(message)

    evidence["errors"] = errors
    evidence["warnings"] = warnings
    evidence["status"] = "PASS" if not errors else "FAIL"
    print(json.dumps(evidence, ensure_ascii=False, indent=2))
    if errors:
        print("[production_git_authority_guard] FAIL")
        return 2
    print("[production_git_authority_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
