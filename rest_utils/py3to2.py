#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Author  :   windpro
E-mail  :   windprog@gmail.com
Date    :   2018/2/1
Desc    :   https://github.com/timothycrosley/deprecated.pies/blob/develop/pies/overrides.py
corss python version 2.5-2.7 3.2~
"""
import sys
import abc

PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3
VERSION = sys.version_info

native_dict = dict
native_round = round
native_filter = filter
native_map = map
native_zip = zip
native_range = range
native_str = str
native_chr = chr
native_input = input
native_next = next
native_object = object


def with_metaclass(meta, *bases):
    """Enables use of meta classes across Python Versions. taken from jinja2/_compat.py.
    Use it like this::
        class BaseForm(object):
            pass
        class FormType(type):
            pass
        class Form(with_metaclass(FormType, BaseForm)):
            pass
    """

    class metaclass(meta):
        __call__ = type.__call__
        __init__ = type.__init__

        def __new__(cls, name, this_bases, d):
            if this_bases is None:
                return type.__new__(cls, name, (), d)
            return meta(name, bases, d)

    return metaclass('temporary_class', None, {})


def unmodified_isinstance(*bases):
    """When called in the form
    MyOverrideClass(unmodified_isinstance(BuiltInClass))
    it allows calls against passed in built in instances to pass even if there not a subclass
    """

    class UnmodifiedIsInstance(type):
        if sys.version_info[0] == 2 and sys.version_info[1] <= 6:

            @classmethod
            def __instancecheck__(cls, instance):
                if cls.__name__ in (str(base.__name__) for base in bases):
                    return isinstance(instance, bases)

                subclass = getattr(instance, '__class__', None)
                subtype = type(instance)
                instance_type = getattr(abc, '_InstanceType', None)
                if not instance_type:
                    class test_object:
                        pass

                    instance_type = type(test_object)
                if subtype is instance_type:
                    subtype = subclass
                if subtype is subclass or subclass is None:
                    return cls.__subclasscheck__(subtype)
                return (cls.__subclasscheck__(subclass) or cls.__subclasscheck__(subtype))
        else:
            @classmethod
            def __instancecheck__(cls, instance):
                if cls.__name__ in (str(base.__name__) for base in bases):
                    return isinstance(instance, bases)

                return type.__instancecheck__(cls, instance)

    return with_metaclass(UnmodifiedIsInstance, *bases)


common = [
    "integer_types",
    "iteritems",
    "iterkeys",
    "itervalues",
    # 'with_metaclass',
]

if PY3:
    import urllib
    import builtins
    from urllib import parse

    from collections import OrderedDict

    integer_types = (int,)


    def iteritems(collection):
        return collection.items()

    def itervalues(collection):
        return collection.values()

    def iterkeys(collection):
        return collection.keys()

    # urllib.quote = parse.quote
    # urllib.quote_plus = parse.quote_plus
    # urllib.unquote = parse.unquote
    # urllib.unquote_plus = parse.unquote_plus
    # urllib.urlencode = parse.urlencode
    if VERSION[1] < 2:
        def callable(entity):
            return hasattr(entity, '__call__')


        common.append('callable')

    __all__ = common + ['OrderedDict']
else:
    from itertools import ifilter as filter
    from itertools import imap as map
    from itertools import izip as zip
    from decimal import Decimal, ROUND_HALF_EVEN

    try:
        from collections import OrderedDict
    except ImportError:
        from ordereddict import OrderedDict

    import codecs

    str = unicode
    chr = unichr
    input = raw_input
    range = xrange
    integer_types = (int, long)


    # Reloading the sys module kills IPython's output printing.
    # import sys
    # stdout = sys.stdout
    # stderr = sys.stderr
    # reload(sys)
    # sys.stdout = stdout
    # sys.stderr = stderr
    # sys.setdefaultencoding('utf-8')

    def _create_not_allowed(name):
        def _not_allow(*args, **kwargs):
            raise NameError("name '{0}' is not defined".format(name))

        _not_allow.__name__ = name
        return _not_allow


    for removed in ('apply', 'cmp', 'coerce', 'execfile', 'raw_input', 'unpacks'):
        globals()[removed] = _create_not_allowed(removed)


    class _dict_view_base(object):
        __slots__ = ('_dictionary',)

        def __init__(self, dictionary):
            self._dictionary = dictionary

        def __repr__(self):
            return "{0}({1})".format(self.__class__.__name__, str(list(self.__iter__())))

        def __unicode__(self):
            return str(self.__repr__())

        def __str__(self):
            return str(self.__unicode__())


    class dict_keys(_dict_view_base):
        __slots__ = ()

        def __iter__(self):
            return self._dictionary.iterkeys()


    class dict_values(_dict_view_base):
        __slots__ = ()

        def __iter__(self):
            return self._dictionary.itervalues()


    class dict_items(_dict_view_base):
        __slots__ = ()

        def __iter__(self):
            return self._dictionary.iteritems()


    class dict(unmodified_isinstance(native_dict)):
        def has_key(self, *args, **kwargs):
            return AttributeError("'dict' object has no attribute 'has_key'")

        def items(self):
            return dict_items(self)

        def keys(self):
            return dict_keys(self)

        def values(self):
            return dict_values(self)


    def iteritems(collection):
        return dict_items(collection)

    def itervalues(collection):
        return dict_values(collection)

    def iterkeys(collection):
        return dict_keys(collection)


    def round(number, ndigits=None):
        return_int = False
        if ndigits is None:
            return_int = True
            ndigits = 0
        if hasattr(number, '__round__'):
            return number.__round__(ndigits)

        if ndigits < 0:
            raise NotImplementedError('negative ndigits not supported yet')
        # Python 2.6 doesn't support from_float.
        if sys.version_info[1] <= 6:
            return native_round(number, ndigits)
        exponent = Decimal('10') ** (-ndigits)
        d = Decimal.from_float(number).quantize(exponent,
            rounding=ROUND_HALF_EVEN)
        if return_int:
            return int(d)
        else:
            return float(d)


    def next(iterator):
        try:
            iterator.__next__()
        except Exception:
            native_next(iterator)


    class FixStr(type):
        def __new__(cls, name, bases, dct):
            if '__str__' in dct:
                dct['__unicode__'] = dct['__str__']
            dct['__str__'] = lambda self: self.__unicode__().encode('utf-8')
            return type.__new__(cls, name, bases, dct)

        if sys.version_info[1] <= 6:
            def __instancecheck__(cls, instance):
                if cls.__name__ == "object":
                    return isinstance(instance, native_object)

                subclass = getattr(instance, '__class__', None)
                subtype = type(instance)
                instance_type = getattr(abc, '_InstanceType', None)
                if not instance_type:
                    class test_object:
                        pass

                    instance_type = type(test_object)
                if subtype is instance_type:
                    subtype = subclass
                if subtype is subclass or subclass is None:
                    return cls.__subclasscheck__(subtype)
                return (cls.__subclasscheck__(subclass) or cls.__subclasscheck__(subtype))
        else:
            def __instancecheck__(cls, instance):
                if cls.__name__ == "object":
                    return isinstance(instance, native_object)
                return type.__instancecheck__(cls, instance)


    class object(with_metaclass(FixStr, object)):
        pass


    __all__ = common + ['round', 'dict', 'apply', 'cmp', 'coerce', 'execfile', 'raw_input', 'unpacks', 'str', 'chr',
        'input', 'range', 'filter', 'map', 'zip', 'object']
