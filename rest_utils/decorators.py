# coding=utf-8

import os
import logging
import traceback
import datetime
import six
import time
import functools
import hashlib

from flask import jsonify, request, url_for, current_app, make_response, g


def cache_control(*directives):
    def decorator(f):
        @functools.wraps(f)
        def wrapped(*args, **kwargs):
            rv = f(*args, **kwargs)
            rv = make_response(rv)
            rv.headers['Cache-Control'] = ', '.join(directives)
            return rv

        return wrapped

    return decorator


def no_cache(f):
    return cache_control('no-cache', 'no-store', 'max-age=0')(f)


def etag(f):
    @functools.wraps(f)
    def wrapped(*args, **kwargs):
        # only for HEAD and GET requests
        assert request.method in ['HEAD', 'GET'], \
            '@etag is only supported for GET requests'
        rv = f(*args, **kwargs)
        rv = make_response(rv)
        etag = '"' + hashlib.md5(rv.get_data()).hexdigest() + '"'
        rv.headers['ETag'] = etag
        if_match = request.headers.get('If-Match')
        if_none_match = request.headers.get('If-None-Match')
        if if_match:
            etag_list = [tag.strip() for tag in if_match.split(',')]
            if etag not in etag_list and '*' not in etag_list:
                rv = precondition_failed()
        elif if_none_match:
            etag_list = [tag.strip() for tag in if_none_match.split(',')]
            if etag in etag_list or '*' in etag_list:
                rv = not_modified()
        return rv

    return wrapped


def not_modified():
    response = jsonify({
        'status': 304,
        'error': 'not modified'
    })
    response.status_code = 304
    return response


def precondition_failed():
    response = jsonify({
        'status': 412,
        'error': 'precondition failed'
    })
    response.status_code = 412
    return response


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
            logging.error('{module}.{func}({func_args_str}): {tb}'.format(
                module=six.get_function_globals(func).get('__name__', ''),
                func=func.__name__,
                tb=traceback.format_exc(),
                func_args_str=func_args_str,
            ))

    return execute


def log_exe_time(func):
    def execute(*args, **kwargs):
        ''' 修饰器代理函数 '''
        start = time.time()
        ret = func(*args, **kwargs)
        logging.info("{module}.{func} execute sec:{total_sec}".format(
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
