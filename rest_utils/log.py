#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Author  :   windpro
E-mail  :   windprog@gmail.com
Date    :   17/11/17
Desc    :   
"""
import sys
import logging


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
        logger,
        id_getter=lambda log: log.name,
        level=logging.INFO,
        enable_err2out=True,
        fmt='%(asctime)s %(levelname)-7s [%(id)s] [%(filename)s:%(lineno)d] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
):
    """
    ERROR日志打印到stderr里，可由enable_err2out控制是否输出到stdout里
    :param logger: logger 对象.通常以:logging.getLogger() 获取
    :param id_getter: 获取id的方式,默认为log名称
    :param level: 日志级别
    :param enable_err2out: 把ERROR日志打印到stdout里
    :param fmt: Formatter fmt
    :param datefmt: Formatter datefmt
    :return:
    """
    logger.setLevel(level)

    # 清空原有handler
    for handler in logger.handlers:
        logger.removeHandler(handler)
    # 添加handler
    logger.addHandler(get_handler(
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
    if not enable_err2out:
        # 打印在 stdout 里就不打印 stderr
        logger.addHandler(get_handler(
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
    from flask import Flask
    from flask_trace import get_flask_id

    app = Flask(__name__)
    set_log_format(logger=logging.getLogger(), id_getter=get_flask_id, enable_err2out=False)
    with app.app_context():
        # normal env
        logging.info("normal env info")
        logging.error("normal env error")

    with app.test_request_context():
        # request env
        logging.info("request env info")
        logging.error("request env error")
