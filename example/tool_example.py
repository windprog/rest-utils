#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Author  :   windpro
E-mail  :   windprog@gmail.com
Date    :   17/12/11
Desc    :   
"""
from rest_utils.process import Command


def run_ping():
    """
    运行命令例子
    :return:
    """
    cmd = ['ping', '-c', '10', 'www.qq.com']
    print cmd
    c = Command(arg=cmd)
    c.wait_kill(timeout=20)
    print c.finish
    print c.killed
    print repr(c.last_stdout)
    print repr(c.last_stderr)


if __name__ == '__main__':
    run_ping()
