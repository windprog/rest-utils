#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Author  :   windpro
E-mail  :   windprog@gmail.com
Date    :   17/11/17
Desc    :   
"""
import uuid
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


class RequestIDLogFilter(logging.Filter):
    """
    Log filter to inject the current request id of the request under `log_record.request_id`
    """

    def filter(self, log_record):
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
        if log_record.name == "root":
            log_record.name = "-%s" % ip if ip else ""
        else:
            log_record.name = "-%s-%s" % (ip, log_record.name)
        return log_record


# def init_flask_log():
# Setup logging
def init_flask_log(level=logging.INFO):
    global_logger = logging.getLogger()
    global_logger.setLevel(level)
    for h in global_logger.handlers:
        for f in h.filters:
            if isinstance(f, RequestIDLogFilter):
                logging.warning("Ready init logger")
                return
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter(
            fmt='%(asctime)s %(levelname)-7s [%(trace_id)s%(name)s] [%(filename)s:%(lineno)d] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    )
    handler.addFilter(RequestIDLogFilter())
    global_logger.addHandler(handler)


if __name__ == '__main__':
    init_flask_log()
    init_flask_log()
    app = Flask(__name__)
    with app.app_context():
        logging.info("test")
        logging.info("test")
        logging.info("test")
