#!/usr/bin/env python3
"""Fail-closed guard for known legacy credential fingerprints.

The guard never reports candidate values. It scans tracked/untracked text,
added diff lines, and an optional offline JSONL export of PR bodies.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import secret_scan


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CATALOG = ROOT / "config/security/legacy_credential_fingerprints.json"
ASSIGNMENT = re.compile(
    r"(?i)(?:user(?:name)?|login|pass(?:word)?|token|secret|api[_-]?key)"
    r"\s*[:=]\s*[`\"']?(?P<value>[^\s`\"',;]{3,256})"
)
SCANNED_SUFFIXES = {".md", ".yaml", ".yml", ".json", ".sh", ".py", ".ts", ".tsx", ".vue"}
ASSIGNMENT_MARKERS = ("username", "user_name", "login", "pass", "token", "secret", "api_key", "api-key")


@dataclass(frozen=True)
class Match:
    location: str
    line: int
    rule: str
    fingerprint_id: str


def load_catalog(path: Path) -> tuple[dict[str, str], set[str], dict[str, object]]:
    if not path.is_file():
        raise ValueError(f"missing fingerprint catalog: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("fingerprint_algorithm") != "sha256-truncated-12":
        raise ValueError("unsupported or missing fingerprint algorithm")
    entries = payload.get("fingerprints")
    if not isinstance(entries, list) or not entries:
        raise ValueError("fingerprint catalog must not be empty")
    confirmed_entries = payload.get("confirmed_history_fingerprints")
    if not isinstance(confirmed_entries, list) or not confirmed_entries:
        raise ValueError("confirmed history fingerprint catalog must not be empty")
    mapping: dict[str, str] = {}
    enforced: set[str] = set()
    for entry in [*entries, *confirmed_entries]:
        fingerprint = str(entry.get("fingerprint", ""))
        fingerprint_id = str(entry.get("id", ""))
        if not re.fullmatch(r"[0-9a-f]{12}", fingerprint) or not fingerprint_id:
            raise ValueError("invalid fingerprint catalog entry")
        mapping[fingerprint] = fingerprint_id
        if str(entry.get("disposition", "")).startswith("CONFIRMED_"):
            enforced.add(fingerprint_id)
    return mapping, enforced, payload


def candidate_fingerprint(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]


def scan_text(text: str, location: str, known: dict[str, str]) -> list[Match]:
    findings: list[Match] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        normalized = line.lower()
        if not any(marker in normalized for marker in ASSIGNMENT_MARKERS):
            continue
        for match in ASSIGNMENT.finditer(line):
            value = match.group("value")
            if secret_scan.is_placeholder(value):
                continue
            fingerprint_id = known.get(candidate_fingerprint(value))
            if fingerprint_id:
                findings.append(Match(location, line_no, "known_legacy_fingerprint", fingerprint_id))
    return findings


def worktree_matches(known: dict[str, str]) -> tuple[list[Match], int]:
    findings: list[Match] = []
    scanned = 0
    for path in secret_scan.worktree_files():
        if path.suffix.lower() not in SCANNED_SUFFIXES and path.name not in {"Makefile", "Dockerfile"}:
            continue
        text = secret_scan.read_text(path)
        if text is None:
            continue
        scanned += 1
        findings.extend(scan_text(text, str(path.relative_to(ROOT)), known))
    return findings, scanned


def diff_matches(known: dict[str, str], base: str) -> list[Match]:
    result = subprocess.run(
        ["git", "diff", "--unified=0", base, "--"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    added = "\n".join(
        line[1:] for line in result.stdout.splitlines() if line.startswith("+") and not line.startswith("+++")
    )
    return scan_text(added, f"git-diff:{base}", known)


def pr_body_matches(path: Path, known: dict[str, str]) -> tuple[list[Match], int]:
    findings: list[Match] = []
    scanned = 0
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            number = int(record["number"])
            body = str(record.get("body") or "")
            scanned += 1
            findings.extend(scan_text(body, f"PR#{number}", known))
    return findings, scanned


def safe_result(
    matches: list[Match],
    enforced_ids: set[str],
    scanned_files: int,
    scanned_prs: int,
    catalog: dict[str, object],
) -> dict[str, object]:
    revocation = catalog.get("revocation") if isinstance(catalog.get("revocation"), dict) else {}
    blocking = [item for item in matches if item.fingerprint_id in enforced_ids]
    candidate_counts: dict[str, int] = {}
    for item in matches:
        if item.fingerprint_id not in enforced_ids:
            candidate_counts[item.fingerprint_id] = candidate_counts.get(item.fingerprint_id, 0) + 1
    return {
        "schema_version": 1,
        "scanned_files": scanned_files,
        "scanned_pr_bodies": scanned_prs,
        "blocking_matches": len(blocking),
        "unreviewed_candidate_matches": sum(candidate_counts.values()),
        "unreviewed_candidate_matches_by_fingerprint": candidate_counts,
        "matches": [
            {
                "location": item.location,
                "line": item.line,
                "rule_id": item.rule,
                "fingerprint_id": item.fingerprint_id,
            }
            for item in blocking
        ],
        "secret_values_recorded": False,
        "credentials_revoked": bool(revocation.get("credentials_revoked", False)),
        "sessions_revoked": bool(revocation.get("sessions_revoked", False)),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--base", default="origin/main")
    parser.add_argument("--pr-jsonl", type=Path)
    parser.add_argument("--report", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        known, enforced_ids, catalog = load_catalog(args.catalog)
        matches, scanned_files = worktree_matches(known)
        matches.extend(diff_matches(known, args.base))
        scanned_prs = 0
        if args.pr_jsonl:
            pr_matches, scanned_prs = pr_body_matches(args.pr_jsonl, known)
            matches.extend(pr_matches)
    except (OSError, ValueError, json.JSONDecodeError, subprocess.CalledProcessError) as exc:
        print(f"[legacy_credential_guard] FAIL: {type(exc).__name__}", file=sys.stderr)
        return 2

    result = safe_result(matches, enforced_ids, scanned_files, scanned_prs, catalog)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    blocking = [item for item in matches if item.fingerprint_id in enforced_ids]
    if blocking:
        print("[legacy_credential_guard] FAIL", file=sys.stderr)
        for item in blocking:
            print(
                f"{item.location}:{item.line}: {item.rule}: fingerprint_id={item.fingerprint_id}",
                file=sys.stderr,
            )
        return 1
    print(
        f"[legacy_credential_guard] PASS files={scanned_files} pr_bodies={scanned_prs} values_recorded=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
