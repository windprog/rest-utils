#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Author  :   windpro
E-mail  :   windprog@gmail.com
Date    :   16/7/13
Desc    :
跨平台超时执行
"""
import time
import subprocess
import os
import signal
import threading
import logging

from rest_utils.utils import get_system
from rest_utils.utils import null_context

IS_WINDOWS = get_system() == "windows"
logger = logging.getLogger(__name__)


def set_uonblock(f):
    """
    不支持windows
    :return:
    """
    from fcntl import fcntl, F_GETFL, F_SETFL
    import os

    # set the O_NONBLOCK flag of p.stdout file descriptor:
    flags = fcntl(f, F_GETFL)  # get current p.stdout flags
    fcntl(f, F_SETFL, flags | os.O_NONBLOCK)


class Command(object):
    """
    使用例子：
    cmd = ['ping', '-c', '10', 'www.qq.com']
    c = Command(arg=cmd)
    c.wait_kill(timeout=20)
    print c.finish
    print c.killed
    print repr(c.last_stdout)
    print repr(c.last_stderr)
    """
    def __init__(self, arg, shell=False, lock=True, output_count=1000):
        """
        call shell-command and either return its output or kill it
        if it doesn't normally exit within timeout seconds and return None
        Support: linux, windows
        :param arg: 命令,支持字符串和列表
        :param shell:是否以shell的形式执行
        :param lock: 是否启用线程锁
        :param output_count: 内存中保存的输出数量
        """
        if IS_WINDOWS:
            raise Exception("Not Support Windows!")
        # 字段初始化
        self._raw_arg = arg
        if shell:
            if isinstance(arg, basestring):
                arg_list = [arg]
            else:
                arg_list = [u" ".join(arg)]
        else:
            if isinstance(arg, basestring):
                arg = arg.split(' ')
            arg_list = [item for item in arg if item]
        self.arg_list = arg_list
        self._shell = shell
        self.output_count = output_count
        # 状态锁
        self._lock = threading.Lock() if lock else null_context

        # 环境变量
        self._env = my_env = os.environ.copy()
        # my_env["PATH"] += ":/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
        # 针对终端输出，使用unknown可能会出错，手动指定
        my_env["TERM"] = "xterm"

        # 执行命令
        self.process = subprocess.Popen(
            self.arg_list,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=shell,
            env=self._env,
        )
        self.start = time.time()
        self.is_nonblock = False
        self._set_nonblock()

        # 临时变量
        self._terminate = False  # 是否杀死
        self._success = False  # 是否执行成功
        self._output = {
            "stdout": [
                "", ""  # 最开始的输出，最后的输出
            ],
            "stderr": [
                "", ""
            ],
        }

    @property
    def last_stdout(self):
        """
        进程最后stdout输出
        :return:
        """
        self._append_data()
        return self._output["stdout"][1]

    @property
    def last_stderr(self):
        """
        进程最后stderr输出
        :return:
        """
        self._append_data()
        return self._output["stderr"][1]

    @property
    def first_stdout(self):
        """
        进程最开始stdout输出
        :return:
        """
        self._append_data()
        return self._output["stdout"][0]

    @property
    def first_stderr(self):
        """
        进程最开始stderr输出
        :return:
        """
        self._append_data()
        return self._output["stderr"][0]

    def _set_nonblock(self):
        """
        设置非阻塞
        :return:
        """
        if IS_WINDOWS:
            return
        for fd in [
            self.process.stdout,
            self.process.stderr,
        ]:
            set_uonblock(fd)
        self.is_nonblock = True

    def _append_data(self):
        """
        不支持windows
        :return:
        """

        def set_data(data):
            if not data:
                return
            first = self._output[attr][0]
            last = self._output[attr][1]
            if len(first) < self.output_count:
                first += data[:self.output_count - len(first)]
            if len(data) >= self.output_count:
                last = data[-self.output_count:]
            else:
                last = last[-(self.output_count - len(data)):] + data
            self._output[attr][0] = first
            self._output[attr][1] = last

        for attr in [
            'stdout',
            'stderr',
        ]:
            fd = getattr(self.process, attr)
            if self.is_nonblock:
                try:
                    set_data(fd.read())
                except IOError:
                    continue
            else:
                if self.process.poll() is not None:
                    # 执行完毕
                    set_data(fd.read())  # windows 需要同步等待执行完毕

    @property
    def finish(self):
        """
        进程是否终止
        :return:
        """
        return self._terminate or self._success

    @property
    def killed(self):
        """
        进程是否被杀死
        :return:
        """
        return self._terminate

    @property
    def pid(self):
        return self.process.pid

    def kill(self):
        """
        杀掉进程
        :return:
        """

        def after_kill():
            self._terminate = True
            self._append_data()

        with self._lock:
            if self._terminate:
                raise Exception("Don't kill again!")
            if self.process.poll() is not None:
                # 进程已经死掉了
                logger.info("pid:{pid} process_ready_death".format(pid=self.process.pid))
                after_kill()
                return
            if not IS_WINDOWS:
                os.kill(self.process.pid, signal.SIGKILL)
                os.waitpid(-1, os.WNOHANG)
            else:
                # kill windows process
                subprocess.call(['taskkill', '/F', '/T', '/PID', str(self.process.pid)])
            after_kill()
            logger.info("pid:{pid} kill_process".format(pid=self.process.pid))

    def get_status(self):
        """
        返回进程执行状态
        :return: 'running'：执行中；
                 'executed'：执行完毕
                 'killed'：进程已被杀死
        """
        with self._lock:
            if self._success:
                return 'executed'
            if self._terminate:
                return 'killed'
            self._append_data()
            if self.process.poll() is None:
                return 'running'
            else:
                self._success = True
                return 'executed'

    def timeout_kill(self, timeout=5 * 60):
        """
        :param timeout: 超时时间，秒
        :return: True:执行完成 False: 执行失败 None:执行中
        """
        status = self.get_status()
        if status == 'executed':
            return True
        elif status == 'killed':
            return False
        elif status == 'running':
            now = time.time()
            if now - self.start >= timeout:
                self.kill()
                return False
        return None

    def wait_kill(self, timeout=5 * 60, one_time=0.2):
        while self.timeout_kill(timeout=timeout) is None:
            time.sleep(one_time)


if __name__ == '__main__':
    cmd = ['ping', '-c', '10', 'www.baidu.com']
    print(cmd)
    c = Command(arg=cmd)
    c.wait_kill(timeout=20)
    print(c.finish)
    print(c.killed)
    print(repr(c.last_stdout))
    print(repr(c.last_stderr))
