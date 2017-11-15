#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Author  :   windpro
E-mail  :   windprog@gmail.com
Date    :   17/10/25
Desc    :   
"""
import os
import logging
import traceback
import datetime
import six
import time


def catch_exc(func):
    '''
    异常捕获修饰器
    捕获函数执行抛出的异常并在日志输出函数名、异常详情

    func - 被修饰函数
    '''

    def get_arg_str(data):
        if isinstance(data, six.string_types[0]):
            ret = '"%s"' % data
        elif isinstance(data, (int, float)):
            ret = str(data)
        elif data is None:
            ret = "None"
        else:
            ret = repr(data)
        if len(ret) > 10:
            return ret[:10] + '...'
        else:
            return ret

    def execute(*args, **kwargs):
        ''' 修饰器代理函数 '''
        try:
            return func(*args, **kwargs)
        except Exception:
            arg_str = ",".join([get_arg_str(arg) for arg in args])
            kwargs_str = ",".join(["%s=%s" % (k, get_arg_str(v)) for k, v in kwargs.items()])
            func_args_str = ",".join([item for item in [arg_str, kwargs_str] if item])
            logging.error('{pid}:{module}.{func}({func_args_str}): {tb}'.format(
                module=six.get_function_globals(func).get('__name__', ''),
                func=func.__name__,
                tb=traceback.format_exc(),
                date=datetime.datetime.now().strftime("%m-%d %H:%M"),
                func_args_str=func_args_str,
                pid=os.getpid()
            ))

    return execute


def log_exe_time(func):
    def execute(*args, **kwargs):
        ''' 修饰器代理函数 '''
        start = time.time()
        ret = func(*args, **kwargs)
        logging.info("{pid}:{module}.{func} execute sec:{total_sec}".format(
            pid=os.getpid(),
            date=datetime.datetime.now().strftime("%m-%d %H:%M"),
            module=six.get_function_globals(func).get('__name__', ''),
            func=func.__name__,
            total_sec=str(round(time.time() - start, 2))
        ))
        return ret

    return execute


if __name__ == '__main__':
    @catch_exc
    def rai(arg, kwargs_str):
        print("test error")
        error


    rai("ccc", kwargs_str=1.2)
