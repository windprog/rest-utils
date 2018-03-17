#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Author  :   windpro
E-mail  :   windprog@gmail.com
Date    :   2018/2/12
Desc    :   A registry of :class:`Schema <marshmallow.Schema>` classes. This allows for sqlalchemy orm
lookup of schemas, which may be used with
class:`fields.Related <transform.fields.Related>`.

.. warning::

    This module is treated as private API.
    Users should not need to use this module directly.
"""
from __future__ import unicode_literals

from marshmallow.exceptions import RegistryError

# {
#   <orm_class>: <list of class objects>
# }
_registry = {}


def register(model, schema):
    """Add a class to the registry of serializer classes.

    Example: ::

        register(Users, UsersSchema)
        # Registry:
        # {
        #   Users: [UsersSchema],
        # }

    """
    from ..sa_util import get_tablename
    exists_schemas = _registry.setdefault(model, [])
    table_name = get_tablename(model)
    if table_name:
        _registry[table_name] = exists_schemas
    if schema not in exists_schemas:
        exists_schemas.append(schema)
    return None


def get_schemas(model):
    """Retrieve a schema class from the registry.

    :raises: marshmallow.exceptions.RegistryError if the class cannot be found
        or if there are multiple entries for the given class name.
    """
    try:
        classes = _registry[model]
    except KeyError:
        if isinstance(model, type):
            name = model.__name__
        else:
            name = model
        raise RegistryError('Class with name {0!r} was not found. You may need '
                            'to import the class.'.format(name))
    return classes


def auto_build_schema(class_):
    from ..schema import ModelSchema

    schema_name = str("SystemAuto{class_name}Schema".format(class_name=class_.__name__))

    try:
        schema_list = get_schemas(class_)
        for schema in schema_list:
            if not schema.__name__.startswith("SystemAuto"):
                # 默认返回用户创建的schema
                return schema
        return schema_list[0]
    except RegistryError:
        # 创建自动生成的schema对象
        create_ins = type(
            schema_name,
            (ModelSchema,),
            {
                str('__model__'): class_
            }
        )
        ins = get_schemas(class_)[0]
        assert create_ins == ins
        return create_ins
