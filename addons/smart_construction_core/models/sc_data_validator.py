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
    def run(self):
        """Run all validators and return structured payload."""
        rule_results = self._run_rules()
        total_issues = sum(len(r.get("issues", [])) for r in rule_results)
        payload = {
            "database": self.env.cr.dbname,
            "timestamp": str(fields.Datetime.now()),
            "rules": rule_results,
            "issues_total": total_issues,
        }
        return payload

    @api.model
    def run_cli(self):
        """Entry for make validate: run, print summary, write JSON."""
        payload = self.run()
        report_path = self._write_report(payload)
        print(f"VALIDATE: db={payload['database']} rules={len(payload['rules'])} issues={payload['issues_total']}")

        has_error = False
        for r in payload["rules"]:
            issue_count = len(r.get("issues", []))
            level = r.get("level", "info").upper()
            prefix = "[OK]" if issue_count == 0 else f"[{level}]"
            if level == "ERROR" and issue_count > 0:
                has_error = True
            print(
                f"{prefix} {r['rule']}: checked={r.get('checked',0)} issues={issue_count}"
            )

        print(f"Report: {report_path}")
        if has_error:
            # 非零退出方便 CI 门禁
            import sys
            sys.exit(1)
        return payload
