#!/usr/bin/env python3
"""High-confidence tracked-file secret scan for CI.

This is intentionally narrow: it catches real token/private-key shapes while
avoiding noisy matches such as branch names containing "task-status".
"""

from __future__ import annotations

import hashlib
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
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


def main() -> int:
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
