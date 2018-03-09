#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Author  :   windpro
E-mail  :   windprog@gmail.com
Date    :   2017/12/28
Desc    :   
"""
import time
import logging

from flask import g, current_app, request
from sqlalchemy import String
from sqlalchemy import asc, desc, or_
from sqlalchemy import inspect as sqla_inspect
from collections import OrderedDict
import inspect

from .exception import RestException
from .exp_format import raise_args_exception
from .utils import get_session, get_api_manager


def process_args_exception(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except RestException as  e:
            raise e
        except:
            _locals = inspect.trace()[-1][0].f_locals
            raise_args_exception(_locals.get('key'))

    return wrapper


class BaseArgs(object):
    ALL_FIELD = [
        '_page',
        '_num',
        '_sort',
        '_direction',
        '_orders',
        '_expand',
        '_fields',
        '_match',
    ]

    # @process_args_exception
    def init(self):
        args = request.args
        for key, value in args.items():
            assert not key.endswith('__')
            attr = "%s%s" % ('set', key)
            if hasattr(self, attr) and key in self.ALL_FIELD:
                getattr(self, attr)(value)
            else:
                if key.endswith('[]') and hasattr(self, attr[:-2]):
                    # example: _orders[]
                    true_attr = "%s%s" % ('set', key[:-2])
                    for true_value in request.args.getlist(key):
                        getattr(self, true_attr)(true_value)
                elif key.startswith('__'):
                    # 用户自行定义的get参数
                    pass
                else:
                    self.other_set(key, value)

    def other_set(self, key, value):
        pass


class PageArgs(BaseArgs):
    def __init__(self):
        self.num = current_app.config.get('RESULTS_PER_PAGE', None)
        self.page = 1
        self.sort = None
        self.direction = asc
        self.order_list = []
        self.array_field = OrderedDict()
        self.equal_field = OrderedDict()
        self.like_field = OrderedDict()
        self.init()

    def set_page(self, value):
        self.page = int(value)
        assert self.page >= 1

    def set_num(self, value):
        self.num = int(value)
        assert self.num >= 0 or self.num == -1

    def set_sort(self, value):
        self.sort = value

    def set_direction(self, value):
        assert value in ('asc', 'desc')
        self.direction = desc if value == 'desc' else asc

    def set_orders(self, value):
        # demo:BillingCity:asc,Total:asc
        for order_phase in value.split(','):
            if not order_phase:
                continue
            if ':' in order_phase:
                field, direction_str = order_phase.split(':', 1)
            else:
                field, direction_str = order_phase, 'asc'
            assert direction_str in ('asc', 'desc')
            direction = desc if direction_str == 'desc' else asc
            self.order_list.append((field, direction))

    def set_match(self, value):
        pass

    def other_set(self, key, value):
        super(PageArgs, self).other_set(key, value)
        if value.startswith('%') or value.endswith('%'):
            self.like_field[key] = value
        elif not key.startswith('_') and key.endswith('[]'):
            # 列表查找,跳过_开头字段
            real_key = key[:-2]
            self.array_field[real_key] = request.args.getlist(key)
        elif not key.startswith('_'):
            self.equal_field[key] = value

    def init(self):
        super(PageArgs, self).init()
        if self.sort:
            self.order_list.insert(0, (self.sort, self.direction))

    # @process_args_exception
    def get_filters(self, cls):
        """
        Parse search fields and values to filters.
        """
        from .exp_format import raise_args_exception

        filters = []
        relationships = sqla_inspect(cls).mapper.relationships
        all_field_items = self.array_field.items() + \
                          self.equal_field.items() + \
                          self.like_field.items()

        for key, value in all_field_items:
            if '.' in key:
                # set children attribute filters
                father_field, child_field = key.split(".", 1)

                if father_field not in relationships:
                    raise_args_exception(key)

                child_cls = relationships[father_field].mapper.class_
                if child_field == '_match':
                    # set children _match filters
                    fc = self._get_match_filter(child_cls, value)
                elif key in self.array_field:
                    fc = getattr(child_cls, child_field).in_(value)
                elif key in self.like_field:
                    fc = getattr(child_cls, child_field).like(value, escape='/')
                else:
                    fc = getattr(child_cls, child_field) == value
                    # 这里到底是子资源过滤还是条件过滤
                    if not relationships[father_field].uselist:
                        # uselist = false
                        obj = get_session().query(child_cls).filter(fc).first()
                        _filter = getattr(cls, father_field) == obj
                        filters.append(_filter)
                        continue
                if relationships[father_field].uselist:
                    _filter = getattr(cls, father_field).any(fc)
                else:
                    _filter = getattr(cls, father_field).has(fc)
            else:
                # set attribute filters
                if not hasattr(cls, key):
                    raise_args_exception(key)

                if key in self.array_field:
                    _filter = getattr(cls, key).in_(value)
                elif key in self.like_field:
                    _filter = getattr(cls, key).like(value, escape='/')
                else:
                    _filter = getattr(cls, key) == value
            filters.append(_filter)

        # set match filters
        args = request.args
        match_keywords = args.get('_match')
        if match_keywords:
            filters.append(self._get_match_filter(cls, match_keywords))
        return filters

    @staticmethod
    def _get_match_filter(cls, match_keywords):
        """
            Returns a search match filter
            Fields to be searched defines in model.__match_fields__
            Keyword should be specified with '%' as mysql 'like' conditions.
        """
        from .ma.model_registry import get_schemas
        match_fields = set()
        for schema in get_schemas(cls):
            if schema.opts.match_fields:
                match_fields.update(schema.opts.match_fields)
        match_filters = []
        for field in match_fields:
            column = getattr(cls, field)
            if not hasattr(cls, field):
                continue
            if not isinstance(column.type, String):
                continue
            for match_keyword in match_keywords.split(','):
                match_keyword = match_keyword.strip()
                if '%' not in match_keyword:
                    match_keyword = "%{}%".format(match_keyword)
                match_filters.append(column.like(match_keyword, escape='/'))
        if len(match_filters) == 1:
            return match_filters[0]
        return or_(*match_filters)

    def get_order_list(self, cls):
        from .exp_format import raise_args_exception

        try:
            return [direction(getattr(cls, field)) for field, direction in self.order_list]
        except:
            if field == self.sort:
                key = '_sort'
            else:
                key = '_orders'
            raise_args_exception(key)

    def get(self, cls, ext_filters=[], filter_object=None):
        filters = self.get_filters(cls)
        filters.extend(ext_filters)
        order_list = self.get_order_list(cls)
        if filter_object is None:
            filter_object = get_session().query(cls)
        resources = filter_object.filter(*filters)
        total = resources.count()

        if self.order_list:
            resources = resources.order_by(*order_list)
        if self.num == -1:
            # 返回所有列表
            pass
        elif self.page is not None and self.num is not None:
            # 分页
            offset = (self.page - 1) * self.num
            resources = resources.offset(offset).limit(self.num)
        return resources, total


class InfoArgs(BaseArgs):
    def __init__(self):
        self.expand = 0
        self.fields = {}
        self.except_ = {}
        self.init()

    def set_expand(self, value):
        self.expand = int(value)
        assert 0 <= self.expand <= 10, "_expand params must [0,10]"

    @staticmethod
    def __set_field_format_dict(result, value):
        """
        demo:BillingCity:asc,Total:asc
        :param value:
        :return:
        """
        for field_info in value.split(';'):
            if not field_info:
                continue
            assert ':' in field_info
            endpoint, fields_str = field_info.split(':')
            fields = [item for item in fields_str.split(',')]
            result[endpoint] = fields

    def set_fields(self, value):
        self.__set_field_format_dict(self.fields, value)

    def set_except(self, value):
        self.__set_field_format_dict(self.except_, value)
