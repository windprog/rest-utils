#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Author  :   windpro
E-mail  :   windprog@gmail.com
Date    :   17/11/17
Desc    :   
"""
import uuid
import sys
import logging
import logging.config
from flask import Flask, g, request


def get_request_id(length=5):
    return uuid.uuid4().get_hex()[:length]


def flask_current_trace_id():
    if getattr(g, "trace_id", None):
        trace_id = g.trace_id
    else:
        g.trace_id = trace_id = get_request_id()
    return trace_id


def modify_log_record_obj(log_record):
    try:
        trace_id = flask_current_trace_id()
    except:
        trace_id = ""
    ip = ""
    try:
        if request.headers.getlist("X-Forwarded-For"):
            # 处理代理结果
            ip = request.headers.getlist("X-Forwarded-For")[0].split(',')[0].strip()
        else:
            ip = request.remote_addr
    except:
        pass
    log_record.trace_id = trace_id
    flask_name = "-%s" % ip if ip else ""
    if log_record.name != "root":
        flask_name = "-%s-%s" % (ip, log_record.name)
    log_record.flask_name = flask_name
    return log_record


class LevelFilter(logging.Filter):
    """
    Log filter to inject the current request id of the request under `log_record.request_id`
    """

    def __init__(self, lower=None, upper=None):
        """

        :param lower: 最小级别
        :param upper: 最大级别
        """
        super(LevelFilter, self).__init__()
        self.lower = lower
        self.upper = upper

    def filter(self, log_record):
        levelno = log_record.levelno

        if self.lower:
            if levelno < self.lower:
                return False
        if self.upper:
            if levelno > self.upper:
                return False
        return True


class RequestIDLogFilter(LevelFilter):
    def filter(self, log_record):
        ret = super(RequestIDLogFilter, self).filter(log_record)
        if not ret:
            return ret
        modify_log_record_obj(log_record)
        return True


def get_handler(stream, level, filter_):
    stdout_handler = logging.StreamHandler(stream)
    stdout_handler.setFormatter(
        logging.Formatter(
            fmt='%(asctime)s %(levelname)-7s [%(trace_id)s%(flask_name)s] [%(filename)s:%(lineno)d] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    )
    stdout_handler.addFilter(filter_)
    stdout_handler.setLevel(level=level)
    return stdout_handler


def set_default_flask_log(level=logging.INFO):
    global_logger = logging.getLogger()
    if global_logger.handlers:
        return
    global_logger.setLevel(level)
    global_logger.addHandler(get_handler(
        sys.stdout, level=level,
        filter_=RequestIDLogFilter()
    ))
    global_logger.addHandler(get_handler(
        sys.stderr, level=logging.ERROR,
        filter_=RequestIDLogFilter(upper=logging.ERROR)
    ))


if __name__ == '__main__':
    set_default_flask_log()
    set_default_flask_log()
    app = Flask(__name__)
    with app.app_context():
        logging.info("test")
        logging.info("test")
        logging.error("error")
