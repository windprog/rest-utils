#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Author  :   windpro
E-mail  :   windprog@gmail.com
Date    :   17/11/8
Desc    :   
"""
import time
import six
import sys
import multiprocessing
import logging
import re

from gunicorn.app.base import Application
from flask_script import Command, Option
from flask import Flask

TRACE_ID = "Trace-Id"
LOG_FORMAT = '[{trace_id}] "{method} {fullpath} HTTP/1.1" {status} {length} {res_content_type} {ip} {delay}'
LOG_FIELDS = re.findall("{(\w+)}", LOG_FORMAT)


def setup_info_log():
    logger_ = logging.getLogger(__name__)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt='%(asctime)s %(levelname)-7s %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    )
    logger_.addHandler(handler)
    logger_.propagate = 0
    logger_.setLevel(logging.INFO)
    return logger_


logger = setup_info_log()


def get_process_num(power=1):
    return multiprocessing.cpu_count() * power or 1


def parse_arg():
    argv = sys.argv
    args = []
    kwargs = {}
    for arg in argv[1:]:
        if '=' in arg:
            key, value = arg.split('=', 2)
            kwargs[key] = value
        else:
            args.append(arg)
    return args, kwargs


def get_options(*args, **kwargs):
    bind = kwargs.get('BIND', "0.0.0.0")
    port = kwargs.get('PORT', 4488)
    return {
        'worker_class': 'gthread',
        'workers': kwargs.get('PROCESS', get_process_num()),
        'bind': "%s:%s" % (bind, port),
        'daemon': False,
        'timeout': 60,
        'sql_debug': kwargs.get('SQL_DEBUG', False)
    }


def after_request_log(res):
    from flask import request

    full_path = request.full_path
    if full_path.endswith("?"):
        full_path = full_path[:-1]
    logger.info('"{method} {fullpath} HTTP/1.1" {status_code} {res_content_type} -'.format(
        method=request.method,
        fullpath=full_path,
        status_code=res.status_code,
        res_content_type=res.headers.get("Content-Type")
    ))
    return res


class LogRequestMiddleware(object):
    """Simple log request info middleware.  Wraps a WSGI application and profiles
    a request.
    """

    def __init__(self, app):
        self._app = app

    def __call__(self, environ, start_response):
        response_body = []
        logger_kw = {}

        def catching_start_response(status, headers, exc_info=None):
            logger_kw["status"] = status.split()[0]
            for key, value in headers:
                if key == 'Content-Length':
                    logger_kw["length"] = str(value)
                elif key == 'Content-Type':
                    logger_kw["res_content_type"] = value
                elif key == "X-Forwarded-For":
                    if "forwarded_ip" not in logger_kw:
                        logger_kw["forwarded_ip"] = value.split(',')[0].strip()
                elif key == TRACE_ID:
                    logger_kw["trace_id"] = value
            start_response(status, headers, exc_info)
            return response_body.append

        def runapp():
            appiter = self._app(environ, catching_start_response)
            response_body.extend(appiter)
            if hasattr(appiter, 'close'):
                appiter.close()

        start = time.time()
        runapp()
        body = b''.join(response_body)
        elapsed = time.time() - start
        logger_kw["delay"] = str(round(elapsed, 2))

        logger_kw.update(dict(
            method=environ['REQUEST_METHOD'].upper(),
            fullpath=environ["RAW_URI"],
            ip=logger_kw.get("forwarded_ip") or environ['REMOTE_ADDR']
        ))

        # 格式化日志
        local_log_format = LOG_FORMAT
        for key in LOG_FIELDS:
            if key not in logger_kw:
                local_log_format = local_log_format.replace("{%s} " % key, "").replace("{%s}" % key, "")

        logger.info(local_log_format.format(**logger_kw))

        return [body]


class GunicornApplication(Application):
    def __init__(self, app, options=None):
        assert isinstance(app, Flask)
        self.app = app
        self.options = options or {}
        super(GunicornApplication, self).__init__()

    def load_config(self):
        for key, value in six.iteritems(self.options):
            if key in self.cfg.settings and value is not None:
                self.cfg.set(key.lower(), value)

    def set_up_flask(self):
        # sqlalchemy.engine.base.Engine
        self.app.config.setdefault(
            "SQLALCHEMY_ECHO",
            self.options.get('sql_debug', False)
        )

        # add trace id
        class TraceableResponse(self.app.response_class):
            def __init__(self, *args, **kwargs):
                super(TraceableResponse, self).__init__(*args, **kwargs)
                self.set_trace_id()

            def set_trace_id(self):
                from .flask_trace import flask_current_trace_id

                self.headers.setdefault(TRACE_ID, flask_current_trace_id())

            @classmethod
            def force_type(cls, response, environ=None):
                res = super(TraceableResponse, cls).force_type(response, environ)
                res.set_trace_id()
                return res

        self.app.response_class = TraceableResponse

    def load(self):
        self.set_up_flask()
        return self.app


def init_logger():
    logging.getLogger('requests').setLevel(logging.ERROR)
    logging.getLogger('werkzeug').setLevel(logging.ERROR)
    logging.getLogger('tornado.access').setLevel(logging.ERROR)

    gunicorn_err = logging.getLogger('gunicorn.error')


class Runserver(Command):
    "run gunicorn server"

    def __init__(self, bind="0.0.0.0", port=4488, **ignore):
        self.default_bind, self.default_port = bind, port
        super(Runserver, self).__init__()

    def get_options(self):
        return [
            Option('--host', '-h', help='gunicorn bind host', default=self.default_bind),
            Option('--port', '-p', help='gunicorn bind port', default=str(self.default_port)),

            Option('--worker_class', help='gunicorn worker class', default="gthread"),
            Option('--capture_output', help='gunicorn log capture stderr stdout to stdout', default=True),
            Option('--enable_stdio_inheritance', help='gunicorn log immediately', default=True),
            Option('--accesslog', help='gunicorn access log; value:"" is disable.', default="-"),
            Option('--loglevel', help='gunicorn log level', default="info"),
            Option('--max_requests', help='gunicorn arg', default=0),
            Option('--workers', help='gunicorn worker num', default=get_process_num()),
            Option('--threads', help='gunicorn worker num', default=4),
            Option('--daemon', help='gunicorn daemon', default=False),
            Option('--timeout', help='gunicorn timeout', default=600),
            Option('--sql_debug', help='print sqlachemy sql', default=False),
            Option('--profile', help='print cProfile result. value:yes/no', default="no"),
        ]

    def __call__(self, app, **kwargs):
        # 处理日志
        from .log import set_log_format
        from .flask_trace import get_flask_id
        from werkzeug.contrib.profiler import ProfilerMiddleware

        for bool_field in [
            "capture_output",
            "enable_stdio_inheritance",
            "profile",
        ]:
            if bool_field not in kwargs:
                continue
            value = kwargs[bool_field]
            if isinstance(value, basestring):
                c_value = value.lower()
                if c_value == "false" or c_value == "no":
                    value = False
                elif c_value == "true" or c_value == "yes":
                    value = True
                else:
                    value = True
            kwargs[bool_field] = value

        if not logging.getLogger().handlers:
            # 设置默认日志处理
            set_log_format(
                logger=logging.getLogger(),  # 获取全局 logger
                id_getter=get_flask_id,
                level=getattr(logging, kwargs.get("loglevel", "info").upper()),
                enable_err2out=True,
            )

        app.raw_wsgi_app = app.wsgi_app

        if kwargs.pop("profile"):
            app.wsgi_app = ProfilerMiddleware(app.wsgi_app)

        if kwargs.pop("accesslog"):
            # 处理日志
            # app.after_request(after_request_log)
            app.wsgi_app = LogRequestMiddleware(app.wsgi_app)

        # 处理端口
        kwargs["bind"] = "%s:%s" % (kwargs.pop("host"), kwargs.pop("port"))

        server = GunicornApplication(app, kwargs)
        server.run()
