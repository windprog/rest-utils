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

from rest_utils import __version__, __author__, __author_email__, __description__, __url__, __title__

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
