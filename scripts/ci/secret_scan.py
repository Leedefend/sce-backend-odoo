#!/usr/bin/env python3
"""High-confidence tracked-file secret scan for CI.

This is intentionally narrow: it catches real token/private-key shapes while
avoiding noisy matches such as branch names containing "task-status".
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


ROOT = Path(__file__).resolve().parents[2]
LEGACY_CATALOG = ROOT / "config/security/legacy_credential_fingerprints.json"
SCANNED_SUFFIXES = {
    ".cjs", ".conf", ".css", ".csv", ".env", ".html", ".ini", ".js",
    ".json", ".lock", ".md", ".mjs", ".properties", ".py", ".scss",
    ".sh", ".sql", ".toml", ".ts", ".tsx", ".txt", ".vue", ".xml",
    ".yaml", ".yml",
}
SCANNED_NAMES = {"Dockerfile", "Makefile", ".gitignore", ".dockerignore"}


PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("github_pat", re.compile("github_" + "pat_" + r"[A-Za-z0-9_]{20,}")),
    ("github_ghp", re.compile(r"(?<![A-Za-z0-9_])" + "ghp_" + r"[A-Za-z0-9_]{30,}")),
    ("openai_sk", re.compile(r"(?<![A-Za-z0-9_])" + "sk" + r"-[A-Za-z0-9_-]{32,}")),
    ("aws_access_key", re.compile(r"(?<![A-Z0-9])(?:AKIA|ASIA)[A-Z0-9]{16}(?![A-Z0-9])")),
    ("bearer_token", re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/-]{24,}={0,2}")),
    (
        "private_key",
        re.compile(
            "-----BEGIN "
            + r"(?:RSA |OPENSSH |EC |DSA )?"
            + "PRIVATE KEY-----"
        ),
    ),
]
PATTERN_MARKERS: dict[str, tuple[str, ...]] = {
    "github_pat": ("github_pat_",),
    "github_ghp": ("ghp_",),
    "openai_sk": ("sk-",),
    "aws_access_key": ("AKIA", "ASIA"),
    "bearer_token": ("bearer ",),
    "private_key": ("-----BEGIN ",),
}

ONLINE_ASSIGNMENT = re.compile(
    r"\b(?P<name>OLD_SCBS_(?:USERNAME|PASSWORD|TOKEN)|SCBSLY_(?:USERNAME|PASSWORD|TOKEN))"
    r"\s*=\s*(?P<value>[^\s`\\]+)"
)
URL_CREDENTIALS = re.compile(r"https?://(?P<value>[^\s/@:]+:[^\s/@]+)@", re.IGNORECASE)
ONLINE_LITERAL_DEFAULTS = (
    re.compile(
        r"os\.(?:getenv|environ\.get)\(\s*['\"](?:OLD_SCBS|SCBSLY)_(?:USERNAME|PASSWORD|TOKEN)['\"]\s*,\s*['\"](?P<value>[^'\"]+)['\"]"
    ),
    re.compile(
        r"process\.env\.(?:OLD_SCBS|SCBSLY)_(?:USERNAME|PASSWORD|TOKEN)\s*\|\|\s*['\"](?P<value>[^'\"]+)['\"]"
    ),
)
SCBSLY_CROSS_FALLBACK = re.compile(
    r"SCBSLY_(?:USERNAME|PASSWORD|TOKEN).*(?:OLD_SCBS_(?:USERNAME|PASSWORD|TOKEN))"
)
PLACEHOLDER_MARKERS = (
    "<redacted>",
    "<provided-via-secret-environment>",
    "<revoked_legacy_username>",
    "<revoked_legacy_secret>",
    "${old_scbs_",
    "${scbsly_",
    "example.invalid",
    "...",
)


@dataclass(frozen=True)
class Finding:
    rule: str
    fingerprint: str


@dataclass(frozen=True)
class LegacyFinding:
    location: str
    line: int
    fingerprint_id: str


def is_placeholder(value: str) -> bool:
    normalized = value.strip().strip("'\"").lower()
    return not normalized or any(marker in normalized for marker in PLACEHOLDER_MARKERS)


def fingerprint(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]


def scan_line(line: str) -> list[Finding]:
    findings: list[Finding] = []
    lowered = line.lower()
    for name, pattern in PATTERNS:
        markers = PATTERN_MARKERS[name]
        comparable = lowered if name == "bearer_token" else line
        if not any(marker in comparable for marker in markers):
            continue
        match = pattern.search(line)
        if match:
            findings.append(Finding(name, fingerprint(match.group(0))))
    assignment = ONLINE_ASSIGNMENT.search(line) if ("OLD_SCBS_" in line or "SCBSLY_" in line) else None
    if assignment and not is_placeholder(assignment.group("value")):
        findings.append(Finding("online_credential_assignment", fingerprint(assignment.group("value"))))
    url_match = URL_CREDENTIALS.search(line) if "http" in lowered and "@" in line else None
    if url_match and not is_placeholder(url_match.group("value")):
        findings.append(Finding("url_embedded_credentials", fingerprint(url_match.group("value"))))
    if "OLD_SCBS" in line or "SCBSLY" in line:
        for pattern in ONLINE_LITERAL_DEFAULTS:
            default_match = pattern.search(line)
            if default_match and not is_placeholder(default_match.group("value")):
                findings.append(Finding("online_credential_literal_default", fingerprint(default_match.group("value"))))
    if "SCBSLY" in line and "OLD_SCBS" in line and SCBSLY_CROSS_FALLBACK.search(line):
        findings.append(Finding("scbsly_cross_system_credential_fallback", fingerprint("scbsly-cross-fallback")))
    return findings


def worktree_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    paths = [ROOT / line.strip() for line in result.stdout.splitlines() if line.strip()]
    return [
        path
        for path in paths
        if path.suffix.lower() in SCANNED_SUFFIXES
        or path.name in SCANNED_NAMES
        or path.name.startswith(".env")
    ]


def read_text(path: Path) -> str | None:
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if b"\x00" in data:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode("utf-8", errors="ignore")


def load_legacy_catalog(path: Path = LEGACY_CATALOG) -> tuple[dict[str, str], set[str], dict[str, object]]:
    if not path.is_file():
        raise ValueError("missing legacy fingerprint catalog")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("fingerprint_algorithm") != "sha256-truncated-12":
        raise ValueError("unsupported legacy fingerprint algorithm")
    candidates = payload.get("fingerprints")
    confirmed = payload.get("confirmed_history_fingerprints")
    if not isinstance(candidates, list) or not candidates or not isinstance(confirmed, list) or not confirmed:
        raise ValueError("legacy fingerprint catalog is incomplete")
    known: dict[str, str] = {}
    enforced: set[str] = set()
    for entry in [*candidates, *confirmed]:
        digest = str(entry.get("fingerprint", ""))
        fingerprint_id = str(entry.get("id", ""))
        if not re.fullmatch(r"[0-9a-f]{12}", digest) or not fingerprint_id:
            raise ValueError("invalid legacy fingerprint entry")
        known[digest] = fingerprint_id
        if str(entry.get("disposition", "")).startswith("CONFIRMED_"):
            enforced.add(fingerprint_id)
    return known, enforced, payload


LEGACY_ASSIGNMENT = re.compile(
    r"(?i)(?:user(?:name)?|login|pass(?:word)?|token|secret|api[_-]?key)"
    r"\s*[:=]\s*[`\"']?(?P<value>[^\s`\"',;]{3,256})"
)
LEGACY_MARKERS = ("username", "user_name", "login", "pass", "token", "secret", "api_key", "api-key")


def scan_legacy_text(text: str, location: str, known: dict[str, str]) -> list[LegacyFinding]:
    findings: list[LegacyFinding] = []
    for line_no, line in enumerate(text.splitlines(), 1):
        if not any(marker in line.lower() for marker in LEGACY_MARKERS):
            continue
        for match in LEGACY_ASSIGNMENT.finditer(line):
            value = match.group("value")
            if is_placeholder(value):
                continue
            fingerprint_id = known.get(fingerprint(value))
            if fingerprint_id:
                findings.append(LegacyFinding(location, line_no, fingerprint_id))
    return findings


def legacy_inputs(known: dict[str, str], base: str, pr_jsonl: Path | None) -> tuple[list[LegacyFinding], int, int]:
    findings: list[LegacyFinding] = []
    scanned_files = 0
    for path in worktree_files():
        text = read_text(path)
        if text is None:
            continue
        scanned_files += 1
        findings.extend(scan_legacy_text(text, str(path.relative_to(ROOT)), known))
    diff = subprocess.run(
        ["git", "diff", "--unified=0", base, "--"], cwd=ROOT, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
    ).stdout
    added = "\n".join(line[1:] for line in diff.splitlines() if line.startswith("+") and not line.startswith("+++"))
    findings.extend(scan_legacy_text(added, f"git-diff:{base}", known))
    scanned_prs = 0
    if pr_jsonl:
        with pr_jsonl.open(encoding="utf-8") as handle:
            for line in handle:
                record = json.loads(line)
                scanned_prs += 1
                findings.extend(scan_legacy_text(str(record.get("body") or ""), f"PR#{int(record['number'])}", known))
    return findings, scanned_files, scanned_prs


def legacy_result(
    findings: list[LegacyFinding], enforced: set[str], scanned_files: int, scanned_prs: int, catalog: dict[str, object]
) -> dict[str, object]:
    blocking = [
        item
        for item in findings
        if item.fingerprint_id in enforced
        and (item.fingerprint_id.startswith("HC-") or item.location.startswith("PR#"))
    ]
    contextual_nonblocking = [
        item for item in findings if item.fingerprint_id in enforced and item not in blocking
    ]
    candidate_counts: dict[str, int] = {}
    for item in findings:
        if item.fingerprint_id not in enforced:
            candidate_counts[item.fingerprint_id] = candidate_counts.get(item.fingerprint_id, 0) + 1
    return {
        "schema_version": 1,
        "scanned_files": scanned_files,
        "scanned_pr_bodies": scanned_prs,
        "blocking_matches": len(blocking),
        "contextual_nonblocking_matches": len(contextual_nonblocking),
        "unreviewed_candidate_matches": sum(candidate_counts.values()),
        "unreviewed_candidate_matches_by_fingerprint": candidate_counts,
        "matches": [
            {"location": item.location, "line": item.line, "rule_id": "known_legacy_fingerprint", "fingerprint_id": item.fingerprint_id}
            for item in blocking
        ],
        "secret_values_recorded": False,
        "risk_status": str(catalog.get("risk_status", "BLOCKED")),
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--legacy-only", action="store_true")
    parser.add_argument("--base", default="origin/main")
    parser.add_argument("--pr-jsonl", type=Path)
    parser.add_argument("--report", type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.legacy_only:
        try:
            known, enforced, catalog = load_legacy_catalog()
            legacy, file_count, pr_count = legacy_inputs(known, args.base, args.pr_jsonl)
        except (OSError, ValueError, json.JSONDecodeError, subprocess.CalledProcessError) as exc:
            print(f"[legacy_credential_guard] FAIL: {type(exc).__name__}", file=sys.stderr)
            return 2
        result = legacy_result(legacy, enforced, file_count, pr_count, catalog)
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if result["blocking_matches"]:
            print("[legacy_credential_guard] FAIL", file=sys.stderr)
            for item in result["matches"]:
                print(
                    f"{item['location']}:{item['line']}: {item['rule_id']}: fingerprint_id={item['fingerprint_id']}",
                    file=sys.stderr,
                )
            return 1
        print(f"[legacy_credential_guard] PASS files={file_count} pr_bodies={pr_count} values_recorded=false")
        return 0
    findings: list[str] = []
    for path in worktree_files():
        text = read_text(path)
        if text is None:
            continue
        rel = path.relative_to(ROOT)
        for line_no, line in enumerate(text.splitlines(), start=1):
            for finding in scan_line(line):
                findings.append(f"{rel}:{line_no}: {finding.rule}: fingerprint={finding.fingerprint}")
    if findings:
        print("[FAIL] high-confidence secret pattern found", file=sys.stderr)
        for item in findings:
            print(item, file=sys.stderr)
        return 1
    print("[OK] high-confidence secret scan passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
