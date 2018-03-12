#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Author  :   windpro
E-mail  :   windprog@gmail.com
Date    :   17/12/15
Desc    :
"""
"""Helper functions for unit tests."""
import os
import sys

PROJECT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_PATH not in sys.path:
    sys.path.append(PROJECT_PATH)
from datetime import date
from datetime import datetime
from datetime import time
from datetime import timedelta
from functools import wraps
import sys
import types
import uuid
import logging

from flask import Flask
from flask import json
import flask_sqlalchemy
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy import event
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import Session as SessionBase
from sqlalchemy.types import CHAR
from sqlalchemy.types import TypeDecorator
from unittest import TestCase

from rest_utils.manager import APIManager
from rest_utils.date import dt2dt_str, dt2date_str

logger = logging.getLogger(__name__)

dumps = json.dumps
loads = json.loads

#: Boolean representing whether this code is being executed on Python 2.
IS_PYTHON2 = (sys.version_info[0] == 2)

#: Tuple of objects representing types.
CLASS_TYPES = (types.TypeType, types.ClassType) if IS_PYTHON2 else (type,)

JSONAPI_MIMETYPE = "application/json"

SQLALCHEMY_ECHO = False


class BetterJSONEncoder(json.JSONEncoder):
    """Extends the default JSON encoder to serialize objects from the
    :mod:`datetime` module.
    """

    def default(self, obj):
        if isinstance(obj, (datetime, time)):
            return dt2dt_str(obj)
        elif isinstance(obj, date):
            return dt2date_str(obj)
        if isinstance(obj, timedelta):
            return int(obj.days * 86400 + obj.seconds)
        return super(BetterJSONEncoder, self).default(obj)


def force_content_type_jsonapi(test_client):
    """Ensures that all requests made by the specified Flask test client
    that include data have the correct :http:header:`Content-Type`
    header.
    """

    def set_content_type(func):
        """Returns a decorated version of ``func``, as described in the
        wrapper defined below.
        """

        @wraps(func)
        def new_func(*args, **kw):
            """Sets the correct :http:header:`Content-Type` headers
            before executing ``func(*args, **kw)``.
            """
            # if 'content_type' not in kw:
            #     kw['content_type'] = CONTENT_TYPE
            if 'headers' not in kw:
                kw['headers'] = dict()
            headers = kw['headers']
            if 'content_type' not in kw and 'Content-Type' not in headers:
                kw['content_type'] = JSONAPI_MIMETYPE
            return func(*args, **kw)

        return new_func

    # Decorate the appropriate test client request methods.
    test_client.patch = set_content_type(test_client.patch)
    test_client.post = set_content_type(test_client.post)


class FlaskTestBase(TestCase):
    """Base class for tests which use a Flask application.

    The Flask test client can be accessed at ``self.app``. The Flask
    application itself is accessible at ``self.flaskapp``.

    """

    def setUp(self):
        """Creates the Flask application and the APIManager."""
        # create the Flask application
        app = Flask(__name__)
        app.config['DEBUG'] = True
        app.config['TESTING'] = True
        # The SERVER_NAME is required by `manager.url_for()` in order to
        # construct absolute URLs.
        app.config['SERVER_NAME'] = 'localhost:5000'
        app.logger.disabled = True
        self.flaskapp = app

        # create the test client
        self.req = app.test_client()

        force_content_type_jsonapi(self.req)

    def json_req(self, method, url, data=None, json=None, **kwargs):
        headers = kwargs.pop("headers", {})
        if json:
            headers.setdefault("Content-Type", 'application/json')
        data = dumps(json)
        res = getattr(self.req, method)(url, data=data, headers=headers, **kwargs)
        res.json = lambda: loads(res.data)
        return res

    def get(self, url, params=None, **kwargs):
        if "query_string" in kwargs:
            params = kwargs.pop("query_string")
        res = self.req.get(url, query_string=params, **kwargs)
        res.json = lambda: loads(res.data)
        return res

    def post(self, url, data=None, json=None, **kwargs):
        return self.json_req(method="post", url=url, data=data, json=json, **kwargs)

    def put(self, url, data=None, json=None, **kwargs):
        return self.json_req(method="put", url=url, data=data, json=json, **kwargs)

    def patch(self, url, data=None, json=None, **kwargs):
        return self.json_req(method="patch", url=url, data=data, json=json, **kwargs)

    def delete(self, url, data=None, json=None, **kwargs):
        return self.json_req(method="delete", url=url, data=data, json=json, **kwargs)

    @staticmethod
    def assertRestException(response, type_):
        assert response.status_code >= 300
        error_type = loads(response.data)["type"]
        assert error_type == unicode(type_), error_type

    def assertListItemEqual(self, list1, list2, msg=None):
        assert len(list1) == len(list2)
        for item in list1:
            assert item in list2, msg

    @classmethod
    def check_almost_like_list_dict(cls, dict1, dict2):
        if not (len(set(dict1.keys()) - set(dict2.keys())) <= 1):
            return False
        if not (len(set(dict2.keys()) - set(dict1.keys())) <= 1):
            return False
        for key1, value1 in dict1.items():
            if key1 in dict2:
                if dict2[key1] != dict1[key1]:
                    return False
        return True

    @classmethod
    def check_json_like(cls, obj1, obj2, exclude_keys=[]):
        if isinstance(obj1, basestring) and isinstance(obj2, basestring):
            # 忽略unicode影响
            pass
        elif type(obj1) != type(obj2):
            return False
        if isinstance(obj1, (tuple, list)):
            if len(obj1) != len(obj2):
                return False
            for index in xrange(len(obj1)):
                if not cls.check_json_like(
                        obj1[index], obj2[index],
                        exclude_keys=exclude_keys
                ):
                    return False
            return True
        elif isinstance(obj1, dict):
            c_obj1 = dict(obj1)
            c_obj2 = dict(obj2)
            for key in exclude_keys:
                c_obj1.pop(key, None)
                c_obj2.pop(key, None)
            if c_obj1.keys() != c_obj2.keys():
                # 字段必须相同
                return False
            for key in c_obj1.keys():
                if not cls.check_json_like(
                        c_obj1.get(key), c_obj2.get(key),
                        exclude_keys=exclude_keys):
                    return False
            return True
        else:
            return obj1 == obj2

    @classmethod
    def assert_almost_like_list(cls, list1, list2):
        assert len(list1) == len(list2)
        if len(list1) == 0:
            return

        for item1 in list1:
            for item2 in list2:
                if cls.check_almost_like_list_dict(item1, item2):
                    break
            else:
                logger.error('%s not match in %s' % (repr(item1), repr(list2)))
                assert False


class FlaskSQLAlchemyTestBase(FlaskTestBase):
    """Base class for tests that use Flask-SQLAlchemy (instead of plain
    old SQLAlchemy).

    If Flask-SQLAlchemy is not installed, the :meth:`.setUp` method will
    raise :exc:`nose.SkipTest`, so that each test method will be
    skipped individually.

    """
    DB_URI = 'sqlite://'

    def setUp(self):
        super(FlaskSQLAlchemyTestBase, self).setUp()
        self.flaskapp.config['SQLALCHEMY_DATABASE_URI'] = self.DB_URI
        self.flaskapp.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        self.flaskapp.config['SQLALCHEMY_ECHO'] = SQLALCHEMY_ECHO
        self.db = SQLAlchemy(self.flaskapp)
        self.session = self.db.session

    def tearDown(self):
        """Drops all tables and unregisters Flask-SQLAlchemy session
        signals.

        """
        self.db.drop_all()


class MemoryManagerTestBase(FlaskTestBase):
    """Base class for tests that use a SQLAlchemy database and an
    :class:`~rest_utils.APIManager`.

    Nearly all test classes should subclass this class. Since we strive
    to make rest-utils compliant with plain old SQLAlchemy first,
    the default database abstraction layer used by tests in this class
    will be SQLAlchemy. Test classes requiring Flask-SQLAlchemy must
    instantiate their own :class:`~rest_utils.APIManager`.

    The :class:`~rest_utils.APIManager` instance for use in
    tests is accessible at ``self.manager``.

    """
    DB_URI = 'sqlite://'

    def setUp(self):
        """Initializes an instance of
        :class:`~rest_utils.APIManager` with a SQLAlchemy
        session.

        """
        super(MemoryManagerTestBase, self).setUp()
        self.engine = create_engine(self.DB_URI, convert_unicode=True)
        self.TestCaseSession = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )
        self.session = scoped_session(self.TestCaseSession)
        self.Base = declarative_base()
        self.Base.metadata.bind = self.engine
        self.manager = APIManager(self.flaskapp, engine=self.engine, prefix="")

    # HACK If we don't include this, there seems to be an issue with the
    # globally known APIManager objects not being cleared after every test.
    def tearDown(self):
        """Clear the :class:`~rest_utils.APIManager` objects
        known by the global helper functions :data:`model_for`,
        :data:`url_for`, etc.

        """
        self.session.remove()
        self.Base.metadata.drop_all()


class SqliteManagerTestBase(FlaskTestBase):
    DB_PATH = os.path.abspath(os.path.join(
        os.path.dirname(__file__),
        "data",
        "Chinook_Sqlite_AutoIncrementPKs.sqlite"
    ))
    assert os.path.isfile(DB_PATH)
    DB_URI = 'sqlite:////' + DB_PATH

    from chinook_models import (
        Album, Artist, Customer, Employee,
        Genre, Invoice, InvoiceLine, MediaType,
        Playlist, Track, Base,
    )

    def setUp(self):
        """Initializes an instance
        """
        super(SqliteManagerTestBase, self).setUp()
        self.engine = create_engine(self.DB_URI, convert_unicode=True, echo=SQLALCHEMY_ECHO)
        self.TestCaseSession = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )
        self.session = scoped_session(self.TestCaseSession)
        self.manager = APIManager(self.flaskapp, engine=self.engine, prefix="")
        self.Base.metadata.bind = self.engine

    def tearDown(self):
        self.session.remove()


class ChinookMemoryManagerTestBase(FlaskTestBase):
    DB_URI = 'sqlite://'
    from chinook_models_flask_sa import (
        Album, Artist, Customer, Employee,
        Genre, Invoice, InvoiceLine, MediaType,
        Playlist, Track, db,
    )

    def setUp(self):
        """Initializes an instance
        """
        super(ChinookMemoryManagerTestBase, self).setUp()
        self.flaskapp.config['SQLALCHEMY_ECHO'] = SQLALCHEMY_ECHO
        self.flaskapp.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        self.db.init_app(self.flaskapp)
        self.manager = APIManager(self.flaskapp, db=self.db, prefix="")
        self.session = self.db.session
        with self.flaskapp.app_context():
            self.db.create_all()

    def tearDown(self):
        """Clear the :class:`~rest_utils.APIManager` objects
        known by the global helper functions :data:`model_for`,
        :data:`url_for`, etc.

        """
        with self.flaskapp.app_context():
            self.db.drop_all()
