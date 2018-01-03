#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Author  :   windpro
E-mail  :   windprog@gmail.com
Date    :   2018/1/3
Desc    :   
"""
import uuid

from flask import g, request


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
