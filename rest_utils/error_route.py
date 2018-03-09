#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Author  :   windpro
E-mail  :   windprog@gmail.com
Date    :   2018/2/7
Desc    :   
"""
import re
import sys
import logging
import traceback

from flask import current_app, request, jsonify, Flask
from sqlalchemy.exc import StatementError
from sqlalchemy.exc import IntegrityError, OperationalError, InvalidRequestError, StatementError
from sqlalchemy.exc import IntegrityError
from marshmallow.exceptions import ValidationError

from .exception import (
    RestException,
    DatabaseConnectionError,
    DatabaseExecutionError,
    ResourcesAlreadyExists,
    ForeignKeyConstraintFails,
    ResourcesConstraintNotNullable,
    ResourcesConstraintNotDefaultValue,
    StatementErrorException,
    RestAssertionError,
    Unknown,
    RequestHeadersAcceptNotSupport,
    IllegalRequestData,
)

JSON, HTML = range(2)
JSON_CONTENT_TYPES = set(['application/json'])
HTML_CONTENT_TYPES = set(['text/html', 'application/x-www-form-urlencoded'])
ALL_CONTENT_TYPES = set(['*/*'])
ACCEPTABLE_CONTENT_TYPES = (
        JSON_CONTENT_TYPES |
        HTML_CONTENT_TYPES |
        ALL_CONTENT_TYPES)
API_LIST = []
ERROR_API_LIST = []


def _get_acceptable_response_type():
    """Return the mimetype for this request."""
    if ('Accept' not in request.headers or
            request.headers['Accept'] in ALL_CONTENT_TYPES):
        return JSON
    acceptable_content_types = set(
        request.headers['ACCEPT'].strip().split(','))
    if acceptable_content_types & HTML_CONTENT_TYPES:
        return HTML
    elif acceptable_content_types & JSON_CONTENT_TYPES:
        return JSON
    else:
        # HTTP 406 Not Acceptable
        raise RequestHeadersAcceptNotSupport(dict(
            ACCEPT=request.headers['ACCEPT']
        ))


def register_err_route(app):
    assert isinstance(app, Flask)

    @app.errorhandler(ValidationError)
    def handle_common_ma_validation_error(error):
        return handle_invalid_api_usage_exception(IllegalRequestData(error.messages))

    @app.errorhandler(StatementError)
    def handle_common_db_statement_error(error):
        error_type, detail = database_error_handler(
            current_app.api_manager.get_engine().dialect.name.lower(), error
        )

        return handle_invalid_api_usage_exception(error_type(detail))

    @app.errorhandler(RestException)
    def handle_invalid_api_usage_exception(error):
        """
        Return a response with the appropriate status code, message, and content
        type when an ``RestException`` exception is raised.
        :param error:
        :return:
        """
        try:
            content_types = _get_acceptable_response_type()
        except RestException:
            content_types = JSON

        try:
            # if content_types == HTML:
            #     # 暂不支持HTML格式
            #     return error.abort()
            response = jsonify(error.to_dict())
            response.status_code = error.status
            return response
        except:
            # 这里的错误属于框架问题
            logging.error(traceback.format_exc())
            response = jsonify({
                "type": u"Unknown",
                "msg": u'未知错误',
                "detail": {},
            })
            response.status_code = 500
            return response

    @app.errorhandler(AssertionError)
    def handle_assertion_error(error):
        """
        Assertion Error
        :param error:
        :return:
        """
        return handle_invalid_api_usage_exception(RestAssertionError(dict(prompt=error.message)))

    @app.errorhandler(Exception)
    def default_error_handler(error):
        """
        Undefined Exception
        :param error:
        :return:
        """
        return handle_invalid_api_usage_exception(Unknown())


def __database_error_handler_mysql(source_exp):  # pragma: no cover
    """
    处理mysql数据库异常
    Mysql Server Error Codes and Messages:https://dev.mysql.com/doc/refman/5.5/en/error-messages-server.html
    :param source_exp:
    :return:
    """

    error_type = DatabaseExecutionError
    detail = {}

    def get_statement_table_name(_statement):
        if _statement.startswith('INSERT'):
            _table = _statement.split(' ')[2]
        else:
            _table = _statement.split(' ')[1]
        _table = _table.strip('`')
        return _table

    if type(source_exp) == StatementError and isinstance(getattr(source_exp, 'orig', None), InvalidRequestError):
        # Can't reconnect until invalid transaction is rolled back
        # Database State Error 一般为mysql连接过期,服务主动断开.时间为:wait_timeout
        error_type = DatabaseConnectionError
    elif isinstance(source_exp, IntegrityError):
        orig = source_exp.orig
        sql_type = orig.args[0]
        if sql_type == 1062:
            # Mysql unique key
            statement = source_exp.statement
            table = get_statement_table_name(statement)

            field = orig.args[1].split(' ')[-1].replace("'", "")
            value = source_exp.orig[1].split("'")[1]
            detail = dict(
                table=table, field=field, value=value
            )
            error_type = ResourcesAlreadyExists
        elif sql_type == 1452:
            # Mysql a foreign key constraint fails
            statement = source_exp.statement
            table = get_statement_table_name(statement)
            detail = dict(
                table=table
            )
            error_type = ForeignKeyConstraintFails
    elif isinstance(source_exp, OperationalError):
        sql_type = source_exp.orig.args[0]
        if sql_type == 1048:
            table = get_statement_table_name(source_exp.statement)
            field = source_exp.orig[1].split("'")[1]
            detail = dict(
                table=table, field=field
            )
            error_type = ResourcesConstraintNotNullable
        elif sql_type == 1364:
            table = get_statement_table_name(source_exp.statement)
            field = source_exp.orig[1].split("'")[1]
            detail = dict(
                table=table, field=field
            )
            error_type = ResourcesConstraintNotDefaultValue
        elif sql_type == 2006:
            # MySQL server has gone away
            # Database State Error 一般为mysql连接过期,服务主动断开.时间为:wait_timeout
            error_type = DatabaseConnectionError
    return error_type, detail


def __database_error_handler_sqlite(source_exp):
    """
    处理sqlite数据库异常
    :param source_exp:
    :return:
    """

    error_type = DatabaseExecutionError
    detail = {}
    if isinstance(source_exp, IntegrityError):
        orig = source_exp.orig
        sql_type = orig.args[0]
        if sql_type.startswith('UNIQUE constraint failed:'):
            # Sqlite unique key
            table, field = sql_type.split(':')[1].strip().split('.')
            statement = source_exp.statement
            p = re.compile('.*?\((.*?)\).*?')
            all_fields = [item.strip(' ').strip('"') for item in p.match(statement).groups()[0].split(',')]
            value = source_exp.params[all_fields.index(field)]
            detail = dict(
                table=table, field=field, value=value
            )
            error_type = ResourcesAlreadyExists
        elif sql_type.startswith('NOT NULL constraint failed:'):
            # Sqlite not null
            table, field = sql_type.split(':')[1].strip().split('.')
            detail = dict(
                table=table, field=field
            )
            error_type = ResourcesConstraintNotNullable
    return error_type, detail


def database_error_handler(db_type, source_exp):
    """
    处理数据库异常
    :param db_type: 数据库类型
    :param source_exp: 异常对象
    :return:
    """
    # 默认类型
    error_type = StatementErrorException
    try:
        if db_type == 'sqlite':
            return __database_error_handler_sqlite(source_exp)
        elif db_type == 'mysql':
            return __database_error_handler_mysql(source_exp)
    except:
        pass
    return error_type, {}
