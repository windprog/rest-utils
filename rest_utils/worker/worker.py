#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Author  :   windpro
E-mail  :   windprog@gmail.com
Date    :   17/10/25
Desc    :   
"""
from abc import ABCMeta, abstractmethod
import time
from multiprocessing import Queue as ProcessQueue
from multiprocessing import Process


def ignore_signal():
    import signal
    def on_sigterm(*ignore):
        pass

    signal.signal(signal.SIGTERM, on_sigterm)
    signal.signal(signal.SIGINT, on_sigterm)


class Worker(object):
    __metaclass__ = ABCMeta
    QUEUE_LEN = 10  # 最大队列长度
    TIMEOUT = 120

    def __init__(self, total, index):
        """

        :param total: 总worker数量
        :param index: 当前worker index
        """
        self.queue = ProcessQueue(self.QUEUE_LEN)
        self.process = Process(target=self.run_forever, args=())
        self.total, self.index = total, index

    def start(self):
        self.process.start()

    def feed(self, msg):
        """
        投喂数据，从fetch进程调用
        timeout 错误由 fetcher do_feed 捕获并重试
        :param msg:
        :return:
        """
        self.queue.put(msg, timeout=self.TIMEOUT)

    @abstractmethod
    def parse(self, msg):
        """
        worker进程使用
        :param msg:
        :return:
        """
        pass

    def run_forever(self):
        ignore_signal()
        while True:
            msg = self.queue.get()
            if msg is None:
                break
            self.parse(msg)

    def join(self):
        self.queue.put(None)
        self.process.join()


if __name__ == '__main__':
    class TestWorker(Worker):
        def parse(self, msg):
            time.sleep(1)
            print(msg)

        def run_forever(self):
            super(TestWorker, self).run_forever()
            print("finish")


    t = TestWorker(1, 0)
    t.start()
    t.feed("test")
    t.join()
