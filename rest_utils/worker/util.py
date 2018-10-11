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
from multiprocessing import Process


def register_signal(on_sigterm):
    signal.signal(signal.SIGTERM, on_sigterm)
    signal.signal(signal.SIGINT, on_sigterm)


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

        register_signal(on_sigterm)

    def setup_thread_name(self, thread_name):
        self._serve_thread.setName(thread_name)

    def serve_async(self, thread_name=None, args=(), daemon=True):
        self._serve_thread = threading.Thread(target=self.serve_forever, args=args)
        if thread_name is not None:
            self.setup_thread_name(thread_name=thread_name)
        self._serve_thread.setDaemon(daemon)
        self.running = True
        self._serve_thread.start()

    def shutdown(self):
        self.running = False

    def join(self, timeout=None):
        super(ThreadMixin, self).join()
        self.shutdown()

        _serve_thread = getattr(self, '_serve_thread', None)
        if _serve_thread:
            _serve_thread.join(timeout=timeout)


class ProcessMixin(SleepMixin):
    def run_forever_decorator(self, func, process_name):
        def wrapper(*args, **kwargs):
            if process_name:
                set_process_name(process_name)
            self.running = True
            register_signal(self.process_join)
            return func(*args, **kwargs)

        return wrapper

    def serve_async(self, process_name=None, args=()):
        run_forever = self.run_forever_decorator(self.serve_forever, process_name)
        self._process = Process(target=run_forever, args=args)
        self._process.start()

    def shutdown(self):
        self.running = False

    def process_join(self, *args, **kwargs):
        super(ProcessMixin, self).join()
        self.shutdown()

    def join(self, timeout=None):
        self._process.join(timeout=timeout)

    def setup_self_join(self, args=(), kwargs={}):
        def on_sigterm(*ignore):
            self.join(*args, **kwargs)

        register_signal(on_sigterm)


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


class CrontabProcess(ProcessMixin):
    __metaclass__ = ABCMeta

    def __init__(self, interval):
        self.interval = interval
        super(CrontabProcess, self).__init__()

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


if __name__ == '__main__':
    def test_process_crontab():
        class TestCrontab(CrontabProcess):
            def run(self):
                print("running")

            def shutdown(self):
                super(TestCrontab, self).shutdown()
                print("exiting process")

        job = TestCrontab(1)
        job.setup_self_join()
        job.serve_async('test_name')
        job.join()
        print("main process exit")


    def test_thread_crontab():
        class TestCrontab(CrontabThread):
            def run(self):
                print("running")

            def shutdown(self):
                super(TestCrontab, self).shutdown()
                print("exiting thread")

        job = TestCrontab(1)
        job.setup_self_join()
        job.serve_async('test_name')
        for i in range(10):
            print("main thread wating:%s" % i)
            time.sleep(10)

    test_process_crontab()
