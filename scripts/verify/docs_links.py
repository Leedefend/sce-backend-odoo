#!/usr/bin/env python3
"""Check docs markdown relative links and emit machine-readable report."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOCS_ROOT = ROOT / "docs"
OUT_JSON = ROOT / "artifacts/docs/docs_links_report.json"
OUT_MD = ROOT / "artifacts/docs/docs_links_report.md"

LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")

MANDATORY_FILES = [
    "docs/README.md",
    "docs/ops/README.md",
    "docs/audit/README.md",
    "docs/contract/README.md",
]


def resolve_link(src: Path, link: str) -> Path | None:
    value = link.strip()
    if not value or value.startswith("http://") or value.startswith("https://") or value.startswith("mailto:"):
        return None
    value = value.split("#", 1)[0].strip()
    if not value:
        return None
    if value.startswith("/"):
        return ROOT / value.lstrip("/")
    return (src.parent / value).resolve()


def main() -> int:
    missing = []
    checked = 0

    files = sorted(p for p in DOCS_ROOT.rglob("*.md") if p.is_file())
    for path in files:
        rel = path.relative_to(ROOT).as_posix()
        text = path.read_text(encoding="utf-8", errors="ignore")
        for raw_link in LINK_RE.findall(text):
            dst = resolve_link(path, raw_link)
            if dst is None:
                continue
            checked += 1
            if not dst.exists():
                missing.append({"source": rel, "link": raw_link})

    for rel in MANDATORY_FILES:
        if not (ROOT / rel).exists():
            missing.append({"source": "<mandatory>", "link": rel})

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "files_scanned": len(files),
            "links_checked": checked,
            "missing_count": len(missing),
        },
        "missing": missing,
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Docs Links Report",
        "",
        f"- files_scanned: {len(files)}",
        f"- links_checked: {checked}",
        f"- missing_count: {len(missing)}",
        "",
    ]
    if missing:
        lines.append("## Missing Links")
        lines.append("")
        for row in missing[:200]:
            lines.append(f"- `{row['source']}` -> `{row['link']}`")
        lines.append("")
    else:
        lines.append("All checked links are valid.")
        lines.append("")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print(str(OUT_JSON))
    print(str(OUT_MD))
    if missing:
        print(f"[FAIL] missing_count={len(missing)}")
        return 2
    print("[OK] docs links")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
