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

from gunicorn.app.base import Application
from flask_script import Command, Option


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
        'worker_class': 'gevent',
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

        logger.info('"{method} {fullpath} HTTP/1.1" {status} {length} {res_content_type} {ip} {delay}'.format(
            method=environ['REQUEST_METHOD'].upper(),
            fullpath=environ["RAW_URI"],
            ip=logger_kw.get("forwarded_ip") or environ['REMOTE_ADDR'],
            **logger_kw
        ))

        return [body]


class GunicornApplication(Application):
    def __init__(self, app_generator, options=None):
        self.app_generator = app_generator
        self.options = options or {}
        super(GunicornApplication, self).__init__()

    def load_config(self):
        for key, value in six.iteritems(self.options):
            if key in self.cfg.settings and value is not None:
                self.cfg.set(key.lower(), value)

    def set_up_flask(self, app):
        from flask import Flask
        if isinstance(app, Flask):
            # sqlalchemy.engine.base.Engine
            app.config.setdefault(
                "SQLALCHEMY_ECHO",
                self.options.get('sql_debug', False)
            )

    def load(self):
        self.init_logger()
        app = self.app_generator()
        self.set_up_flask(app)
        return app

    def init_logger(self):
        logging.getLogger('requests').setLevel(logging.ERROR)
        logging.getLogger('werkzeug').setLevel(logging.ERROR)
        logging.getLogger('tornado.access').setLevel(logging.ERROR)


def run(app_generator, options):
    server = GunicornApplication(app_generator, options)
    sys.exit(server.run())


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
            Option('--profile', help='print cProfile result', default=False),

        ]

    def __call__(self, app, **kwargs):
        # 处理日志
        from .log import set_default_flask_log
        from werkzeug.contrib.profiler import ProfilerMiddleware

        for bool_field in [
            "capture_output",
            "enable_stdio_inheritance",
        ]:
            if bool_field not in kwargs:
                continue
            value = kwargs[bool_field]
            if isinstance(value, basestring):
                if value.lower() == "false":
                    value = False
                elif value.lower() == "true":
                    value = True
                else:
                    value = True
            kwargs[bool_field] = value

        set_default_flask_log(getattr(logging, kwargs.get("loglevel", "info").upper()))

        if kwargs.pop("accesslog"):
            # 处理日志
            app.after_request(after_request_log)

        # 处理端口
        kwargs["bind"] = "%s:%s" % (kwargs.pop("host"), kwargs.pop("port"))

        run_app = app

        if kwargs.pop("profile"):
            run_app = ProfilerMiddleware(app)

        run_app = LogRequestMiddleware(run_app)

        run(lambda: run_app, kwargs)
