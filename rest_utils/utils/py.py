#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Author  :   windpro
E-mail  :   windprog@gmail.com
Date    :   2018/3/6
Desc    :   
"""
import signal
import bisect
import hashlib
import socket
import six

long = six.integer_types[-1]

from six.moves import range as xrange

__all__ = [
    "get_all_class",
    "delay_initialization",
    "InstanceDescriptor",
    "ignore_signal",
    "ConsistentHashRing",
    "is_open",
    "get_ip",
    "prof_call",
    "get_system",
    "NullContext",
    "null_context",
]


def get_all_class(model, check_attr):
    model_list = []
    if model.__subclasses__():
        for submodel in model.__subclasses__():
            model_list.extend(get_all_class(submodel, check_attr))
    else:
        if getattr(model, check_attr, None):
            model_list.append(model)
    return model_list


def delay_initialization(callback=None):
    """
    延迟实例化生成器
    :param callback: 回调函数，用于生成args,kwargs，提供类初始化参数
    :return:
    """

    class ArgsInstanceDescriptor(object):
        """
        描述符
        """

        def __get__(self, instance, owner):
            v = getattr(owner, "__instance__", None)
            if not v:
                args, kwargs = callback() if callback else ((), {})
                v = owner(*args, **kwargs)  # 构造参数!
                owner.__instance__ = v

            return v

    return ArgsInstanceDescriptor()


class InstanceDescriptor(object):
    """
    描述符: 延迟实例化
    """

    def __get__(self, instance, owner):
        v = getattr(owner, "__instance__", None)
        if not v:
            v = owner()  # 构造参数!
            owner.__instance__ = v

        return v


def ignore_signal(signal_list=(signal.SIGTERM, signal.SIGINT)):
    """
    默认忽略：
    1、SIGTERM：Termiate信号
    2、SIGINT：ctrl+c关闭程序的时候
    :param signal_list:
    :return:
    """

    def on_signal(*ignore):
        # print 'child_process accept signal!', ignore
        pass

    for sig in signal_list:
        signal.signal(sig, on_signal)


class ConsistentHashRing(object):
    """
    Implement a consistent hashing ring.
    http://xiaorui.cc/2014/09/20/%E4%BD%BF%E7%94%A8hashring%E5%AE%9E%E7%8E%B0python%E4%B8%8B%E7%9A%84%E4%B8%80%E8%87%B4%E6%80%A7hash/
    http://techspot.zzzeek.org/2012/07/07/the-absolutely-simplest-consistent-hashing-example/
    """

    def __init__(self, replicas=100):
        """Create a new ConsistentHashRing.

        :param replicas: number of replicas.

        """
        self.replicas = replicas
        self._keys = []
        self._nodes = {}

    def _hash(self, key):
        """Given a string key, return a hash value."""

        return long(hashlib.md5(key.encode("utf-8")).hexdigest(), 16)

    def _repl_iterator(self, nodename):
        """Given a node name, return an iterable of replica hashes."""
        return (
            self._hash("%s:%s" % (nodename, i))
            for i in xrange(self.replicas)
        )

    def __setitem__(self, nodename, node):
        """Add a node, given its name.

        The given nodename is hashed
        among the number of replicas.

        """
        for hash_ in self._repl_iterator(nodename):
            if hash_ in self._nodes:
                raise ValueError("Node name %r is "
                                 "already present" % nodename)
            self._nodes[hash_] = node
            bisect.insort(self._keys, hash_)

    def __delitem__(self, nodename):
        """Remove a node, given its name."""

        for hash_ in self._repl_iterator(nodename):
            # will raise KeyError for nonexistent node name
            del self._nodes[hash_]
            index = bisect.bisect_left(self._keys, hash_)
            del self._keys[index]

    def __getitem__(self, key):
        """Return a node, given a key.

        The node replica with a hash value nearest
        but not less than that of the given
        name is returned.   If the hash of the
        given name is greater than the greatest
        hash, returns the lowest hashed node.

        """
        hash_ = self._hash(key)
        start = bisect.bisect(self._keys, hash_)
        if start == len(self._keys):
            start = 0
        return self._nodes[self._keys[start]]


def is_open(ip, port, timeout=2):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.settimeout(timeout)
        s.connect((ip, int(port)))
        s.shutdown(socket.SHUT_RDWR)  # 关闭读写
        s.close()  # 关闭连接
        return True
    except Exception as e:
        return False


def _get_ip_udp(ip):
    import socket
    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp.connect((ip, 8))
    return udp.getsockname()[0]


def _get_ip_hostname():
    import socket
    hostname = socket.getfqdn(socket.gethostname())
    ip = socket.gethostbyname(hostname)
    return ip


def get_ip(check_ip):
    import platform
    if platform.system().lower() == "windows":
        ip = _get_ip_hostname()
    else:
        ip = _get_ip_udp(check_ip)
    return ip


def prof_call(func, *args, **kw):
    from cProfile import Profile
    from pstats import Stats
    # 输出函数调用性能分析。
    prof = Profile(builtins=False)
    ret = prof.runcall(func, *args, **kw)

    Stats(prof).sort_stats("cumtime").print_stats()
    return ret


def get_system():
    import platform

    os = platform.system().lower()
    if os.startswith('cygwin'):
        os = 'windows'
    return os


class NullContext(object):

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


null_context = NullContext()

if __name__ == '__main__':
    cr = ConsistentHashRing(100)

    cr["node1"] = "host1"
    cr["node2"] = "host2"

    print(cr["some key"])
    print(cr["test key"])

    print('socket ', ['127.0.0.1', 44686], 'is', is_open('127.0.0.1', 44686))
