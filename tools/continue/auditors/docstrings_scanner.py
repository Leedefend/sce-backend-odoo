#!/usr/bin/env python3
"""
Continue CLI 文档字符串审计器
扫描指定模块的Python文件，分析文档字符串覆盖率

输出：
- artifacts/continue/audit_docstrings.md (人读报告)
- artifacts/continue/audit_docstrings.json (机器数据)
"""

import os
import sys
import json
import ast
import traceback
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional
import subprocess

class DocstringsScanner:
    """文档字符串扫描器"""
    
    def __init__(self, module_path: str, output_dir: str = "artifacts/continue"):
        self.module_path = Path(module_path).resolve()
        self.output_dir = Path(output_dir).resolve()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 排除目录列表
        self.exclude_dirs = {
            "__pycache__",
            ".venv",
            "venv",
            "env",
            ".env",
            "node_modules",
            "migrations",
            "runtime",
            "artifacts",
            "tmp",
            ".tmp",
            "temp",
            ".cache",
            ".state",
            ".codex_home",
            ".config"
        }
        
        # 扫描结果
        self.scan_results = {
            "metadata": {},
            "statistics": {},
            "files": [],
            "errors": [],
            "missing_docstrings": [],
            "by_category": {}
        }
    
    def collect_metadata(self):
        """收集元数据"""
        self.scan_results["metadata"] = {
            "scan_time": datetime.now().isoformat(),
            "module_path": str(self.module_path),
            "output_dir": str(self.output_dir),
            "git_info": self.get_git_info(),
            "python_version": sys.version,
            "scanner_version": "v0.1.0"
        }
    
    def get_git_info(self) -> Dict[str, str]:
        """获取Git信息"""
        try:
            commit_hash = subprocess.check_output(
                ["git", "rev-parse", "HEAD"],
                cwd=self.module_path.parent,
                text=True
            ).strip()
            
            branch = subprocess.check_output(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=self.module_path.parent,
                text=True
            ).strip()
            
            return {
                "commit": commit_hash,
                "branch": branch,
                "repo_root": str(self.module_path.parent)
            }
        except Exception as e:
            return {"error": str(e)}
    
    def should_exclude_file(self, filepath: Path) -> bool:
        """判断是否应该排除文件"""
        # 检查排除目录
        for part in filepath.parts:
            if part in self.exclude_dirs:
                return True
        
        # 检查文件名
        if filepath.name.startswith('.'):
            return True
        
        return False
    
    def is_dunder_method(self, name: str) -> bool:
        """判断是否是魔术方法（dunder method）"""
        return name.startswith('__') and name.endswith('__')
    
    def scan_file(self, filepath: Path) -> Dict[str, Any]:
        """扫描单个Python文件"""
        try:
            # 检查文件编码
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                # 尝试其他编码
                try:
                    with open(filepath, 'r', encoding='latin-1') as f:
                        content = f.read()
                except Exception as e:
                    raise UnicodeDecodeError(f"无法解码文件 {filepath}: {e}")
            
            tree = ast.parse(content, filename=str(filepath))
            
            # 统计信息
            stats = {
                "file": str(filepath.relative_to(self.module_path)),
                "total_lines": len(content.splitlines()),
                "classes": [],
                "functions": [],
                "methods": [],
                "has_module_docstring": ast.get_docstring(tree) is not None,
                "qualified_names": []  # 用于排序
            }
            
            # 使用自定义访问器来建立父子关系
            class NodeVisitor(ast.NodeVisitor):
                def __init__(self, stats, is_dunder_method):
                    self.stats = stats
                    self.is_dunder_method = is_dunder_method
                    self.current_class = None
                
                def visit_ClassDef(self, node):
                    # 保存当前类
                    old_class = self.current_class
                    self.current_class = node.name
                    
                    class_info = {
                        "name": node.name,
                        "line": node.lineno,
                        "has_docstring": ast.get_docstring(node) is not None,
                        "methods": []
                    }
                    
                    # 检查类方法
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            # 跳过魔术方法
                            if self.is_dunder_method(item.name):
                                continue
                                
                            method_info = {
                                "name": item.name,
                                "line": item.lineno,
                                "has_docstring": ast.get_docstring(item) is not None
                            }
                            class_info["methods"].append(method_info)
                            self.stats["methods"].append(method_info)
                    
                    self.stats["classes"].append(class_info)
                    self.stats["qualified_names"].append(f"{self.stats['file']}:{node.lineno}:class:{node.name}")
                    
                    # 继续遍历子节点
                    self.generic_visit(node)
                    self.current_class = old_class
                
                def visit_FunctionDef(self, node):
                    # 跳过魔术方法
                    if self.is_dunder_method(node.name):
                        return
                    
                    # 如果是类方法，已经在visit_ClassDef中处理
                    if self.current_class is not None:
                        return
                    
                    # 顶层函数
                    func_info = {
                        "name": node.name,
                        "line": node.lineno,
                        "has_docstring": ast.get_docstring(node) is not None
                    }
                    self.stats["functions"].append(func_info)
                    self.stats["qualified_names"].append(f"{self.stats['file']}:{node.lineno}:function:{node.name}")
                    
                    self.generic_visit(node)
            
            visitor = NodeVisitor(stats, self.is_dunder_method)
            visitor.visit(tree)
            
            return stats
            
        except SyntaxError as e:
            error_msg = f"语法错误: {e.msg} (行{e.lineno}, 列{e.offset})"
            return {
                "file": str(filepath.relative_to(self.module_path)),
                "error": error_msg,
                "error_type": "syntax_error"
            }
        except UnicodeDecodeError as e:
            return {
                "file": str(filepath.relative_to(self.module_path)),
                "error": str(e),
                "error_type": "encoding_error"
            }
        except Exception as e:
            return {
                "file": str(filepath.relative_to(self.module_path)),
                "error": f"{type(e).__name__}: {str(e)}",
                "error_type": "other_error"
            }
    
    def scan_module(self):
        """扫描整个模块"""
        python_files = []
        for filepath in self.module_path.rglob("*.py"):
            if not self.should_exclude_file(filepath):
                python_files.append(filepath)
        
        print(f"扫描模块: {self.module_path}")
        print(f"找到 {len(python_files)} 个Python文件（已排除 {len(list(self.module_path.rglob('*.py'))) - len(python_files)} 个排除文件）")
        
        for i, filepath in enumerate(python_files, 1):
            print(f"  [{i}/{len(python_files)}] 扫描: {filepath.relative_to(self.module_path)}")
            file_stats = self.scan_file(filepath)
            
            if "error" in file_stats:
                self.scan_results["errors"].append(file_stats)
                print(f"    ⚠ 错误: {file_stats['error']}")
            else:
                self.scan_results["files"].append(file_stats)
        
        self.calculate_statistics()
    
    def calculate_statistics(self):
        """计算统计信息"""
        total_files = len(self.scan_results["files"])
        total_errors = len(self.scan_results["errors"])
        total_classes = 0
        total_functions = 0
        total_methods = 0
        classes_with_docstrings = 0
        functions_with_docstrings = 0
        methods_with_docstrings = 0
        
        missing_items = []
        
        for file_stats in self.scan_results["files"]:
            # 统计类
            for class_info in file_stats["classes"]:
                total_classes += 1
                if class_info["has_docstring"]:
                    classes_with_docstrings += 1
                else:
                    missing_items.append({
                        "type": "class",
                        "file": file_stats["file"],
                        "name": class_info["name"],
                        "line": class_info["line"],
                        "qualified_name": f"{file_stats['file']}:{class_info['line']}:class:{class_info['name']}"
                    })
                
                # 统计方法
                for method_info in class_info["methods"]:
                    total_methods += 1
                    if method_info["has_docstring"]:
                        methods_with_docstrings += 1
                    else:
                        missing_items.append({
                            "type": "method",
                            "file": file_stats["file"],
                            "class": class_info["name"],
                            "name": method_info["name"],
                            "line": method_info["line"],
                            "qualified_name": f"{file_stats['file']}:{method_info['line']}:method:{class_info['name']}.{method_info['name']}"
                        })
            
            # 统计函数
            for func_info in file_stats["functions"]:
                total_functions += 1
                if func_info["has_docstring"]:
                    functions_with_docstrings += 1
                else:
                    missing_items.append({
                        "type": "function",
                        "file": file_stats["file"],
                        "name": func_info["name"],
                        "line": func_info["line"],
                        "qualified_name": f"{file_stats['file']}:{func_info['line']}:function:{func_info['name']}"
                    })
        
        # 计算覆盖率
        class_coverage = (classes_with_docstrings / total_classes * 100) if total_classes > 0 else 100
        function_coverage = (functions_with_docstrings / total_functions * 100) if total_functions > 0 else 100
        method_coverage = (methods_with_docstrings / total_methods * 100) if total_methods > 0 else 100
        
        overall_total = total_classes + total_functions + total_methods
        overall_with_docstrings = classes_with_docstrings + functions_with_docstrings + methods_with_docstrings
        overall_coverage = (overall_with_docstrings / overall_total * 100) if overall_total > 0 else 100
        
        # 按qualified_name排序，确保输出稳定
        missing_items.sort(key=lambda x: x["qualified_name"])
        
        self.scan_results["statistics"] = {
            "total_files": total_files,
            "total_errors": total_errors,
            "total_classes": total_classes,
            "total_functions": total_functions,
            "total_methods": total_methods,
            "classes_with_docstrings": classes_with_docstrings,
            "functions_with_docstrings": functions_with_docstrings,
            "methods_with_docstrings": methods_with_docstrings,
            "class_coverage_percent": round(class_coverage, 2),
            "function_coverage_percent": round(function_coverage, 2),
            "method_coverage_percent": round(method_coverage, 2),
            "overall_coverage_percent": round(overall_coverage, 2),
            "missing_count": len(missing_items),
            "statistics_calculation": {
                "denominator_excludes": [
                    "dunder_methods (__init__, __str__, etc.)",
                    "excluded_directories (__pycache__, migrations, etc.)",
                    "files_with_errors"
                ],
                "coverage_formula": "(items_with_docstrings / total_items * 100)",
                "item_types": ["class", "function", "method"]
            }
        }
        
        self.scan_results["missing_docstrings"] = missing_items
        
        # 按类别分组
        self.scan_results["by_category"] = {
            "controllers": self.filter_by_category("controllers"),
            "models": self.filter_by_category("models"),
            "services": self.filter_by_category("services"),
            "other": self.filter_by_category("other")
        }
    
    def filter_by_category(self, category: str) -> List[Dict]:
        """按类别过滤缺失的文档字符串"""
        if category == "controllers":
            return [item for item in self.scan_results["missing_docstrings"] 
                   if "/controllers/" in item["file"]]
        elif category == "models":
            return [item for item in self.scan_results["missing_docstrings"] 
                   if "/models/" in item["file"]]
        elif category == "services":
            return [item for item in self.scan_results["missing_docstrings"] 
                   if "/services/" in item["file"] or "/wizards/" in item["file"]]
        else:
            return [item for item in self.scan_results["missing_docstrings"] 
                   if not any(x in item["file"] for x in ["/controllers/", "/models/", "/services/", "/wizards/"])]
    
    def generate_json_report(self):
        """生成JSON报告"""
        json_path = self.output_dir / "audit_docstrings.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(self.scan_results, f, indent=2, ensure_ascii=False)
        
        print(f"✅ JSON报告已生成: {json_path}")
        return json_path
    
    def generate_markdown_report(self):
        """生成Markdown报告"""
        md_path = self.output_dir / "audit_docstrings.md"
        
        stats = self.scan_results["statistics"]
        metadata = self.scan_results["metadata"]
        errors = self.scan_results["errors"]
        
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(f"# 文档字符串审计报告\n\n")
            f.write(f"**扫描时间**: {metadata['scan_time']}\n")
            f.write(f"**扫描模块**: `{metadata['module_path']}`\n")
            f.write(f"**Git提交**: `{metadata['git_info'].get('commit', 'N/A')}`\n")
            f.write(f"**Git分支**: `{metadata['git_info'].get('branch', 'N/A')}`\n")
            f.write(f"**Git仓库**: `{metadata['git_info'].get('repo_root', 'N/A')}`\n")
            f.write(f"**Python版本**: {metadata['python_version'].split()[0]}\n")
            f.write(f"**扫描器版本**: {metadata['scanner_version']}\n\n")
            
            f.write(f"## 📊 统计概览\n\n")
            f.write(f"| 指标 | 数量 | 覆盖率 |\n")
            f.write(f"|------|------|--------|\n")
            f.write(f"| 成功扫描文件 | {stats['total_files']} | - |\n")
            f.write(f"| 错误文件 | {stats['total_errors']} | - |\n")
            f.write(f"| 类总数 | {stats['total_classes']} | {stats['class_coverage_percent']}% |\n")
            f.write(f"| 函数总数 | {stats['total_functions']} | {stats['function_coverage_percent']}% |\n")
            f.write(f"| 方法总数 | {stats['total_methods']} | {stats['method_coverage_percent']}% |\n")
            f.write(f"| **总计** | **{stats['total_classes'] + stats['total_functions'] + stats['total_methods']}** | **{stats['overall_coverage_percent']}%** |\n\n")
            
            if errors:
                f.write(f"## ⚠️ 扫描错误 ({len(errors)}个文件)\n\n")
                f.write(f"| 文件 | 错误类型 | 错误信息 |\n")
                f.write(f"|------|----------|----------|\n")
                for error in errors[:10]:  # 只显示前10个错误
                    error_type = error.get('error_type', 'unknown')
                    f.write(f"| `{error['file']}` | {error_type} | `{error['error'][:100]}...` |\n")
                if len(errors) > 10:
                    f.write(f"| ... | 还有 {len(errors) - 10} 个错误未显示 | ... |\n")
                f.write("\n")
            
            f.write(f"## ⚠️ 缺失文档字符串 ({stats['missing_count']}个)\n\n")
            
            # 按类别显示
            for category_name, items in self.scan_results["by_category"].items():
                if items:
                    f.write(f"### {category_name.upper()} ({len(items)}个)\n\n")
                    f.write(f"| 类型 | 文件 | 名称 | 行号 |\n")
                    f.write(f"|------|------|------|------|\n")
                    for item in items[:20]:  # 只显示前20个
                        if item["type"] == "method":
                            name = f"{item['class']}.{item['name']}"
                        else:
                            name = item["name"]
                        f.write(f"| {item['type']} | `{item['file']}` | `{name}` | {item['line']} |\n")
                    
                    if len(items) > 20:
                        f.write(f"| ... | 还有 {len(items) - 20} 个未显示 | ... | ... |\n")
                    f.write("\n")
            
            f.write(f"## 📋 审计规则说明\n\n")
            f.write(f"### 统计口径\n")
            f.write(f"1. **覆盖率公式**: `(有文档字符串的项 / 总项数 * 100)`\n")
            f.write(f"2. **项类型**: 类、函数、方法\n")
            f.write(f"3. **排除项**:\n")
            for exclude in stats.get('statistics_calculation', {}).get('denominator_excludes', []):
                f.write(f"   - {exclude}\n")
            f.write(f"\n### 扫描规则\n")
            f.write(f"1. **审计范围**: Python类、函数、方法\n")
            f.write(f"2. **文档字符串判定**: 使用Python标准库 `ast.get_docstring()`\n")
            f.write(f"3. **排除魔术方法**: `__init__`, `__str__`, `__repr__` 等\n")
            f.write(f"4. **排除目录**: `__pycache__`, `migrations`, `runtime`, `artifacts` 等\n")
            f.write(f"5. **类别划分**:\n")
            f.write(f"   - `controllers`: `/controllers/` 目录下的文件\n")
            f.write(f"   - `models`: `/models/` 目录下的文件\n")
            f.write(f"   - `services`: `/services/` 或 `/wizards/` 目录下的文件\n")
            f.write(f"   - `other`: 其他目录下的文件\n\n")
            
            f.write(f"## 🔧 如何修复\n\n")
            f.write(f"1. **为缺失文档字符串的类/函数/方法添加docstring**\n")
            f.write(f"2. **标准格式**: `\"\"\"简要描述。\"\"\"`\n")
            f.write(f"3. **复杂方法应包含**: 参数说明、返回值说明、示例等\n")
            f.write(f"4. **重新运行审计**: `make cn.audit.docstrings`\n")
            f.write(f"5. **测试审计**: `make cn.audit.docstrings.test` (仅扫描controllers目录)\n\n")
            
            f.write(f"## 🔗 相关链接\n\n")
            f.write(f"- [Python文档字符串规范 (PEP 257)](https://www.python.org/dev/peps/pep-0257/)\n")
            f.write(f"- [Google风格文档字符串指南](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings)\n")
            f.write(f"- [Continue CLI集成文档](docs/devtools/continue/README.md)\n")
        
        print(f"✅ Markdown报告已生成: {md_path}")
        return md_path
    
    def run(self):
        """运行扫描器"""
        print("=" * 60)
        print("Continue CLI 文档字符串审计器")
        print("=" * 60)
        
        self.collect_metadata()
        self.scan_module()
        
        json_path = self.generate_json_report()
        md_path = self.generate_markdown_report()
        
        print("=" * 60)
        print("✅ 审计完成!")
        print(f"   报告文件: {md_path}")
        print(f"   数据文件: {json_path}")
        print("=" * 60)


def main():
    """主函数"""
    if len(sys.argv) > 1:
        module_path = sys.argv[1]
    else:
        module_path = "addons/smart_construction_core"
    
    if len(sys.argv) > 2:
        output_dir = sys.argv[2]
    else:
        output_dir = "artifacts/continue"
    
    scanner = DocstringsScanner(module_path, output_dir)
    scanner.run()


if __name__ == "__main__":
    main()