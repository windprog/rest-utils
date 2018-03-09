#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Author  :   windpro
E-mail  :   windprog@gmail.com
Date    :   17/11/15
Desc    :   
"""
import common  # 实现引用上级目录
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand

from rest_utils import migrate_skip
from rest_utils.flask_engine import Runserver
from demo_app import app, db

manager = Manager(app)
migrate = Migrate(app, db)

# 数据库比对升级跳过指定的表
skip_list = [
    "demo_table",
]

migrate_skip(migrate, skip_list)

if __name__ == '__main__':
    manager.add_command('db', MigrateCommand)
    manager.add_command('runserver', Runserver(
        bind="0.0.0.0",
        port=4488
    ))
    manager.run()
