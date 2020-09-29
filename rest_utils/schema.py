#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Author  :   windpro
E-mail  :   windprog@gmail.com
Date    :   2018/2/8
Desc    :
manager.add(model_or_schema, methods=["GET"])
"""
import datetime as dt
import uuid
import decimal

import marshmallow as ma
from marshmallow import Schema as marshmallowSchema
from marshmallow import fields
from marshmallow.compat import with_metaclass, iteritems

from sqlalchemy import Integer, DateTime, Date, Numeric, JSON
from sqlalchemy.orm.dynamic import AppenderQuery

from .sa_util import get_instance, get_instance_by_cond
from .ma.convert import ModelConverter
from .utils import add_padding_callback, check_need_modify
from .ma import model_registry
from .fields import Related

READONLY_METHODS = frozenset(('GET',))


def default_filters():
    return []


def default_create(model, data):
    return model(**data)


def default_update(instance, data):
    for key, value in iteritems(data):
        # AppenderQuery 必须整体替换,不然无法实现替换子资源操作
        # if isinstance(getattr(instance, key, None), AppenderQuery):
        #     continue
        setattr(instance, key, value)
    return instance


def default_delete(instance):
    return instance


def default_completed(instance):
    pass


DEFAULT_MODEL_OPTS = {
    "model_converter": ModelConverter,
    "include_fk": True,  # 展示外键
    # restfull api相关配置
    "key_field": None,  # /users/@windpro
    "endpoint": None,
    "match_fields": [],  # 用于_match参数搜索的字段
    "results_per_page": 10,  # 默认每页返回数目。None则不限制返回条数
    "max_results_per_page": 100,  # 最大每页返回数目。None则不限制返回条数
    "methods": READONLY_METHODS,  # 默认的HTTP方法
    "filters": default_filters,  # 查询时默认添加的orm filter
    "create": default_create,  # 创建实例回调方法。(instance, data)
    "update": default_update,  # 修改实例回调方法。(instance, data)
    "delete": default_delete,  # 删除实例回调方法。(instance)
    "created": default_completed,  # commit数据库之后的创建实例回调方法。
    "updated": default_completed,  # commit数据库之后的修改实例回调方法。
    "deleted": default_completed,  # commit数据库之后的删除实例回调方法。
}


class TableSchemaOpts(ma.SchemaOpts):
    """Options class for `TableSchema`.
    Adds the following options:
    - ``table``: The SQLAlchemy table to generate the `Schema` from (required).
    - ``model_converter``: `ModelConverter` class to use for converting the SQLAlchemy table to
        marshmallow fields.
    - ``include_fk``: Whether to include foreign fields; defaults to `False`.
    """

    def __init__(self, meta, *args, **kwargs):
        super(TableSchemaOpts, self).__init__(meta, *args, **kwargs)
        self.table = getattr(meta, 'table', None)
        self.model_converter = getattr(meta, 'model_converter', ModelConverter)
        self.include_fk = getattr(meta, 'include_fk', False)


class ModelSchemaOpts(ma.SchemaOpts):
    """Options class for `ModelSchema`.
    Adds the following options:

    - ``model``: The SQLAlchemy model to generate the `Schema` from (required).
    - ``model_converter``: `ModelConverter` class to use for converting the SQLAlchemy model to
        marshmallow fields.
    - ``include_fk``: Whether to include foreign fields; defaults to `False`.
    """

    def __init__(self, meta, *args, **kwargs):
        super(ModelSchemaOpts, self).__init__(meta, *args, **kwargs)
        for attr, default_value in iteritems(DEFAULT_MODEL_OPTS):
            if hasattr(meta, attr):
                value = getattr(meta, attr)
            else:
                value = default_value
            setattr(self, attr, value)
        self.model = getattr(meta, 'model', None)


class SchemaMeta(ma.schema.SchemaMeta):
    """Metaclass for `ModelSchema`."""

    # override SchemaMeta
    def __new__(mcs, name, bases, attrs):
        from marshmallow.compat import OrderedDict
        from marshmallow.schema import _get_fields, _get_fields_by_mro
        from marshmallow import base

        meta = attrs.get('Meta')
        ordered = getattr(meta, 'ordered', False)
        if not ordered:
            # Inherit 'ordered' option
            # Warning: We loop through bases instead of MRO because we don't
            # yet have access to the class object
            # (i.e. can't call super before we have fields)
            for base_ in bases:
                if hasattr(base_, 'Meta') and hasattr(base_.Meta, 'ordered'):
                    ordered = base_.Meta.ordered
                    break
            else:
                ordered = False
        cls_fields = _get_fields(attrs, base.FieldABC, pop=True, ordered=ordered)
        klass = super(SchemaMeta, mcs).__new__(mcs, name, bases, attrs)
        inherited_fields = _get_fields_by_mro(klass, base.FieldABC, ordered=ordered)

        # Use getattr rather than attrs['Meta'] so that we get inheritance for free
        meta = getattr(klass, 'Meta')
        # Set klass.opts in __new__ rather than __init__ so that it is accessible in
        # get_declared_fields
        klass.opts = klass.OPTIONS_CLASS(meta)
        # Pass the inherited `ordered` into opts
        klass.opts.ordered = ordered
        # Add fields specifid in the `include` class Meta option
        cls_fields += list(klass.opts.include.items())

        mcs.before_declared_fields(klass)

        dict_cls = OrderedDict if ordered else dict
        # Assign _declared_fields on class
        klass._declared_fields = mcs.get_declared_fields(
            klass=klass,
            cls_fields=cls_fields,
            inherited_fields=inherited_fields,
            dict_cls=dict_cls
        )
        return klass

    @classmethod
    def before_declared_fields(mcs, klass):
        # assign table or model to Meta
        for key in DEFAULT_MODEL_OPTS.keys():
            attr = "__%s__" % key
            if hasattr(klass, attr):
                # 使用内部成员来配置opts
                setattr(klass.opts, key, getattr(klass, attr))
        for key in ["table", "model"]:
            # 注册model或者table
            if getattr(klass.opts, key, None):
                model_registry.register(getattr(klass.opts, key), klass)

    @classmethod
    def get_declared_fields(mcs, klass, cls_fields, inherited_fields, dict_cls):
        """Updates declared fields with fields converted from the SQLAlchemy model
        passed as the `model` class Meta option.
        """
        opts = klass.opts
        Converter = opts.model_converter
        converter = Converter(schema_cls=klass)
        base_fields = super(SchemaMeta, mcs).get_declared_fields(
            klass, cls_fields, inherited_fields, dict_cls
        )
        declared_fields = mcs.get_fields(converter, opts, base_fields, dict_cls)
        declared_fields.update(base_fields)
        return declared_fields

    @classmethod
    def get_fields(mcs, converter, base_fields, opts):
        pass


class TableSchemaMeta(SchemaMeta):

    @classmethod
    def before_declared_fields(mcs, klass):
        # assign __table__ to Meta
        table = getattr(klass, '__table__', klass.opts.table)
        if table:
            klass.opts.table = table
            model_registry.register(table, klass)

    @classmethod
    def get_fields(mcs, converter, opts, base_fields, dict_cls):
        if opts.table is not None:
            return converter.fields_for_table(
                opts.table,
                fields=opts.fields,
                exclude=opts.exclude,
                include_fk=opts.include_fk,
                base_fields=base_fields,
                dict_cls=dict_cls,
            )
        return dict_cls()


class ModelSchemaMeta(SchemaMeta):

    @classmethod
    def before_declared_fields(mcs, klass):
        # assign __model__ to Meta
        model = getattr(klass, '__model__', klass.opts.model)
        if model:
            klass.opts.model = model
            model_registry.register(model, klass)

    @classmethod
    def get_fields(mcs, converter, opts, base_fields, dict_cls):
        if opts.model is not None:
            return converter.fields_for_model(
                opts.model,
                fields=opts.fields,
                exclude=opts.exclude,
                include_fk=opts.include_fk,
                base_fields=base_fields,
                dict_cls=dict_cls,
            )
        return dict_cls()


class TableSchema(with_metaclass(TableSchemaMeta, ma.Schema)):
    """Base class for SQLAlchemy model-based Schemas.
    Example: ::
        from rest_utils import TableSchema
        from mymodels import engine, users
        class UserSchema(TableSchema):
            class Meta:
                table = users
        schema = UserSchema()
        select = users.select().limit(1)
        user = engine.execute(select).fetchone()
        serialized = schema.dump(user).data
    """
    OPTIONS_CLASS = TableSchemaOpts


class ModelSchema(with_metaclass(ModelSchemaMeta, ma.Schema)):
    """Base class for SQLAlchemy model-based Schemas.

    Example: ::

        from rest_utils import ModelSchema
        from mymodels import User, session

        class UserSchema(ModelSchema):
            class Meta:
                model = User

        or

        class UserSchema(ModelSchema):
            __model__ = User

        schema = UserSchema()

        user = schema.load({'name': 'Bill'}, session=session)
        existing_user = schema.load({'name': 'Bill'}, instance=User.query.first())

    :param session: Optional SQLAlchemy session; may be overridden in `load.`
    :param instance: Optional existing instance to modify; may be overridden in `load`.
    """
    OPTIONS_CLASS = ModelSchemaOpts

    def __init__(self, related_kwargs={}, check_existence=True, *args, **kwargs):
        """
        :param only:
        :param exclude:
        :param related_kwargs: fields.Related字段展开时的参数。如{UserSchema: {"exclude": ["id"]}}
        :param check_existence: 创建资源之前先检查是否存在,默认检查
        :param args:
        :param kwargs:
        """
        if not self.opts.model:
            raise ValueError('ModelSchema requires a sa orm model.')
        self.model = self.opts.model
        self._instance = kwargs.pop('instance', None)  # instance必须存在于数据库中
        # 存在instance则不能为many
        if self._instance and kwargs.get("many", False) is True:
            raise ValueError('ModelSchema instance require many=False')
        self._session = kwargs.pop('session', None)

        # 上层对象的attr(uslist=True的情况下)
        self._father_attr = kwargs.pop('father_attr', None)
        # 上层对象
        self._father_instance = kwargs.pop('father_instance', None)

        # self.ext_data = dict()
        # 展开层级
        self._current_expand = None
        # 创建资源之前先检查是否存在
        self._check_existence = check_existence
        self._related_kwargs = related_kwargs

        super(ModelSchema, self).__init__(*args, **kwargs)

    @ma.post_load
    def make_instance(self, data):
        """Deserialize data to an instance of the model. Update an existing row
        loaded by primary key(s) in the data;
        else create a new row.
        :param data: Data to deserialize.
        """
        if self._check_existence:
            # 存在 _owner_query 则使用 ins.relationship.filter 查询
            if self.many:
                # 一般情况下都是schema 一对一 ins.如果用到了many,则只能重新查询一次
                instance = get_instance(self._session, self.model, data)
            else:
                instance = self._instance
            if instance is not None:
                # 检查是否需要变更
                if check_need_modify(instance, data):
                    instance = self.opts.update(instance, data)
                    add_padding_callback(self.opts.updated, instance)  # commit数据库之后调用
                return instance
        instance = self.opts.create(self.model, data)
        add_padding_callback(self.opts.created, instance)  # commit数据库之后调用
        return instance

    def dump(self, obj, many=None, expand=0, **kwargs):
        """
        serialize
        :param obj:
        :param many:
        :param expand: 当expand>=1或者None时，field.Related生效，展开展开子资源
        :param kwargs:
        :return:
        """

        old_exclude = self.exclude
        old_only = self.only
        try:
            self._current_expand = expand
            if self._current_expand is not None and self._current_expand <= 0:
                exclude = list(old_exclude) if old_exclude else []
                only = list(old_only) if old_only else []
                for key, field in iteritems(self._declared_fields):
                    if isinstance(field, Related):
                        if key not in exclude:
                            exclude.append(key)
                        if key in only:
                            only.remove(key)
                if exclude:
                    self.exclude = exclude
                if only:
                    self.only = only
            return super(ModelSchema, self).dump(obj, many=many, **kwargs)
        finally:
            self._current_expand = None
            self.exclude = old_exclude
            self.only = old_only

    def load(self, data, *args, **kwargs):
        """Deserialize data to internal representation.

        :param session: Optional SQLAlchemy session.
        :param instance: Optional existing instance to modify.
        """
        if not self._session:
            raise ValueError('Deserialization requires a session')
        many = self.many if kwargs.get("many") is None else bool(kwargs.get("many"))
        if self._check_existence and not many and not self._instance:
            self._instance = (
                get_instance_by_cond(self._session, self._father_instance, self._father_attr, self.model, data)
                if self._father_attr else
                get_instance(self._session, self.model, data)
            )
        return super(ModelSchema, self).load(data, *args, **kwargs)

    def validate(self, data, *args, **kwargs):
        if not self._session:
            raise ValueError('Validation requires a session')
        return super(ModelSchema, self).validate(data, *args, **kwargs)
