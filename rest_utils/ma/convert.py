#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Author  :   windpro
E-mail  :   windprog@gmail.com
Date    :   2018/2/9
Desc    :
https://github.com/marshmallow-code/marshmallow-sqlalchemy/blob/dev/src/marshmallow_sqlalchemy/convert.py
"""
import inspect
import functools
import six

import uuid
import datetime
import marshmallow as ma
from marshmallow import validate, fields
from sqlalchemy.dialects import postgresql, mysql, mssql
from sqlalchemy.sql import sqltypes
import sqlalchemy as sa

from marshmallow import class_registry
from marshmallow.exceptions import RegistryError

from rest_utils.ma import model_registry


class ModelConversionError(Exception):
    """Raised when an error occurs in converting a SQLAlchemy construct
    to a marshmallow object.
    """


def _is_field(value):
    return (
            isinstance(value, type) and
            issubclass(value, fields.Field)
    )


def _has_default(column):
    return (
            column.default is not None or
            column.server_default is not None or
            _is_auto_increment(column)
    )


def _is_auto_increment(column):
    return (
            column.table is not None and
            column is column.table._autoincrement_column
    )


def _postgres_array_factory(converter, data_type):
    return functools.partial(
        fields.List,
        converter._get_field_class_for_data_type(data_type.item_type),
    )


def _should_exclude_field(column, fields=None, exclude=None):
    if fields and column.key not in fields:
        return True
    if exclude and column.key in exclude:
        return True
    return False


class MysqlTimestampField(fields.DateTime):
    def _serialize(self, value, attr, obj):
        if isinstance(value, six.string_types) and value.startswith("0000"):
            return None
        return super(MysqlTimestampField, self)._serialize(value, attr, obj)


class BigNumberField(fields.Integer):
    def _serialize(self, value, attr, obj):
        return str(value)


class ModelConverter(object):
    """Class that converts a SQLAlchemy model into a dictionary of corresponding
    marshmallow `Fields <marshmallow.fields.Field>`.
    """

    SQLA_TYPE_MAPPING = {
        sa.Enum: fields.Field,

        postgresql.BIT: fields.Integer,
        postgresql.UUID: fields.UUID,
        postgresql.MACADDR: fields.String,
        postgresql.INET: fields.String,
        postgresql.JSON: fields.Raw,
        postgresql.JSONB: fields.Raw,
        postgresql.HSTORE: fields.Raw,
        postgresql.ARRAY: _postgres_array_factory,

        mysql.BIT: fields.Integer,
        mysql.YEAR: fields.Integer,
        mysql.SET: fields.List,
        mysql.ENUM: fields.Field,

        # for mysql timestamp "0000-00-00 00:00:00"
        sqltypes.DateTime: MysqlTimestampField,
        sqltypes.TIMESTAMP: MysqlTimestampField,
        # end mysql timestamp

        sqltypes.BIGINT: BigNumberField,

        mssql.BIT: fields.Integer,
    }
    if hasattr(sa, 'JSON'):
        SQLA_TYPE_MAPPING[sa.JSON] = fields.Raw

    def __init__(self, schema_cls=None):
        self.schema_cls = schema_cls

    @property
    def type_mapping(self):
        if self.schema_cls:
            return self.schema_cls.TYPE_MAPPING
        else:
            return ma.Schema.TYPE_MAPPING

    def fields_for_model(self, model, include_fk=False, fields=None, exclude=None, base_fields=None,
            dict_cls=dict):
        result = dict_cls()
        base_fields = base_fields or {}
        for prop in model.__mapper__.iterate_properties:
            if _should_exclude_field(prop, fields=fields, exclude=exclude):
                continue
            if hasattr(prop, 'columns'):
                if not include_fk:
                    # Only skip a column if there is no overriden column
                    # which does not have a Foreign Key.
                    for column in prop.columns:
                        if not column.foreign_keys:
                            break
                    else:
                        continue
            field = base_fields.get(prop.key) or self.property2field(prop)
            if field:
                result[prop.key] = field
        return result

    def fields_for_table(self, table, include_fk=False, fields=None, exclude=None, base_fields=None,
            dict_cls=dict):
        result = dict_cls()
        base_fields = base_fields or {}
        for column in table.columns:
            if _should_exclude_field(column, fields=fields, exclude=exclude):
                continue
            if not include_fk and column.foreign_keys:
                continue
            field = base_fields.get(column.key) or self.column2field(column)
            if field:
                result[column.key] = field
        return result

    def property2field(self, prop, instance=True, field_class=None, **kwargs):
        field_class = field_class or self._get_field_class_for_property(prop)
        if not instance:
            return field_class
        field_kwargs = self._get_field_kwargs_for_property(prop)
        field_kwargs.update(kwargs)
        ret = field_class(**field_kwargs)
        return ret

    def column2field(self, column, instance=True, **kwargs):
        field_class = self._get_field_class_for_column(column)
        if not instance:
            return field_class
        field_kwargs = self.get_base_kwargs()
        self._add_column_kwargs(field_kwargs, column)
        field_kwargs.update(kwargs)
        return field_class(**field_kwargs)

    def field_for(self, model, property_name, **kwargs):
        prop = model.__mapper__.get_property(property_name)
        return self.property2field(prop, **kwargs)

    def _get_field_class_for_column(self, column):
        return self._get_field_class_for_data_type(column.type)

    def _get_field_class_for_data_type(self, data_type):
        field_cls = None
        types = inspect.getmro(type(data_type))
        # First search for a field class from self.SQLA_TYPE_MAPPING
        for col_type in types:
            if col_type in self.SQLA_TYPE_MAPPING:
                field_cls = self.SQLA_TYPE_MAPPING[col_type]
                if callable(field_cls) and not _is_field(field_cls):
                    field_cls = field_cls(self, data_type)
                break
        else:
            # Try to find a field class based on the column's python_type
            try:
                python_type = data_type.python_type
            except NotImplementedError:
                python_type = None

            if python_type in self.type_mapping:
                field_cls = self.type_mapping[python_type]
            else:
                if hasattr(data_type, 'impl'):
                    return self._get_field_class_for_data_type(data_type.impl)
                raise ModelConversionError(
                    'Could not find field column of type {0}.'.format(types[0]))
        return field_cls

    def _get_field_class_for_property(self, prop):
        from ..fields import Related

        if hasattr(prop, 'direction'):
            field_cls = Related
        else:
            column = prop.columns[0]
            field_cls = self._get_field_class_for_column(column)
        return field_cls

    def _get_field_kwargs_for_property(self, prop):
        kwargs = self.get_base_kwargs()
        if hasattr(prop, 'columns'):
            column = prop.columns[0]
            self._add_column_kwargs(kwargs, column)
        if hasattr(prop, 'direction'):  # Relationship property
            self._add_relationship_kwargs(kwargs, prop)
        if getattr(prop, 'doc', None):  # Useful for documentation generation
            kwargs['description'] = prop.doc
        return kwargs

    def _add_column_kwargs(self, kwargs, column):
        """Add keyword arguments to kwargs (in-place) based on the passed in
        `Column <sqlalchemy.schema.Column>`.
        """
        if not getattr(column, "foreign_keys", set()):
            # forgeign key不进行required校验, 使用errorhandler(StatementError)捕获错误处理
            if column.nullable:
                kwargs['allow_none'] = True
            kwargs['required'] = not column.nullable and not _has_default(column)

        if hasattr(column.type, 'enums'):
            kwargs['validate'].append(validate.OneOf(choices=column.type.enums))

        # Add a length validator if a max length is set on the column
        # Skip UUID columns
        if hasattr(column.type, 'length'):
            try:
                python_type = column.type.python_type
            except (AttributeError, NotImplementedError):
                python_type = None
            if not python_type or not issubclass(python_type, uuid.UUID):
                kwargs['validate'].append(validate.Length(max=column.type.length))

        if hasattr(column.type, "python_type"):
            # set sqlachemy.DateTime default format
            python_type = column.type.python_type
            if python_type is datetime.datetime:
                # 这里处理datetime的默认参数
                kwargs["format"] = "%Y-%m-%d %H:%M:%S"

        if hasattr(column.type, 'scale'):
            kwargs['places'] = getattr(column.type, 'scale', None)

    def _add_relationship_kwargs(self, kwargs, prop):
        """Add keyword arguments to kwargs (in-place) based on the passed in
        relationship `Property`.
        """
        # from ..sa_util import get_prop_nullable
        # nullable = get_prop_nullable(prop)
        nullable = True  # 暂时不需要限制关系的required参数

        class_ = prop.mapper.class_

        kwargs.update({
            'allow_none': nullable,
            'required': not nullable,
            "schema": class_
        })

    def get_base_kwargs(self):
        return {
            'validate': []
        }
