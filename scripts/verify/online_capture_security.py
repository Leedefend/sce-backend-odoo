#!/usr/bin/env python3
"""Fail-closed configuration boundary for legacy online capture.

This module performs configuration validation only.  It never resolves DNS,
opens sockets, writes capture manifests, or accesses an Odoo database.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence
from urllib.parse import urlsplit


EXIT_PREFLIGHT_FAILED = 78
ONLINE_CONFIRM_VALUE = "ONLINE_CAPTURE_AUTHORIZED"
PLACEHOLDER_VALUES = {
    "",
    "...",
    "changeme",
    "example",
    "password",
    "placeholder",
    "redacted",
    "username",
}


@dataclass(frozen=True)
class SystemContract:
    system: str
    base_url_var: str
    username_var: str
    password_var: str
    timeout_var: str
    retries_var: str
    window_var: str
    raw_output_var: str
    manifest_output_var: str
    audit_log_var: str


@dataclass(frozen=True)
class CaptureConfig:
    system: str
    mode: str
    base_url: str
    username: str
    password: str
    timeout_seconds: int
    retry_limit: int
    capture_window: str
    raw_output_dir: str
    manifest_output_dir: str
    audit_log_path: str
    dry_run: bool

    def public_summary(self) -> dict[str, object]:
        return {
            "system": self.system,
            "mode": self.mode,
            "base_url_origin": origin(self.base_url) if self.base_url else "",
            "secret_present": bool(self.username and self.password),
            "secret_source": "environment" if self.username and self.password else "missing",
            "timeout_seconds": self.timeout_seconds,
            "retry_limit": self.retry_limit,
            "capture_window": self.capture_window,
            "raw_output_dir": self.raw_output_dir,
            "manifest_output_dir": self.manifest_output_dir,
            "audit_log_path": self.audit_log_path,
            "dry_run": self.dry_run,
            "network_requests": 0,
            "database_access": 0,
        }


CONTRACTS = {
    "scbs": SystemContract(
        system="scbs",
        base_url_var="OLD_SCBS_BASE_URL",
        username_var="OLD_SCBS_USERNAME",
        password_var="OLD_SCBS_PASSWORD",
        timeout_var="OLD_SCBS_REQUEST_TIMEOUT_SECONDS",
        retries_var="OLD_SCBS_REQUEST_RETRY_LIMIT",
        window_var="OLD_SCBS_CAPTURE_WINDOW",
        raw_output_var="SCBS_CAPTURE_RAW_OUTPUT_DIR",
        manifest_output_var="SCBS_CAPTURE_MANIFEST_OUTPUT_DIR",
        audit_log_var="SCBS_CAPTURE_AUDIT_LOG_PATH",
    ),
    "scbsly": SystemContract(
        system="scbsly",
        base_url_var="SCBSLY_BASE_URL",
        username_var="SCBSLY_USERNAME",
        password_var="SCBSLY_PASSWORD",
        timeout_var="SCBSLY_REQUEST_TIMEOUT_SECONDS",
        retries_var="SCBSLY_REQUEST_RETRY_LIMIT",
        window_var="SCBSLY_CAPTURE_WINDOW",
        raw_output_var="SCBSLY_CAPTURE_RAW_OUTPUT_DIR",
        manifest_output_var="SCBSLY_CAPTURE_MANIFEST_OUTPUT_DIR",
        audit_log_var="SCBSLY_CAPTURE_AUDIT_LOG_PATH",
    ),
}


class CapturePreflightError(RuntimeError):
    def __init__(self, reasons: Sequence[str]):
        self.reasons = tuple(dict.fromkeys(reasons))
        super().__init__("online capture preflight failed: " + ", ".join(self.reasons))


def clean(value: object) -> str:
    return str(value or "").strip()


def parse_bool(value: object) -> bool:
    return clean(value).lower() in {"1", "true", "yes", "on"}


def is_placeholder(value: str) -> bool:
    normalized = clean(value).lower()
    return (
        normalized in PLACEHOLDER_VALUES
        or normalized.startswith("<")
        or normalized.startswith("${")
        or "provided-via-secret" in normalized
    )


def origin(url: str) -> str:
    parsed = urlsplit(clean(url))
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return ""
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        return ""
    return f"{parsed.scheme.lower()}://{parsed.netloc.lower()}"


def allowed_origins(env: Mapping[str, str]) -> set[str]:
    raw = clean(env.get("SCBS_CAPTURE_DESTINATION_ALLOWLIST"))
    return {item_origin for item in raw.split(",") if (item_origin := origin(item))}


def _bounded_int(env: Mapping[str, str], name: str, default: int, minimum: int, maximum: int, reasons: list[str]) -> int:
    raw = clean(env.get(name))
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        reasons.append(f"invalid:{name}")
        return default
    if value < minimum or value > maximum:
        reasons.append(f"out_of_range:{name}")
        return default
    return value


def load_capture_config(system: str, env: Mapping[str, str] | None = None) -> CaptureConfig:
    source = os.environ if env is None else env
    contract = CONTRACTS[system]
    mode = clean(source.get("SCBS_CAPTURE_MODE")).lower() or "offline"
    reasons: list[str] = []
    if mode not in {"offline", "online"}:
        reasons.append("invalid:SCBS_CAPTURE_MODE")

    base_url = clean(source.get(contract.base_url_var))
    username = clean(source.get(contract.username_var))
    password = clean(source.get(contract.password_var))
    timeout = _bounded_int(source, contract.timeout_var, 90, 1, 600, reasons)
    retries = _bounded_int(source, contract.retries_var, 3, 0, 10, reasons)

    config = CaptureConfig(
        system=system,
        mode=mode,
        base_url=base_url,
        username=username,
        password=password,
        timeout_seconds=timeout,
        retry_limit=retries,
        capture_window=clean(source.get(contract.window_var)),
        raw_output_dir=clean(source.get(contract.raw_output_var)),
        manifest_output_dir=clean(source.get(contract.manifest_output_var)),
        audit_log_path=clean(source.get(contract.audit_log_var)),
        dry_run=parse_bool(source.get("SCBS_CAPTURE_DRY_RUN")),
    )

    if mode == "online":
        for variable, value in (
            (contract.base_url_var, base_url),
            (contract.username_var, username),
            (contract.password_var, password),
            (contract.window_var, config.capture_window),
            (contract.raw_output_var, config.raw_output_dir),
            (contract.manifest_output_var, config.manifest_output_dir),
            (contract.audit_log_var, config.audit_log_path),
        ):
            if not value:
                reasons.append(f"missing:{variable}")
        for variable, value in ((contract.username_var, username), (contract.password_var, password)):
            if value and is_placeholder(value):
                reasons.append(f"placeholder:{variable}")
        if clean(source.get("SCBS_ONLINE_CAPTURE_CONFIRM")) != ONLINE_CONFIRM_VALUE:
            reasons.append("missing_or_invalid:SCBS_ONLINE_CAPTURE_CONFIRM")
        requested_origin = origin(base_url)
        if not requested_origin:
            reasons.append(f"invalid:{contract.base_url_var}")
        elif requested_origin not in allowed_origins(source):
            reasons.append(f"destination_not_allowed:{contract.base_url_var}")

    if reasons:
        raise CapturePreflightError(reasons)
    return config


def require_online_capture(systems: Sequence[str], env: Mapping[str, str] | None = None) -> dict[str, CaptureConfig]:
    configs = {system: load_capture_config(system, env) for system in systems}
    offline = [system for system, config in configs.items() if config.mode != "online"]
    if offline:
        raise CapturePreflightError([f"online_mode_required:{system}" for system in offline])
    return configs


def redact_text(value: object) -> str:
    text = clean(value)
    patterns = (
        re.compile(r"(?i)(password|authorization|cookie|token)\s*[:=]\s*[^\s,;]+"),
        re.compile(r"(?i)(https?://)[^/@\s]+:[^/@\s]+@"),
    )
    for pattern in patterns:
        text = pattern.sub(lambda match: f"{match.group(1)}=<redacted>", text)
    return text


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Offline-only legacy capture configuration preflight")
    parser.add_argument("--system", choices=("scbs", "scbsly", "both"), default="both")
    parser.add_argument("--require-online", action="store_true")
    args = parser.parse_args(argv)
    systems = ("scbs", "scbsly") if args.system == "both" else (args.system,)
    try:
        configs = (
            require_online_capture(systems)
            if args.require_online
            else {system: load_capture_config(system) for system in systems}
        )
    except CapturePreflightError as exc:
        print(json.dumps({"status": "FAIL", "reasons": list(exc.reasons), "network_requests": 0, "database_access": 0}, sort_keys=True), file=sys.stderr)
        return EXIT_PREFLIGHT_FAILED
    print(json.dumps({"status": "PASS", "systems": [config.public_summary() for config in configs.values()], "network_requests": 0, "database_access": 0}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
