#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORT_JSON = ROOT / "artifacts/backend/frontend_contract_consumer_intrusion_report.json"
REPORT_MD = ROOT / "docs/ops/audit/frontend_contract_consumer_intrusion_report.md"


@dataclass(frozen=True)
class Rule:
    key: str
    scope: str
    kind: str
    severity: str
    path: str
    pattern: str
    rationale: str
    suggestion: str


RULES: tuple[Rule, ...] = (
    Rule(
        key="list_batch_bar_hardcoded_labels",
        scope="list_batch_actions",
        kind="literal",
        severity="high",
        path="frontend/apps/web/src/pages/ListPage.vue",
        pattern="批量归档",
        rationale="列表批量动作由前端固定文案定义，不是 contract bulk actions 声明。",
        suggestion="把 bulk action 集合下沉为 contract/provider，ListPage 只渲染契约声明动作。",
    ),
    Rule(
        key="list_batch_bar_hardcoded_activate",
        scope="list_batch_actions",
        kind="literal",
        severity="high",
        path="frontend/apps/web/src/pages/ListPage.vue",
        pattern="批量激活",
        rationale="列表批量动作由前端固定文案定义，不是 contract bulk actions 声明。",
        suggestion="把 bulk action 集合下沉为 contract/provider，ListPage 只渲染契约声明动作。",
    ),
    Rule(
        key="list_batch_bar_hardcoded_delete",
        scope="list_batch_actions",
        kind="literal",
        severity="high",
        path="frontend/apps/web/src/pages/ListPage.vue",
        pattern="批量删除",
        rationale="列表批量动作由前端固定文案定义，不是 contract bulk actions 声明。",
        suggestion="把 bulk action 集合下沉为 contract/provider，ListPage 只渲染契约声明动作。",
    ),
    Rule(
        key="list_batch_bar_hardcoded_assign",
        scope="list_batch_actions",
        kind="literal",
        severity="high",
        path="frontend/apps/web/src/pages/ListPage.vue",
        pattern="批量指派",
        rationale="列表批量动作由前端固定文案定义，不是 contract bulk actions 声明。",
        suggestion="把 bulk action 集合下沉为 contract/provider，ListPage 只渲染契约声明动作。",
    ),
    Rule(
        key="list_batch_bar_hardcoded_export_selected",
        scope="list_batch_actions",
        kind="literal",
        severity="medium",
        path="frontend/apps/web/src/pages/ListPage.vue",
        pattern="导出选中 CSV",
        rationale="导出能力由前端固定暴露，未经过 contract bulk action 声明。",
        suggestion="把 export 也纳入 contract action surface 或独立 capability contract。",
    ),
    Rule(
        key="list_batch_bar_hardcoded_export_page",
        scope="list_batch_actions",
        kind="literal",
        severity="medium",
        path="frontend/apps/web/src/pages/ListPage.vue",
        pattern="导出当前页 CSV",
        rationale="导出能力由前端固定暴露，未经过 contract bulk action 声明。",
        suggestion="把 export 也纳入 contract action surface 或独立 capability contract。",
    ),
    Rule(
        key="list_batch_bar_delete_note",
        scope="list_batch_actions",
        kind="literal",
        severity="medium",
        path="frontend/apps/web/src/pages/ListPage.vue",
        pattern="当前按归档处理，物理删除能力未开放",
        rationale="删除模式说明由前端硬编码，属于 contract/runtime policy 语义。",
        suggestion="由后端返回 delete_mode / delete_hint，由前端只做显示。",
    ),
    Rule(
        key="batch_runtime_hardcoded_action_union",
        scope="list_batch_runtime",
        kind="regex",
        severity="high",
        path="frontend/apps/web/src/app/action_runtime/useActionViewBatchRuntime.ts",
        pattern=r"type BatchAction = 'archive' \\| 'activate' \\| 'delete';",
        rationale="批量动作集合在运行时源码中写死，不是 contract 声明动作集合。",
        suggestion="将批量动作集合改为 contract/provider 输入，不在运行时定义固定枚举。",
    ),
    Rule(
        key="batch_runtime_delete_branch",
        scope="list_batch_runtime",
        kind="literal",
        severity="high",
        path="frontend/apps/web/src/app/action_runtime/useActionViewBatchRuntime.ts",
        pattern="if (action === 'delete') {",
        rationale="前端按固定动作类型分支执行，说明 bulk runtime 仍是前端主导。",
        suggestion="将动作执行计划改为 contract action executor plan。",
    ),
    Rule(
        key="batch_runtime_assign_handler",
        scope="list_batch_runtime",
        kind="literal",
        severity="medium",
        path="frontend/apps/web/src/app/action_runtime/useActionViewBatchRuntime.ts",
        pattern="async function handleBatchAssign(assigneeId: number)",
        rationale="批量指派属于业务动作，目前仍由前端 runtime 固定定义入口。",
        suggestion="把 assign 纳入 contract bulk actions 或显式 provider capability。",
    ),
    Rule(
        key="home_keyword_inference",
        scope="home_inference",
        kind="literal",
        severity="medium",
        path="frontend/apps/web/src/views/HomeView.vue",
        pattern="keywordList(",
        rationale="首页仍通过关键词表推导交互语义，容易脱离后端契约。",
        suggestion="将剩余关键词驱动行为替换为 contract/provider 显式字段。",
    ),
    Rule(
        key="home_role_inference_from_groups",
        scope="home_inference",
        kind="literal",
        severity="medium",
        path="frontend/apps/web/src/views/HomeView.vue",
        pattern="groups.includes('base.group_system') || groups.includes('smart_construction_core.group_sc_cap_config_admin')",
        rationale="首页仍通过 groups_xmlids 推导管理态能力，越过了 role/permission 契约边界。",
        suggestion="改为消费后端显式 role/capability surface，而不是前端扫 groups。",
    ),
    Rule(
        key="home_internal_tag_keyword_fallback",
        scope="home_inference",
        kind="literal",
        severity="medium",
        path="frontend/apps/web/src/views/HomeView.vue",
        pattern="return merged.includes('smoke') || merged.includes('internal') || merged.includes('test');",
        rationale="首页仍通过 scene/title/key 关键词猜内部入口，这属于前端业务推导。",
        suggestion="改为由后端 provider 明确返回 internal/test 标记。",
    ),
    Rule(
        key="home_error_reason_keyword_fallback_permission",
        scope="home_inference",
        kind="literal",
        severity="medium",
        path="frontend/apps/web/src/views/HomeView.vue",
        pattern="const code = lowered.includes('permission')",
        rationale="首页仍通过错误文案关键词推导 reason code，错误语义未完全契约化。",
        suggestion="要求错误 contract/intent 显式返回 reason_code，不由前端 message parsing 推导。",
    ),
    Rule(
        key="home_error_reason_keyword_fallback_not_found",
        scope="home_inference",
        kind="literal",
        severity="medium",
        path="frontend/apps/web/src/views/HomeView.vue",
        pattern=": lowered.includes('not found')",
        rationale="首页仍通过错误文案关键词推导 reason code，错误语义未完全契约化。",
        suggestion="要求错误 contract/intent 显式返回 reason_code，不由前端 message parsing 推导。",
    ),
    Rule(
        key="home_error_reason_keyword_fallback_timeout",
        scope="home_inference",
        kind="literal",
        severity="medium",
        path="frontend/apps/web/src/views/HomeView.vue",
        pattern=": lowered.includes('timeout')",
        rationale="首页仍通过错误文案关键词推导 reason code，错误语义未完全契约化。",
        suggestion="要求错误 contract/intent 显式返回 reason_code，不由前端 message parsing 推导。",
    ),
    Rule(
        key="list_sort_contract_fallback_id_desc",
        scope="list_sorting",
        kind="literal",
        severity="medium",
        path="frontend/apps/web/src/app/action_runtime/useActionViewLoadPreflightRuntime.ts",
        pattern="|| 'id desc'",
        rationale="默认排序仍有前端 fallback，尚未完全收口到 contract order。",
        suggestion="没有 contract order 时不要伪造默认排序，或由后端显式给出 canonical default_order。",
    ),
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.is_file() else ""


def _scan_rule(rule: Rule) -> list[dict[str, object]]:
    path = ROOT / rule.path
    text = _read(path)
    if not text:
        return [{
            "rule_key": rule.key,
            "scope": rule.scope,
            "severity": rule.severity,
            "path": rule.path,
            "line": 0,
            "match": "<file-missing>",
            "rationale": rule.rationale,
            "suggestion": rule.suggestion,
        }]

    findings: list[dict[str, object]] = []
    if rule.kind == "literal":
        for lineno, line in enumerate(text.splitlines(), start=1):
            if rule.pattern in line:
                findings.append({
                    "rule_key": rule.key,
                    "scope": rule.scope,
                    "severity": rule.severity,
                    "path": rule.path,
                    "line": lineno,
                    "match": line.strip(),
                    "rationale": rule.rationale,
                    "suggestion": rule.suggestion,
                })
        return findings

    regex = re.compile(rule.pattern)
    for match in regex.finditer(text):
        lineno = text.count("\n", 0, match.start()) + 1
        snippet = match.group(0).strip()
        findings.append({
            "rule_key": rule.key,
            "scope": rule.scope,
            "severity": rule.severity,
            "path": rule.path,
            "line": lineno,
            "match": snippet,
            "rationale": rule.rationale,
            "suggestion": rule.suggestion,
        })
    return findings


def _write_json(payload: dict[str, object]) -> None:
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_md(payload: dict[str, object]) -> None:
    findings = payload["findings"]
    assert isinstance(findings, list)
    lines = [
        "# Frontend Contract Consumer Intrusion Report",
        "",
        f"- total_findings: {payload['total_findings']}",
        f"- files_scanned: {payload['files_scanned']}",
        f"- scopes: {', '.join(payload['scopes'])}",
        "",
        "## Summary",
        "",
    ]
    by_scope = payload["by_scope"]
    assert isinstance(by_scope, dict)
    for scope, count in sorted(by_scope.items()):
        lines.append(f"- {scope}: {count}")
    lines.extend(["", "## Findings", ""])
    for item in findings:
        assert isinstance(item, dict)
        lines.append(
            f"- [{item['severity']}] {item['path']}:{item['line']} `{item['rule_key']}`"
        )
        lines.append(f"  match: `{item['match']}`")
        lines.append(f"  rationale: {item['rationale']}")
        lines.append(f"  suggestion: {item['suggestion']}")
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    report_only = "--report-only" in sys.argv
    findings: list[dict[str, object]] = []
    files = sorted({rule.path for rule in RULES})
    for rule in RULES:
        findings.extend(_scan_rule(rule))

    by_scope = Counter(str(item["scope"]) for item in findings)
    by_severity = Counter(str(item["severity"]) for item in findings)
    payload = {
        "report_name": "frontend_contract_consumer_intrusion_report",
        "report_mode": "report_only" if report_only else "guard",
        "files_scanned": len(files),
        "scopes": sorted(by_scope.keys()),
        "total_findings": len(findings),
        "by_scope": dict(sorted(by_scope.items())),
        "by_severity": dict(sorted(by_severity.items())),
        "findings": findings,
    }
    _write_json(payload)
    _write_md(payload)

    if findings:
        status = "[frontend_contract_consumer_intrusion_guard] REPORT" if report_only else "[frontend_contract_consumer_intrusion_guard] FAIL"
        print(status)
        print(f"total_findings={len(findings)}")
        print(f"report_json={REPORT_JSON.relative_to(ROOT)}")
        print(f"report_md={REPORT_MD.relative_to(ROOT)}")
        if not report_only:
            return 1
        return 0

    print("[frontend_contract_consumer_intrusion_guard] PASS")
    print(f"files_scanned={len(files)}")
    print(f"report_json={REPORT_JSON.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
