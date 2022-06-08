#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Copyright (c) 2014 windpro

Author  :   windpro
E-mail  :   windprog@gmail.com
Date    :   14-12-1
Desc    :   
"""
import os
from setuptools import setup

__version__ = "1.2.5"
__author__ = "Windpro"
__author_email__ = "windprog@gmail.com"
__description__ = "Rest-Utils provides simple generation of Restful APIs for database models defined using SQLAlchemy (or Flask-SQLAlchemy). The generated APIs send and receive messages in JSON format. support gunicorn and multiline process worker. "
__title__ = 'Rest-Utils'
__url__ = "https://github.com/windprog/rest-utils"

req = os.path.join(os.path.dirname(__file__), 'requirements.txt')
with open(req) as f:
    install_requires = [line for line in f.read().split("\n") if line]

setup(
    name=__title__,
    version=__version__,
    description=__description__,
    url=__url__,
    author=__author__,
    author_email=__author_email__,
    packages=['rest_utils', 'rest_utils.worker', 'rest_utils.utils', 'rest_utils.libs', 'rest_utils.ma'],
    install_requires=install_requires,
    data_files=[(".", ['requirements.txt'])],  # save requirements.txt to install package
)
