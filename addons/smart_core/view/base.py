from abc import ABC, abstractmethod
from odoo import api, models
from odoo.http import request
from odoo.exceptions import UserError
from lxml import etree
from odoo.tools.safe_eval import safe_eval
import logging

_logger = logging.getLogger(__name__)


class BaseViewParser(ABC):
    def __init__(self, env, model=None, view_type=None, view_id=None, context=None):
        """
                初始化视图解析器。
                :param env:环境构造
                :param model: 模型名称
                :param view_type: 视图类型 (如 'kanban', 'form')
                :param view_id: 视图 ID
                :param context: 上下文字典
             """
        self._cached_env = env  # ✅ 提前注入
        self.model = model
        self.view_type = view_type
        self.view_id = view_id
        self.context = context or {}

    def _get_environment(self):
        """
        获取 Odoo 环境对象：
        - 优先使用缓存环境
        - HTTP 请求中使用 request 上下文
        - 非 HTTP 环境抛出异常或使用注入环境
        """
        if self._cached_env:
            return self._cached_env

        if request and hasattr(request, "cr"):
            cr = request.cr
            uid = getattr(request, "_secure_user", request.env.user).id
            ctx = dict(request.context or {}, **self.context)  # 合并上下文
        elif not self._cached_env:
            raise RuntimeError("无法获取 request 环境，请通过 set_environment 注入 env")
        else:
            cr, uid, ctx = self._cached_env.cr, self._cached_env.uid, self._cached_env.context

        self._cached_env = api.Environment(cr, uid, ctx)
        return self._cached_env

    def set_environment(self, env):
        """
        外部注入环境（如测试或服务使用）。
        """
        self._cached_env = env

    @abstractmethod
    def parse(self):
        """
        所有子类必须实现解析方法，返回结构化视图数据。
        """
        pass

    def get_view_info(self, fallback_view_type='form'):
        """
        获取视图信息，处理模型和视图的动态加载。

        :param fallback_view_type: 默认视图类型
        :return: 视图信息字典 (包含 arch 和 fields)
        :raises UserError: 如果模型或视图无效
        """
        env = self._get_environment()
        if not self.model:
            raise UserError("模型名称未指定")

        model_cls = env[self.model]
        view_type = self.view_type or fallback_view_type
        view_id = self.view_id

        try:
            view_info = model_cls.get_view(
                view_id=view_id,
                view_type=view_type,
                context=self.context
            )
            # 确保 arch 是 etree.Element
            if isinstance(view_info['arch'], str):
                view_info['arch'] = etree.fromstring(view_info['arch'])
            return view_info
        except Exception as e:
            _logger.error(f"获取视图信息失败: {str(e)}")
            raise UserError(f"无法加载 {view_type} 视图: {str(e)}")

    def extract_fields(self, arch):
        """
        提取视图中用到的字段集合，处理 XML 节点。

        :param arch: lxml.etree.Element 类型的视图 XML
        :return: 字段名称集合
        """
        if not isinstance(arch, etree._Element):
            raise ValueError("arch 必须是 lxml.etree.Element 类型")
        return {node.get("name") for node in arch.xpath("//field[@name]") if node.get("name")}

def parse_safe_context(expr_str):
        """
        若包含 QWeb 动态表达式（如 #{record.id}），则返回原始字符串；
        否则尝试 safe_eval 成字典。
        """
        if not expr_str or "#{".lower() in expr_str.lower():
            return expr_str  # 保留为字符串供前端处理
        try:
            return safe_eval(expr_str)
        except Exception:
            return expr_str  # 回退为字符串
