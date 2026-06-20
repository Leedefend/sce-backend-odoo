#!/usr/bin/env python3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import product_boundary_catalog_guard as guard


VALID_DOC = """
# 正式产品边界 v1

## 产品分层

| 层级 | 正式产品 | 当前载体 | 面向对象 | 事实权威 |
| --- | --- | --- | --- | --- |
| P0 | 平台内核产品 | `smart_core` | 平台研发 | 通用机制 |
| P1 | 施工行业标准产品 | `smart_construction_core` | 标准部署 | 行业默认 |
| P2 | 特定用户产品 | `smart_construction_custom` | 指定客户 | 客户确认 |
| P3 | 低代码配置产品 | 配置工作台 | 管理员 | 显式配置 |
| P4 | 运维交付工具 | `scripts` | 交付 | 修复验证 |

## 当前模块归属

| 模块 | 正式归属 | 产品定位 | 不能承担 |
| --- | --- | --- | --- |
| `alpha` | P0 平台内核产品 | alpha | none |
| `beta` | P1/P4 行业交付包 | beta | none |

## 平台产品
## 行业标准产品
## 用户产品
## 低代码配置产品
## 运维交付工具
## 归属判定规则
## 配置沉淀规则
## 交付验收

- 是否可重放：yes
- 是否可覆盖：yes
- 是否可审计：yes
- 是否可回滚：yes
- 是否经业务端验证：yes

## 当前结论
"""


class ProductBoundaryCatalogGuardTests(unittest.TestCase):
    def _run_report(self, doc_text: str, modules: list[str]) -> dict:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            addons = root / "addons"
            addons.mkdir()
            for module in modules:
                module_dir = addons / module
                module_dir.mkdir()
                (module_dir / "__manifest__.py").write_text("{}", encoding="utf-8")
            doc = root / "formal_product_boundary_v1.md"
            doc.write_text(doc_text, encoding="utf-8")
            with patch.object(guard, "ADDONS_ROOT", addons), patch.object(guard, "BOUNDARY_DOC", doc):
                return guard.build_report()

    def test_valid_boundary_doc_passes(self):
        report = self._run_report(VALID_DOC, ["alpha", "beta"])
        self.assertTrue(report["summary"]["ok"])
        self.assertEqual(report["summary"]["addon_module_count"], 2)
        self.assertEqual(report["summary"]["documented_layer_count"], 5)
        self.assertEqual(report["documented_layer_names"]["P0"], "平台内核产品")
        self.assertEqual(report["module_assignments"]["beta"], "P1/P4 行业交付包")

    def test_missing_module_fails(self):
        report = self._run_report(VALID_DOC, ["alpha", "beta", "gamma"])
        self.assertFalse(report["summary"]["ok"])
        self.assertEqual(report["missing"], ["gamma"])

    def test_duplicate_module_rows_fail(self):
        doc = VALID_DOC.replace(
            "| `beta` | P1/P4 行业交付包 | beta | none |\n",
            "| `beta` | P1/P4 行业交付包 | beta | none |\n| `beta` | P2 特定用户产品 | duplicate | none |\n",
        )
        report = self._run_report(doc, ["alpha", "beta"])
        self.assertFalse(report["summary"]["ok"])
        self.assertEqual(report["duplicate_modules"], ["beta"])

    def test_missing_required_section_and_layer_fail(self):
        doc = VALID_DOC.replace("## 交付验收\n", "").replace(
            "| P4 | 运维交付工具 | `scripts` | 交付 | 修复验证 |\n",
            "",
        )
        report = self._run_report(doc, ["alpha", "beta"])
        self.assertFalse(report["summary"]["ok"])
        self.assertIn("## 交付验收", report["missing_sections"])
        self.assertIn("P4", report["missing_layers"])

    def test_invalid_module_assignment_fails(self):
        doc = VALID_DOC.replace("P1/P4 行业交付包", "行业交付包")
        report = self._run_report(doc, ["alpha", "beta"])
        self.assertFalse(report["summary"]["ok"])
        self.assertEqual(
            report["invalid_module_assignments"],
            [{"module": "beta", "assignment": "行业交付包"}],
        )

    def test_invalid_layer_name_fails(self):
        doc = VALID_DOC.replace("P0 | 平台内核产品", "P0 | 平台产品")
        report = self._run_report(doc, ["alpha", "beta"])
        self.assertFalse(report["summary"]["ok"])
        self.assertEqual(
            report["invalid_layer_names"],
            [{"layer": "P0", "expected": "平台内核产品", "actual": "平台产品"}],
        )


if __name__ == "__main__":
    unittest.main()
