#!/usr/bin/env python3
# Usage: python scripts/diag/test-default-menu.py
"""
测试 Odoo 默认返回的菜单是什么
"""

import sys
import json

# 模拟前端请求
import requests

def test_app_init():
    url = "http://localhost:8069/api/v1/intent"
    headers = {
        "Content-Type": "application/json",
        "X-Odoo-DB": "sc_demo"
    }
    
    # 测试1: 不带root_xmlid
    payload1 = {
        "intent": "app.init",
        "params": {
            "scene": "web",
            "with_preload": False
            # 不指定root_xmlid
        }
    }
    
    print("测试1: 不带root_xmlid")
    try:
        response = requests.post(url, headers=headers, json=payload1, timeout=10)
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"响应keys: {list(data.keys())}")
            if 'data' in data and 'nav' in data['data']:
                nav = data['data']['nav']
                print(f"菜单数量: {len(nav)}")
                if nav:
                    print("前3个菜单:")
                    for i, item in enumerate(nav[:3]):
                        print(f"  [{i}] name: {item.get('name', item.get('label', 'N/A'))}")
        else:
            print(f"响应: {response.text[:200]}")
    except Exception as e:
        print(f"错误: {e}")
    
    print("\n" + "="*60 + "\n")
    
    # 测试2: 带错误的root_xmlid
    payload2 = {
        "intent": "app.init",
        "params": {
            "scene": "web",
            "with_preload": False,
            "root_xmlid": "smart_construction_core.menu_sc_root"  # 这个不存在
        }
    }
    
    print("测试2: 带错误的root_xmlid")
    try:
        response = requests.post(url, headers=headers, json=payload2, timeout=10)
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"响应keys: {list(data.keys())}")
        else:
            print(f"响应: {response.text[:200]}")
    except Exception as e:
        print(f"错误: {e}")

if __name__ == "__main__":
    test_app_init()
