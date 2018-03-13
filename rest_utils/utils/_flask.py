#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Author  :   windpro
E-mail  :   windprog@gmail.com
Date    :   2017/12/28
Desc    :   
"""
import logging
from sqlalchemy.orm.util import class_mapper, object_mapper
from sqlalchemy.orm.exc import UnmappedInstanceError
from flask import current_app, request, jsonify, g
from marshmallow.compat import iteritems
from marshmallow import missing
from ..exception import RequestHeadersContentTypeNotSupport

__all__ = [
    "jsonres",
    "get_resource_data",
    "convert_to_json_value",
    "current_blueprint",
    "get_class",
    "get_session",
    "add_padding_callback",
    "do_padding_callback",
    "check_need_modify",
    "is_sa_mapped",
    "is_mapped",
    "get_page_args",
    "get_info_args",
    "get_api_manager",
]

JSON_CONTENT_TYPES = set(['application/json'])
HTML_CONTENT_TYPES = set(['text/html', 'application/x-www-form-urlencoded'])


def jsonres(data):
    from flask.json import dumps
    indent = None
    if current_app.config['JSONIFY_PRETTYPRINT_REGULAR'] and not request.is_xhr:
        indent = 2
    return current_app.response_class(
        dumps(data, indent=indent),
        mimetype='application/json'
    )


def get_resource_data(incoming_request):
    """Return the data from the incoming *request* based on the
    Content-type."""
    from ..exp_format import raise_request_format_error

    content_type = incoming_request.headers.get('Content-type', '').split(';')
    content_type = content_type[0] if content_type else ''
    if ('Content-type' not in incoming_request.headers or
            content_type in JSON_CONTENT_TYPES):
        try:
            ret = incoming_request.json
            assert isinstance(ret, (dict, list)), u"请求数据错误"
            return ret
        except:
            error_type = 'json'

    elif content_type in HTML_CONTENT_TYPES:
        try:
            ret = incoming_request.form
            ret_dict = dict()
            if ret:
                for key, value in iteritems(ret):
                    ret_dict[key] = value
            return ret_dict
        except:
            error_type = 'form'
    else:
        # HTTP 415: Unsupported Media Type
        raise RequestHeadersContentTypeNotSupport(dict(
            types=incoming_request.headers.get('Content-type', '')
        ))
    raise_request_format_error(error_type)


def convert_to_json_value(column_attrs, attr, value):
    """
    将资源的字段转换成json的格式输出
    :param column_attrs: inspect_.mapper.column_attrs
    :param attr:
    :param value:
    :return:
    """
    from sqlalchemy import Integer, DateTime, Date, Numeric, JSON
    try:
        type_ins = column_attrs[attr].columns[0].type
        if isinstance(type_ins, DateTime):
            return value.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(type_ins, Date):
            return str(value)
        elif isinstance(type_ins, Numeric):
            # if isinstance(value, Decimal): return float(value)
            return value
        elif isinstance(type_ins, JSON):
            return value
    except:
        pass
    return value


def current_blueprint():
    blueprint = request.blueprint
    return current_app.blueprints[blueprint]


def get_class(obj):
    """
    可以获取如下类型的class
    RelationshipProperty
    db.Model
    :param obj:
    :return:
    """
    from sqlalchemy.orm.relationships import RelationshipProperty
    from sqlalchemy import inspect

    if isinstance(obj, RelationshipProperty):
        return obj.mapper.class_
    if is_sa_mapped(obj) and hasattr(obj, "__tablename__"):
        # model
        return inspect(obj).class_
    return obj


def get_session():
    """Return (and memoize) a database session"""
    session = getattr(g, '_session', None)
    if session is None:
        session = g._session = current_app.api_manager.get_session()
    return session


def _ensure_padding():
    if not hasattr(g, "padding_callback"):
        padding = g.padding_callback = []
    else:
        padding = g.padding_callback
    return padding


def add_padding_callback(func, *args, **kwargs):
    try:
        padding = _ensure_padding()
    except RuntimeError:
        # Working outside of application context. skip it
        return
    padding.append((func, args, kwargs))


def do_padding_callback():
    for func, args, kwargs in _ensure_padding():
        func(*args, **kwargs)


def check_need_modify(instance, data):
    """
    检查对象是否需要变更
    :param instance:
    :param data:
    :return:
    """
    for key, value in iteritems(data):
        if getattr(instance, key, missing) != value:
            return True
    return False


def is_sa_mapped(cls, log=False):
    """
    判断是否为sqlalchemy orm model
    :param cls:
    :param log: 是否记录日志
    :return:
    """
    try:
        class_mapper(cls)
        return True
    except Exception as e:
        if log:
            logging.exception("type_check_warning")
        return False


def is_mapped(obj):
    try:
        object_mapper(obj)
        return True
    except UnmappedInstanceError:
        return False


def get_page_args():
    from ..params import PageArgs

    if not hasattr(g, "page_args"):
        page_args = g.page_args = PageArgs()
    else:
        page_args = g.page_args
    assert isinstance(page_args, PageArgs)
    return page_args


def get_info_args():
    from ..params import InfoArgs
    if not hasattr(g, "info_args"):
        info_args = g.info_args = InfoArgs()
    else:
        info_args = g.info_args
    assert isinstance(info_args, InfoArgs)
    return info_args


def get_api_manager():
    return current_app.api_manager
