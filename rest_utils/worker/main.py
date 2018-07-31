#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Author  :   windpro
E-mail  :   windprog@gmail.com
Date    :   17/10/25
Desc    :   
"""
import logging
import os
import multiprocessing
import signal
from .util import ThreadMixin, CrontabThread

CPU_NUM = multiprocessing.cpu_count()


class ConfigCenter(CrontabThread):
    def __init__(self, interval=1, worker_num=CPU_NUM, fetcher_num=1, worker_class=None, fetcher_class=None):
        super(ConfigCenter, self).__init__(interval=interval)
        # 设置退出信号量
        self.setup_self_join()

        self.worker_class = worker_class
        self.worker_num = worker_num
        self.fetcher_class = fetcher_class
        self.fetcher_num = fetcher_num

        self.worker_list = [
            worker_class(total=self.worker_num, index=index)
            for index in range(self.worker_num)
        ]
        self.fetcher_list = [fetcher_class(self.worker_list) for _ in range(self.fetcher_num)]

    def wait_stop(self):
        logging.info("waiting fetcher and worker")
        for fetcher in self.fetcher_list:
            if fetcher.process.is_alive():
                fetcher.join()

        for worker in self.worker_list:
            if worker.process.is_alive():
                worker.join()
        logging.info("finish fetcher and worker")

    def join(self, timeout=None):
        self.wait_stop()
        logging.info("exiting config")
        super(ConfigCenter, self).join(timeout=timeout)
        logging.info("exited config")

    def start(self):
        for worker in self.worker_list:
            worker.start()

        for fetcher in self.fetcher_list:
            fetcher.start()

    def restart(self):
        for fetcher in self.fetcher_list:
            # 发送停止信号量
            pid = fetcher.process.pid
            os.kill(pid, signal.SIGINT)

        self.wait_stop()

        self.worker_list = [self.worker_class() for _ in range(self.worker_num)]
        self.fetcher_list = [self.fetcher_class() for _ in range(self.fetcher_num)]

        self.start()

    def run(self):
        # 检测配置和任务存活
        worker_alive = 0
        for worker in self.worker_list:
            if worker.process.is_alive():
                worker_alive += 1
        fetcher_alive = 0
        for fetcher in self.fetcher_list:
            if fetcher.process.is_alive():
                fetcher_alive += 1
        if worker_alive != self.worker_num or fetcher_alive != self.fetcher_num:
            logging.error("worker_num:%s fetcher_alive:%s. exiting program." % (
                str(worker_alive), str(fetcher_alive)
            ))
            self.wait_stop()
            # 设置标志位
            self.shutdown()
