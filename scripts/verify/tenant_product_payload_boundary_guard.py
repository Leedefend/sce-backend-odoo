#!/usr/bin/env python3
from __future__ import annotations

import ast
import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INTERFACE = ROOT / "config" / "product_customer_package_interface.v1.json"
FORBIDDEN_PREFIXES = (
    "artifacts/",
    "migration_assets/",
    "tmp/raw/",
    "docs/migration_alignment/",
    "addons/smart_construction_custom/",
)
ARCHIVE_SUFFIXES = (".dump", ".tar", ".tar.gz", ".tgz", ".zst", ".age", ".zip", ".xlsx")
CUSTOMER_ADDON_DIR = re.compile(r"(?:^|/)sce_customer_(?!sample(?:/|$)|template(?:/|$))[a-z0-9_]+(?:/|$)")
LEGACY_EXTERNAL_ID = re.compile(r"\blegacy_\d{8,}\b")
LEGAL_COMPANY = re.compile(r"[\u4e00-\u9fff]{4,}(?:建设|建筑)?集团有限公司")
RUNTIME_SCOPES = (
    "addons/",
    "make/",
    "scripts/deploy/",
    "scripts/release/",
    "config/",
)
RUNTIME_FILES = {
    "Dockerfile",
    "Dockerfile.production-candidate",
    "docker-compose.yml",
    "docker-compose.ci.yml",
    "docker-compose.customer-addons.yml",
}
CUSTOMER_RUNTIME_TOKENS = ("smart_construction_custom",)
PLACEHOLDER_MARKERS = ("<tenant_key>", "sce_customer_sample", "sce_customer_template")


def tracked_files() -> list[Path]:
    output = subprocess.check_output(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT,
        text=True,
    )
    return [ROOT / item for item in output.splitlines() if item]


def text(path: Path) -> str | None:
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if b"\0" in data:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return None


def is_runtime_scope(relative: str) -> bool:
    return relative in RUNTIME_FILES or relative.startswith(RUNTIME_SCOPES)


def is_tenant_reference_scope(relative: str) -> bool:
    return relative in RUNTIME_FILES or relative.startswith(
        (
            "addons/smart_construction_demo/",
            "addons/smart_construction_seed/",
            "addons/smart_construction_acceptance_fixture/",
            "make/",
            "scripts/deploy/",
            "scripts/release/",
            "config/",
        )
    )


def customer_module_dependencies(errors: list[tuple[str, str]]) -> None:
    for manifest_path in sorted((ROOT / "addons").glob("*/__manifest__.py")):
        relative = str(manifest_path.relative_to(ROOT))
        try:
            manifest = ast.literal_eval(manifest_path.read_text(encoding="utf-8"))
        except (OSError, SyntaxError, ValueError):
            errors.append(("invalid_product_manifest", relative))
            continue
        for dependency in manifest.get("depends", []):
            if dependency == "smart_construction_custom" or (
                dependency.startswith("sce_customer_") and dependency not in {"sce_customer_sample"}
            ):
                errors.append(("product_dependency_references_customer_module", relative))


def validate_interface(errors: list[tuple[str, str]]) -> None:
    try:
        payload = json.loads(INTERFACE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        errors.append(("invalid_product_customer_interface", str(INTERFACE.relative_to(ROOT))))
        return
    required = {
        "schema_version",
        "product_api_version",
        "odoo_major_version",
        "customer_package_interface_version",
        "minimum_customer_package_version",
    }
    if set(payload) != required:
        errors.append(("product_customer_interface_fields", str(INTERFACE.relative_to(ROOT))))
    serialized = json.dumps(payload, sort_keys=True).lower()
    if any(token in serialized for token in ("repository", "token", "archive_sha", "customer_key")):
        errors.append(("product_customer_interface_contains_private_identity", str(INTERFACE.relative_to(ROOT))))


def validate_mount_boundary(errors: list[tuple[str, str]]) -> None:
    base_files = (ROOT / "docker-compose.yml", ROOT / "docker-compose.ci.yml")
    for path in base_files:
        content = path.read_text(encoding="utf-8")
        if "SC_CUSTOMER_ADDONS_ROOT" in content or "/mnt/customer-addons" in content:
            errors.append(("base_compose_implicitly_mounts_customer_addons", str(path.relative_to(ROOT))))
    override = ROOT / "docker-compose.customer-addons.yml"
    content = override.read_text(encoding="utf-8") if override.exists() else ""
    if "${SC_CUSTOMER_ADDONS_ROOT:?" not in content or ":/mnt/customer-addons:ro" not in content:
        errors.append(("customer_mount_override_not_required_read_only", str(override.relative_to(ROOT))))


def main() -> int:
    errors: list[tuple[str, str]] = []
    files = tracked_files()
    for path in files:
        relative = str(path.relative_to(ROOT))
        lowered = relative.lower()
        if relative.startswith(FORBIDDEN_PREFIXES):
            errors.append(("tracked_customer_payload_path", relative))
        if CUSTOMER_ADDON_DIR.search(relative):
            errors.append(("tenant_specific_customer_addon_in_product_tree", relative))
        if lowered.endswith(ARCHIVE_SUFFIXES):
            errors.append(("tracked_payload_or_archive", relative))
        content = text(path)
        if content is None:
            continue
        if LEGACY_EXTERNAL_ID.search(content):
            errors.append(("confirmed_customer_external_identifier", relative))
        for match in LEGAL_COMPANY.finditer(content):
            if not any(marker in match.group(0) for marker in ("示例", "某某")):
                errors.append(("non_example_legal_company_identity", relative))
                break
        if is_runtime_scope(relative):
            if any(token in content for token in CUSTOMER_RUNTIME_TOKENS):
                errors.append(("runtime_customer_module_reference", relative))
            if (
                is_tenant_reference_scope(relative)
                and "sce_customer_" in content
                and not any(marker in content for marker in PLACEHOLDER_MARKERS)
            ):
                errors.append(("runtime_tenant_specific_module_reference", relative))
    customer_module_dependencies(errors)
    validate_interface(errors)
    validate_mount_boundary(errors)
    if errors:
        print("[tenant_product_payload_boundary_guard] FAIL", file=sys.stderr)
        for rule, path in sorted(set(errors)):
            print(f"- rule={rule} path={path}", file=sys.stderr)
        return 1
    print(f"[tenant_product_payload_boundary_guard] PASS files={len(files)} values_recorded=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
