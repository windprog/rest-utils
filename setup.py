#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Copyright (c) 2014 windpro

Author  :   windpro
E-mail  :   windprog@gmail.com
Date    :   14-12-1
Desc    :   
"""
from setuptools import setup

__version__ = "0.1.0"
__author__ = "windprog"
__author_email__ = "windprog@gmail.com"
__description__ = "gunicorn wrapper. support worker"
__title__ = 'rest-utils'
__url__ = "https://github.com/windprog/rest-utils"

try:
    INSTALL_REQUIRES = [r for r in open('requirements.txt').read().split('\n') if len(r) > 0]
except:
    INSTALL_REQUIRES = []

setup(
    name=__title__,
    version=__version__,
    description=__description__,
    url=__url__,
    author=__author__,
    author_email=__author_email__,
    packages=['rest_utils', 'rest_utils.worker'],
    install_requires=INSTALL_REQUIRES
)
