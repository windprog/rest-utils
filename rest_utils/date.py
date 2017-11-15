#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Author  :   windpro
E-mail  :   windprog@gmail.com
Date    :   17/9/26
Desc    :   
"""
import datetime
import time


def dt_str2dt(dt_str):
    return datetime.datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")


def date_str2dt(date_str):
    return datetime.datetime.strptime(date_str, "%Y-%m-%d")


def dt2date_str(dt):
    return dt.strftime("%Y-%m-%d")


def dt2dt_str(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def dt2ts(dt):
    return time.mktime(dt.timetuple())


def ts2dt(ts):
    return datetime.datetime.fromtimestamp(ts)
