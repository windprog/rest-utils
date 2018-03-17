#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Author  :   windpro
E-mail  :   windprog@gmail.com
Date    :   16/9/18
Desc    :   
"""
import json
from flask import request
from .exception import (
    PermissionDenied,
    IllegalRequestData,
    # MethodNotAcceptable,
)
from .sa_util import get_tablename


def raise_main_filters_not_exist(function, class_, _type):
    raise PermissionDenied(dict(
        function=repr(function),
        prompt=u'table:%s %s Filters Error.' % (get_tablename(class_), _type)
    ))


def raise_validate_failure():
    raise PermissionDenied(dict(
        prompt=u'Validate Failure'
    ))


def raise_collection_attribute_not_change(collection, key):
    raise PermissionDenied(dict(
        prompt='Collection:%s attribute:%s Not Be Changed.' % (collection, key)
    ))


def raise_collection_attribute_not_found(collection, attribute):
    raise IllegalRequestData(dict(
        prompt='Collection:%s attribute:%s Not Found.' % (collection, attribute),
    ))


def raise_collection_attribute_not_relationships(collection, attribute):
    raise IllegalRequestData(dict(
        prompt='Collection:%s attribute:%s Not Relationships.' % (collection, attribute),
    ))


def raise_collection_attribute_not_list(collection, attribute):
    raise IllegalRequestData(dict(
        prompt='Collection:%s attribute:%s Not List.' % (collection, attribute),
    ))


def raise_request_format_error(error_type):
    raise IllegalRequestData(dict(
        prompt=u'request.%s format error.' % error_type
    ))


# def raise_validate_methods(method, cls):
#     raise MethodNotAcceptable(dict(
#         method=method,
#         endpoint=cls.endpoint(),
#         support_methods=u','.join(cls.__methods__)
#     ))


def raise_args_exception(key):
    raise IllegalRequestData(dict(
        prompt=u"Invalid argument key:%s value:%s." % (key, request.args.get(key, '')),
    ))


def raise_request_data_attr_format_error(resource, attr_name, value):
    raise IllegalRequestData(dict(
        prompt=u"collection %s key:%s value:%s" % (
            getattr(resource, '__tablename__', ''), attr_name, repr(value))
    ))


def raise_request_data_not_convert_int(attr_name, value):
    raise IllegalRequestData(dict(
        prompt="attribute:%s type:%s value:%s Not Convert." % (
            attr_name, "Integer", value
        )
    ))


def raise_ext_field(cls, ext_dict):
    raise IllegalRequestData(dict(
        prompt=u"collection %s ext data:%s" % (
            getattr(cls, '__tablename__', ''), json.dumps(ext_dict))
    ))
