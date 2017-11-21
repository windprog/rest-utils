#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Author  :   windpro
E-mail  :   windprog@gmail.com
Date    :   17/11/8
Desc    :   
"""
import six
import sys
import multiprocessing
import logging

from gunicorn.app.base import Application
from flask_script import Manager, Command, Option

logger = logging.getLogger(__name__)


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

    def __init__(self, app, bind="0.0.0.0", port=4488):
        self.app = app
        self.default_bind, self.default_port = bind, port
        super(Runserver, self).__init__()

    def get_options(self):
        return [
            Option('--worker_class', help='gunicorn worker class', default="gevent"),
            Option('--capture_output', help='gunicorn log capture stderr stdout to stdout', default=True),
            Option('--enable_stdio_inheritance', help='gunicorn log immediately', default=True),
            Option('--accesslog', help='gunicorn access log; value:"" is disable.', default="-"),
            Option('--loglevel', help='gunicorn log level', default="info"),
            Option('--max_requests', help='gunicorn arg', default=2000),
            Option('--workers', help='gunicorn worker num', default=get_process_num()),
            Option('--daemon', help='gunicorn daemon', default=False),
            Option('--timeout', help='gunicorn timeout', default=600),
            Option('--sql_debug', help='print sqlachemy sql', default=False),
            Option('--bind', help='gunicorn bind addr. example:127.0.0.1:8080',
                default="%s:%s" % (
                    str(self.default_bind), str(self.default_port)
                )
            ),
        ]

    def run(self, **kwargs):
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

        # 处理日志
        from log import init_flask_log
        init_flask_log(getattr(logging, kwargs.get("loglevel", "info").upper()))

        if kwargs.pop("accesslog"):
            # 处理日志
            from flask import request

            @self.app.after_request
            def after_request_log(res):
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

        run(lambda: self.app, kwargs)
