#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Author  :   windpro
E-mail  :   windprog@gmail.com
Date    :   17/11/14
Desc    :   
"""
from sqlalchemy import inspect
from sqlalchemy.orm import object_session, object_mapper, properties

from flask_sqlalchemy import Model, SQLAlchemy as FlaskSQLAlchemy
from flask import g, current_app


class SQLAlchemy(FlaskSQLAlchemy):
    """
    重新封装的sqlachemy，实现一些内部功能
    """
    def __init__(self, app=None, *args, **kwargs):
        super(SQLAlchemy, self).__init__(app, *args, **kwargs)
        if app:
            app.db = self


def get_session():
    """Return a database session"""
    session = getattr(g, '_session', None)
    if session is None:
        if not getattr(current_app, "db", None):
            raise Exception("Please use rest_utils.SQLAlchemy. example:"
                            "https://github.com/windprog/rest-utils/blob/master/example/demo_app.py#L10")
        session = g._session = current_app.db.session()
    return session


def add_session(resource):
    return get_session().add(resource)


def get_class(obj):
    """
    可以获取如下类型的class
    RelationshipProperty
    db.Model
    :param obj:
    :return:
    """
    from sqlalchemy.orm.relationships import RelationshipProperty

    if isinstance(obj, Model):
        return inspect(obj).class_
    if isinstance(obj, RelationshipProperty):
        return obj.mapper.class_
    return obj


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
            add_session(resource)
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
