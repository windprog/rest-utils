#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Author  :   windpro
E-mail  :   windprog@gmail.com
Date    :   17/11/15
Desc    :   
"""
import os
import sys

project_path = os.path.abspath(os.path.join(
    os.path.dirname(__file__),
    '..',
))
if project_path not in sys.path:
    sys.path.append(project_path)
