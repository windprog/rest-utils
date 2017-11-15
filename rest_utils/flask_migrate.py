#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Author  :   windpro
E-mail  :   windprog@gmail.com
Date    :   17/11/8
Desc    :   
"""


def migrate_skip(migrate, skip_list):
    @migrate.configure
    def configure_alembic(config):
        from alembic.autogenerate.compare import comparators

        @comparators.dispatch_for("schema")
        def _autogen_for_tables(autogen_context, upgrade_ops, schemas):
            # 处理跳过的表
            upgrade_ops.ops = [op for op in upgrade_ops.ops if op.table_name not in skip_list]

        return config
