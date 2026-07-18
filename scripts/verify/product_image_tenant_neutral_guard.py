#!/usr/bin/env python3
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ALLOWLIST = ROOT / "config/product_addons_allowlist.txt"
DOCKERFILES = [ROOT / "Dockerfile", ROOT / "Dockerfile.production-candidate"]
FORBIDDEN_MODULES = {
    "smart_construction_custom",
    "smart_construction_demo",
    "smart_construction_seed",
    "smart_construction_bootstrap",
}
CUSTOMER_EXTERNAL_ID = re.compile(r"\blegacy_\d{8,}\b")
NON_EXAMPLE_LEGAL_COMPANY = re.compile(r"[\u4e00-\u9fff]{4,}(?:建设|建筑)?集团有限公司")


def allowlist() -> list[str]:
    return [
        line.strip()
        for line in ALLOWLIST.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


def docker_copy_modules(path: Path) -> set[str]:
    modules: set[str] = set()
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or not line.startswith("COPY "):
            continue
        if re.search(r"\baddons/?\s+", line):
            raise AssertionError(f"{path.name} must not copy the complete addons directory")
        match = re.search(r"\baddons/([a-zA-Z0-9_]+)/?\s", line)
        if match:
            modules.add(match.group(1))
    return modules


def main() -> int:
    errors: list[str] = []
    modules = allowlist()
    if not modules or len(modules) != len(set(modules)):
        errors.append("product addons allowlist must be non-empty and unique")
    forbidden = sorted(set(modules) & FORBIDDEN_MODULES)
    if forbidden:
        errors.append(f"product allowlist contains forbidden modules: {forbidden}")
    for module in modules:
        if not (ROOT / "addons" / module / "__manifest__.py").exists():
            errors.append(f"allowlisted product module is missing: {module}")
    local_modules = {
        path.parent.name
        for path in (ROOT / "addons").glob("*/__manifest__.py")
    }
    for module in modules:
        manifest_path = ROOT / "addons" / module / "__manifest__.py"
        if not manifest_path.exists():
            continue
        try:
            manifest = ast.literal_eval(manifest_path.read_text(encoding="utf-8"))
        except (SyntaxError, ValueError) as exc:
            errors.append(f"invalid module manifest {module}: {exc}")
            continue
        missing_dependencies = sorted(
            dependency
            for dependency in manifest.get("depends", [])
            if dependency in local_modules and dependency not in modules
        )
        if missing_dependencies:
            errors.append(
                f"product allowlist is not dependency-closed for {module}: {missing_dependencies}"
            )
    for dockerfile in DOCKERFILES:
        try:
            copied = docker_copy_modules(dockerfile)
        except AssertionError as exc:
            errors.append(str(exc))
            continue
        if copied != set(modules):
            errors.append(
                f"{dockerfile.name} product copies differ from allowlist: "
                f"missing={sorted(set(modules) - copied)} extra={sorted(copied - set(modules))}"
            )
    config = (ROOT / "config/odoo.conf.template").read_text(encoding="utf-8")
    for mount in ("/mnt/product-addons", "/mnt/customer-addons"):
        if mount not in config:
            errors.append(f"odoo.conf.template missing addons path {mount}")
    development_config = (ROOT / "config/odoo.ci.conf").read_text(encoding="utf-8")
    if "/mnt/source-addons" not in development_config:
        errors.append("odoo.ci.conf must load the development source mount")
    release_config = (ROOT / "config/release/odoo.release-rehearsal.conf.template").read_text(encoding="utf-8")
    for mount in ("/mnt/product-addons", "/mnt/customer-addons"):
        if mount not in release_config:
            errors.append(f"release rehearsal config missing addons path {mount}")
    if "/mnt/source-addons" in release_config:
        errors.append("release rehearsal config must not load the development source mount")
    for module in modules:
        module_root = ROOT / "addons" / module
        for path in module_root.rglob("*"):
            if not path.is_file() or path.suffix in {".pyc", ".png", ".jpg", ".jpeg", ".gif", ".woff", ".woff2"}:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            if CUSTOMER_EXTERNAL_ID.search(text):
                errors.append(f"customer external identifier in product module: {path.relative_to(ROOT)}")
            for match in NON_EXAMPLE_LEGAL_COMPANY.finditer(text):
                if not any(marker in match.group(0) for marker in ("示例", "某某")):
                    errors.append(f"customer company identity in product module: {path.relative_to(ROOT)}")
                    break
    if errors:
        print("[product_image_tenant_neutral_guard] FAIL", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(f"[product_image_tenant_neutral_guard] PASS modules={len(modules)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
