#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Author  :   windpro
E-mail  :   windprog@gmail.com
Date    :   17/10/25
Desc    :   
"""
from abc import ABCMeta, abstractmethod
import six

if six.PY2:
    from Queue import Full
    from multiprocessing.process import Process
else:
    from queue import Full
    from multiprocessing import Process
import logging


class Fetcher(object):
    __metaclass__ = ABCMeta

    def __init__(self, worker_list):
        from .worker import Worker
        self.worker_list = worker_list
        assert isinstance(self.worker_list, list)
        for worker in self.worker_list:
            assert isinstance(worker, Worker)
        self.process = Process(target=self.run_forever, args=())
        self.running = False

    def start(self):
        self.process.start()

    @abstractmethod
    def shutdown(self):
        # 处理进程关闭
        self.running = False

    def setup_shutdown(self):
        """
        设置优雅退出
        :return:
        """
        import signal
        def on_sigterm(*ignore):
            self.shutdown()

        signal.signal(signal.SIGTERM, on_sigterm)
        signal.signal(signal.SIGINT, on_sigterm)

    @abstractmethod
    def choose(self, msg):
        """
        选择进程的处理进程下标
        如：hash(msg) % len(self.worker_list)
        :param msg:
        :return:
        """
        pass

    def do_feed(self, msg):
        index = self.choose(msg)
        assert isinstance(index, int) and index < len(self.worker_list)
        while True:
            try:
                self.worker_list[index].feed(msg)
            except Full:
                p = self.worker_list[index].process
                assert isinstance(p, Process)
                # 队列满了重试发送
                logging.error("pid:%s worker is full. Please check the Thread blocking situation." % str(p.pid))
                continue
            break

    @abstractmethod
    def run_forever(self):
        """
        启动处理
        :return:
        """
        self.running = True

    def join(self):
        self.process.join()
