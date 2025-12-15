# -*- coding: utf-8 -*-
import json
from datetime import datetime
from pathlib import Path

from odoo import api, fields, models

from ..tools.validator.rules import get_registered_rules


class ScDataValidator(models.AbstractModel):
    _name = "sc.data.validator"
    _description = "Smart Construction Data Validator"

    name = fields.Char(default="Data Validator")

    def validate_or_raise(self):
        """业务门禁入口：若存在 ERROR 级别问题则抛出 UserError。"""
        from odoo.exceptions import UserError

        payload = self.run(return_dict=True)
        rule_results = payload.get("rules", [])
        error_issues = []
        for r in rule_results:
            if str(r.get("severity", "")).upper() != "ERROR":
                continue
            for issue in r.get("issues", []):
                issue["rule_code"] = r.get("code") or r.get("rule")
                issue["title"] = r.get("title")
                error_issues.append(issue)
        if error_issues:
            lines = ["数据校验未通过："]
            for it in error_issues[:20]:
                code = it.get("rule_code") or "UNKNOWN"
                msg = it.get("message") or it.get("title") or ""
                name = it.get("refs", {}).get("name") if isinstance(it.get("refs"), dict) else ""
                lines.append(f"- {code}: {msg} {name or ''}".strip())
            raise UserError("\n".join(lines))
        return payload

    def _run_rules(self):
        """Execute all registered rules and return aggregated result."""
        env = self.env
        results = []
        for rule_cls in get_registered_rules():
            rule = rule_cls(env)
            results.append(rule.run())
        return results

    def _write_report(self, payload):
        """Persist report to addon-local var/validate directory."""
        addon_root = Path(__file__).resolve().parents[1]
        out_dir = addon_root / "var" / "validate"
        out_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.env.cr.dbname}_{ts}.json"
        out_path = out_dir / filename
        with out_path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        return str(out_path)

    @api.model
    def run(self, return_dict=True):
        """Run all validators and return structured payload."""
        rule_results = self._run_rules()
        total_issues = sum(len(r.get("issues", [])) for r in rule_results)
        payload = {
            "database": self.env.cr.dbname,
            "timestamp": str(fields.Datetime.now()),
            "rules": rule_results,
            "issues_total": total_issues,
        }
        return payload if return_dict else True

    @api.model
    def run_cli(self):
        """Entry for make validate: run, print summary, write JSON."""
        payload = self.run(return_dict=True)
        report_path = self._write_report(payload)
        print(f"VALIDATE: db={payload['database']} rules={len(payload['rules'])} issues={payload['issues_total']}")

        has_error = False
        for r in payload["rules"]:
            issue_count = len(r.get("issues", []))
            level = r.get("severity", "INFO").upper()
            prefix = "[OK]" if issue_count == 0 else f"[{level}]"
            if level == "ERROR" and issue_count > 0:
                has_error = True
            print(
                f"{prefix} {r.get('code', r.get('rule'))}: {r.get('title', '')} checked={r.get('checked',0)} issues={issue_count}"
            )

        print(f"Report: {report_path}")
        if has_error:
            # 非零退出方便 CI 门禁
            import sys
            sys.exit(1)
        return 0
