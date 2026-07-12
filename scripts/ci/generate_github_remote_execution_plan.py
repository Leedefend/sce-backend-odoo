#!/usr/bin/env python3
from __future__ import annotations

import re
import shlex
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOC_ROOT = ROOT / "docs" / "engineering_convergence"
SEED = DOC_ROOT / "github_issue_seed_v1.1.md"
LABELS = DOC_ROOT / "github_labels.tsv"
OUTPUT = DOC_ROOT / "github_remote_execution_plan.md"
SCRIPT_OUTPUT = DOC_ROOT / "github_remote_execute.sh"
BODY_DIR = DOC_ROOT / "github_issue_bodies"


def slugify(title: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "-", title.strip()).strip("-").lower()
    return slug or "issue"


def parse_seed() -> tuple[str, list[dict[str, object]]]:
    text = SEED.read_text(encoding="utf-8")
    milestone = "v1.1 Engineering Convergence"
    for line in text.splitlines():
        if line.startswith("Milestone:"):
            milestone = line.split(":", 1)[1].strip().strip("`")
            break

    issues: list[dict[str, object]] = []
    matches = list(re.finditer(r"^## (.+)$", text, flags=re.MULTILINE))
    for index, match in enumerate(matches):
        title = match.group(1).strip()
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        block = text[start:end].strip()
        labels: list[str] = []
        body_lines: list[str] = []
        for line in block.splitlines():
            if line.startswith("Labels:"):
                labels = re.findall(r"`([^`]+)`", line)
                continue
            body_lines.append(line)
        body = "\n".join(body_lines).strip()
        issues.append({"title": title, "labels": labels, "body": body})
    return milestone, issues


def parse_labels() -> list[tuple[str, str, str]]:
    labels: list[tuple[str, str, str]] = []
    for line in LABELS.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        parts = line.split("\t", 2)
        if len(parts) != 3:
            raise ValueError(f"invalid label row: {line!r}")
        labels.append((parts[0], parts[1], parts[2]))
    return labels


def issue_body_path(title: str) -> Path:
    return BODY_DIR / f"{slugify(title)}.md"


def issue_create_command(issue: dict[str, object], milestone: str) -> str:
    title = str(issue["title"])
    labels_arg = ",".join(issue["labels"])
    cmd = [
        "gh",
        "issue",
        "create",
        "--title",
        title,
        "--milestone",
        milestone,
        "--body-file",
        issue_body_path(title).relative_to(ROOT).as_posix(),
    ]
    if labels_arg:
        cmd.extend(["--label", labels_arg])
    return " ".join(shlex.quote(part) for part in cmd)


def render_shell(milestone: str, issues: list[dict[str, object]], labels: list[tuple[str, str, str]]) -> str:
    lines = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        "",
        "MILESTONE=" + shlex.quote(milestone),
        "",
        'echo "[github-remote] preflight"',
        "gh auth status",
        "gh repo view --json nameWithOwner,viewerPermission",
        "REPO=$(gh repo view --json nameWithOwner --jq .nameWithOwner)",
        "",
        'echo "[github-remote] milestone"',
        "if gh api \"repos/$REPO/milestones?state=all\" --jq '.[].title' | grep -Fxq \"$MILESTONE\"; then",
        '  echo "[github-remote] milestone exists: $MILESTONE"',
        "else",
        "  gh api --method POST \"repos/$REPO/milestones\" "
        "-f title=\"$MILESTONE\" "
        "-f description='6-week engineering convergence, production validation, and pilot-readiness milestone.'",
        "fi",
        "",
        'echo "[github-remote] labels"',
    ]
    for label, color, description in labels:
        lines.append(
            "gh label create "
            + shlex.quote(label)
            + " --color "
            + shlex.quote(color)
            + " --description "
            + shlex.quote(description)
            + " --force"
        )

    lines.extend(["", 'echo "[github-remote] seed issues"'])
    for issue in issues:
        title = str(issue["title"])
        lines.extend(
            [
                "if gh issue list --state all --search "
                + shlex.quote(f"{title} in:title")
                + " --json title --jq '.[].title' | grep -Fxq "
                + shlex.quote(title)
                + "; then",
                "  echo "
                + shlex.quote(f"[github-remote] issue exists: {title}"),
                "else",
                "  " + issue_create_command(issue, milestone),
                "fi",
            ]
        )

    pr_title = "v1.1 Engineering Convergence"
    head_branch = "topic/v1.1-engineering-convergence"
    lines.extend(
        [
            "",
            'echo "[github-remote] draft PR"',
            "if gh pr list --head "
            + shlex.quote(head_branch)
            + " --state all --json title --jq '.[].title' | grep -Fxq "
            + shlex.quote(pr_title)
            + "; then",
            "  echo "
            + shlex.quote(f"[github-remote] PR exists: {pr_title}"),
            "else",
            "  gh pr create --draft --base main --head "
            + shlex.quote(head_branch)
            + " --title "
            + shlex.quote(pr_title)
            + " --body-file docs/engineering_convergence/pr_v1_1_engineering_convergence.md",
            "fi",
            "",
            'echo "[github-remote] branch protection remains a GitHub settings/admin step; see github_governance_runbook.md"',
        ]
    )
    return "\n".join(lines) + "\n"


def render_markdown(milestone: str, issues: list[dict[str, object]], labels: list[tuple[str, str, str]]) -> str:
    lines = [
        "# GitHub Remote Execution Plan",
        "",
        "Generated from `github_governance_runbook.md`, `github_labels.tsv`, and `github_issue_seed_v1.1.md`.",
        "",
        "## Preflight",
        "",
        "```bash",
        "gh auth status",
        "gh repo view --json nameWithOwner,viewerPermission",
        "REPO=$(gh repo view --json nameWithOwner --jq .nameWithOwner)",
        "```",
        "",
        "Required permission: repository admin for branch protection and required check settings.",
        "",
        "## Milestone",
        "",
        "```bash",
        "gh api --method POST \"repos/$REPO/milestones\" "
        + "-f title="
        + shlex.quote(milestone)
        + " -f description="
        + shlex.quote("6-week engineering convergence, production validation, and pilot-readiness milestone."),
        "```",
        "",
        "## Labels",
        "",
        "```bash",
    ]
    for label, color, description in labels:
        lines.append(
            "gh label create "
            + shlex.quote(label)
            + " --color "
            + shlex.quote(color)
            + " --description "
            + shlex.quote(description)
            + " --force"
        )
    lines.extend(["```", "", "## Seed Issues", ""])
    lines.extend(["| Title | Labels | Body File |", "| --- | --- | --- |"])
    for issue in issues:
        title = str(issue["title"])
        labels_text = ", ".join(f"`{label}`" for label in issue["labels"]) or "none"
        path = issue_body_path(title).relative_to(ROOT).as_posix()
        lines.append(f"| {title} | {labels_text} | `{path}` |")

    lines.extend(["", "## Issue Creation Commands", "", "```bash"])
    for issue in issues:
        lines.append(issue_create_command(issue, milestone))
    lines.extend(
        [
            "```",
            "",
            "## Branch Protection",
            "",
            "Configure `main` in GitHub settings according to `github_governance_runbook.md`:",
            "",
            "- Require pull requests before merging.",
            "- Require at least one approving review.",
            "- Require CODEOWNERS review.",
            "- Require status checks and `v1.1 quality gate / quality_gate` on the dedicated self-hosted CI runner.",
            "- Require branches to be up to date.",
            "- Block force pushes and branch deletion.",
            "",
            "## PR Creation",
            "",
            "```bash",
            "gh pr create --draft --base main --head topic/v1.1-engineering-convergence "
            "--title 'v1.1 Engineering Convergence' "
            "--body-file docs/engineering_convergence/pr_v1_1_engineering_convergence.md",
            "```",
            "",
            "## One-command Execution",
            "",
            "After GitHub authentication is restored, run:",
            "",
            "```bash",
            "bash docs/engineering_convergence/github_remote_execute.sh",
            "```",
        ]
    )
    return "\n".join(lines) + "\n"


def render() -> tuple[str, str]:
    milestone, issues = parse_seed()
    labels = parse_labels()
    BODY_DIR.mkdir(parents=True, exist_ok=True)

    for issue in issues:
        title = str(issue["title"])
        body = str(issue["body"]).strip()
        path = issue_body_path(title)
        path.write_text(
            body
            + "\n\n---\n"
            + f"Source: `docs/engineering_convergence/github_issue_seed_v1.1.md`\n",
            encoding="utf-8",
        )

    return render_markdown(milestone, issues, labels), render_shell(milestone, issues, labels)


def check_current(expected_plan: str, expected_script: str) -> int:
    if not OUTPUT.exists():
        print(f"[ERROR] missing plan: {OUTPUT.relative_to(ROOT)}", file=sys.stderr)
        return 1
    if not SCRIPT_OUTPUT.exists():
        print(f"[ERROR] missing script: {SCRIPT_OUTPUT.relative_to(ROOT)}", file=sys.stderr)
        return 1
    current_plan = OUTPUT.read_text(encoding="utf-8")
    current_script = SCRIPT_OUTPUT.read_text(encoding="utf-8")
    if current_plan != expected_plan or current_script != expected_script:
        print(
            "[ERROR] GitHub remote execution plan is stale. Run: "
            "python3 scripts/ci/generate_github_remote_execution_plan.py --write",
            file=sys.stderr,
        )
        return 1
    print("[OK] GitHub remote execution plan is current")
    return 0


def main(argv: list[str]) -> int:
    expected_plan, expected_script = render()
    if "--write" in argv:
        OUTPUT.write_text(expected_plan, encoding="utf-8")
        SCRIPT_OUTPUT.write_text(expected_script, encoding="utf-8")
        print(f"[OK] wrote {OUTPUT.relative_to(ROOT)}")
        print(f"[OK] wrote {SCRIPT_OUTPUT.relative_to(ROOT)}")
        return 0
    return check_current(expected_plan, expected_script)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
