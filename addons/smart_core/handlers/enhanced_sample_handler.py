# 📁 smart_core/handlers/enhanced_sample_handler.py
# -*- coding: utf-8 -*-
"""
示例增强意图处理程序
展示如何使用BaseIntentHandler中的增强工具方法
"""

from ..core.base_handler import BaseIntentHandler
from typing import Tuple, Dict, Any

class EnhancedSampleHandler(BaseIntentHandler):
    """示例增强意图处理程序"""
    INTENT_TYPE = "sample.enhanced"
    DESCRIPTION = "示例增强意图处理程序"
    VERSION = "1.0.0"
    
    def handle(self) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """处理示例意图"""
        # 开始计时器
        self.start_timer("sample_processing")
        
        # 记录处理开始
        self.log_info("开始处理示例意图")
        
        # 获取参数
        sample_param = self.get_str("sample_param", "default_value")
        number_param = self.get_int("number_param", 0)
        flag_param = self.get_bool("flag_param", False)
        
        # 验证必需参数
        missing_params = self.validate_params(["sample_param"])
        if missing_params:
            return self.err(400, f"缺少必需参数: {missing_params}")
        
        # 构建搜索域
        filters = {
            "name": f"%{sample_param}%" if sample_param else None,
            "active": flag_param
        }
        domain = self.build_search_domain(filters)
        
        # 执行带权限检查的搜索
        try:
            records, total_count = self.search_with_permissions(
                "res.partner", 
                domain, 
                offset=0, 
                limit=20, 
                order="name"
            )
        except Exception as e:
            self.log_error(f"搜索失败: {str(e)}")
            return self.err(500, f"搜索失败: {str(e)}")
        
        # 格式化记录
        formatted_records = self.format_records(records, ["name", "email", "phone"])
        
        # 数据聚合示例
        aggregated_data = self.aggregate(
            formatted_records, 
            "name", 
            "id", 
            "count"
        )
        
        # 加密敏感数据示例
        encrypted_data = self.encrypt_data(sample_param)
        decrypted_data = self.decrypt_data(encrypted_data)
        
        # 国际化示例
        greeting = self._("hello")
        farewell = self._("goodbye")
        
        # 缓存示例
        cache_key = self.get_cache_key("sample_data")
        self.cache_set(cache_key, {"records": formatted_records, "count": total_count}, ttl=600)
        cached_data, ttl = self.cache_get_with_ttl(cache_key)
        
        # 停止计时器
        processing_time = self.stop_timer("sample_processing")
        
        # 准备响应数据
        data = {
            "sample_param": sample_param,
            "number_param": number_param,
            "flag_param": flag_param,
            "records": formatted_records,
            "total_count": total_count,
            "aggregated_data": aggregated_data,
            "encrypted_data": encrypted_data,
            "decrypted_data": decrypted_data,
            "greeting": greeting,
            "farewell": farewell,
            "cached_data": cached_data,
            "cache_ttl": ttl
        }
        
        # 准备元数据
        meta = {
            "processing_time_ms": processing_time,
            "cache_key": cache_key
        }
        
        # 记录处理完成
        self.log_info("示例意图处理完成")
        
        return data, meta