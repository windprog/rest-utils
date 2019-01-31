#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Author  :   windpro
E-mail  :   windprog@gmail.com
Date    :   16/9/18
Desc    :
"""
import inspect
import sys
import re
import traceback
import logging
import json
import six
from requests import codes
from marshmallow.compat import iteritems

if six.PY3:
    # 不再使用from types import NoneType,不兼容py3
    JSON_TYPES = tuple([float, str, type(None)] + list(six.integer_types))
else:
    from types import NoneType

    JSON_TYPES = tuple([float, unicode, str, NoneType] + list(six.integer_types))


class RestException(Exception):
    """
    REST异常基类，该异常会被整个app捕获生成错误结果
    类字段：
    * status: http status code
    * msg: 错误信息，支持模板{field}
    """
    status = codes.INTERNAL_SERVER_ERROR  # 500

    def __init__(self, detail=None):
        """
        :param detail: example: {"name": "Must be an string"}
        """
        self.detail = detail = detail or dict()  # 结果中的detailed字段
        self.msg_kwargs = dict()
        self.msg_kwargs.update(detail)

        self.exc_info = sys.exc_info()

        self.class_ = type(self)

        # 类名作为错误类型
        self.type = self.class_.__name__

        if hasattr(self.class_, "msg"):
            # 自定义信息
            msg = self.class_.msg
        else:
            # 使用类型描述
            msg = self.class_.__doc__.strip()

        if "{" in msg:
            # 模板类型消息
            list_stack = inspect.stack()  # 取得调用链
            try:
                # 取得上一层调用frame
                last_stack = list_stack[1]
                var_iter = iteritems(last_stack[0].f_locals)
                # 取得上一层调用的名称空间
                self.msg_kwargs.update({key: value for key, value in var_iter if isinstance(value, JSON_TYPES)})
            except:
                pass

        self.format_msg = self._get_msg(msg)

    def format_exc(self, limit=None):
        """Like print_exc() but return a string."""
        etype, value, tb = self.exc_info
        if tb:
            return ''.join(traceback.format_exception(etype, value, tb, limit))

    def to_dict(self):
        """Return a dictionary representation of the exception."""
        as_dict = {
            "type": self.type,  # 异常类型
            "msg": self.format_msg,  # 错误描述（内部)
            "detail": self.detail,  # 用户自定义数据
        }
        # 记录log
        self.write_log()
        return as_dict

    def _get_msg(self, msg):
        """
        异常msg生成规则:
        1.默认使用raise出异常位置的locals作为字典
        2.使用self.detail更新locals字典
        3.从MSG_FORMAT取出模板,然后template.format(locals())
        :return: str msg
        """
        if "{" in msg:
            msg_dict = {key: u"" for key in re.findall("{(\w+)}", msg)}
            msg_dict.update(self.msg_kwargs)
            message = msg.format(**msg_dict)
        else:
            message = msg
        return message

    def write_log(self):
        source_exp = self.format_exc()
        if source_exp:
            logging.error(source_exp)

        result = dict(type=self.type)
        result.update(self.detail)

        try:
            logging.info("%s %s" % (self.format_msg, json.dumps(result)))
        except:
            logging.error("logging type error: " + repr([self.format_msg, result, self.exc_info]))


class Unknown(RestException):
    """
    未知错误
    """
    # 10000
    status = codes.INTERNAL_SERVER_ERROR


class PermissionDenied(RestException):
    """
    操作资源的权限错误
    """
    # 10007
    status = codes.FORBIDDEN


class AccessDenied(RestException):
    """
    非法访问
    """
    status = codes.FORBIDDEN


class RequestHeadersAcceptNotSupport(RestException):
    """
    Headers:ACCEPT 类型不支持
    """
    # 10007
    status = codes.NOT_ACCEPTABLE


class RequestHeadersContentTypeNotSupport(RestException):
    """
    Headers:Content-type 类型不支持
    """
    # 31001
    status = codes.UNSUPPORTED_MEDIA_TYPE


class RestAssertionError(RestException):
    """
    断言异常
    """
    # 11002
    status = codes.BAD_REQUEST


class ResourceNotFound(RestException):
    """
    资源不存在
    """
    # 10003
    status = codes.NOT_FOUND


class ResourceRelationNotExists(RestException):
    """
    两个资源关系不存在
    """
    # 21000
    status = codes.NOT_FOUND


class IllegalRequestData(RestException):
    """
    提交数据错误
    """
    # 30000
    status = codes.BAD_REQUEST


# class MethodNotAcceptable(RestException):
#     """
#     访问行为限制
#     """
#     # 11001
#     status = codes.FORBIDDEN


class StatementErrorException(RestException):
    """
    数据库错误
    """
    status = codes.INTERNAL_SERVER_ERROR

    def __init__(self, detail=None):
        if type(self) is StatementErrorException:
            # 当raise为本实例的话就拿出默认错误信息返回客户端
            detail = self.default_detail(sys.exc_info()[1])
        super(StatementErrorException, self).__init__(detail)

    @staticmethod
    def default_detail(source_exp):
        if not source_exp:
            return {}
        # 系统异常处理; auto parse exception
        result = {}
        params = getattr(source_exp, 'params', None)
        if isinstance(params, (list, tuple)):
            params = list(params)
            for index, item in enumerate(params):
                if not isinstance(item, JSON_TYPES):
                    try:
                        params[index] = str(item)
                    except:
                        params[index] = repr(item)
        result.update({
            'params': params,
            'statement': getattr(source_exp, 'statement', None),
            'sql_args': getattr(getattr(source_exp, 'orig', object()), 'args', None),
            'sql_detail': getattr(source_exp, 'detail', None),
        })
        return result


class DatabaseExecutionError(StatementErrorException):
    """
    数据库执行错误
    """
    # 10001
    status = codes.BAD_REQUEST


class DatabaseConnectionError(StatementErrorException):
    """
    数据库连接异常
    """
    status = codes.INTERNAL_SERVER_ERROR


class ResourcesAlreadyExists(StatementErrorException):
    """
    资源已存在.
    """
    # 10004
    status = codes.BAD_REQUEST


class ForeignKeyConstraintFails(StatementErrorException):
    """
    外键依赖异常
    """
    status = codes.BAD_REQUEST


class ResourcesConstraintNotNullable(StatementErrorException):
    """
    字段必须非空
    """
    status = codes.BAD_REQUEST


class ResourcesConstraintNotDefaultValue(StatementErrorException):
    """
    字段没有默认值
    """
    status = codes.BAD_REQUEST
