#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Author  :   windpro
E-mail  :   windprog@gmail.com
Date    :   17/10/25
Desc    :   
"""
import signal
import threading
import time
from abc import ABCMeta, abstractmethod


class SleepMixin(object):
    def __init__(self):
        self._sam_cancelled = threading.Event()
        self.running = False

    def sleep(self, seconds):
        """
        设置睡眠，如果退出线程则立刻终止睡眠
        :param seconds:
        :return:
        """
        self._sam_cancelled.wait(seconds)

    def join(self):
        self._sam_cancelled.set()


class ThreadMixin(SleepMixin):
    def setup_self_join(self, args=(), kwargs={}):

        def on_sigterm(*ignore):
            self.join(*args, **kwargs)

        signal.signal(signal.SIGTERM, on_sigterm)
        signal.signal(signal.SIGINT, on_sigterm)

    def setup_thread_name(self, thread_name):
        self._serve_thread.setName(thread_name)

    def serve_async(self, thread_name=None, args=(), daemon=True):
        self._serve_thread = threading.Thread(target=self.serve_forever, args=args)
        if thread_name is not None:
            self.setup_thread_name(thread_name=thread_name)
        self._serve_thread.setDaemon(daemon)
        self._serve_thread.start()
        self.running = True

    def shutdown(self):
        self.running = False

    def join(self, timeout=None):
        super(ThreadMixin, self).join()
        self.shutdown()

        _serve_thread = getattr(self, '_serve_thread', None)
        if _serve_thread:
            _serve_thread.join(timeout=timeout)


class CrontabThread(ThreadMixin):
    __metaclass__ = ABCMeta

    def __init__(self, interval):
        self.interval = interval
        super(CrontabThread, self).__init__()

    @abstractmethod
    def run(self):
        pass

    def serve_forever(self):
        self.running = True
        while self.running:
            this_ts = time.time()
            self.run()
            next_ts = this_ts + self.interval
            cur_ts = time.time()
            if next_ts > cur_ts:
                self.sleep(next_ts - cur_ts)


def set_process_name(name):
    import setproctitle
    setproctitle.setproctitle(name)
