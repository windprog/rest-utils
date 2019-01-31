#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Author  :   windpro
E-mail  :   windprog@gmail.com
Date    :   2019/1/31
Desc    :   pip 7.0.1
"""
import os
from pip.req import parse_requirements
from pip.download import PipSession

req = os.path.join(os.path.dirname(__file__), 'requirements.txt')
install_reqs = parse_requirements(req, session=PipSession())
install_requires = [str(ir.req) for ir in install_reqs]

with open(req, "w+") as f:
    f.write("\n".join(install_requires) + "\n")
