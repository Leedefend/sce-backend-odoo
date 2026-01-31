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
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Any
import subprocess

class DocstringsScanner:
    """文档字符串扫描器"""
    
    def __init__(self, module_path: str, output_dir: str = "artifacts/continue"):
        self.module_path = Path(module_path).resolve()
        self.output_dir = Path(output_dir).resolve()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 扫描结果
        self.scan_results = {
            "metadata": {},
            "statistics": {},
            "files": [],
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
    
    def scan_file(self, filepath: Path) -> Dict[str, Any]:
        """扫描单个Python文件"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            # 统计信息
            stats = {
                "file": str(filepath.relative_to(self.module_path)),
                "total_lines": len(content.splitlines()),
                "classes": [],
                "functions": [],
                "methods": [],
                "has_module_docstring": ast.get_docstring(tree) is not None
            }
            
            # 遍历AST节点
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    class_info = {
                        "name": node.name,
                        "line": node.lineno,
                        "has_docstring": ast.get_docstring(node) is not None,
                        "methods": []
                    }
                    
                    # 检查类方法
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            method_info = {
                                "name": item.name,
                                "line": item.lineno,
                                "has_docstring": ast.get_docstring(item) is not None
                            }
                            class_info["methods"].append(method_info)
                            stats["methods"].append(method_info)
                    
                    stats["classes"].append(class_info)
                
                elif isinstance(node, ast.FunctionDef):
                    # 顶层函数
                    func_info = {
                        "name": node.name,
                        "line": node.lineno,
                        "has_docstring": ast.get_docstring(node) is not None
                    }
                    stats["functions"].append(func_info)
            
            return stats
            
        except Exception as e:
            return {
                "file": str(filepath.relative_to(self.module_path)),
                "error": str(e)
            }
    
    def scan_module(self):
        """扫描整个模块"""
        python_files = list(self.module_path.rglob("*.py"))
        
        print(f"扫描模块: {self.module_path}")
        print(f"找到 {len(python_files)} 个Python文件")
        
        for i, filepath in enumerate(python_files, 1):
            print(f"  [{i}/{len(python_files)}] 扫描: {filepath.relative_to(self.module_path)}")
            file_stats = self.scan_file(filepath)
            self.scan_results["files"].append(file_stats)
        
        self.calculate_statistics()
    
    def calculate_statistics(self):
        """计算统计信息"""
        total_files = len(self.scan_results["files"])
        total_classes = 0
        total_functions = 0
        total_methods = 0
        classes_with_docstrings = 0
        functions_with_docstrings = 0
        methods_with_docstrings = 0
        
        missing_items = []
        
        for file_stats in self.scan_results["files"]:
            if "error" in file_stats:
                continue
            
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
                        "line": class_info["line"]
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
                            "line": method_info["line"]
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
                        "line": func_info["line"]
                    })
        
        # 计算覆盖率
        class_coverage = (classes_with_docstrings / total_classes * 100) if total_classes > 0 else 100
        function_coverage = (functions_with_docstrings / total_functions * 100) if total_functions > 0 else 100
        method_coverage = (methods_with_docstrings / total_methods * 100) if total_methods > 0 else 100
        
        overall_total = total_classes + total_functions + total_methods
        overall_with_docstrings = classes_with_docstrings + functions_with_docstrings + methods_with_docstrings
        overall_coverage = (overall_with_docstrings / overall_total * 100) if overall_total > 0 else 100
        
        self.scan_results["statistics"] = {
            "total_files": total_files,
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
            "missing_count": len(missing_items)
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
        
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(f"# 文档字符串审计报告\n\n")
            f.write(f"**扫描时间**: {metadata['scan_time']}\n")
            f.write(f"**扫描模块**: `{metadata['module_path']}`\n")
            f.write(f"**Git提交**: `{metadata['git_info'].get('commit', 'N/A')}`\n")
            f.write(f"**Git分支**: `{metadata['git_info'].get('branch', 'N/A')}`\n")
            f.write(f"**扫描器版本**: {metadata['scanner_version']}\n\n")
            
            f.write(f"## 📊 统计概览\n\n")
            f.write(f"| 指标 | 数量 | 覆盖率 |\n")
            f.write(f"|------|------|--------|\n")
            f.write(f"| 文件总数 | {stats['total_files']} | - |\n")
            f.write(f"| 类总数 | {stats['total_classes']} | {stats['class_coverage_percent']}% |\n")
            f.write(f"| 函数总数 | {stats['total_functions']} | {stats['function_coverage_percent']}% |\n")
            f.write(f"| 方法总数 | {stats['total_methods']} | {stats['method_coverage_percent']}% |\n")
            f.write(f"| **总计** | **{stats['total_classes'] + stats['total_functions'] + stats['total_methods']}** | **{stats['overall_coverage_percent']}%** |\n\n")
            
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
            f.write(f"1. **审计范围**: Python类、函数、方法\n")
            f.write(f"2. **文档字符串判定**: 使用Python标准库 `ast.get_docstring()`\n")
            f.write(f"3. **排除项**: 魔术方法（`__init__`, `__str__`等）暂未排除\n")
            f.write(f"4. **类别划分**:\n")
            f.write(f"   - `controllers`: `/controllers/` 目录下的文件\n")
            f.write(f"   - `models`: `/models/` 目录下的文件\n")
            f.write(f"   - `services`: `/services/` 或 `/wizards/` 目录下的文件\n")
            f.write(f"   - `other`: 其他目录下的文件\n\n")
            
            f.write(f"## 🔧 如何修复\n\n")
            f.write(f"1. 为缺失文档字符串的类/函数/方法添加docstring\n")
            f.write(f"2. 使用标准格式：`\"\"\"简要描述。\"\"\"`\n")
            f.write(f"3. 复杂方法应包含参数说明、返回值说明、示例等\n")
            f.write(f"4. 重新运行审计：`make cn.audit.docstrings`\n")
        
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