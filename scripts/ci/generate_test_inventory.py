#!/usr/bin/env python3
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = ROOT / "docs" / "engineering_convergence" / "test_inventory.csv"

SCAN_ROOTS = [
    ROOT / "scripts" / "audit",
    ROOT / "scripts" / "ci",
    ROOT / "scripts" / "diag",
    ROOT / "scripts" / "e2e",
    ROOT / "scripts" / "migration",
    ROOT / "scripts" / "ops",
    ROOT / "scripts" / "prod",
    ROOT / "scripts" / "verify",
    ROOT / "frontend" / "apps" / "web" / "scripts",
]

VALID_EXTENSIONS = {".py", ".js", ".cjs", ".mjs", ".sh"}
KEYWORDS = (
    "test",
    "verify",
    "guard",
    "acceptance",
    "smoke",
    "audit",
    "contract",
    "e2e",
)

MANUAL_ENTRIES = [
    {
        "id": "T-GATE-001",
        "layer": "gate",
        "entrypoint": "make ci",
        "purpose": "PR quality gate combining secret scan, Python syntax, frontend checks, and contract checks.",
        "estimated_runtime": "10-15m",
        "owner": "test owner",
        "status": "active",
        "notes": "Mandatory local and GitHub PR gate.",
    },
    {
        "id": "T-GATE-002",
        "layer": "e2e",
        "entrypoint": "make test.e2e",
        "purpose": "Full browser productization acceptance.",
        "estimated_runtime": "30-60m",
        "owner": "qa owner",
        "status": "active",
        "notes": "Release/full verification gate, not required for every small PR.",
    },
    {
        "id": "T-ODOO-001",
        "layer": "odoo_integration",
        "entrypoint": "make test.odoo.integration",
        "purpose": "Odoo smoke and runtime integration gate through existing ci.smoke target.",
        "estimated_runtime": "30-60m",
        "owner": "backend owner",
        "status": "active",
        "notes": "Requires Docker/Odoo runtime.",
    },
    {
        "id": "T-E2E-ODOO-001",
        "layer": "e2e",
        "entrypoint": "make test.e2e.fixed_data.odoo",
        "purpose": (
            "Fixed-data Odoo post-test gate for BOQ import, BOQ-to-WBS/task generation, "
            "and settlement approval journeys."
        ),
        "estimated_runtime": "10-30m",
        "owner": "qa owner",
        "status": "active",
        "notes": "Runs TEST_TAGS=e2e_fixed_journey on a clean Odoo test database.",
    },
]


def classify_layer(path: Path) -> str:
    text = path.as_posix().lower()
    name = path.name.lower()
    if "/e2e/" in text or "full_browser" in name or "browser" in name:
        return "e2e"
    if "contract" in name or "schema" in name or "intent" in name:
        return "contract"
    if "/migration/" in text or "asset_verify" in name or "replay" in name:
        return "data_migration"
    if "permission" in name or "role" in name or "auth" in name:
        return "security"
    if "/ops/" in text or "/prod/" in text or "runtime" in name or "deploy" in name:
        return "odoo_integration"
    if "/frontend/apps/web/scripts/" in text:
        return "frontend_acceptance"
    if "audit" in name or "guard" in name or "verify" in name:
        return "governance"
    return "unit"


def runtime_class(path: Path, layer: str) -> str:
    name = path.name.lower()
    if layer == "e2e" or "full_browser" in name:
        return "30-60m"
    if layer in {"odoo_integration", "data_migration"}:
        return "10-30m"
    if path.suffix == ".sh":
        return "unknown"
    return "<5m"


def owner_for(layer: str) -> str:
    return {
        "contract": "platform owner",
        "data_migration": "data owner",
        "e2e": "qa owner",
        "frontend_acceptance": "frontend owner",
        "governance": "architecture owner",
        "odoo_integration": "backend owner",
        "security": "security owner",
        "unit": "test owner",
    }.get(layer, "test owner")


def purpose_for(path: Path, layer: str) -> str:
    stem = path.stem.replace("_", " ").replace("-", " ")
    return f"{stem} validation asset classified as {layer}."


def status_for(path: Path) -> str:
    text = path.as_posix().lower()
    if "/demo/" in text or "/diag/" in text or "/test/" in text:
        return "review"
    return "active"


def iter_assets() -> list[Path]:
    assets: list[Path] = []
    for root in SCAN_ROOTS:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix not in VALID_EXTENSIONS:
                continue
            if "__pycache__" in path.parts:
                continue
            lowered = path.name.lower()
            if any(keyword in lowered for keyword in KEYWORDS):
                assets.append(path)
    return sorted(set(assets), key=lambda p: p.relative_to(ROOT).as_posix())


def build_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = list(MANUAL_ENTRIES)
    for index, path in enumerate(iter_assets(), start=1):
        rel = path.relative_to(ROOT).as_posix()
        layer = classify_layer(path)
        rows.append(
            {
                "id": f"T-ASSET-{index:03d}",
                "layer": layer,
                "entrypoint": rel,
                "purpose": purpose_for(path, layer),
                "estimated_runtime": runtime_class(path, layer),
                "owner": owner_for(layer),
                "status": status_for(path),
                "notes": "Generated by scripts/ci/generate_test_inventory.py",
            }
        )
    return rows


def write_csv(path: Path) -> None:
    rows = build_rows()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "id",
                "layer",
                "entrypoint",
                "purpose",
                "estimated_runtime",
                "owner",
                "status",
                "notes",
            ],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def check_csv(path: Path) -> int:
    expected = build_rows()
    if not path.exists():
        print(f"[ERROR] inventory file missing: {path.relative_to(ROOT)}", file=sys.stderr)
        return 1
    with path.open(newline="", encoding="utf-8") as handle:
        actual = list(csv.DictReader(handle))
    if actual != expected:
        print(
            "[ERROR] test inventory is stale. Run: "
            "python3 scripts/ci/generate_test_inventory.py --write",
            file=sys.stderr,
        )
        return 1
    print(f"[OK] test inventory is current ({len(actual)} entries)")
    return 0


def main(argv: list[str]) -> int:
    output = DEFAULT_OUTPUT
    if "--write" in argv:
        write_csv(output)
        print(f"[OK] wrote {output.relative_to(ROOT)}")
        return 0
    return check_csv(output)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
