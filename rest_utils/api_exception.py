#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Author  :   windpro
E-mail  :   windprozhao@tencent.com
Date    :   17/7/10
Desc    :   
"""
import inspect
import traceback
import sys
from types import NoneType
import re

from flask import jsonify, request

JSON_TYPES = (int, float, long, unicode, str, NoneType)

MSG_FORMAT = {
    10000: u'Undefined Exception',
    10003: u'Resource not found.Collection:{collection} field:{field} value:{value}.',
    10007: u'Permission Denied; prompt:{prompt}',
    11002: u'Assertion Error; prompt:{prompt}',
    30000: u'Request Data Exception; prompt:{prompt}',
    30003: u"Token Not Found.",
    30004: u"Token Invalid.",
    30005: u"Token Expired.",
}

CHINESE_MSG = {
    10000: u'未知错误。',
    10003: u'资源不存在。',
    10007: u'操作资源的权限错误。',
    11002: u'断言异常。',
    30000: u'非法数据。',
    30003: u"无法找到token",
    30004: u"token无效",
    30005: u"token失效",
}

HTTP_STATUS_CODE = {
    400: [
        10001,
        10004,
        11002,
        11004,
        11005,
        21001,
        21002,
        30000,
    ],
    403: [
        11001,
        10007,
        30003,
        30004,
        30005,
    ],
    404: [
        10003,
        11000,
        21000,
    ],
    406: [
        31002,
    ],
    415: [
        31001,
    ],
    500: [
        10000,
        11003,
        31000,
        31004,
    ]
}
# Reversal
# 实际使用时是 HTTP_STATUS_CODE = {code: http_status_code} 这里进行翻转
__http_status_code_mapper__ = {}
for __key__, __value__ in HTTP_STATUS_CODE.iteritems():
    for __item__ in __value__:
        __http_status_code_mapper__[__item__] = __key__
HTTP_STATUS_CODE = __http_status_code_mapper__


class RestException(Exception):
    default_code = 10000

    def __init__(self, code=None, **kwargs):
        self.code = code
        if code is None:
            self.code = self.default_code

        try:
            # 调取调用记录
            list_stack = inspect.stack()
            # 取得上一层调用frame
            last_stack = list_stack[1]
            var_iter = last_stack[0].f_locals.iteritems()
        except:
            var_iter = {}
        self.msg_kwargs = {key: value for key, value in var_iter if isinstance(value, JSON_TYPES)}

        self.msg_kwargs.update(kwargs)
        self.traceback_format_exc = traceback.format_exc()
        try:
            self.source_exp = sys.exc_info()[1]
        except:
            pass
        self._build_msg()

    def to_dict(self):
        """Return a dictionary representation of the exception."""
        as_dict = {
            "code": self.code,  # 错误代号
            "msg": self.message,  # 错误描述（内部)
            "request": self.request(),  # 请求相关的数据
            "detail": self.detail(),  # 用户自定义数据
        }
        return as_dict

    @staticmethod
    def request():
        result = {}
        try:
            # 处理uri
            start_pox = request.url.find('://')
            if start_pox == -1:
                start_pox = 0
            else:
                start_pox += 3
            uri = request.url
            if uri.find('/', start_pox) != -1:
                uri = uri[uri.find('/', start_pox):]

            # 本次请求一些数据
            result = {
                "method": request.method,
                'req_data': request.data,
                'uri': uri,
            }
        except RuntimeError:
            pass
        return result

    def detail(self):
        """
        错误详细信息
        :return:
        """
        return {}

    def _build_msg(self):
        """
        异常msg生成规则:
        1.默认使用raise出异常位置的locals作为字典
        2.使用self.msg_kwargs更新locals字典
        3.从MSG_FORMAT取出末班,然后template.format(locals())
        :return:
        """
        fm = MSG_FORMAT.get(self.code, MSG_FORMAT[10000])
        msg_dict = {key: u"" for key in re.findall("{(\w+)}", fm)}
        msg_dict.update(self.msg_kwargs)
        self.message = fm.format(**msg_dict)

    @classmethod
    def _lookup_http_code(cls, code):
        return HTTP_STATUS_CODE.get(code, 500)

    def http_code(self):
        return self._lookup_http_code(self.code)


def handler_app(_app):
    @_app.errorhandler(RestException)
    def handle_invalid_api_usage_exception(error):
        """
        Return a response with the appropriate status code, message, and content
        type when an ``RestException`` exception is raised.
        :param error:
        :return:
        """

        try:
            response = jsonify(error.to_dict())
            response.status_code = error.http_code()
            return response
        except:
            import logging
            import traceback

            # 这里的错误属于框架问题
            logging.error(traceback.format_exc())
            response = jsonify({
                "code": 10000,
                "msg": u'Undefined Exception',
                "request": {},
                "detail": {},
            })
            response.status_code = 500
            return response

    @_app.errorhandler(AssertionError)
    def handle_assertion_error(error):
        """
        Assertion Error
        :param error:
        :return:
        """
        return handle_invalid_api_usage_exception(RestException(11002, prompt=error.message))
