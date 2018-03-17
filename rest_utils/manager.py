#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Author  :   windpro
E-mail  :   windprog@gmail.com
Date    :   17/12/15
Desc    :   
"""
import functools
import inspect as sys_inspect
from flask import Flask, Blueprint, jsonify, g, request, Response, current_app, _app_ctx_stack
from types import ModuleType

from marshmallow.compat import iteritems, itervalues
from marshmallow.exceptions import ValidationError
from sqlalchemy import inspect, orm
from sqlalchemy.util import IdentitySet
from sqlalchemy.orm import object_session
from sqlalchemy.orm import relationship, backref
from flask.json import _json
from flask.json import JSONEncoder
from sqlalchemy.engine import reflection
from sqlalchemy.schema import Table
from sqlalchemy.ext.automap import automap_base

from .utils import jsonres, get_session, get_resource_data
from .sa_util import get_instance, get_list_attr_query, get_tablename
from .decorators import no_cache
from .error_route import register_err_route
from .ma.model_registry import get_schemas
from .exception import (
    ResourceNotFound,
    AccessDenied,
    ResourceRelationNotExists,
    IllegalRequestData,
)
from .utils import (
    add_padding_callback,
    do_padding_callback,
    is_sa_mapped,
    get_api_manager,
    get_info_args,
    get_page_args,
)
from .schema import ModelSchema
from .ma.model_registry import auto_build_schema

#: The set of methods which are allowed by default when creating an API
ALL_METHODS = frozenset(('GET', "POST", "PUT", "DELETE"))
READONLY_METHODS = frozenset(('GET',))
UPDATE_METHODS = frozenset(('PUT', 'PATCH'))

NO_CONTENT = 204


def cls_primary_key(model):
    """
    Return the name of the table's primary key
    获取第一个主键
    :rtype: string
    """
    return model.__table__.primary_key.columns.values()[0].name


@no_cache
def no_content_response(code=NO_CONTENT):
    """Return the appropriate *Response* with status code *204*, signaling a
    completed action which does not require data in the response body

    :rtype: :class:`flask.Response`

    """
    response = Response()
    response.status_code = code
    return response


def _get_schema_endpoint(schema):
    """
    返回可能的endpoint列表
    :param schema:
    :return:
    """
    tablename = get_tablename(schema.opts.model)
    if not schema.opts.endpoint:
        # 默认使用表名
        return tablename,
    else:
        # 自定义名称
        return schema.opts.endpoint, tablename


def get_schema_endpoint(schema):
    """
    返回绑定的路由的endpoint
    :param schema:
    :return:
    """
    return _get_schema_endpoint(schema)[0]


class DynamicJSONEncoder(_json.JSONEncoder):
    """ JSON encoder for custom classes:
        Uses __json__() method if available to prepare the object.
        Especially useful for SQLAlchemy models
    """
    from decimal import Decimal

    def default(self, o):
        # Custom JSON-encodeable objects
        if hasattr(o, '__json__'):
            return o.__json__()

        elif isinstance(o, self.Decimal):
            return str(o)

        # Default
        return super(DynamicJSONEncoder, self).default(o)


def schema_dump_one(schema, resource, expand=0, **schema_kwargs):
    schema_ins = schema(**schema_kwargs)
    data, errors = schema_ins.dump(resource, expand=expand)
    if errors:
        raise ValidationError(errors, data=data)
    return data


def schema_load(schema, data, many=False, **schema_kwargs):
    schema_ins = schema(**schema_kwargs)
    ins, errors = schema_ins.load(data, many=many)
    if errors:
        raise ValidationError(errors, data=ins)
    return ins


def get_related_kwargs():
    info_args = get_info_args()
    related_kwargs = {}

    register_schemas = {}
    if info_args.fields or info_args.except_:
        for schema in get_api_manager().register_schemas:
            for endpoint in _get_schema_endpoint(schema):
                register_schemas.setdefault(endpoint, []).append(schema)

    # 指定类型返回的字段
    for one_coll_name, fields in iteritems(info_args.fields):
        schemas = register_schemas.get(one_coll_name, [])
        for schema in schemas:
            related_kwargs.setdefault(schema, {})["only"] = [
                field for field in fields
                if field in schema._declared_fields
            ]

    # 排除类型返回的字段
    for one_coll_name, fields in iteritems(info_args.except_):
        schemas = register_schemas.get(one_coll_name, [])
        for schema in schemas:
            related_kwargs.setdefault(schema, {})["exclude"] = [
                field for field in fields
                if field in schema._declared_fields
            ]
    return related_kwargs


class RouteApiView(object):
    def __init__(self, manager, schema):
        assert isinstance(manager, APIManager)
        self.manager = manager
        self.schema = schema
        self.model = model = schema.opts.model
        self.table_name = get_tablename(model)

        blueprint_name = "_".join([name for name in [
            self.table_name,
            "api"
        ] if name])
        self.blueprint = Blueprint(blueprint_name, __name__)
        self.blueprint.view = self
        self.endpont = get_schema_endpoint(schema)
        self.register_route()

    def register_route(self):
        # 路由注册
        current_methods = set(self.schema.opts.methods)
        # "PATCH" 和 "PUT" 含义一样
        if current_methods & UPDATE_METHODS:
            current_methods = current_methods - UPDATE_METHODS
            current_methods.add("PUT")
        for method in ALL_METHODS:
            if method in current_methods:
                self.register_uri(method)
            else:
                self.register_uri(method, lambda o, *args: o.handle_unmatchable)

    def register_default(self):
        # TODO 不再使用
        # 注册非法路径
        self.blueprint.add_url_rule(
            "/<path:invalid_path>",
            methods=(ALL_METHODS | UPDATE_METHODS),
            view_func=self.handle_unmatchable
        )

    def handle_unmatchable(self, *args, **kwargs):
        """
        规则以外结果
        :param args:
        :param kwargs:
        :return:
        """
        raise AccessDenied

    def _key_field_filter(self, key):
        return [getattr(self.model, key) == value for key, value in self._key_field_cond(key).items()]

    def _key_field_cond(self, key):
        key_field = self.schema.opts.key_field
        if key.startswith(self.manager.key_field_prefix) and key_field:
            value = key[len(self.manager.key_field_prefix):]
            return {
                key_field: value
            }
        else:
            attr = cls_primary_key(self.model)
            column = getattr(self.model, attr)
            try:
                value = column.type.python_type(key)
            except:
                raise ResourceNotFound(dict(
                    endpoint=self.endpont, key=key
                ))
            return {
                attr: value
            }

    def _get_resource(self, key):
        session = get_session()
        return session.query(self.model).filter_by(**self._key_field_cond(key)).first()

    @staticmethod
    def res(data, status_code=200):
        if isinstance(data, (list, tuple)):
            res = jsonres(data)
        else:
            res = jsonify(data)
        res.status_code = status_code
        return res

    def register_uri(self, http_method, route_get=None):
        """
        注册路由
        :param endpoint:
        :param http_method:
        :param route_get: 获取路由handler
        :return:
        """
        if route_get is None:
            route_get = getattr
        http_method = http_method.lower()
        if http_method == "put":
            # 同时注册：PUT PATCH
            ms = UPDATE_METHODS
        else:
            ms = (http_method.upper(),)

        cls_attr = route_get(self, "%s_%s" % (http_method, "cls"), None)
        if cls_attr:
            self.blueprint.add_url_rule(
                "", methods=ms,
                view_func=cls_attr
            )
            self.blueprint.add_url_rule(
                "/", methods=ms,
                view_func=cls_attr
            )

        one_attr = route_get(self, "%s_%s" % (http_method, "one"), None)
        if one_attr:
            self.blueprint.add_url_rule(
                "/<key>", methods=ms,
                view_func=one_attr
            )

        # 注册子资源链接
        sub_attr = route_get(self, "%s_%s" % (http_method, "attr"), None)
        for attr in inspect(self.model).mapper.relationships.keys():
            # @functools.wraps(func)
            # def wrapper(key):
            #     return func(key=key, attribute=attr)
            if not sub_attr:
                continue
            attr_func = functools.partial(sub_attr, attribute=attr)
            view_func = functools.update_wrapper(attr_func, sub_attr)  # 添加名称信息
            endpoint = "%s_%s" % (attr, view_func.__name__)
            if http_method not in endpoint:
                endpoint = "%s_%s" % (http_method, endpoint)
            self.blueprint.add_url_rule(
                "/<key>/{attr}".format(
                    attr=attr,
                ), methods=ms,
                view_func=view_func,
                endpoint=endpoint
            )

    @classmethod
    def dump_one(cls, schema, resource):
        """
        使用flask request 参数展开资源
        :param schema:
        :param resource:
        :return:
        """
        info_args = get_info_args()

        related_kwargs = get_api_manager().related_kwargs
        current_kwargs = related_kwargs.get(schema, {})

        return schema_dump_one(
            session=get_session(),
            schema=schema,
            resource=resource,
            expand=info_args.expand,
            related_kwargs=related_kwargs,
            **current_kwargs
        )

    def get_cls(self):
        """
        查询列表
        :return:
        """
        resources, total = get_page_args().get(
            self.model,
            ext_filters=self.schema.opts.filters(),
        )
        result_list = []
        for resource in resources:
            one_dump = self.dump_one(self.schema, resource)
            result_list.append(one_dump)

        payload = dict(
            total=total,
        )
        payload[self.manager.top_level_json_name] = result_list
        return self.res(payload, 200)

    def post_cls(self):
        """
        创建新对象
        :return:
        """
        data = get_resource_data(request)
        # 支持批量
        if isinstance(data, (list, tuple)):
            many = True
        else:
            many = False
        session = get_session()
        ins = schema_load(
            self.schema, data,
            many=many,
            session=get_session(),
            check_existence=False,
        )
        if many:
            session.add_all(ins)
        else:
            session.add(ins)
        session.commit()
        if many:
            return self.res([self.dump_one(
                self.schema, item
            ) for item in ins], 201)
        else:
            return self.res(self.dump_one(
                self.schema, ins
            ), 201)

    def put_cls(self):
        """
        查询对象，不存在则创建
        :return:
        """
        data = get_resource_data(request)
        # 支持批量
        if isinstance(data, (list, tuple)):
            many = True
        else:
            many = False
        session = get_session()
        ins = schema_load(
            self.schema, data,
            many=many,
            session=session,
            check_existence=True,
        )
        status_code = 200
        if many:
            ins_list = ins
        else:
            ins_list = [ins]

        create_count = 0
        for obj in ins_list:
            if not object_session(obj):
                # 创建的
                session.add(obj)
                create_count += 1
            else:
                session.merge(obj)
        if create_count == len(ins_list):
            # 纯创建的情况，status code为201
            status_code = 201
        session.commit()
        if many:
            return self.res([self.dump_one(
                self.schema, item
            ) for item in ins], status_code)
        else:
            return self.res(self.dump_one(
                self.schema, ins
            ), status_code)

    def delete_cls(self):
        raw_data = get_resource_data(request)
        # 支持批量
        if isinstance(raw_data, (list, tuple)):
            data_list = raw_data
        else:
            data_list = raw_data
        session = get_session()
        for data in data_list:
            instance = get_instance(session, self.model, data)
            if not instance:
                raise ResourceNotFound({
                    "endpoint": self.endpont,
                    "data": data,
                })
            instance = self.schema.opts.delete(instance)
            add_padding_callback(self.schema.opts.deleted, instance)
            session.delete(instance)
        session.commit()
        return no_content_response()

    def _get_keyfield_instance(self, key):
        resource = self._get_resource(key)
        if not resource:
            raise ResourceNotFound(dict(
                endpoint=self.endpont, key=key
            ))
        return resource

    def get_one(self, key):
        """
        获取单个资源
        :param key:
        :return:
        """
        return self.res(self.dump_one(
            self.schema, self._get_keyfield_instance(key))
        )

    def post_one(self, key):
        """
        创建单个资源
        :param key:
        :return:
        """
        data = dict(get_resource_data(request))
        key_field_cond = self._key_field_cond(key)
        data.update(key_field_cond)
        session = get_session()
        ins = schema_load(
            self.schema, data,
            many=False,
            session=session,
            check_existence=False,
        )
        session.add(ins)
        session.commit()
        return self.res(self.dump_one(
            self.schema, ins
        ), 201)

    def put_one(self, key):
        """
        修改单个资源
        :param key:
        :return:
        """
        data = dict(get_resource_data(request))
        key_field_cond = self._key_field_cond(key)
        data.update(key_field_cond)
        session = get_session()
        # 使用key_field查找
        old_ins = session.query(self.schema.opts.model).filter_by(**key_field_cond).first()
        ins = schema_load(
            self.schema, data,
            instance=old_ins,
            many=False,
            session=session,
            check_existence=True,
        )
        if not object_session(ins):
            session.add(ins)
            status_code = 201
        else:
            session.merge(ins)
            status_code = 200
        session.commit()
        return self.res(self.dump_one(
            self.schema, ins
        ), status_code)

    def delete_one(self, key):
        resource = self._get_keyfield_instance(key)
        session = get_session()
        add_padding_callback(self.schema.opts.deleted, resource)
        session.delete(resource)
        session.commit()
        return no_content_response()

    def _get_attr_info(self, key, attribute):
        resource = self._get_keyfield_instance(key)
        relationships = inspect(resource).mapper.relationships
        if attribute not in relationships or attribute not in self.schema._declared_fields:
            raise ResourceRelationNotExists
        sub_schema = self.schema._declared_fields[attribute].schema_class
        return resource, relationships[attribute], sub_schema

    def get_attr(self, key, attribute):
        resource, rela_prop, sub_schema = self._get_attr_info(key=key, attribute=attribute)
        if rela_prop.uselist:
            filter_obj = get_list_attr_query(resource, attribute)
            resources, total = get_page_args().get(
                sub_schema.opts.model,
                filter_object=filter_obj,
                ext_filters=sub_schema.opts.filters(),
            )
            result_list = []
            for resource in resources:
                one_dump = self.dump_one(sub_schema, resource)
                result_list.append(one_dump)

            payload = dict(
                total=total,
            )
            payload[self.manager.top_level_json_name] = result_list
            return self.res(payload)
        else:
            return self.res(self.dump_one(sub_schema, getattr(resource, attribute)))

    def post_attr(self, key, attribute):
        """
        仅新增关系
        :param key:
        :param attribute:
        :return:
        """
        return self._modify_attr(key=key, attribute=attribute, replace=False)

    def _modify_attr(self, key, attribute, replace=True):
        """
        关系增删改不会调用主资源的对应回调方法
        :param key:
        :param attribute:
        :param replace:
        :return:
        """
        data = get_resource_data(request)
        resource, rela_prop, sub_schema = self._get_attr_info(key=key, attribute=attribute)
        if rela_prop.uselist:
            # 支持批量
            unload_data = data if isinstance(data, (list, tuple)) else [data]
        else:
            if isinstance(data, (list, tuple)):
                raise IllegalRequestData({
                    u"msg": u"该类型资源无法批量操作",
                    u"data": data
                })
            unload_data = data

        session = get_session()
        ins = schema_load(
            sub_schema, unload_data,
            many=rela_prop.uselist,
            session=session,
            check_existence=True,
        )

        if rela_prop.uselist:
            sub_resource = getattr(resource, attribute)
            if replace:
                for obj in ins:
                    sub_resource.append(obj)
                self.schema.opts.update(resource, {
                    attribute: getattr(resource, attribute)
                })
            else:
                self.schema.opts.update(resource, {
                    attribute: ins
                })
        else:
            self.schema.opts.update(resource, {
                attribute: ins
            })

        session.merge(resource)
        # 对关系的操作相当于对主资源的修改
        add_padding_callback(self.schema.opts.updated, resource)  # commit数据库之后调用
        session.commit()

        if rela_prop.uselist:
            return self.res([self.dump_one(
                sub_schema, item
            ) for item in ins])
        else:
            return self.res(self.dump_one(
                sub_schema, ins
            ))

    def put_attr(self, key, attribute):
        """
        替换关系
        :param key:
        :param attribute:
        :return:
        """
        return self._modify_attr(key=key, attribute=attribute, replace=True)

    def delete_attr(self, key, attribute):
        session = get_session()
        resource, rela_prop, sub_schema = self._get_attr_info(key=key, attribute=attribute)
        if rela_prop.uselist:
            data = get_resource_data(request)
            sub_resource = getattr(resource, attribute)
            # 支持批量
            unload_data = data if isinstance(data, (list, tuple)) else [data]
            for one in unload_data:
                del_res = get_instance(session, sub_schema.opts.model, one)
                # if sub_res not in sub_resource:
                #     # TODO 删除大量资源中的一个可能会出问题
                #     # 无法找到需要删除的资源
                #     # 暂不需要这个判定条件，改为测试删除空资源是否有问题
                #     raise ResourceNotFound(dict(
                #         key=key,
                #         attribute=attribute,
                #         child=one
                #     ))
                if not del_res:
                    raise ResourceNotFound(dict(
                        endpoint=get_schema_endpoint(sub_schema),
                        data=one,
                    ))
                elif del_res not in sub_resource:
                    raise ResourceRelationNotExists(dict(
                        endpoint=get_schema_endpoint(sub_schema),
                        data=one,
                    ))
                sub_resource.remove(del_res)
        else:
            setattr(resource, attribute, None)
        session.commit()
        return no_content_response()


class APIManager(object):
    """
    管理api
    """
    JSON_ENCODER = DynamicJSONEncoder

    def __init__(self, app, db=None, engine=None, prefix="/api", top_level_json_name='items'):
        """

        :param app:
        :param db: flask_sqlalchemy.SQLAlchemy instance.
        :param engine: example: sqlalchemy.create_engine("sqlite://")
        :param prefix:
        :param top_level_json_name:
        """
        assert isinstance(app, Flask)
        self.app = app
        self.app.api_manager = self
        self.use_flask_sqlalchemy = False
        self.use_pure_sqlalchemy = False
        if db:
            self.use_flask_sqlalchemy = True
            self.db = db
            # example: db = flask_sqlalchemy.SQLAlchemy(app)
            try:
                from flask_sqlalchemy import SQLAlchemy
            except:
                raise ImportError("please pip install flask_sqlalchemy")

            assert isinstance(db, SQLAlchemy)
            self.get_session = db.session
            self.get_engine = lambda: db.engine
        elif engine:
            self.use_pure_sqlalchemy = True
            # example: engine = sqlalchemy.create_engine("sqlite://")
            from sqlalchemy.engine.base import Engine
            from sqlalchemy.orm import sessionmaker
            from .libs.flask_sqlalchemy_session import flask_scoped_session

            assert isinstance(engine, Engine)
            self._scoped_session = flask_scoped_session(sessionmaker(
                autocommit=False, autoflush=True, bind=engine
            ), app)
            self.get_session = lambda: self._scoped_session
            self.get_engine = lambda: engine
        else:
            raise ValueError("Must give db or engine")
        self.prefix = prefix
        self.key_field_prefix = "@"
        self.top_level_json_name = top_level_json_name

        # 注册路由的schemas
        self.schemas = {}

        register_err_route(app)

        if app.json_encoder == JSONEncoder:
            app.json_encoder = self.JSON_ENCODER

        @app.after_request
        def do_callback(response, *args, **kwargs):
            if response.status_code < 300:
                # 正常的请求，执行回调方法
                do_padding_callback()
            return response

    @property
    def register_schemas(self):
        """
        所有存在的model schemas
        :return:
        """
        from .ma.model_registry import _registry
        cache_name = "_register_schemas_cache"
        if hasattr(g, cache_name):
            return getattr(g, cache_name)

        all_schema = set()
        for sms in itervalues(_registry):
            all_schema.update([sm for sm in sms if getattr(sm.opts, "model", None)])
        setattr(g, cache_name, all_schema)
        return all_schema

    @property
    def related_kwargs(self):
        """
        请求参数 生成的related_kwargs
        :return:
        """
        cache_name = "_related_kwargs_cache"
        if hasattr(g, cache_name):
            return getattr(g, cache_name)
        related_kw = get_related_kwargs()
        setattr(g, cache_name, related_kw)
        return related_kw

    def get_cls(self, collection_name):
        self.schemas.get(collection_name)

    def add(self, schema, **kwargs):
        """
        添加api
        :param schema: "ModelSchema" or "sqlalchemy model" instance
        :param methods: 注册的HTTP方法。有：'GET': 查询, "POST": 新增, "PUT": 修改, "DELETE": 删除
        :param include_fk: 展示外键. 默认:True
        :param key_field: 查找字段。如：/users/@windpro
        :param endpoint: 资源名称。默认为tablename
        :param match_fields: 搜索的字段。默认：[]. 如:["name"]
        :param filters: 查询资源时使用的filters。如def get_users(): return [Users.name=="windpro"]
        :param create: 创建实例回调方法。(model, data)
        :param update: 修改实例回调方法。(instance, data)
        :param delete: 删除实例回调方法。(instance)
        :param created: commit数据库之后的创建实例回调方法。(instance)
        :param updated: commit数据库之后的修改实例回调方法。(instance)
        :param deleted: commit数据库之后的删除实例回调方法。(instance)
        :param kwargs:
        :return:
        """
        if isinstance(schema, type) and issubclass(schema, ModelSchema):
            # schema
            schema = schema
            model = schema.opts.model
        elif is_sa_mapped(schema, log=True):
            # ORM模型
            model = schema
            schema = auto_build_schema(model)
        else:
            raise ValueError

        # 写入配置
        for attr, value in iteritems(kwargs):
            setattr(schema.opts, attr, value)

        view = RouteApiView(
            manager=self,
            schema=schema,
        )
        self.app.register_blueprint(view.blueprint, url_prefix="/".join([self.prefix, view.endpont]))

        # 记录schemas
        self.schemas[view.endpont] = schema
        return view

    def add_all(self, container):
        if isinstance(container, ModuleType):
            # obj is from module.
            cls_list = []
            for cls in vars(container).values():
                if sys_inspect.isclass(cls) and is_sa_mapped(cls):
                    cls_list.append(cls)
        elif isinstance(container, (list, tuple)):
            cls_list = container
        else:
            raise ValueError
        for cls in cls_list:
            self.add(cls, methods=ALL_METHODS)

    def auto_create(self, metadata=None, generate_pks=False):
        if self.use_flask_sqlalchemy:
            with self.app.app_context():
                if not metadata:
                    metadata = self.db.metadata
                metadata.reflect(bind=self.db.engine)
                auto_base = automap_base(metadata=metadata)
                auto_base.prepare()
                cls_list = auto_base.classes.values()
        elif self.use_pure_sqlalchemy:
            assert metadata, "pure SQLAlchemy must provide BaseModel.metadata"
            metadata.reflect(bind=self.get_engine())
            auto_base = automap_base(metadata=metadata)
            auto_base.prepare()
            cls_list = auto_base.classes.values()
        else:
            raise ValueError
        self.add_all(cls_list)
        return cls_list

    def register_admin(self, name='Admin', template_mode='bootstrap3', url="/admin", **kwargs):
        try:
            from flask_admin import Admin
            from flask_admin.contrib.sqla import ModelView
        except:
            raise ImportError("Please install flask_admin")
        self.admin = admin = Admin(self.app, name=name, template_mode=template_mode, url=url, **kwargs)
        for schema in itervalues(self.schemas):
            cls = schema.opts.model
            admin.add_view(ModelView(cls, self.get_session))
