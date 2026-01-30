#!/usr/bin/env python3
import argparse
import json
import os
import re
from datetime import datetime


KEYWORDS = [
    "construction",
    "boq",
    "settlement",
    "payment",
    "ledger",
    "project_cost",
    "smart_construction",
]

REVERSE_DEP_PATTERNS = [
    re.compile(r"\\bimport\\s+.*smart_construction", re.IGNORECASE),
    re.compile(r"\\bfrom\\s+odoo\\.addons\\.smart_construction", re.IGNORECASE),
]


def _is_text_file(path: str) -> bool:
    # Skip obvious binary by extension
    _, ext = os.path.splitext(path)
    if ext.lower() in {".pyc", ".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip"}:
        return False
    return True


def _scan_file(path: str, kw_regex: re.Pattern):
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except OSError:
        return [], []

    kw_hits = []
    for m in kw_regex.finditer(content):
        kw_hits.append({"keyword": m.group(0), "pos": m.start()})

    rev_hits = []
    for rx in REVERSE_DEP_PATTERNS:
        for m in rx.finditer(content):
            rev_hits.append({"pattern": rx.pattern, "pos": m.start()})

    return kw_hits, rev_hits


def _load_allowlist(path: str):
    if not path or not os.path.exists(path):
        return set()
    allow = set()
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            allow.add(line)
    return allow


def main():
    parser = argparse.ArgumentParser(description="Audit smart_core boundary violations")
    parser.add_argument("--root", default=".", help="Repo root")
    parser.add_argument("--scan-dir", default="addons/smart_core", help="Scan directory")
    parser.add_argument("--json-out", required=True, help="JSON output path")
    parser.add_argument("--md-out", required=True, help="Markdown output path")
    parser.add_argument("--fail-on-reverse-deps", action="store_true", help="Fail on reverse deps")
    parser.add_argument("--allowlist", default="", help="Allowlist file for reverse deps")
    args = parser.parse_args()

    repo_root = os.path.abspath(args.root)
    scan_root = os.path.join(repo_root, args.scan_dir)
    allowlist = _load_allowlist(os.path.join(repo_root, args.allowlist) if args.allowlist else "")

    kw_regex = re.compile("|".join(re.escape(k) for k in KEYWORDS), re.IGNORECASE)

    kw_results = {}
    rev_results = {}
    total_files = 0

    for dirpath, _, filenames in os.walk(scan_root):
        for name in filenames:
            path = os.path.join(dirpath, name)
            if not _is_text_file(path):
                continue
            total_files += 1
            rel = os.path.relpath(path, repo_root)
            kw_hits, rev_hits = _scan_file(path, kw_regex)
            if kw_hits:
                kw_results[rel] = kw_hits
            if rev_hits:
                if rel in allowlist:
                    continue
                rev_results[rel] = rev_hits

    os.makedirs(os.path.dirname(args.json_out), exist_ok=True)
    os.makedirs(os.path.dirname(args.md_out), exist_ok=True)

    payload = {
        "scan_root": args.scan_dir,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "total_files": total_files,
        "keyword_hits": kw_results,
        "reverse_dependency_hits": rev_results,
    }
    with open(args.json_out, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    with open(args.md_out, "w", encoding="utf-8") as f:
        f.write("# smart_core boundary audit\n\n")
        f.write(f"- Scan root: {args.scan_dir}\n")
        f.write(f"- Generated at (UTC): {payload['generated_at']}\n")
        f.write(f"- Files scanned: {total_files}\n\n")

        f.write("## Keyword Hits\n")
        if not kw_results:
            f.write("- None\n\n")
        else:
            for path in sorted(kw_results.keys()):
                f.write(f"- {path}\n")
        f.write("\n")

        f.write("## Reverse Dependency Hits\n")
        if not rev_results:
            f.write("- None\n")
        else:
            for path in sorted(rev_results.keys()):
                f.write(f"- {path}\n")

    if args.fail_on_reverse_deps and rev_results:
        raise SystemExit("[boundary_audit] reverse dependency violations found")


if __name__ == "__main__":
    main()
