#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCAN_ROOTS = [
    ROOT / "addons" / "smart_construction_custom",
    ROOT / "addons" / "smart_construction_core",
    ROOT / "addons" / "smart_enterprise_base",
]

ROLE_GROUP_RE = re.compile(r"smart_construction_(?:custom|core)\.group_sc_role_(?!bridge_)[A-Za-z0-9_]+")
CAPABILITY_ADD_RE = re.compile(
    r"\(4,\s*ref\('smart_construction_core\.(?:group_sc_cap_[A-Za-z0-9_]+|group_sc_business_full|group_sc_super_admin)'\)\)"
)
GROUPS_FIELD_RE = re.compile(r"(?:<field\s+name=\"groups_id\"|groups=\")")
PY_ROLE_AUTH_RE = re.compile(
    r"(?:has_group\(|ACCESS_GROUPS\s*=|required_group_xmlid['\"]?\s*:)\s*[^\\n]*smart_construction_custom\.group_sc_role_"
)

KNOWN_EXECUTABLE_ROLE_DEBT = {
    "addons/smart_construction_core/models/core/payment_request.py",
    "addons/smart_construction_core/handlers/payment_request_available_actions.py",
    "addons/smart_construction_core/handlers/payment_request_execute.py",
}

ALLOWED_SEED_CAPABILITY_REMOVAL_FILES = {
    "addons/smart_construction_custom/data/customer_user_authorization.xml",
}
ALLOWED_DIRECT_CAPABILITY_SEED_FILES = {
    "addons/smart_construction_core/data/sc_cap_config_admin_user.xml",
}


@dataclass
class Finding:
    level: str
    category: str
    path: str
    line: int
    detail: str


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def iter_files(suffixes: tuple[str, ...]):
    for root in SCAN_ROOTS:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.is_file() and path.suffix in suffixes:
                yield path


def scan_acl_role_carriers(findings: list[Finding]) -> None:
    for path in iter_files((".csv",)):
        if path.name != "ir.model.access.csv":
            continue
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if ROLE_GROUP_RE.search(line):
                findings.append(
                    Finding(
                        "hard",
                        "role_group_acl_carrier",
                        rel(path),
                        lineno,
                        "SC role group is used as an ORM ACL carrier.",
                    )
                )


def scan_xml_group_carriers(findings: list[Finding]) -> None:
    for path in iter_files((".xml",)):
        relative = rel(path)
        if relative.endswith("/security/role_matrix_groups.xml") or relative.endswith("/security/sc_role_groups.xml"):
            continue
        if "/data/" in relative:
            continue
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if GROUPS_FIELD_RE.search(line) and ROLE_GROUP_RE.search(line):
                findings.append(
                    Finding(
                        "hard",
                        "role_group_menu_action_view_carrier",
                        relative,
                        lineno,
                        "SC role group is used as a menu/action/view carrier.",
                    )
                )


def scan_seed_capability_writes(findings: list[Finding]) -> None:
    for path in iter_files((".xml",)):
        relative = rel(path)
        if "/data/" not in relative:
            continue
        if relative in ALLOWED_DIRECT_CAPABILITY_SEED_FILES:
            continue
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if CAPABILITY_ADD_RE.search(line):
                findings.append(
                    Finding(
                        "hard",
                        "direct_capability_seed_assignment",
                        relative,
                        lineno,
                        "Customer seed/data file directly adds an SC capability group to a user.",
                    )
                )
            if (
                "smart_construction_core.group_sc_business_full" in line
                and "(3," not in line
                and relative not in ALLOWED_SEED_CAPABILITY_REMOVAL_FILES
            ):
                findings.append(
                    Finding(
                        "hard",
                        "business_full_seed_assignment",
                        relative,
                        lineno,
                        "Customer seed/data file references business_full outside an allowed cleanup removal.",
                    )
                )


def scan_python_role_authorization(findings: list[Finding]) -> None:
    for path in iter_files((".py",)):
        relative = rel(path)
        if "/tests/" in relative:
            continue
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if PY_ROLE_AUTH_RE.search(line):
                level = "debt" if relative in KNOWN_EXECUTABLE_ROLE_DEBT else "hard"
                findings.append(
                    Finding(
                        level,
                        "role_group_executable_authorization",
                        relative,
                        lineno,
                        "Executable authorization references a user-facing role group instead of a capability carrier.",
                    )
                )


def main() -> int:
    strict = os.getenv("STRICT") == "1"
    findings: list[Finding] = []

    scan_acl_role_carriers(findings)
    scan_xml_group_carriers(findings)
    scan_seed_capability_writes(findings)
    scan_python_role_authorization(findings)

    hard = [finding for finding in findings if finding.level == "hard"]
    debt = [finding for finding in findings if finding.level == "debt"]
    status = "PASS"
    if hard or (strict and debt):
        status = "FAIL"
    elif debt:
        status = "PASS_WITH_DEBT"

    payload = {
        "status": status,
        "strict": strict,
        "summary": {
            "hard": len(hard),
            "debt": len(debt),
            "total": len(findings),
        },
        "findings": [asdict(finding) for finding in findings],
        "rules": [
            "SC role groups must not be ORM ACL carriers.",
            "SC role groups must not be menu/action/view carriers for business access.",
            "Customer seed data must not directly add SC capability groups to users.",
            "Executable authorization must use capability carriers or a resolver, not raw user-facing role groups.",
        ],
    }

    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 1 if status == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
