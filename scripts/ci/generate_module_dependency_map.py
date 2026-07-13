#!/usr/bin/env python3
from __future__ import annotations

import ast
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ADDONS = ROOT / "addons"
OUTPUT = ROOT / "docs" / "engineering_convergence" / "module_dependency_map.md"


def read_manifest(path: Path) -> dict:
    try:
        parsed = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError as exc:
        raise ValueError(f"invalid manifest syntax in {path.relative_to(ROOT)}: {exc}") from exc
    for node in parsed.body:
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Dict):
            try:
                value = ast.literal_eval(node.value)
            except ValueError as exc:
                raise ValueError(f"manifest is not literal: {path.relative_to(ROOT)}") from exc
            if isinstance(value, dict):
                return value
    raise ValueError(f"manifest dict not found: {path.relative_to(ROOT)}")


def load_modules() -> dict[str, dict]:
    modules: dict[str, dict] = {}
    for manifest_path in sorted(ADDONS.glob("*/__manifest__.py")):
        module = manifest_path.parent.name
        manifest = read_manifest(manifest_path)
        depends = manifest.get("depends", [])
        if not isinstance(depends, list):
            depends = []
        modules[module] = {
            "name": manifest.get("name", module),
            "version": manifest.get("version", ""),
            "depends": [str(dep) for dep in depends],
            "installable": bool(manifest.get("installable", False)),
            "application": bool(manifest.get("application", False)),
            "manifest": manifest_path.relative_to(ROOT).as_posix(),
        }
    return modules


def internal_edges(modules: dict[str, dict]) -> dict[str, list[str]]:
    internal = set(modules)
    return {
        module: sorted(dep for dep in meta["depends"] if dep in internal)
        for module, meta in modules.items()
    }


def external_dependencies(modules: dict[str, dict]) -> dict[str, list[str]]:
    internal = set(modules)
    return {
        module: sorted(dep for dep in meta["depends"] if dep not in internal)
        for module, meta in modules.items()
    }


def missing_internal_like(modules: dict[str, dict]) -> dict[str, list[str]]:
    internal_prefixes = ("smart_", "sc_")
    internal = set(modules)
    result: dict[str, list[str]] = {}
    for module, meta in modules.items():
        missing = [
            dep
            for dep in meta["depends"]
            if dep.startswith(internal_prefixes) and dep not in internal
        ]
        if missing:
            result[module] = sorted(missing)
    return result


def find_cycles(edges: dict[str, list[str]]) -> list[list[str]]:
    cycles: list[list[str]] = []
    visiting: set[str] = set()
    visited: set[str] = set()
    stack: list[str] = []

    def visit(node: str) -> None:
        if node in visiting:
            start = stack.index(node)
            cycle = stack[start:] + [node]
            if cycle not in cycles:
                cycles.append(cycle)
            return
        if node in visited:
            return
        visiting.add(node)
        stack.append(node)
        for child in edges.get(node, []):
            visit(child)
        stack.pop()
        visiting.remove(node)
        visited.add(node)

    for node in sorted(edges):
        visit(node)
    return cycles


def reverse_edges(edges: dict[str, list[str]]) -> dict[str, list[str]]:
    reverse: dict[str, list[str]] = defaultdict(list)
    for module, deps in edges.items():
        for dep in deps:
            reverse[dep].append(module)
    return {key: sorted(value) for key, value in sorted(reverse.items())}


def render(modules: dict[str, dict]) -> str:
    edges = internal_edges(modules)
    external = external_dependencies(modules)
    reverse = reverse_edges(edges)
    cycles = find_cycles(edges)
    missing = missing_internal_like(modules)

    lines: list[str] = [
        "# Module Dependency Map",
        "",
        "Generated from addon manifests.",
        "",
        "## Summary",
        "",
        f"- Addon modules: `{len(modules)}`",
        f"- Internal dependency edges: `{sum(len(v) for v in edges.values())}`",
        f"- External Odoo dependency references: `{sum(len(v) for v in external.values())}`",
        f"- Circular internal dependencies: `{len(cycles)}`",
        f"- Missing internal-like dependencies: `{sum(len(v) for v in missing.values())}`",
        "",
        "## Modules",
        "",
        "| Module | Version | Installable | Application | Internal Depends | External Depends | Reverse Internal Depends |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]

    for module, meta in sorted(modules.items()):
        internal_depends = ", ".join(edges[module]) or "-"
        external_depends = ", ".join(external[module]) or "-"
        reverse_depends = ", ".join(reverse.get(module, [])) or "-"
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{module}`",
                    str(meta["version"] or "-"),
                    "yes" if meta["installable"] else "no",
                    "yes" if meta["application"] else "no",
                    internal_depends,
                    external_depends,
                    reverse_depends,
                ]
            )
            + " |"
        )

    lines.extend(["", "## Internal Edges", ""])
    if any(edges.values()):
        lines.extend(["| From | To |", "| --- | --- |"])
        for module, deps in sorted(edges.items()):
            for dep in deps:
                lines.append(f"| `{module}` | `{dep}` |")
    else:
        lines.append("No internal dependency edges.")

    lines.extend(["", "## Circular Dependencies", ""])
    if cycles:
        for cycle in cycles:
            lines.append(f"- {' -> '.join(f'`{node}`' for node in cycle)}")
    else:
        lines.append("No circular internal dependencies detected.")

    lines.extend(["", "## Missing Internal-Like Dependencies", ""])
    if missing:
        lines.extend(["| Module | Missing Dependencies |", "| --- | --- |"])
        for module, deps in sorted(missing.items()):
            lines.append(f"| `{module}` | {', '.join(f'`{dep}`' for dep in deps)} |")
    else:
        lines.append("No missing internal-like dependencies detected.")

    lines.extend(
        [
            "",
            "## Boundary Notes",
            "",
            "- `smart_core` should remain the platform core and avoid depending on construction business modules.",
            "- Construction modules may depend on platform modules, but platform modules must not depend back on construction domains.",
            "- Bundle, seed, demo, and portal modules should stay at the outer edge of the dependency graph.",
            "- Any new cross-domain dependency requires an ADR before becoming part of the release baseline.",
        ]
    )
    return "\n".join(lines) + "\n"


def write() -> None:
    OUTPUT.write_text(render(load_modules()), encoding="utf-8")
    print(f"[OK] wrote {OUTPUT.relative_to(ROOT)}")


def check() -> int:
    expected = render(load_modules())
    if not OUTPUT.exists():
        print(f"[ERROR] missing module dependency map: {OUTPUT.relative_to(ROOT)}", file=sys.stderr)
        return 1
    if OUTPUT.read_text(encoding="utf-8") != expected:
        print(
            "[ERROR] module dependency map is stale. Run: "
            "python3 scripts/ci/generate_module_dependency_map.py --write",
            file=sys.stderr,
        )
        return 1
    print("[OK] module dependency map is current")
    return 0


def main(argv: list[str]) -> int:
    if "--write" in argv:
        write()
        return 0
    return check()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
