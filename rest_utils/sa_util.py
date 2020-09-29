#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Author  :   windpro
E-mail  :   windprog@gmail.com
Date    :   17/11/14
Desc    :   
"""
from sqlalchemy import inspect
from flask import g, current_app
from sqlalchemy import inspect
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import object_session, object_mapper, properties
from sqlalchemy import inspect as sa_inspect
from .utils import get_session, get_class


def get_primary_keys(model):
    """Get primary key properties for a SQLAlchemy model.

    :param model: SQLAlchemy model class
    """
    mapper = model.__mapper__
    return [
        mapper.get_property_by_column(column)
        for column in mapper.primary_key
    ]


def get_unique_keys_list(model):
    table = model.__mapper__.tables[0]
    ret = []
    for constraint in table.constraints:
        if isinstance(constraint, UniqueConstraint):
            ret.append(constraint.columns)
    return ret


def get_instance(session, model, data):
    """Retrieve an existing record by primary key(s) or unique key(s)."""
    unique_list = [
        get_primary_keys(model)
    ]
    unique_list.extend(get_unique_keys_list(model))
    for props in unique_list:
        keys = set(prop.key for prop in props)
        cond = {
            key: data[key]
            for key in keys if key in data
        }
        if set(cond) == keys:
            # field all exists
            return session.query(model).filter_by(**cond).first()
    return None


def get_instance_by_cond(session, father_instance, father_attr, model, data):
    """Retrieve an existing record by primary key(s) or unique key(s)."""
    # m = m.data_bindings.parent.class_
    # m.data_bindings.expression.clauses[0].left.table == sa_inspect(m).tables[0]
    # query_condition.attr.parent_token.primaryjoin.clauses
    from sqlalchemy.sql.elements import BinaryExpression
    unique_list = [
        get_primary_keys(model)
    ]
    copy_data = dict(data)
    father_mapper = sa_inspect(father_instance).mapper
    father_table = father_mapper.tables[0]
    clauses = (
        [father_attr.expression]
        if isinstance(father_attr.expression, BinaryExpression) else
        father_attr.expression.clauses
    )
    for be in clauses:
        if be.left.table == father_table:
            father_val = getattr(father_instance, be.left.key)
            child_key = be.right.key
        elif be.right.table == father_table:
            father_val = getattr(father_instance, be.right.key)
            child_key = be.left.key
        else:
            # 多对多关系会捕获无效条件
            # father_attr.prop.direction: sqlalchemy.util.langhelpers.symbol
            continue
        copy_data[child_key] = father_val
    unique_list.extend(get_unique_keys_list(model))
    for props in unique_list:
        keys = set(prop.key for prop in props)
        cond = {
            key: copy_data[key]
            for key in keys if key in copy_data
        }
        if set(cond) == keys:
            # field all exists
            return session.query(model).filter_by(**cond).first()
    return None


def get_list_attr_query(resource, attr):
    """
    获取子资源的query,主资源不存在则自动session.add
    :param resource: 资源
    :param attr: 子资源
    :return:
    """
    relationships = inspect(resource).mapper.relationships
    # 确保是列表
    assert attr in relationships and relationships[attr].uselist
    ra = relationships[attr]
    if ra.lazy == 'dynamic':
        # dynamic support filter
        return getattr(resource, attr)
    else:
        # build relationship query
        # http://docs.sqlalchemy.org/en/latest/orm/join_conditions.html#building-query-enabled-properties
        obs = object_session(resource)
        if not obs:
            get_session().add(resource)
            obs = object_session(resource)
            assert obs
        sub_cls = get_class(ra)

        # 处理mapper property
        with_parent_args = [resource]
        obj_mapper = object_mapper(resource)
        sub_property = obj_mapper.get_property(attr)
        obj_query = obs.query(sub_cls)
        if isinstance(sub_property, properties.RelationshipProperty) \
                and sub_property.mapper is obj_query._mapper_zero():
            with_parent_args.append(sub_property)

        # 产生query
        ret = obj_query.with_parent(*with_parent_args)
        # 支持默认排序
        if ra.order_by:
            ret = ret.order_by(*ra.order_by)
        return ret


def migrate_skip(migrate, skip_list):
    """
    flask_migrate 跳过指定表
    :param migrate:
    :param skip_list:
    :return:
    """
    try:
        import flask_migrate
    except:
        raise ImportError("please pip install Flask-Migrate")

    @migrate.configure
    def configure_alembic(config):
        from alembic.autogenerate.compare import comparators

        @comparators.dispatch_for("schema")
        def _autogen_for_tables(autogen_context, upgrade_ops, schemas):
            # 处理跳过的表
            upgrade_ops.ops = [op for op in upgrade_ops.ops if op.table_name not in skip_list]

        return config


def get_prop_nullable(prop):
    nullable = True
    if prop.direction.name != "MANYTOMANY":
        for pair in prop.local_remote_pairs:
            if not pair[0].nullable:
                if prop.uselist is True:
                    nullable = False
                break
    return nullable


def get_tablename(model):
    mapper = inspect(model)
    if not getattr(mapper, "tables", None):
        return None
    return mapper.tables[0].name
