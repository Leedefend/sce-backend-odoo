#!/usr/bin/env bash
set -euo pipefail

release_log="${1:-}"
if [[ -z "${release_log}" ]]; then
  echo "usage: codex_release_note.sh <release_log_path>" >&2
  exit 2
fi

branch="$(git rev-parse --abbrev-ref HEAD)"
head_sha="$(git rev-parse --short HEAD)"
release_tag="${RELEASE_TAG:-codex-autonomous-delivery-v1}"
release_date="$(date +%Y-%m-%d)"
release_title="${RELEASE_TITLE:-Codex Autonomous Delivery v1}"
verify_cmd="${RELEASE_VERIFY_CMD:-make codex.run FLOW=gate}"
pr_url="${RELEASE_PR_URL:-}"

if [[ -z "${pr_url}" && "$(command -v gh)" ]]; then
  pr_url="$(gh pr list --state merged --search "head:${branch}" --json url --jq '.[0].url' 2>/dev/null || true)"
fi

python3 - <<PY
import io
import re
import sys

path = ${release_log!r}
release_date = ${release_date!r}
release_title = ${release_title!r}
release_tag = ${release_tag!r}
verify_cmd = ${verify_cmd!r}
head_sha = ${head_sha!r}
pr_url = ${pr_url!r}

with open(path, "r", encoding="utf-8") as f:
    lines = f.read().splitlines()

out = []
inserted = False
entry = [
    f"1) {release_date} - {release_title}",
    f"   - Tag: `{release_tag}`",
    "   - Type: infra",
    "   - Status: merged",
    f"   - Verify: `{verify_cmd}`",
    f"   - Commit: `{head_sha}`",
]
if pr_url:
    entry.append(f"   - PR: {pr_url}")

for i, line in enumerate(lines):
    out.append(line)
    if line.strip() == "## Release List (Newest First)" and not inserted:
        out.append("")
        out.extend(entry)
        inserted = True
        continue
    if inserted:
        m = re.match(r"^(\d+)\)", line.strip())
        if m:
            num = int(m.group(1)) + 1
            out[-1] = re.sub(r"^\d+\)", f"{num})", line, count=1)

if not inserted:
    print("Release list header not found", file=sys.stderr)
    sys.exit(2)

with open(path, "w", encoding="utf-8") as f:
    f.write("\n".join(out) + "\n")
PY
