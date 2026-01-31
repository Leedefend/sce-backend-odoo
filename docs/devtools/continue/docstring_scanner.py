#!/usr/bin/env python3
"""
AST-based docstring scanner for smart_construction_core module.
只读扫描，不修改任何文件。
"""

import ast
import os
import sys
from pathlib import Path
from typing import List, Dict, Any
import json
from datetime import datetime

class DocstringScanner:
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.results = {
            "scan_time": datetime.now().isoformat(),
            "files_scanned": 0,
            "missing_docstrings": [],
            "statistics": {
                "total_files": 0,
                "total_classes": 0,
                "total_methods": 0,
                "total_functions": 0,
                "missing_class_docstrings": 0,
                "missing_method_docstrings": 0,
                "missing_function_docstrings": 0,
                "missing_module_docstrings": 0,
            }
        }
        
    def should_skip(self, filepath: Path) -> bool:
        """判断是否跳过文件"""
        skip_patterns = [
            "__pycache__",
            "migrations",
            ".pyc",
            ".pyo",
            ".pyd",
        ]
        path_str = str(filepath)
        return any(pattern in path_str for pattern in skip_patterns)
    
    def get_decorators(self, node) -> List[str]:
        """提取装饰器列表"""
        decorators = []
        if hasattr(node, 'decorator_list'):
            for decorator in node.decorator_list:
                decorator_str = self._ast_to_string(decorator)
                if decorator_str:
                    decorators.append(decorator_str)
        return decorators
    
    def _ast_to_string(self, node) -> str:
        """将 AST 节点转换为字符串表示"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            # 处理链式属性，如 odoo.api.model
            value_str = self._ast_to_string(node.value)
            if value_str:
                return f"{value_str}.{node.attr}"
            return node.attr
        elif isinstance(node, ast.Call):
            # 处理带参数的装饰器，如 @api.model_create_multi
            func_str = self._ast_to_string(node.func)
            if func_str:
                return func_str
        elif isinstance(node, ast.Str):
            # Python 3.7 及之前版本的字符串常量
            return node.s
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            # Python 3.8+ 的字符串常量
            return node.value
        return ""
    
    def is_odoo_api_decorator(self, decorators: List[str]) -> bool:
        """判断是否是 Odoo API 装饰器"""
        odoo_api_patterns = ['api.model', 'api.depends', 'api.constrains', 
                            'api.onchange', 'api.returns', 'api.multi',
                            'api.one', 'api.autovacuum']
        return any(any(pattern in str(d) for pattern in odoo_api_patterns) 
                  for d in decorators)
    
    def _set_parents_recursive(self, node, parent=None):
        """递归设置AST节点的parent指针"""
        # 设置当前节点的parent
        node.parent = parent
        
        # 递归处理所有子节点
        for child in ast.iter_child_nodes(node):
            self._set_parents_recursive(child, node)
    
    def scan_file(self, filepath: Path):
        """扫描单个文件"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            # 正确设置父节点引用（用于判断是否是方法）
            self._set_parents_recursive(tree)  # 根节点没有parent
            
            # 检查模块级 docstring
            module_docstring = ast.get_docstring(tree)
            if not module_docstring:
                self.results["missing_docstrings"].append({
                    "file": str(filepath.relative_to(self.root_dir)),
                    "symbol_type": "module",
                    "qualified_name": filepath.stem,
                    "line": 1,
                    "decorators": [],
                    "context_snippet": content.split('\n')[0:3]
                })
                self.results["statistics"]["missing_module_docstrings"] += 1
            
            # 遍历 AST 节点
            for node in ast.walk(tree):
                # 检查类
                if isinstance(node, ast.ClassDef):
                    self.results["statistics"]["total_classes"] += 1
                    class_docstring = ast.get_docstring(node)
                    if not class_docstring:
                        decorators = self.get_decorators(node)
                        self.results["missing_docstrings"].append({
                            "file": str(filepath.relative_to(self.root_dir)),
                            "symbol_type": "class",
                            "qualified_name": node.name,
                            "line": node.lineno,
                            "decorators": decorators,
                            "context_snippet": content.split('\n')[node.lineno-1:node.lineno+2]
                        })
                        self.results["statistics"]["missing_class_docstrings"] += 1
                
                # 检查函数/方法
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if node.name.startswith('__') and node.name.endswith('__'):
                        # 跳过魔术方法
                        continue
                    
                    # 判断是方法还是函数
                    # 所有节点都有parent属性（通过_set_parents_recursive设置）
                    parent = node.parent
                    is_method = isinstance(parent, ast.ClassDef)
                    
                    if is_method:
                        self.results["statistics"]["total_methods"] += 1
                    else:
                        self.results["statistics"]["total_functions"] += 1
                    
                    func_docstring = ast.get_docstring(node)
                    if not func_docstring:
                        decorators = self.get_decorators(node)
                        symbol_type = "method" if is_method else "function"
                        
                        # 构建限定名
                        if is_method and parent:
                            qualified_name = f"{parent.name}.{node.name}"
                        else:
                            qualified_name = node.name
                        
                        self.results["missing_docstrings"].append({
                            "file": str(filepath.relative_to(self.root_dir)),
                            "symbol_type": symbol_type,
                            "qualified_name": qualified_name,
                            "line": node.lineno,
                            "decorators": decorators,
                            "context_snippet": content.split('\n')[node.lineno-1:node.lineno+2]
                        })
                        
                        if is_method:
                            self.results["statistics"]["missing_method_docstrings"] += 1
                        else:
                            self.results["statistics"]["missing_function_docstrings"] += 1
            
            self.results["files_scanned"] += 1
            
        except (SyntaxError, UnicodeDecodeError) as e:
            print(f"警告: 无法解析文件 {filepath}: {e}", file=sys.stderr)
    
    def scan_directory(self):
        """扫描整个目录"""
        py_files = list(self.root_dir.rglob("*.py"))
        self.results["statistics"]["total_files"] = len(py_files)
        
        for filepath in py_files:
            if self.should_skip(filepath):
                continue
            self.scan_file(filepath)
    
    def generate_report(self) -> Dict[str, Any]:
        """生成报告数据"""
        return self.results
    
    def save_json_report(self, output_path: str):
        """保存 JSON 格式报告"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)

def main():
    if len(sys.argv) != 2:
        print("用法: python docstring_scanner.py <目录路径>")
        sys.exit(1)
    
    root_dir = sys.argv[1]
    if not os.path.exists(root_dir):
        print(f"错误: 目录不存在 {root_dir}")
        sys.exit(1)
    
    scanner = DocstringScanner(root_dir)
    print(f"开始扫描目录: {root_dir}")
    scanner.scan_directory()
    
    # 输出统计信息
    stats = scanner.results["statistics"]
    print(f"\n扫描完成!")
    print(f"扫描文件数: {scanner.results['files_scanned']}/{stats['total_files']}")
    print(f"类总数: {stats['total_classes']}")
    print(f"方法总数: {stats['total_methods']}")
    print(f"函数总数: {stats['total_functions']}")
    print(f"缺失类文档: {stats['missing_class_docstrings']}")
    print(f"缺失方法文档: {stats['missing_method_docstrings']}")
    print(f"缺失函数文档: {stats['missing_function_docstrings']}")
    print(f"缺失模块文档: {stats['missing_module_docstrings']}")
    
    # 保存 JSON 报告
    output_dir = Path("docs/devtools/continue")
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "docstring_scan_results.json"
    scanner.save_json_report(str(json_path))
    print(f"\nJSON 报告已保存到: {json_path}")
    
    return scanner.results

if __name__ == "__main__":
    main()