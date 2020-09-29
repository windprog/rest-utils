#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Author  :   windpro
E-mail  :   windprog@gmail.com
Date    :   2018/2/9
Desc    :   
"""
from marshmallow import fields
from marshmallow.utils import missing as missing_
from marshmallow.base import SchemaABC
from marshmallow import class_registry
from marshmallow.compat import basestring
from marshmallow.exceptions import ValidationError
from marshmallow.fields import *

from sqlalchemy import inspect as sa_inspect

from .utils import is_sa_mapped
from .ma import model_registry
from .sa_util import get_prop_nullable

_RECURSIVE_NESTED = 'self'

__all__ = [
    'Field',
    'Raw',
    'Nested',
    'Dict',
    'List',
    'String',
    'UUID',
    'Number',
    'Integer',
    'Decimal',
    'Boolean',
    'FormattedString',
    'Float',
    'DateTime',
    'LocalDateTime',
    'Time',
    'Date',
    'TimeDelta',
    'Url',
    'URL',
    'Email',
    'Method',
    'Function',
    'Str',
    'Bool',
    'Int',
    'Constant',
    "Related",
]


def get_schema_for_field(field):
    """
    该方法必须确保field的schema实例化
    :param field:
    :return:
    """
    if hasattr(field, 'root'):  # marshmallow>=2.1
        return field.root
    else:
        return field.parent


class Related(fields.Field):
    """Related data represented by a SQLAlchemy `relationship`. Must be attached
    to a :class:`Schema` class whose options includes a SQLAlchemy `model`, such
    as :class:`ModelSchema`.

    Examples: ::

        user1 = fields.Related(User)
        user2 = fields.Related(UserSchema)
        user3 = fields.Related('UserSchema')  # Equivalent to above
        parent = fields.Related('self')

    When passing a `Schema <marshmallow.Schema>` instance as the first argument,
    the instance's ``exclude``, ``only``, and ``many`` attributes will be respected.

    Therefore, when passing the ``exclude``, ``only``, or ``many`` arguments to `fields.Nested`,
    you should pass a `Schema <marshmallow.Schema>` class (not an instance) as the first argument.

    :param Schema schema: The Schema class or class name (string)
        to nest, or ``"self"`` to nest the :class:`Schema` within itself.
    """

    default_error_messages = {
        'invalid': 'Could not deserialize related value {value!r}; '
                   'expected a dictionary with keys {keys!r}'
    }

    def __init__(self, schema, default=missing_, **kwargs):
        self.unload_schema = schema
        self.__schema_class = None  # Cached Schema
        if isinstance(self.unload_schema, type) and \
                issubclass(self.unload_schema, SchemaABC):
            self.__schema_class = self.unload_schema
        elif isinstance(self.unload_schema, type) and is_sa_mapped(self.unload_schema):
            # SQLAlchemy model
            self.__schema_class = model_registry.auto_build_schema(self.unload_schema)
        super(Related, self).__init__(default=default, **kwargs)

    @property
    def model(self):
        schema = get_schema_for_field(self)
        return schema.opts.model

    @property
    def related_prop(self):
        return getattr(self.model, self.attribute or self.name).property

    @property
    def session(self):
        schema = get_schema_for_field(self)
        return schema.session

    @property
    def schema_class(self):
        """The Schema object.
        """
        if not self.__schema_class:
            # 延后载入的数据类型
            if isinstance(self.unload_schema, basestring):
                if self.unload_schema == _RECURSIVE_NESTED:
                    parent_class = get_schema_for_field(self).__class__
                    self.__schema_class = parent_class
                else:
                    schema_class = class_registry.get_class(self.unload_schema)
                    self.__schema_class = schema_class
            else:
                raise ValueError('Related fields must be passed a '
                                 'Schema, not {0}.'.format(self.unload_schema.__class__))
        return self.__schema_class

    def _serialize(self, value, attr, obj):
        father_schema = get_schema_for_field(self)
        # 当前展开层级
        expand = father_schema._current_expand
        # schema展开配置
        related_kwargs = father_schema._related_kwargs
        # 子级 schema
        schema_class = self.schema_class

        dump_kwargs = dict()
        if expand is not None:
            dump_kwargs["expand"] = expand - 1

        schema = schema_class(
            many=self.related_prop.uselist,
            session=getattr(father_schema, "_session", None),
            related_kwargs=related_kwargs,
            **related_kwargs.get(schema_class, {})
        )

        ret, errors = schema.dump(value, **dump_kwargs)
        if errors:
            raise ValidationError(errors, data=ret)
        return ret

    def _deserialize_one(self, value, attr, data):
        father_schema = get_schema_for_field(self)
        # schema展开配置
        related_kwargs = father_schema._related_kwargs
        # 子级 schema
        schema_class = self.schema_class

        schema_kwargs = dict(
            # many=self.related_prop.uselist,
            session=getattr(father_schema, "_session", None),
            check_existence=father_schema._check_existence,  # 子资源创建检查策略跟随父策略
            related_kwargs=related_kwargs,
            **related_kwargs.get(schema_class, {})
        )

        # 上一级的查询
        if father_schema._instance:
            father_class = sa_inspect(father_schema._instance).mapper.class_
            father_attr = getattr(father_class, self.attribute or self.name)

            schema_kwargs["father_instance"] = father_schema._instance
            if self.related_prop.uselist:
                schema_kwargs["father_attr"] = father_attr
            else:
                # uselist=False
                old = getattr(father_schema._instance, self.attribute or self.name)
                if self.related_prop.lazy == 'select' and old:
                    schema_kwargs["instance"] = old

        schema = schema_class(**schema_kwargs)

        ins, errors = schema.load(value)
        if errors:
            raise ValidationError(errors, data=ins)
        return ins

    def _deserialize(self, value, attr, data):
        from marshmallow import utils

        if not self.related_prop.uselist:
            return self._deserialize_one(value, attr, data)

        if not utils.is_collection(value):
            self.fail('invalid')

        result = []
        errors = {}
        for idx, each in enumerate(value):
            try:
                result.append(self._deserialize_one(each, attr, data))
            except ValidationError as e:
                result.append(e.data)
                errors.update({idx: e.messages})

        if errors:
            raise ValidationError(errors, data=result)

        return result
