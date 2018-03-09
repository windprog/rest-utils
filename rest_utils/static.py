#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Author  :   windpro
E-mail  :   windprog@gmail.com
Date    :   2018/2/7
Desc    :   
"""

MSG_FORMAT = {
    10000: u'Undefined Exception',
    10001: u'Database Execution Error',
    10003: u'Resource not found.Collection:{collection} key:{key}.',
    10004: u'Resources already exists.table:{table} field:{field} value:{value}.',
    10007: u'Permission Denied; prompt:{prompt}',
    11000: u'Collection {collection} not exists.',
    11001: u'Method [{method}] not acceptable for resource type [{endpoint}].  Acceptable methods: [{support_methods}]',
    11002: u'Assertion Error; prompt:{prompt}',
    11003: u'Database Connection Error.',
    11004: u'Resources Constraint Failed.table:{table} field:{field} Not nullable',
    11005: u'Resources Constraint Failed.table:{table} field:{field} Not Default Value',
    21000: u"Relation between resource {collection} {key} and {sub_collection} {sub_key} not exists.",
    21001: u"Relation Resource Depend Other.",
    21002: u"Foreign key constraint fails.table:{table}",
    30000: u'Request Data Exception; prompt:{prompt}',
    31000: u'Unique check error; resource {collection} {key} count:{count}',
    31001: u'Content-type [{types}] not supported.',
    31002: u'request headers ACCEPT:{ACCEPT} Not Acceptable',
    31004: u'Filter definition error. Primary key count Not One.',
    30003: u"Token Not Found.",
    30004: u"Token Invalid.",
    30005: u"Token Expired.",
}

MSG_DETAILED = {
    10000: u'未知错误。',
    10001: u'数据库执行错误。',
    10003: u'资源不存在。',
    10004: u'资源已存在。',
    10007: u'操作资源的权限错误。',
    11000: u'资源表不存在。',
    11001: u'资源表访问行为限制。如限制GET',
    11002: u'断言异常。',
    11003: u'数据库连接异常。',
    11004: u'字段必须非空。',
    11005: u'字段没有默认值。',
    21000: u"两个资源关系不存在。",
    21001: u"删除的资源被依赖。",
    21002: u"外键依赖异常。",
    30000: u'非法数据。',
    31000: u'唯一的数据存在多个,无法继续操作,请检查数据库。',
    31001: u'headers Content-type类型不支持。',
    31002: u'headers ACCEPT类型不支持。',
    31004: u'当模型是唯一主键时才可使用filters限制资源,否则只能在在action filters callback返回None 拒绝该action。',
    30003: u"无法找到token",
    30004: u"token无效",
    30005: u"token失效",
}

HTTP_STATUS_CODE = {
    400: [
        10001,
        10004,
        11002,
        11004,
        11005,
        21001,
        21002,
        30000,
    ],
    403: [
        11001,
        10007,
        30003,
        30004,
        30005,
    ],
    404: [
        10003,
        11000,
        21000,
    ],
    406: [
        31002,
    ],
    415: [
        31001,
    ],
    500: [
        10000,
        11003,
        31000,
        31004,
    ]
}
