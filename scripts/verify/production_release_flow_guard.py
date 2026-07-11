#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]

FILES = {
    "flow": ROOT / "docs/ops/production_release_flow_standard_v1.md",
    "upgrade_standard": ROOT / "docs/ops/production_upgrade_standard_v1.md",
    "ops_readme": ROOT / "docs/ops/README.md",
    "deploy_runbook": ROOT / "docs/ops/production_deployment_runbook_v1.md",
    "server_post_upgrade_runbook": ROOT / "docs/ops/server_post_upgrade_business_data_closure_runbook_v1.md",
    "prod_policy": ROOT / "docs/ops/prod_command_policy.md",
    "verify_readme": ROOT / "docs/ops/verify/README.md",
    "release_checklist": ROOT / "docs/ops/release_checklist_v2.0.0.md",
    "release_index_en": ROOT / "docs/ops/releases/README.md",
    "release_index_zh": ROOT / "docs/ops/releases/README.zh.md",
    "template": ROOT / "docs/ops/releases/templates/production_deployment_record_TEMPLATE.zh.md",
    "record_guard": ROOT / "scripts/verify/production_deployment_record_guard.py",
    "makefile": ROOT / "Makefile",
}

FLOW_TOKENS = (
    "生产发布链路规范 v1",
    "docs/ops/production_upgrade_standard_v1.md",
    "发布包对齐",
    "模块版本对齐",
    "全量代码树对齐",
    "数据对齐",
    "生产不得直接用日常开发目录整包覆盖",
    "docs/ops/releases/templates/production_deployment_record_TEMPLATE.zh.md",
    "make verify.production_deployment.record.guard",
    "该 guard 会拒绝具体生产部署记录中的开放占位",
    "make verify.business_system.usability_readiness.prod",
    "make policy.restore.formal_product_menu",
    "make verify.production_menu.release_gate.guard.prod",
    "make verify.formal_menu.runtime_no_legacy_carrier_guard.prod",
    "make verify.formal_list_surface.no_test_placeholder_guard.prod",
    "make history.attachment.custody.probe.prod",
    "make verify.legacy_attachment.mirror.completeness.audit.prod",
    "make verify.legacy_online_attachment.custody.evidence.prod",
    "make verify.legacy_online_attachment.mirror.job.audit.prod",
    "make legacy_attachment.custody_marker.backfill.prod",
    "生产与日常开发服务器完全一致",
    "发布结论区分了“发布包对齐”和“全量对齐”",
    "生产目录不是 Git 工作区时，不得临场 `git pull` 或整目录覆盖",
    "全量主线对齐发布必须在部署记录中留存 `production_git_authority_guard` 完整 JSON 证据",
    "至少包含 `status`、`branch`、`head`、`remote_head`、`status_porcelain`、`remote_auth_ok`、`env_file_skip_worktree`",
)

UPGRADE_STANDARD_TOKENS = (
    "生产环境升级标准 v1",
    "全量版本升级",
    "增量功能升级",
    "只读验证资产升级",
    "生产热修复",
    "数据重建/补链",
    "生产 Git 权威对齐",
    "生产目录不是 Git 工作区时，不允许 `git pull`",
    "生产 Git 工作区必须具备只读拉取主线的 deploy key",
    "`make verify.production_git.authority.guard`",
    "该检查不连接 Odoo 或 Docker Compose，不使用 `PROD_READONLY_VERIFY`",
    "`PRODUCTION_GIT_AUTHORITY_*` 环境变量控制",
    "changed_files.txt",
    "module_upgrade.txt",
    "SHA256SUMS",
    "PRECHECK.md",
    "APPLY.md",
    "VALIDATION.md",
    "ROLLBACK.md",
    "不覆盖数据库、filestore、附件镜像目录",
    "Python handler/model 变更：至少 `prod.restart.safe`。",
    "XML/security/data/migration 变更：必须 `mod.upgrade`，然后 `prod.restart.safe`。",
    "make verify.formal_menu.runtime_no_legacy_carrier_guard.prod",
    "make verify.formal_list_surface.no_test_placeholder_guard.prod",
    "低代码升级必须执行",
    "deployed_not_verified",
    "rolled_forward_with_open_risk",
    "部署记录不得保留开放占位",
)

TEMPLATE_TOKENS = (
    "# Production Deployment Record",
    "## 1. 基本信息",
    "## 2. 发布范围声明",
    "## 4. 备份",
    "## 7. 发布后验证",
    "## 9. 收口结论",
    "`verify.non_demo_data_contamination`",
    "smart_construction_demo",
    "Production Git authority evidence for `full tree` releases",
    "PRODUCTION_GIT_AUTHORITY_REQUIRE_ENV_SKIP=1",
    "\"guard\": \"production_git_authority_guard\"",
    "\"remote_auth_ok\": true",
    "\"env_file_skip_worktree\": true",
    "生产与日常开发服务器不是全量一致",
    "`planned: <meaning>` / `retained: <meaning>` / `tracked: <meaning>` / `closed: <evidence>`",
)

MAKEFILE_TOKENS = (
    ".PHONY: verify.production_deployment.record.guard",
    ".PHONY: verify.business_capability.productization_p1 verify.business_system.usability_readiness verify.business_system.usability_readiness.prod",
    "verify.business_system.usability_readiness.prod: guard.prod.readonly check-compose-project check-compose-env",
    "policy.restore.formal_product_menu: guard.prod.danger check-compose-project check-compose-env",
    "verify.production_menu.release_gate.guard.prod: guard.prod.readonly check-compose-project check-compose-env",
    "verify.formal_menu.runtime_no_legacy_carrier_guard.prod: guard.prod.readonly check-compose-project check-compose-env verify.formal_menu.no_legacy_carrier_guard",
    "verify.formal_list_surface.no_test_placeholder_guard.prod: guard.prod.readonly check-compose-project check-compose-env",
    "BUSINESS_SYSTEM_READINESS_PROD_READONLY=1 BUSINESS_SYSTEM_READINESS_INCLUDE_P1=0",
    "history.attachment.custody.probe.prod: guard.prod.readonly check-compose-project check-compose-env",
    "legacy_attachment.custody_marker.backfill.prod: guard.prod.danger check-compose-project check-compose-env",
    "verify.legacy_attachment.mirror.completeness.audit.prod: guard.prod.readonly check-compose-project check-compose-env",
    "verify.legacy_online_attachment.custody.evidence.prod: guard.prod.readonly check-compose-project check-compose-env",
    "verify.legacy_online_attachment.mirror.job.audit.prod: guard.prod.readonly check-compose-project check-compose-env",
    "python3 -m py_compile scripts/verify/production_deployment_record_guard.py",
    "python3 scripts/verify/production_deployment_record_guard.py",
    "prod.frontend.build: guard.prod.danger check-compose-project check-compose-env",
    ".PHONY: verify.production_git.authority.guard",
    "verify.production_git.authority.guard:",
    "python3 -m py_compile scripts/verify/production_git_authority_guard.py",
    "python3 scripts/verify/production_git_authority_guard.py",
)

VERIFY_README_TOKENS = (
    "`make verify.production_deployment.record.guard`",
    "`make verify.business_system.usability_readiness.prod`",
    "`make policy.restore.formal_product_menu`",
    "`make verify.production_menu.release_gate.guard.prod`",
    "`make verify.formal_menu.runtime_no_legacy_carrier_guard.prod`",
    "`make verify.formal_list_surface.no_test_placeholder_guard.prod`",
    "`make history.attachment.custody.probe.prod`",
    "`make legacy_attachment.custody_marker.backfill.prod`",
    "Verifies concrete production deployment records",
    "explicit `incremental package` / `full tree` / `hotfix` release type",
    "For full-tree releases, requires production Git authority evidence",
    "future full-tree releases to preserve the full `production_git_authority_guard` JSON evidence",
    "`status`, `branch`, `head`, `remote_head`, `status_porcelain`, `remote_auth_ok`, and `env_file_skip_worktree`",
    "If the record claims production and daily development are fully aligned",
    "explicit non-full-alignment wording",
    "Rejects open-ended production record placeholders",
    "Requires `planned` / `retained` / `tracked` follow-up rows",
    "production read-only business readiness gate",
    "`make verify.production_git.authority.guard`",
    "Verifies the production Git work tree authority baseline",
    "Does not use Odoo, Docker Compose, or `PROD_READONLY_VERIFY`",
)

DEPLOY_RUNBOOK_TOKENS = (
    "make verify.business_system.usability_readiness.prod",
    "make policy.restore.formal_product_menu",
    "make verify.production_menu.release_gate.guard.prod",
    "make verify.formal_menu.runtime_no_legacy_carrier_guard.prod",
    "make verify.formal_list_surface.no_test_placeholder_guard.prod",
    "make history.attachment.custody.probe.prod",
    "make legacy_attachment.custody_marker.backfill.prod",
    "PROD_READONLY_VERIFY=1",
    "PROD_DANGER=1",
    "只运行历史业务可用性 probe 与 formal backfill audit",
)

SERVER_POST_UPGRADE_RUNBOOK_TOKENS = (
    "make prod.frontend.build",
    "Then verify the real served browser path for the acceptance user.",
)

PROD_POLICY_TOKENS = (
    "make verify.business_system.usability_readiness.prod",
    "make policy.restore.formal_product_menu",
    "make verify.production_menu.release_gate.guard.prod",
    "make verify.formal_menu.runtime_no_legacy_carrier_guard.prod",
    "make verify.formal_list_surface.no_test_placeholder_guard.prod",
    "make history.attachment.custody.probe.prod",
    "make prod.frontend.build",
    "make legacy_attachment.custody_marker.backfill.prod",
    "make verify.legacy_attachment.mirror.completeness.audit.prod",
    "make verify.legacy_online_attachment.custody.evidence.prod",
    "make verify.legacy_online_attachment.mirror.job.audit.prod",
    "PROD_READONLY_VERIFY=1",
)

CHECKLIST_TOKENS = (
    "docs/ops/production_release_flow_standard_v1.md",
    "docs/ops/releases/templates/production_deployment_record_TEMPLATE.zh.md",
    "make verify.production_deployment.record.guard",
    "rerun `make verify.production_release.flow.guard` to verify the production release-flow control plane remains wired at deployment time",
)

INDEX_TOKENS = (
    "production_deployment_record_TEMPLATE.zh.md",
)

RECORD_GUARD_TOKENS = (
    "DEFAULT_GLOB = \"docs/ops/releases/current/production_deployment_*.md\"",
    "REQUIRED_VALIDATION_TOKENS",
    "REQUIRED_CLOSURE_TOKENS",
    "FORBIDDEN_OPEN_ENDED_TOKENS",
    "EXPLAINED_FOLLOWUP_STATUS_PREFIXES",
    "smart_construction_demo XMLID count=0",
    "is_hotfix_package",
    "full-tree release missing git authority evidence",
    "full-tree alignment checked without module-version diff PASS evidence",
    "full-tree alignment unchecked but non-full-alignment statement missing",
)


def _read(path: Path, errors: list[str]) -> str:
    if not path.is_file():
        errors.append(f"missing file: {path.relative_to(ROOT).as_posix()}")
        return ""
    return path.read_text(encoding="utf-8")


def _require_tokens(label: str, text: str, tokens: tuple[str, ...], errors: list[str]) -> None:
    for token in tokens:
        if token not in text:
            errors.append(f"{label}: missing token: {token}")


def _require_order(label: str, text: str, tokens: tuple[str, ...], errors: list[str]) -> None:
    positions = []
    for token in tokens:
        index = text.find(token)
        if index < 0:
            errors.append(f"{label}: missing ordered token: {token}")
            return
        positions.append(index)
    if positions != sorted(positions):
        errors.append(f"{label}: token order mismatch: {tokens!r}")


def _makefile_prereqs(text: str, target: str) -> tuple[str, ...] | None:
    prefix = f"{target}:"
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if not line.startswith(prefix):
            continue
        chunks = [line[len(prefix) :].strip()]
        cursor = index
        while chunks[-1].endswith("\\"):
            chunks[-1] = chunks[-1][:-1].strip()
            cursor += 1
            if cursor >= len(lines):
                return ()
            chunks.append(lines[cursor].strip())
        prereq_text = " ".join(chunk for chunk in chunks if chunk)
        return tuple(prereq_text.split())
    return None


def _makefile_recipe(text: str, target: str) -> tuple[str, ...] | None:
    prefix = f"{target}:"
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if not line.startswith(prefix):
            continue
        cursor = index
        while lines[cursor].rstrip().endswith("\\"):
            cursor += 1
            if cursor >= len(lines):
                return ()
        recipe = []
        for recipe_line in lines[cursor + 1 :]:
            if not recipe_line.startswith("\t"):
                break
            recipe.append(recipe_line.strip())
        return tuple(recipe)
    return None


def _require_production_git_authority_target(text: str, errors: list[str]) -> None:
    target = "verify.production_git.authority.guard"
    prereqs = _makefile_prereqs(text, target)
    if prereqs is None:
        errors.append(f"makefile: missing target: {target}")
    elif prereqs != ():
        errors.append(f"makefile: {target} must remain host-only with no prerequisites, got {prereqs!r}")

    expected_recipe = (
        "@python3 -m py_compile scripts/verify/production_git_authority_guard.py",
        "@python3 scripts/verify/production_git_authority_guard.py",
    )
    recipe = _makefile_recipe(text, target)
    if recipe is None:
        errors.append(f"makefile: missing recipe: {target}")
    elif recipe != expected_recipe:
        errors.append(
            f"makefile: {target} recipe mismatch: expected={expected_recipe!r} actual={recipe!r}"
        )


def main() -> int:
    errors: list[str] = []
    contents = {label: _read(path, errors) for label, path in FILES.items()}

    _require_tokens("flow", contents["flow"], FLOW_TOKENS, errors)
    _require_tokens("upgrade_standard", contents["upgrade_standard"], UPGRADE_STANDARD_TOKENS, errors)
    _require_order(
        "upgrade_standard",
        contents["upgrade_standard"],
        (
            "## 1. 目标",
            "## 2. 升级类型",
            "## 3. 标准升级链路",
            "## 4. 回滚标准",
            "## 5. 部署记录",
            "## 6. 收口判定",
        ),
        errors,
    )
    _require_order(
        "flow",
        contents["flow"],
        (
            "## 1. 目标",
            "## 2. 环境职责",
            "## 3. 对齐定义",
            "## 4. 硬规则",
            "## 5. 标准发布流程",
            "## 6. 发布后差异登记",
            "## 7. 后续迭代节奏",
            "## 8. 收口判定",
        ),
        errors,
    )
    _require_tokens("template", contents["template"], TEMPLATE_TOKENS, errors)
    _require_tokens("makefile", contents["makefile"], MAKEFILE_TOKENS, errors)
    _require_tokens("verify_readme", contents["verify_readme"], VERIFY_README_TOKENS, errors)
    _require_tokens("deploy_runbook", contents["deploy_runbook"], DEPLOY_RUNBOOK_TOKENS, errors)
    _require_tokens(
        "server_post_upgrade_runbook",
        contents["server_post_upgrade_runbook"],
        SERVER_POST_UPGRADE_RUNBOOK_TOKENS,
        errors,
    )
    _require_tokens("prod_policy", contents["prod_policy"], PROD_POLICY_TOKENS, errors)
    _require_tokens("release_checklist", contents["release_checklist"], CHECKLIST_TOKENS, errors)
    _require_tokens("release_index_en", contents["release_index_en"], INDEX_TOKENS, errors)
    _require_tokens("release_index_zh", contents["release_index_zh"], INDEX_TOKENS, errors)
    _require_tokens("record_guard", contents["record_guard"], RECORD_GUARD_TOKENS, errors)
    _require_production_git_authority_target(contents["makefile"], errors)

    if "production_release_flow_standard_v1.md" not in contents["ops_readme"]:
        errors.append("ops_readme: missing production release flow entry")
    if "production_upgrade_standard_v1.md" not in contents["ops_readme"]:
        errors.append("ops_readme: missing production upgrade standard entry")
    if "production_release_flow_standard_v1.md" not in contents["deploy_runbook"]:
        errors.append("deploy_runbook: missing production release flow reference")

    if errors:
        print("[production_release_flow_guard] FAIL")
        for error in errors:
            print(error)
        return 2

    print("[production_release_flow_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
