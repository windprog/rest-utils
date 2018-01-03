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


def check_flask_env():
    try:
        request.environ
        return True
    except:
        return False


def flask_current_trace_id():
    if getattr(g, "trace_id", None):
        trace_id = g.trace_id
    else:
        g.trace_id = trace_id = get_request_id()
    return trace_id


def flask_current_client_ip():
    if getattr(g, "ip", None):
        return g.ip
    forwarded_ip = request.headers.getlist("X-Forwarded-For")
    if forwarded_ip:
        # 处理代理结果
        try:
            ip = forwarded_ip[0].split(',')[0].strip()
        except:
            ip = ""
    else:
        ip = request.remote_addr

    g.ip = ip
    return ip


def get_flask_id(log):
    if check_flask_env():
        trace_id = flask_current_trace_id()
        ip = flask_current_client_ip()

        return "-".join([
            item for item in [
                trace_id,
                ip,
                log.name if log.name != "root" else "",
            ] if item
        ])
    else:
        return log.name


class LevelFilter(logging.Filter):
    """
    Log filter to inject the current request id of the request under `log_record.request_id`
    """

    def __init__(self, id_getter, lower=logging.NOTSET, upper=logging.CRITICAL):
        """

        :param id_getter: 获取当前log的id，例如记录request id。默认为logger名
        :param lower: 最小值
        :param upper: 最大值
        """
        super(LevelFilter, self).__init__()
        self.lower = lower
        self.upper = upper
        self.id_getter = id_getter

    def filter(self, log_record):
        levelno = log_record.levelno

        if self.lower <= levelno <= self.upper:
            log_record.id = self.id_getter(log_record)
            return True
        return False


def get_handler(fmt, datefmt, stream, level, filter):
    stdout_handler = logging.StreamHandler(stream)
    stdout_handler.setFormatter(logging.Formatter(fmt=fmt, datefmt=datefmt))
    stdout_handler.addFilter(filter)
    stdout_handler.setLevel(level=level)
    return stdout_handler


def set_log_format(
        id_getter=lambda log: log.name,
        level=logging.INFO,
        enable_err2out=True,
        fmt='%(asctime)s %(levelname)-7s [%(id)s] [%(filename)s:%(lineno)d] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
):
    """
    ERROR日志打印到stderr里，可由enable_err2out控制是否输出到stdout里
    :param id_getter: 获取id的方式,默认为log名称
    :param level: 日志级别
    :param enable_err2out: 把ERROR日志打印到stdout里
    :param fmt: Formatter fmt
    :param datefmt: Formatter datefmt
    :return:
    """
    global_logger = logging.getLogger()
    global_logger.setLevel(level)

    # 清空原有handler
    for handler in global_logger.handlers:
        global_logger.removeHandler(handler)
    # 添加handler
    global_logger.addHandler(get_handler(
        fmt=fmt,
        datefmt=datefmt,
        stream=sys.stdout,
        level=level,
        filter=LevelFilter(
            id_getter=id_getter,
            lower=level,
            upper=logging.CRITICAL if enable_err2out else logging.WARNING,
        )
    ))
    global_logger.addHandler(get_handler(
        fmt=fmt,
        datefmt=datefmt,
        stream=sys.stderr,
        level=logging.ERROR,
        filter=LevelFilter(
            id_getter=id_getter,
            lower=logging.ERROR,
            upper=logging.CRITICAL,
        )
    ))


if __name__ == '__main__':
    app = Flask(__name__)
    set_log_format(get_flask_id, enable_err2out=False)
    with app.app_context():
        # normal env
        logging.info("normal env info")
        logging.error("normal env error")

    with app.test_request_context():
        # request env
        logging.info("request env info")
        logging.error("request env error")
